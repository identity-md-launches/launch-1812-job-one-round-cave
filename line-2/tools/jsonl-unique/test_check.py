"""Regression checks for explicit cross-row uniqueness; no network needed."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import socket
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('unique_check', Path(__file__).with_name('check.py'))
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)

class Reader:
    def __init__(self, files):
        self.files, self.reads = files, []
    def read_bytes(self, name):
        self.reads.append(name)
        return self.files[name]

class UniqueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reader, cls.framing, cls.source, cls.engine, cls.rules = check.dependencies()

    def review(self, data, pointers=['/id'], contract=b'{"type":"object"}', **pins):
        self.capture = Reader({'c':contract, 'd':data})
        return check.inspect(self.capture, self.framing, self.source, self.engine,
                             self.rules, 'c', 'd', pointers, **pins)

    def test_unique_values(self):
        report=self.review(b'{"id":1}\n{"id":2}\n')
        self.assertTrue(report['valid'])
        self.assertEqual(self.capture.reads, ['c','d'])

    def test_duplicate_tracks_first_not_previous(self):
        r=self.review(b'{"id":"x"}\n{"id":"x"}\n{"id":"x"}')
        self.assertFalse(r['valid'])
        self.assertTrue(r['structural']['valid'])
        self.assertEqual([e['first']['line'] for e in r['uniqueness']['errors']], [1,1])

    def test_numeric_equivalence_and_boolean_separation(self):
        r=self.review(b'1\ntrue\n"1"\nnull\n1.0\n10e-1', [''], b'{"type":"number"}')
        self.assertEqual([e['line'] for e in r['uniqueness']['errors']], [5,6])
        self.assertEqual([e['first']['line'] for e in r['uniqueness']['errors']], [1,1])

    def test_exact_decimal_tokens_avoid_float_rounding(self):
        r=self.review(b'9007199254740992.0\n9007199254740993.0\n0.10000000000000000001\n0.1', [''], b'{"type":"number"}')
        self.assertTrue(r['valid'])
        self.assertFalse(self.review(b'-0\n0.0', [''], b'{"type":"number"}')['valid'])

    def test_null_is_value_missing_is_error(self):
        r=self.review(b'{"id":null}\n{}\n{"id":null}')
        self.assertEqual([e['kind'] for e in r['uniqueness']['errors']], ['missing_value','duplicate_value'])

    def test_nested_escaped_array_pointers(self):
        data=b'{"a/b~":[{"x":1}]}\n{"a/b~":[{"x":1}]}'
        r=self.review(data, ['/a~1b~0/0/x'])
        e=r['uniqueness']['errors'][0]
        self.assertEqual(e['kind'],'duplicate_value')
        span=e['document_source']['value']
        self.assertEqual(data[span['start']['byte_offset']:span['end']['byte_offset']], b'1')
        r=self.review(data, ['/a~1b~0/01/x'])
        self.assertEqual(r['uniqueness']['errors'][0]['kind'], 'missing_value')

    def test_deep_missing_anchors_nearest_existing(self):
        r=self.review(b'{"a":{}}\n{}', ['/a/b/c'])
        self.assertEqual([e['anchor_pointer'] for e in r['uniqueness']['errors']], ['/a',''])

    def test_containers_rejected(self):
        r=self.review(b'{"id":[]}\n{"id":{}}')
        self.assertEqual([e['kind'] for e in r['uniqueness']['errors']], ['non_scalar','non_scalar'])

    def test_malformed_recovery_and_structurally_invalid_rows_checked(self):
        r=self.review(b'{"id":1}\n{\n{"id":1}', contract=b'{"type":"object","required":["other"],"properties":{"other":{"type":"string"}}}')
        self.assertFalse(r['valid'])
        self.assertEqual(r['uniqueness']['skipped_malformed_lines'], [2])
        self.assertEqual(r['uniqueness']['errors'][0]['line'],3)
        self.assertEqual(r['structural']['summary']['structural_errors'],2)

    def test_unicode_crlf_and_escaped_string_equality(self):
        data='{"id":"日"}\r\n\t{"id":"\\u65e5"}\r\n'.encode()
        r=self.review(data)
        e=r['uniqueness']['errors'][0]
        for loc, expected in ((e['document_source'],b'"\\u65e5"'), (e['first']['document_source'],'"日"'.encode())):
            span=loc['value']
            self.assertEqual(data[span['start']['byte_offset']:span['end']['byte_offset']], expected)
            self.assertEqual(data.decode()[span['start']['char_offset']:span['end']['char_offset']].encode(), expected)
        self.assertEqual(e['document_source']['value']['start']['line'],2)

    def test_extreme_numeric_exponent_rejects_without_rounding(self):
        r=self.review(b'1e-9999999999999999999999999999999\n0', [''], b'{"type":"number"}')
        self.assertFalse(r['valid'])
        self.assertEqual(r['uniqueness']['errors'][0]['kind'], 'unsupported_number')
        self.assertEqual(r['uniqueness']['error_count'], 1)

    def test_independent_pointers_not_composite_keys(self):
        r=self.review(b'{"id":1,"name":"a"}\n{"id":2,"name":"a"}', ['/id','/name'])
        self.assertEqual(r['uniqueness']['errors'][0]['pointer'],'/name')

    def test_invalid_pointer_and_limits_precede_input(self):
        for pointers in ([], ['/id','/id'], ['id'], ['/~'], ['/~2'], ['/'+ 'x'*1025], ['/'+str(i) for i in range(17)]):
            with self.subTest(pointers=pointers), self.assertRaises(ValueError):
                self.review(b'{}', pointers)
            self.assertEqual(self.capture.reads,[])
        for p in ('', '/~01', '//', '/-'):
            check.pointers_checked([p])

    def test_pins_fail_before_parse(self):
        raw=b'{"id":1}'
        r=self.review(raw, document_sha256=hashlib.sha256(raw).hexdigest())
        self.assertTrue(r['valid'])
        with self.assertRaisesRegex(ValueError,'SHA-256 mismatch'):
            self.review(b'{', document_sha256=hashlib.sha256(raw).hexdigest())

    def test_same_path_captured_once(self):
        reader=Reader({'same':b'{"type":"object"}'})
        r=check.inspect(reader,self.framing,self.source,self.engine,self.rules,'same','same',['/type'])
        self.assertTrue(r['valid'])
        self.assertEqual(reader.reads,['same'])

    def test_output_overflow_no_partial_report(self):
        out,err=io.StringIO(),io.StringIO()
        deps=(self.reader,self.framing,self.source,self.engine,self.rules)
        r=self.review(b'{"id":1}')
        with patch.object(check,'dependencies',return_value=deps), patch.object(check,'inspect',return_value=r), patch.object(self.framing,'MAX_OUTPUT_BYTES',100), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            status=check.main(['c','d','--unique','/id'])
        self.assertEqual(status,2)
        self.assertEqual(out.getvalue(),'')
        self.assertFalse(json.loads(err.getvalue())['complete'])

    def test_cli_codes_and_source_immutability(self):
        deps=(self.reader,self.framing,self.source,self.engine,self.rules)
        for data, expected in ((b'{"id":1}',0),(b'{"id":1}\n{"id":1}',1),(b'{\n{"id":1}',2)):
            r=self.review(data)
            out,err=io.StringIO(),io.StringIO()
            with patch.object(check,'dependencies',return_value=deps), patch.object(check,'inspect',return_value=r), contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
                status=check.main(['c','d','--unique','/id'])
            self.assertEqual(status,expected)
            self.assertEqual(err.getvalue(),'')
            self.assertEqual(json.loads(out.getvalue()),r)
            self.assertEqual(self.capture.files['d'],data)

    def test_real_saved_zto_policy_offline(self):
        with patch.object(socket,'socket',side_effect=AssertionError('network forbidden')):
            r=check.inspect(self.reader,self.framing,self.source,self.engine,self.rules,
                'shared/payment-evidence/policy.contract.json','line-2/tools/jsonl-contract/zto-policy.jsonl',['/tx'])
        self.assertTrue(r['valid'])

    def test_boundary_refusals(self):
        for path in ('../outside','.hidden','/outside'):
            with self.assertRaises((ValueError,OSError)):
                check.inspect(self.reader,self.framing,self.source,self.engine,self.rules,
                    'line-2/tools/json-contract/report.contract.json',path,['/id'])

if __name__=='__main__':
    unittest.main(verbosity=2)
