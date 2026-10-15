"""Source binding checks against historical ZTO and published EIP-712 fixtures."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

import source_witness as tool

HERE = Path(__file__).resolve().parent
ZTO = '0xf33e2506e5c103f98dbfe3feb6d4b87d55f1fad4e423dbaa8462465ff4ab9774'
MAIL = '0xbe609aee343fb3c4b28e1df9e632fca64fcfaede20f02e86244efddf30957bd2'
EDGE = '0xbf1f9acedd3f9924aafba0d1b362a4bb33ab5c7fa4855b930ed2ededc2ce9ba6'


def fixture(name):
    return json.loads((HERE / name).read_bytes())


class BindingTests(unittest.TestCase):
    def test_historical_real_zto_source_and_trace(self):
        report = tool.review(fixture('zto-payment.json'), fixture('zto-trace.json'), ZTO)
        self.assertTrue(report['accepted'])
        self.assertTrue(report['sourceTypedDataChecked'])
        self.assertEqual((report['sourceNodesChecked'], report['hashesChecked']), (12, 7))

    def test_published_ether_mail_with_nested_structs_and_mixed_case_addresses(self):
        report = tool.review(fixture('ether-mail.json'), fixture('ether-mail-trace.json'), MAIL)
        self.assertTrue(report['accepted'])
        self.assertEqual(report['sourceNodesChecked'], 13)

    def test_recursive_struct_nested_array_and_empty_array_schema(self):
        report = tool.review(fixture('edge-data.json'), fixture('edge-trace.json'), EDGE)
        self.assertTrue(report['accepted'])
        self.assertEqual(report['sourceNodesChecked'], 21)

    def test_source_token_substitution_rejected_even_with_valid_witness(self):
        source = fixture('zto-payment.json')
        source['message']['token'] = '0xd34a99bc0f67ae1bbd63c660e6d0b0dd03e263b7'
        result = tool.review(source, fixture('zto-trace.json'), ZTO)
        self.assertFalse(result['accepted'])
        self.assertTrue(result['witnessValid'])
        self.assertTrue(result['matchesExpected'])
        self.assertEqual(result['differences'],
                         [{'path': '/message/token', 'reason': 'atomic encoded word differs'}])

    def test_source_amount_and_domain_change(self):
        source = fixture('zto-payment.json')
        source['message']['minimumRaw'] = str(int(source['message']['minimumRaw']) + 1)
        source['domain']['chainId'] = 2
        result = tool.review(source, fixture('zto-trace.json'), ZTO)
        self.assertEqual({d['path'] for d in result['differences']},
                         {'/domain/chainId', '/message/minimumRaw'})

    def test_source_dynamic_change(self):
        source = fixture('ether-mail.json')
        source['message']['contents'] = 'Hello, Eve!'
        result = tool.review(source, fixture('ether-mail-trace.json'), MAIL)
        self.assertEqual(result['differences'],
                         [{'path': '/message/contents', 'reason': 'dynamic bytes differ'}])

    def test_source_field_order_change(self):
        source = fixture('zto-payment.json')
        fields = source['types']['PaymentEvidence']
        fields[0], fields[1] = fields[1], fields[0]
        result = tool.review(source, fixture('zto-trace.json'), ZTO)
        self.assertFalse(result['accepted'])
        self.assertIn('/message', [d['path'] for d in result['differences']])

    def test_empty_array_dependency_schema_change(self):
        source = fixture('edge-data.json')
        source['types']['Pod'][0]['name'] = 'different'
        result = tool.review(source, fixture('edge-trace.json'), EDGE)
        self.assertFalse(result['accepted'])
        self.assertIn('/message', [d['path'] for d in result['differences']])

    def test_array_order_and_length_changes(self):
        source = fixture('edge-data.json')
        source['message']['nested'] = [[2, 1], [3, 4], [5, 6]]
        result = tool.review(source, fixture('edge-trace.json'), EDGE)
        self.assertFalse(result['accepted'])
        self.assertEqual({d['path'] for d in result['differences']},
                         {'/message/nested', '/message/nested/0/0', '/message/nested/0/1',
                          '/message/nested/2', '/message/nested/2/0', '/message/nested/2/1'})

    def test_expected_digest_is_separate_gate(self):
        result = tool.review(fixture('zto-payment.json'), fixture('zto-trace.json'), MAIL)
        self.assertFalse(result['accepted'])
        self.assertFalse(result['matchesExpected'])
        self.assertTrue(result['sourceMatchesWitness'])

    def test_unused_source_declaration_fails_closed(self):
        source = fixture('zto-payment.json')
        source['types']['Unseen'] = [{'name': 'x', 'type': 'uint8'}]
        with self.assertRaisesRegex(ValueError, 'absent'):
            tool.review(source, fixture('zto-trace.json'), ZTO)

    def test_unsafe_number_must_be_decimal_string(self):
        source = fixture('zto-payment.json')
        source['message']['minimumRaw'] = 166357571280020680094504
        with self.assertRaisesRegex(ValueError, 'unsafe JSON numeric literal'):
            tool.review(source, fixture('zto-trace.json'), ZTO)
        source['message']['minimumRaw'] = '0x233a43130efdb61e3328'
        self.assertTrue(tool.review(source, fixture('zto-trace.json'), ZTO)['accepted'])

    def test_malformed_source_rejected(self):
        source = fixture('zto-payment.json')
        source['message']['extra'] = 1
        with self.assertRaisesRegex(ValueError, 'fields differ'):
            tool.review(source, fixture('zto-trace.json'), ZTO)
        source = fixture('zto-payment.json')
        source['types']['PaymentEvidence'][0]['type'] = 'uint7'
        with self.assertRaisesRegex(ValueError, 'unknown field type'):
            tool.review(source, fixture('zto-trace.json'), ZTO)

    def test_input_objects_are_unchanged(self):
        source, trace = fixture('zto-payment.json'), fixture('zto-trace.json')
        before = copy.deepcopy((source, trace))
        tool.review(source, trace, ZTO)
        self.assertEqual((source, trace), before)

    def test_cli_success_and_digest_mismatch(self):
        cmd = [sys.executable, '-B', str(HERE/'source_witness.py'),
               str(HERE/'zto-payment.json'), str(HERE/'zto-trace.json'), '--expect']
        for expected, exit_code in [(ZTO, 0), (MAIL, 1), ('0x1', 2)]:
            result = subprocess.run(cmd + [expected], capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, exit_code, result.stderr)
            if exit_code == 2:
                self.assertEqual(result.stdout, '')
            else:
                self.assertEqual(json.loads(result.stdout)['accepted'], exit_code == 0)


if __name__ == '__main__':
    unittest.main()
