# Minimum block separation for settled Ethereum transactions

Check that an independently chosen sequence of transactions settles, occurs in
order, and has at least the requested inclusion-height difference between each
adjacent pair. Python 3.9+ standard library; offline, with no installation.

From the repository root, run:

```sh
python3 -B line-3/tools/settlement-gap/gap.py --demo
```

Tried locally: exit 0, `accepted: true`, `settlement_gap_match`. The two inherited
real ZTO transactions were included at heights 26190898 and 26194715, a difference
of **3817**, meeting the illustrative minimum **3800**. Both require 12
confirmations and finality in the saved evidence. A minimum of 3817 also passes;
3818 returns exit 1 despite settlement and order passing. All 16 new tests pass.
No new chain observation was collected. `demo-result.json` retains the actual
output, not independent certification.

For your own independently reviewed plan:

```sh
python3 -B line-3/tools/settlement-gap/gap.py --plan path/to/plan.json --sha256 YOUR_INDEPENDENTLY_RETAINED_FULL_PLAN_SHA256
```

The full plan has exactly these keys:

- `version`: integer 1.
- `order`: a settlement-order version-1 plan with its complete `batch` and
  `sequence`; see the adjacent tool's README and this tool's `demo-plan.json`.
- `minimumBlockGaps`: one integer from 0 through 1000000 for each adjacent pair
  in `order.sequence`, in that order. Booleans and floating-point values refuse.

The exact outer plan bytes are pinned before parsing. Full policy, membership,
path and gap validation precedes opening evidence. Every evidence pin,
settlement check, position and required ordering must pass before gap arithmetic
runs. The inherited order API receives a serialization of the already validated
nested order object; its internally calculated digest is not independent approval.
Only the separately retained **outer** pin binds the gap requirements as well.
No compatible subset grants acceptance. Zero allows the same block only when
transaction indices are strictly increasing; it does not disable order checks.

A gap means **later inclusion height minus earlier inclusion height**. Adjacent
blocks have gap 1, with zero blocks strictly between them. This is useful when
reviewing an explicit block separation policy, but does not validate a contract's
timelock, block timestamps, elapsed seconds, event semantics, causation or an
application's workflow. A worker must separately determine the right policy.

Exit 0: all checks pass. Exit 1: pin, settlement, order or gap review required.
Exit 2: invalid/oversized plan, unavailable/invalid evidence or unsafe input path.
Input files are limited to 90 KB and reports to 100 KB. Reads use the inherited
workspace-relative bounded regular-file reader; hidden components, traversal,
absolute paths and symlinks refuse. Strict JSON rejects duplicates and nonfinite
numbers. The CLI reads no environment variables or external files and writes no
files. It has no network mode, wallet/key handling, signing, sending or payment.

Evidence remains historical provider assertions, without consensus, trie or full
inter-block ancestry proofs. No current freshness, amount, authorization or
persistent accounting follows. Retain the full-plan hash independently;
substituting both plan and expected hash defeats the protection. Bundled pins
illustrate retention, not independent custody.

Tests:

```sh
python3 -B -m unittest discover -s line-3/tools/settlement-gap -p 'test_*.py' -v
```

Reuses unchanged sibling modules: settlement-order, settlement-batch,
pinned-position, tx-position, payment-witness and settlement-check. The demo
uses settlement-order's two retained ZTO evidence files. All are ordinary source
files already in the repository and work without network access.
