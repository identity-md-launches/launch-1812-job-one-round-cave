"""Cross-line gates over real retained ZTO evidence; no transport."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

import witness_payment as tool
from check import load, witness

HERE = Path(__file__).resolve().parent
DOMAIN = {'chainId': 1, 'name': 'Read-only Payment Evidence', 'version': '1'}
DIGEST = '0x41d9999db383e39c78be45661d68307592ad1b8da2fcace128efcfa5e4e29d2c'


class WitnessPaymentTests(unittest.TestCase):
    def setUp(self):
        self.sample = load(HERE/'example.transcript.json')
        self.policy = load(HERE/'example.policy.json')
        self.client = load(HERE/'example.typed-data.json')
        self.trace = tool.read_workspace(HERE/'example.source-witness.json')

    def review(self, digest=DIGEST, domain=None, primary='PaymentEvidence'):
        return tool.review(self.sample, self.policy, self.client, self.trace,
                           DOMAIN if domain is None else domain, primary, digest)

    def test_real_zto_all_gates_and_no_transport(self):
        with patch.object(witness.settlement.urllib.request, 'build_opener', side_effect=AssertionError('network')):
            result = self.review()
        self.assertTrue(result['accepted'])
        self.assertTrue(result['sourceWitnessReview']['sourceTypedDataChecked'])
        self.assertEqual(result['sourceWitnessReview']['hashesChecked'], 7)
        self.assertFalse(result['paymentReview']['providerAuthenticated'])

    def test_source_token_substitution_with_unchanged_valid_witness(self):
        self.client['message']['token'] = '0xd34a99bc0f67ae1bbd63c660e6d0b0dd03e263b7'
        result = self.review()
        self.assertFalse(result['accepted'])
        self.assertTrue(result['sourceWitnessReview']['witnessValid'])
        self.assertEqual(result['sourceWitnessReview']['differences'][0]['path'], '/message/token')

    def test_valid_witness_cannot_override_payment_failure(self):
        # A retained source/witness pair still agrees, but its independent domain does not.
        result = self.review(domain={**DOMAIN, 'chainId': 2})
        self.assertTrue(result['sourceWitnessReview']['accepted'])
        self.assertFalse(result['paymentReview']['accepted'])
        self.assertFalse(result['accepted'])

    def test_unmet_settlement_policy_cannot_be_hidden_by_valid_witness(self):
        self.policy['confirmations'] = 1000000
        self.sample['policy']['confirmations'] = 1000000
        self.assertTrue(tool.witness_review(self.client, self.trace, DIGEST)['accepted'])
        # The inherited replayer rejects unused reads after its early refusal.
        with self.assertRaises(ValueError):
            self.review()

    def test_expected_digest_is_mandatory_and_independent(self):
        with self.assertRaises(ValueError):
            self.review(digest=None)
        self.assertFalse(self.review(digest='0xbe609aee343fb3c4b28e1df9e632fca64fcfaede20f02e86244efddf30957bd2')['accepted'])

    def test_damaged_witness_refuses(self):
        self.trace['envelope']['preimage'] = '0x1901'
        with self.assertRaises(ValueError):
            self.review()

    def test_witness_cannot_replace_independent_policy(self):
        self.sample['policy']['minimum_raw'] = '1'
        with self.assertRaises(ValueError):
            self.review()

    def test_large_numeric_literal_refuses(self):
        self.client['message']['minimumRaw'] = int(self.client['message']['minimumRaw'])
        with self.assertRaises(ValueError):
            self.review()

    def test_input_immutability(self):
        before = copy.deepcopy((self.sample, self.policy, self.client, self.trace))
        self.review()
        self.assertEqual((self.sample, self.policy, self.client, self.trace), before)

    def test_complete_output_limit(self):
        with self.assertRaises(ValueError):
            tool.render({'data': 'x'*100000})

    def test_cli_success_and_missing_witness(self):
        args = [sys.executable, '-B', str(HERE/'witness_payment.py'),
                str(HERE/'example.transcript.json'), str(HERE/'example.policy.json'),
                str(HERE/'example.typed-data.json'), str(HERE/'example.source-witness.json'),
                '--chain-id', '1', '--name', DOMAIN['name'], '--version', '1',
                '--primary-type', 'PaymentEvidence', '--no-verifier', '--expect-digest', DIGEST]
        done = subprocess.run(args, capture_output=True, text=True, timeout=30)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertTrue(json.loads(done.stdout)['accepted'])
        args[6] = 'missing-witness.json'
        done = subprocess.run(args, capture_output=True, text=True, timeout=30)
        self.assertEqual(done.returncode, 2, done.stderr)
        self.assertFalse(json.loads(done.stdout)['accepted'])


if __name__ == '__main__':
    unittest.main()
