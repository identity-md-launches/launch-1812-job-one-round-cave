#!/usr/bin/env python3
"""Require historical payment review and independently hashed source-witness agreement."""
import argparse
import json

from precision_payment import review as payment_review
from check import load
from source_witness import review as witness_review
from hash_witness import read_workspace

MAX_OUTPUT = 100_000


def render(report):
    raw = json.dumps(report, indent=2, ensure_ascii=True, allow_nan=False) + '\n'
    if len(raw.encode('ascii')) > MAX_OUTPUT:
        raise ValueError('complete witness payment report exceeds 100000 bytes')
    return raw


def review(sample, policy, client, trace, domain, primary, expected_digest):
    if expected_digest is None:
        raise ValueError('independently retained digest required')
    # The supplied witness is checked as supplied. Never regenerate or repair it.
    witness = witness_review(client, trace, expected_digest)
    payment = payment_review(sample, policy, client, domain, primary, expected_digest)
    accepted = witness['accepted'] is True and payment['accepted'] is True
    report = {
        'accepted': accepted,
        'state': 'payment_source_witness_match' if accepted else 'review_required',
        'paymentReview': payment,
        'sourceWitnessReview': witness,
        'limitations': 'Historical provider assertions, not current chain state or a state proof. '
                      'Independent policy, domain, type and digest remain essential. '
                      'The second Keccak implementation checks witness bytes; source binding '
                      'is not a second independent encoder. No signing or payment authorization.'}
    render(report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('transcript', 'policy', 'client', 'witness'):
        parser.add_argument(name)
    for name in ('chain-id', 'name', 'version', 'primary-type', 'expect-digest'):
        parser.add_argument('--' + name, required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--verifier')
    group.add_argument('--no-verifier', action='store_true')
    parser.add_argument('--salt')
    args = parser.parse_args(argv)
    domain = {'chainId': args.chain_id, 'name': args.name, 'version': args.version}
    if args.verifier is not None:
        domain['verifyingContract'] = args.verifier
    if args.salt is not None:
        domain['salt'] = args.salt
    try:
        report = review(load(args.transcript), load(args.policy), load(args.client),
                        read_workspace(args.witness), domain, args.primary_type,
                        args.expect_digest)
        print(render(report), end='')
        return 0 if report['accepted'] else 1
    except (ValueError, OSError, KeyError, TypeError, RecursionError):
        print('{"accepted":false,"state":"input_error"}')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
