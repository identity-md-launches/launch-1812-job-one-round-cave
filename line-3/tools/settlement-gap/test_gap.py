import contextlib
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location('gap_test', HERE / 'gap.py')
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)


class GapTests(unittest.TestCase):
    def setUp(self):
        self.raw = (HERE / 'demo-plan.json').read_bytes()
        self.plan = json.loads(self.raw)
        self.pin = hashlib.sha256(self.raw).hexdigest()

    def review(self, plan):
        raw = json.dumps(plan).encode()
        return g.review_bytes(raw, hashlib.sha256(raw).hexdigest())

    def cli(self, raw, pin=None):
        path = Path('test/scratch/settlement-gap/plan.json')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        with contextlib.redirect_stdout(io.StringIO()) as out:
            code = g.main(['--plan', str(path), '--sha256', pin or hashlib.sha256(raw).hexdigest()])
        return code, json.loads(out.getvalue())

    def test_real_zto_demo(self):
        r = g.review_bytes(self.raw, self.pin)
        self.assertTrue(r['accepted'])
        self.assertEqual(r['comparisons'][0]['observedBlockGap'], 3817)
        self.assertEqual(r['comparisons'][0]['minimumBlockGap'], 3800)
        self.assertTrue(r['orderReview']['batch']['accepted'])

    def test_inclusive_threshold(self):
        self.plan['minimumBlockGaps'] = [3817]
        self.assertTrue(self.review(self.plan)['accepted'])
        self.plan['minimumBlockGaps'] = [3818]
        r = self.review(self.plan)
        self.assertFalse(r['accepted'])
        self.assertTrue(r['orderReview']['accepted'])
        self.assertEqual(r['state'], 'gap_review_required')
        self.assertEqual(self.cli(json.dumps(self.plan).encode())[0], 1)

    def test_zero_still_requires_order(self):
        self.plan['minimumBlockGaps'] = [0]
        self.assertTrue(self.review(self.plan)['accepted'])
        self.plan['order']['sequence'].reverse()
        r = self.review(self.plan)
        self.assertFalse(r['accepted'])
        self.assertFalse(r['gapChecked'])

    def test_bad_gap_before_evidence(self):
        for value in (None, {}, [], [1, 2], [True], [False], [-1], [1000001], [1.0], ['1']):
            with self.subTest(value=value):
                plan = dict(self.plan, minimumBlockGaps=value)
                with patch.object(g.o.b, 'review', side_effect=AssertionError('read')):
                    with self.assertRaises(g.Error):
                        self.review(plan)

    def test_envelope(self):
        for value in (None, [], {}, dict(self.plan, version=True), dict(self.plan, version=2),
                      dict(self.plan, ignored=True)):
            with self.subTest(value=value), self.assertRaises(g.Error):
                self.review(value)

    def test_entire_order_validated_before_reads(self):
        for mutate in ('extra', 'duplicate', 'policy', 'path'):
            plan = copy.deepcopy(self.plan)
            order = plan['order']
            if mutate == 'extra':
                order['extra'] = 1
            elif mutate == 'duplicate':
                order['sequence'][1] = order['sequence'][0].upper().replace('0X', '0x')
            elif mutate == 'policy':
                order['batch']['items'][1]['policy']['requireFinalized'] = 1
            else:
                order['batch']['items'][1]['evidence'] = '../outside'
            with self.subTest(mutate=mutate), patch.object(g.o.b, 'review', side_effect=AssertionError('read')):
                with self.assertRaises(g.Error):
                    self.review(plan)

    def test_pin_precedes_parse(self):
        with patch.object(g.o.b.k.p.s, 'strict_json', side_effect=AssertionError('parse')):
            r = g.review_bytes(b'not json', self.pin)
        self.assertEqual(r['state'], 'plan_pin_mismatch')
        self.assertFalse(r['evidenceChecked'])

    def test_changed_gap_needs_new_pin(self):
        self.plan['minimumBlockGaps'] = [0]
        code, r = self.cli(json.dumps(self.plan).encode(), self.pin)
        self.assertEqual(code, 1)
        self.assertFalse(r['gapChecked'])

    def test_evidence_pin_failure_blocks_gap(self):
        self.plan['order']['batch']['items'][0]['sha256'] = 'a' * 64
        r = self.review(self.plan)
        self.assertFalse(r['accepted'])
        self.assertFalse(r['gapChecked'])
        self.assertTrue(r['evidenceChecked'])

    def test_missing_evidence(self):
        self.plan['order']['batch']['items'][0]['evidence'] = 'test/scratch/settlement-gap/missing.json'
        code, r = self.cli(json.dumps(self.plan).encode())
        self.assertEqual(code, 2)
        self.assertEqual(r['state'], 'input_error')
        self.assertFalse(r['gapChecked'])

    def test_duplicate_json_and_nonfinite(self):
        for raw in (b'{"version":1,"version":1}', b'NaN', b'{"x": Infinity}', b'\xff'):
            self.assertEqual(self.cli(raw)[0], 2)

    def test_bounds(self):
        with self.assertRaises(g.Error):
            g.review_bytes(b' ' * 90001, self.pin)
        with self.assertRaises(g.Error):
            g.review_bytes(bytearray(self.raw), self.pin)
        self.plan['minimumBlockGaps'] = [1000000]
        self.assertFalse(self.review(self.plan)['accepted'])

    def test_bad_pin_precedes_file_read(self):
        with patch.object(g.o.b.k, 'load_bytes', side_effect=AssertionError('read')):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(g.main(['--plan', 'anything', '--sha256', 'bad']), 2)

    def test_cli_missing_overrides_paths(self):
        for args in ([], ['--plan', 'missing'], ['--demo', '--sha256', self.pin],
                     ['--demo', '--plan', 'missing']):
            with self.subTest(args=args), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(g.main(args), 2)
        for path in ('/outside', '../outside', '.hidden', 'a//b', 'a/./b'):
            with self.subTest(path=path), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(g.main(['--plan', path, '--sha256', self.pin]), 2)

    def test_offline_immutable(self):
        files = [HERE/'demo-plan.json', HERE/'demo-plan.sha256'] + [
            Path(i['evidence']) for i in self.plan['order']['batch']['items']]
        before = [p.read_bytes() for p in files]
        with patch.object(g.o.b.k.p.s.RPC, 'call', side_effect=AssertionError('network')):
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(g.main(['--demo']), 0)
        self.assertTrue(json.loads(out.getvalue())['accepted'])
        self.assertLess(len(out.getvalue().encode()), 100000)
        self.assertEqual(before, [p.read_bytes() for p in files])

    def test_same_block_gap_zero_and_multiple_pairs(self):
        # Only arithmetic is mocked here; full evidence is exercised in the demo.
        txs = self.plan['order']['sequence']
        tx3 = '0x' + 'e' * 64
        item = copy.deepcopy(self.plan['order']['batch']['items'][1])
        item['policy']['transactionHash'] = tx3
        self.plan['order']['batch']['items'].append(item)
        self.plan['order']['sequence'].append(tx3)
        self.plan['minimumBlockGaps'] = [0, 1]
        order = {'accepted': True, 'evidenceChecked': True, 'positions': [
            {'transactionHash': txs[0], 'blockNumber': 100},
            {'transactionHash': txs[1], 'blockNumber': 100},
            {'transactionHash': tx3, 'blockNumber': 101}]}
        with patch.object(g.o, 'review_bytes', return_value=order):
            r = self.review(self.plan)
            self.assertTrue(r['accepted'])
            self.assertEqual([x['observedBlockGap'] for x in r['comparisons']], [0, 1])
            self.plan['minimumBlockGaps'] = [1, 0]
            r = self.review(self.plan)
            self.assertFalse(r['accepted'])
            self.assertEqual([x['meetsMinimum'] for x in r['comparisons']], [False, True])


if __name__ == '__main__':
    unittest.main()
