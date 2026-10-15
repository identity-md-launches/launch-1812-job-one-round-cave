"""Intent mismatches, full replay and offline file/CLI boundaries."""
import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch

M = runpy.run_path(str(Path(__file__).with_name('match.py')))
SAMPLE = 'line-1/tools/snapshot-integer/live-zto.json'
BLOCK = 'line-1/tools/snapshot-select/live-block.json'
METHOD = 'eth_call'
PARAMS = '[{"to":"0xd782bdea4ef02a0bd391eb9089470c8080f0a68e","data":"0x18160ddd"},"latest"]'


class RequestMatchTests(unittest.TestCase):
    def setUp(self):
        Path('test/scratch').mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir='test/scratch')
        self.directory = Path(self.temporary.name).resolve().relative_to(Path.cwd())
        self.addCleanup(self.temporary.cleanup)

    def fixture(self, value, name='snapshot.json'):
        path = self.directory / name
        path.write_text(json.dumps(value), encoding='utf-8')
        return str(path)

    def cli(self, path=SAMPLE, method=METHOD, params=PARAMS):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = M['main']([path, '--method', method, '--params', params])
        return code, out.getvalue(), err.getvalue()

    def test_real_zto_is_offline_and_immutable(self):
        before = Path(SAMPLE).read_bytes()
        with patch('urllib.request.OpenerDirector.open', side_effect=AssertionError('network')):
            code, out, err = self.cli()
        report = json.loads(out)
        self.assertEqual((code, err), (0, ''))
        self.assertTrue(report['matched'])
        self.assertEqual(report['differences'], [])
        self.assertEqual(report['expected_request_sha256'], report['observed_request_sha256'])
        self.assertNotIn('result', report)
        self.assertNotIn('response', report)
        self.assertEqual(Path(SAMPLE).read_bytes(), before)
        self.assertLessEqual(len(out.encode('ascii')), 100000)

    def test_real_block(self):
        with patch('urllib.request.OpenerDirector.open', side_effect=AssertionError('network')):
            code, out, err = self.cli(BLOCK, 'eth_getBlockByNumber', '["finalized",false]')
        self.assertEqual((code, err), (0, ''))
        self.assertTrue(json.loads(out)['matched'])

    def test_reordered_object_keys_and_json_spacing_match(self):
        params = '[ { "data": "0x18160ddd", "to": "0xd782bdea4ef02a0bd391eb9089470c8080f0a68e" }, "latest" ]'
        self.assertEqual(self.cli(params=params)[0], 0)

    def test_wrong_selector_token_tag_and_method(self):
        trials = [
            (METHOD, PARAMS.replace('0x18160ddd', '0x313ce567'), '/params/0/data'),
            (METHOD, PARAMS.replace('0xd782bdea4ef02a0bd391eb9089470c8080f0a68e',
                                   '0xd34a99bc0f67ae1bbd63c660e6d0b0dd03e263b7'), '/params/0/to'),
            (METHOD, PARAMS.replace('latest', 'finalized'), '/params/1'),
            ('eth_chainId', '[]', '/method'),
        ]
        for method, params, pointer in trials:
            with self.subTest(pointer=pointer):
                code, out, err = self.cli(method=method, params=params)
                report = json.loads(out)
                self.assertEqual((code, err), (1, ''))
                self.assertFalse(report['matched'])
                self.assertIn(pointer, [item['path'] for item in report['differences']])
                self.assertNotEqual(report['expected_request_sha256'], report['observed_request_sha256'])

    def test_hex_case_is_literal(self):
        code, out, _ = self.cli(params=PARAMS.replace('0x18160ddd', '0x18160DDD'))
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(out)['differences'][0]['path'], '/params/0/data')

    def test_edit_request_without_response_change_is_detected(self):
        snapshot = json.loads(Path(SAMPLE).read_text())
        snapshot['request']['params'][1] = 'finalized'
        path = self.fixture(snapshot)
        # The inherited response-only checksum still passes after this edit.
        M['B']['verify_snapshot'](path)
        code, out, _ = self.cli(path)
        self.assertEqual(code, 1)
        self.assertFalse(json.loads(out)['matched'])

    def test_invalid_expected_request_is_rejected_before_open(self):
        trials = [
            ('eth_sendRawTransaction', '[]'), ('eth_sign', '[]'),
            (METHOD, '{"not":"array"}'), (METHOD, PARAMS[:-1]),
            (METHOD, PARAMS.replace('"data":', '"to":"duplicate","data":')),
            ('eth_getBlockByNumber', '["finalized",0]'),
            ('eth_getBlockByNumber', '["finalized",0.0]'),
            ('eth_getBlockByNumber', '["finalized",NaN]'),
            ('eth_getBlockByNumber', '["finalized",Infinity]'),
            ('eth_getBlockByNumber', '[[],false]'),
        ]
        with patch('os.open', side_effect=AssertionError('input opened')):
            for method, params in trials:
                with self.subTest(method=method, params=params):
                    code, out, err = self.cli(method=method, params=params)
                    self.assertEqual((code, out), (1, ''))
                    self.assertTrue(err.startswith('snapshot-request-match:'))

    def test_type_sensitive_comparison(self):
        for a, b in ((False, 0), (True, 1), (1, 1.0), ('1', 1)):
            changes = M['differences']({'params': [a]}, {'params': [b]})
            self.assertEqual(changes[0]['path'], '/params/0')
            self.assertEqual(changes[0]['kind'], 'type')

    def test_pointer_escapes_and_missing_fields(self):
        changes = M['differences']({'a/b~': [1, 2], 'gone': True}, {'a/b~': [1], 'new': None})
        self.assertEqual([row['path'] for row in changes], ['/a~1b~0/1', '/gone', '/new'])
        self.assertEqual([row['kind'] for row in changes], ['missing', 'missing', 'unexpected'])

    def test_params_and_complete_request_limits(self):
        for params in (' ' * 16385, '["' + '\u00e9' * 8192 + '"]', '[' * 2000 + ']' * 2000):
            code, out, _ = self.cli(params=params)
            self.assertEqual((code, out), (1, ''))
        # Valid expected shape, but the complete envelope is over its bound.
        params = '["0x' + 'a' * 16320 + '",false]'
        self.assertLess(len(params.encode()), 16384)
        code, out, _ = self.cli(method='eth_getBlockByNumber', params=params)
        self.assertEqual((code, out), (1, ''))

    def test_oversized_observed_request_is_refused(self):
        snapshot = json.loads(Path(SAMPLE).read_text())
        snapshot['request']['params'][1] = '0x' + 'a' * 17000
        path = self.fixture(snapshot)
        M['B']['verify_snapshot'](path)
        code, out, err = self.cli(path)
        self.assertEqual((code, out), (1, ''))
        self.assertIn('complete request exceeds', err)

    def test_checksum_and_envelope_validation_precede_report(self):
        original = json.loads(Path(SAMPLE).read_text())
        mutations = []
        changed = copy.deepcopy(original)
        changed['response']['result'] = '0x' + 'f' * 64
        mutations.append(changed)
        changed = copy.deepcopy(original)
        changed['response'] = {'jsonrpc': '2.0', 'id': 1,
                               'error': {'code': -32000, 'message': 'test-only refusal'}}
        mutations.append(changed)
        changed = copy.deepcopy(original)
        changed['request']['id'] = True
        mutations.append(changed)
        changed = copy.deepcopy(original)
        changed['response']['id'] = 2
        mutations.append(changed)
        changed = copy.deepcopy(original)
        changed['extra'] = True
        mutations.append(changed)
        for value in mutations:
            code, out, err = self.cli(self.fixture(value))
            self.assertEqual((code, out), (1, ''))
            self.assertTrue(err)

    def test_strict_snapshot_json(self):
        path = self.directory / 'bad.json'
        for raw in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}', '{'):
            path.write_text(raw)
            code, out, _ = self.cli(str(path))
            self.assertEqual((code, out), (1, ''))

    def test_path_and_input_bounds(self):
        link = self.directory / 'link.json'
        link.symlink_to(Path(SAMPLE).resolve())
        oversized = self.directory / 'large.json'
        oversized.write_bytes(b' ' * (M['B']['MAX_RESPONSE'] + M['B']['MAX_REQUEST'] + 1))
        for path in ('../outside', '/outside', '.hidden', str(self.directory), str(link), str(oversized)):
            code, out, err = self.cli(path)
            self.assertEqual((code, out), (1, ''))
            self.assertTrue(err)

    def test_both_expectations_are_mandatory(self):
        for args in ([SAMPLE], [SAMPLE, '--method', METHOD], [SAMPLE, '--params', PARAMS]):
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as exc:
                M['main'](args)
            self.assertEqual(exc.exception.code, 2)

    def test_output_bound(self):
        with self.assertRaises(M['MatchError']):
            M['render']({'value': 'x' * 100000})

    def test_consistently_resealed_fabrication_is_not_authenticated(self):
        snapshot = json.loads(Path(SAMPLE).read_text())
        snapshot['response']['result'] = '0x' + format(42, '064x')
        raw = json.dumps(snapshot['response'], sort_keys=True, separators=(',', ':'),
                         ensure_ascii=False).encode('utf-8')
        snapshot['response_sha256'] = hashlib.sha256(raw).hexdigest()
        code, out, _ = self.cli(self.fixture(snapshot))
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(out)['matched'])


if __name__ == '__main__':
    unittest.main()
