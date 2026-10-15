#!/usr/bin/env python3
"""Exercise new line refusals and portable cross-line witness payment gates."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
BASE = 'shared/payment-evidence/'
DIGEST = '0x41d9999db383e39c78be45661d68307592ad1b8da2fcace128efcfa5e4e29d2c'
DEMO = [BASE+'witness_payment.py', BASE+'example.transcript.json',
        BASE+'example.policy.json', BASE+'example.typed-data.json',
        BASE+'example.source-witness.json', '--chain-id', '1',
        '--name', 'Read-only Payment Evidence', '--version', '1',
        '--primary-type', 'PaymentEvidence', '--no-verifier', '--expect-digest', DIGEST]


def main():
    assert Path.cwd() == ROOT
    scratch = ROOT/'test/scratch/round16'
    scratch.mkdir(parents=True, exist_ok=True)
    detached = scratch/'portable'
    shutil.copytree(ROOT/BASE, detached/BASE, dirs_exist_ok=True)
    substituted = json.loads((ROOT/BASE/'example.typed-data.json').read_bytes())
    substituted['message']['token'] = '0xd34a99bc0f67ae1bbd63c660e6d0b0dd03e263b7'
    bad_client = scratch/'substituted.json'
    bad_client.write_text(json.dumps(substituted)+'\n')
    substitute_args = list(DEMO)
    substitute_args[3] = str(bad_client.relative_to(ROOT))
    plan = json.loads((ROOT/'line-3/tools/settlement-gap/demo-plan.json').read_bytes())
    plan['minimumBlockGaps'] = [3818]
    bad_plan = scratch/'gap3818.json'
    raw = (json.dumps(plan)+'\n').encode()
    bad_plan.write_bytes(raw)
    cases = [
        (ROOT, 0, [BASE+'test_witness_payment.py'], None),
        (ROOT, 0, DEMO, BASE+'example.witness-payment.json'),
        (ROOT, 1, substitute_args, BASE+'example.witness-payment-rejection.json'),
        (detached, 0, [BASE+'test_witness_payment.py'], None),
        (detached, 0, DEMO, None),
        (ROOT, 1, ['line-1/tools/snapshot-request-match/match.py',
                   'line-1/tools/snapshot-integer/live-zto.json', '--method', 'eth_call',
                   '--params', '[{"to":"0xd782bdea4ef02a0bd391eb9089470c8080f0a68e","data":"0x18160ddd"},"finalized"]'], None),
        (ROOT, 1, ['line-2/tools/jsonl-unique/check.py', BASE+'policy.contract.json',
                   'line-2/tools/jsonl-unique/repeated-policy.jsonl', '--unique', '/tx'], None),
        (ROOT, 1, ['line-3/tools/settlement-gap/gap.py', '--plan', str(bad_plan.relative_to(ROOT)),
                   '--sha256', hashlib.sha256(raw).hexdigest()], None),
        (ROOT, 1, ['line-4/tools/source-witness/source_witness.py',
                   'line-4/tools/source-witness/zto-imd-substitution.json',
                   'line-4/tools/source-witness/zto-trace.json', '--expect',
                   '0xf33e2506e5c103f98dbfe3feb6d4b87d55f1fad4e423dbaa8462465ff4ab9774'], None),
    ]
    rows = []
    for cwd, expected, args, save in cases:
        done = subprocess.run([sys.executable, '-B', *args], cwd=cwd, capture_output=True,
                              text=True, timeout=45,
                              env={'PATH':'/usr/bin:/bin','PYTHONDONTWRITEBYTECODE':'1'})
        row = {'command':['python3','-B',*args], 'detached':cwd != ROOT,
               'expectedExit':expected, 'exitCode':done.returncode,
               'passed':done.returncode == expected,
               'stdout':done.stdout,'stderr':done.stderr}
        rows.append(row)
        if save and row['passed']:
            assert len(done.stdout.encode()) <= 100000
            (ROOT/save).write_text(done.stdout)
        print('PASS' if row['passed'] else 'FAIL', args[0], done.returncode)
    output = json.dumps(rows, indent=2)+'\n'
    assert len(output.encode()) <= 100000
    (ROOT/'gathering/round-checks-16.json').write_text(output)
    return 0 if all(r['passed'] for r in rows) else 1


if __name__ == '__main__':
    raise SystemExit(main())
