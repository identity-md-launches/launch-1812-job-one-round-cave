#!/usr/bin/env python3
"""Check a saved Ethereum snapshot against an explicit intended read, offline."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys

B = runpy.run_path(str(Path(__file__).resolve().parents[1] /
                       'bounded-rpc-snapshot' / 'snapshot.py'))
MAX_REQUEST = B['MAX_REQUEST']
MAX_OUTPUT = 100_000


class MatchError(ValueError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode('ascii')


def request_bytes(request):
    raw = canonical(request)
    if len(raw) > MAX_REQUEST:
        raise MatchError('complete request exceeds 16384 bytes')
    return raw


def expected_request(method, params_text):
    """The caller supplies intent; never derive it from the candidate snapshot."""
    if type(method) is not str or len(method) > 128:
        raise MatchError('expected method must be a string of at most 128 characters')
    if type(params_text) is not str or len(params_text.encode('utf-8')) > MAX_REQUEST:
        raise MatchError('expected params exceed 16384 UTF-8 bytes')
    params = B['parse_json'](params_text)
    B['validate_request'](method, params)
    request = {'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}
    request_bytes(request)
    return request


def differences(expected, observed):
    """Exact JSON comparison, including types, with paths into the request."""
    result = []

    def visit(wanted, found, path):
        if type(wanted) is not type(found):
            result.append({'path': path, 'kind': 'type',
                           'expected': wanted, 'observed': found})
        elif type(wanted) is dict:
            for key in sorted(wanted.keys() | found.keys()):
                child = path + '/' + key.replace('~', '~0').replace('/', '~1')
                if key not in wanted:
                    result.append({'path': child, 'kind': 'unexpected',
                                   'observed': found[key]})
                elif key not in found:
                    result.append({'path': child, 'kind': 'missing',
                                   'expected': wanted[key]})
                else:
                    visit(wanted[key], found[key], child)
        elif type(wanted) is list:
            for index in range(max(len(wanted), len(found))):
                child = path + '/' + str(index)
                if index >= len(wanted):
                    result.append({'path': child, 'kind': 'unexpected',
                                   'observed': found[index]})
                elif index >= len(found):
                    result.append({'path': child, 'kind': 'missing',
                                   'expected': wanted[index]})
                else:
                    visit(wanted[index], found[index], child)
        elif wanted != found:
            result.append({'path': path, 'kind': 'value',
                           'expected': wanted, 'observed': found})

    visit(expected, observed, '')
    return result


def review(snapshot_path, method, params_text):
    # Check independent intent before opening the evidence. Full inherited replay
    # checks its response checksum; this tool never interprets or emits the result.
    expected = expected_request(method, params_text)
    snapshot = B['verify_snapshot'](snapshot_path)
    observed = snapshot['request']
    expected_raw, observed_raw = request_bytes(expected), request_bytes(observed)
    changes = differences(expected, observed)
    return {
        'schema': 'line1-snapshot-request-match-v1',
        'matched': not changes,
        'expected_request': expected,
        'observed_request': observed,
        'expected_request_sha256': hashlib.sha256(expected_raw).hexdigest(),
        'observed_request_sha256': hashlib.sha256(observed_raw).hexdigest(),
        'differences': changes,
        'response_sha256': snapshot['response_sha256'],
        'meaning': 'Exact intended-read comparison of a validated saved snapshot; '
                   'not proof that this request produced the response, '
                   'Ethereum state, or freshness.',
    }


def render(report):
    raw = canonical(report) + b'\n'
    if len(raw) > MAX_OUTPUT:
        raise MatchError('request-match report exceeds 100000 bytes')
    return raw.decode('ascii')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('snapshot', help='visible relative workspace snapshot path')
    parser.add_argument('--method', required=True, help='independently chosen expected read method')
    parser.add_argument('--params', required=True, help='independently chosen expected JSON array')
    args = parser.parse_args(argv)
    try:
        report = review(args.snapshot, args.method, args.params)
        sys.stdout.write(render(report))
        return 0 if report['matched'] else 1
    except (MatchError, B['SnapshotError'], ValueError, OSError, RecursionError,
            TypeError, OverflowError) as exc:
        print('snapshot-request-match: ' + str(exc)[:1000], file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
