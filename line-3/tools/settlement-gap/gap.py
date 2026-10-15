#!/usr/bin/env python3
"""Replay pinned settlement/order evidence and enforce minimum block separation."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

_spec = importlib.util.spec_from_file_location(
    'gap_order', Path(__file__).resolve().parent.parent / 'settlement-order' / 'order.py')
o = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(o)
Error = o.Error
LIMITATIONS = (
    'Historical provider assertions, not consensus, trie or full inter-block ancestry proofs. '
    'A block gap is later inclusion height minus earlier inclusion height; it is not elapsed '
    'seconds, intermediate block count, causation or a contract timelock check. '
    'No current freshness, payment amount, authorization or persistent deduplication. '
    'Keep the full plan hash independently; replacing plan and expected hash defeats this check.')


def validate(plan):
    if (not isinstance(plan, dict) or set(plan) != {'version', 'order', 'minimumBlockGaps'}
            or type(plan['version']) is not int or plan['version'] != 1):
        raise Error('exact version 1 gap plan required')
    sequence = o.validate(plan['order'])
    gaps = plan['minimumBlockGaps']
    if (not isinstance(gaps, list) or len(gaps) != len(sequence) - 1
            or any(type(g) is not int or not 0 <= g <= 1000000 for g in gaps)):
        raise Error('one integer minimum block gap in 0..1000000 per adjacent pair required')
    return gaps


def review_bytes(raw, expected_sha256):
    expected = o.b.k.pin(expected_sha256)
    if type(raw) is not bytes or len(raw) > o.b.k.LIMIT:
        raise Error('bounded exact plan bytes required')
    actual = hashlib.sha256(raw).hexdigest()
    result = {'accepted': False, 'state': 'plan_pin_mismatch',
              'expectedPlanSha256': expected, 'actualPlanSha256': actual,
              'gapChecked': False, 'evidenceChecked': False, 'limitations': LIMITATIONS}
    if actual != expected:
        return result
    plan = o.b.k.p.s.strict_json(raw)
    gaps = validate(plan)  # Includes full order/batch validation before evidence reads.
    # The outer exact-byte pin covers this nested object and the gap policy.
    # The inherited order API accepts bytes, so serialize the already validated
    # nested object once. This internal digest is not a second approval boundary.
    nested = json.dumps(plan['order'], ensure_ascii=True, allow_nan=False).encode('ascii')
    order = o.review_bytes(nested, hashlib.sha256(nested).hexdigest())
    result.update(orderReview=order, evidenceChecked=order['evidenceChecked'])
    if not order['accepted']:
        result['state'] = 'input_error' if order['state'] == 'input_error' else 'settlement_or_order_review_required'
        return result
    comparisons = []
    for left, right, minimum in zip(order['positions'], order['positions'][1:], gaps):
        observed = right['blockNumber'] - left['blockNumber']
        comparisons.append({'before': left['transactionHash'], 'after': right['transactionHash'],
                            'minimumBlockGap': minimum, 'observedBlockGap': observed,
                            'meetsMinimum': observed >= minimum})
    accepted = all(row['meetsMinimum'] for row in comparisons)
    result.update(gapChecked=True, comparisons=comparisons, accepted=accepted,
                  state='settlement_gap_match' if accepted else 'gap_review_required')
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--demo', action='store_true')
    parser.add_argument('--plan', help='visible workspace-relative gap plan')
    parser.add_argument('--sha256', help='independently retained full-plan SHA-256')
    args = parser.parse_args(argv)
    try:
        if args.demo:
            if args.plan or args.sha256:
                raise Error('demo refuses overrides')
            folder = Path(__file__).resolve().parent.relative_to(Path.cwd())
            raw = o.b.k.load_bytes(folder / 'demo-plan.json')
            expected = o.b.k.load_bytes(folder / 'demo-plan.sha256').decode('ascii').strip()
        else:
            if args.plan is None or args.sha256 is None:
                raise Error('plan and independent full-plan hash required')
            expected = o.b.k.pin(args.sha256)
            raw = o.b.k.load_bytes(args.plan)
        result = review_bytes(raw, expected)
        if args.demo:
            result['demoNote'] = ('Two retained real ZTO transactions, 3817 inclusion heights apart; '
                                  'illustrative minimum 3800. No fresh chain observation or independent approval.')
        encoded = json.dumps(result, indent=2, ensure_ascii=True, allow_nan=False)
        if len(encoded.encode('ascii')) > 100000:
            raise Error('report exceeds 100 KB')
        print(encoded)
        return 0 if result['accepted'] else 2 if result['state'] == 'input_error' else 1
    except (Error, ValueError, TypeError, KeyError, OSError, RecursionError):
        print(json.dumps({'accepted': False, 'state': 'input_error',
                          'reason': 'Invalid bounded gap plan, independent pin or evidence'}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
