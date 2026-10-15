# Offline JSON Lines uniqueness checker

Check a queue, API export or worker batch against an explicit structural contract
and require selected scalar fields to be unique across its rows. Duplicates point
to both the repeated token and its first occurrence in the original file. Missing
fields and containers reject; malformed rows do not hide later duplicates.

From the repository root, Python 3.10+ on POSIX, no installation:

```sh
python3 -B line-2/tools/jsonl-unique/check.py shared/payment-evidence/policy.contract.json line-2/tools/jsonl-contract/zto-policy.jsonl --unique /tx
```

Tried locally: exit **0**, one structurally valid saved ZTO policy, no uniqueness
errors. This reuses the real historical policy, whose contract allows ZTO first
and IMD second. It does not observe current chain state or prove payment.

To see a duplicate rejected:

```sh
python3 -B line-2/tools/jsonl-unique/check.py shared/payment-evidence/policy.contract.json line-2/tools/jsonl-unique/repeated-policy.jsonl --unique /tx
```

Tried locally: exit **1**, both rows satisfy the structural contract, but row 2's
`/tx` duplicates row 1's exact transaction string. The file deliberately repeats
one saved policy to demonstrate rejection; it is not two payment observations.
Actual reports are `policy.result.json` and `repeated.result.json`.

## Contract and comparison

`--unique POINTER` is mandatory and repeatable, with 1–16 distinct JSON Pointers,
at most 1,024 characters each. An empty argument (`--unique ''`) selects the root.
RFC 6901 `~0` and `~1` escapes select literal tildes and slashes. Arrays require
canonical nonnegative indices (`0`, `1`, …); `01`, `-` and nonexistent paths fail.
Each pointer is checked independently, not as a composite key. Null is a present
scalar; a missing value is an error even if it occurs only once. A missing deep
path reports the nearest existing container as an explicit `anchor_pointer`.

Strings compare decoded code points, with no case folding or Unicode
normalization; escapes do not change identity. Booleans, numbers, strings and
null have separate types. Numbers compare exact decimal source tokens: `1`,
`1.0` and `10e-1` agree; `true` and `"1"` differ. Negative zero agrees with zero.
Different large numbers are not merged by float rounding. Decimal construction
or hashing outside Python's supported range rejects as `unsupported_number`.
The inherited structural engine still uses its original int/float semantics;
this tool does not change numeric structural rules or their limitations.

Every strictly parsed row participates, including rows with structural errors.
Malformed rows are listed under `skipped_malformed_lines`, make uniqueness invalid,
and do not interrupt later checking. First occurrences remain the anchors for
all later duplicates. Unsupported numbers and nonscalar values reject rather
than being silently coerced or compared. The output preserves the ancestor's
full row report under `structural` and adds a separate `uniqueness` decision.
Acceptance requires top-level **`valid: true` and exit 0**. `complete: true` means
processing finished, not acceptance or complete uniqueness coverage of malformed rows.

## Boundaries and exits

Inputs are explicit visible relative workspace regular files, at most 1,000,000
bytes, read with the inherited no-follow descriptor traversal. Absolute, parent,
hidden, symlink and special-file paths refuse. Each path is captured only once;
hashes, structural diagnostics and uniqueness use those same captured bytes.
`--contract-sha256` and `--document-sha256` optionally bind independently retained
lowercase exact hashes before parsing. The document is not read until the
contract is prepared. A hash does not authenticate an author or grant permission.

Up to 256 LF-delimited rows; optional final LF and CRLF retain original bytes.
Blank rows, duplicate keys and nonfinite numbers reject under the inherited
strict parser. Source spans use one-based lines and Unicode code-point columns,
zero-based whole-file byte/character offsets and exclusive ends. All output is
ASCII-escaped JSON. The complete report plus newline must fit 100,000 bytes;
overflow emits no partial report. Split large batches explicitly.

Exit 0: structure and uniqueness pass. Exit 1: structural or uniqueness violations.
Exit 2 with complete stdout: malformed rows. Exit 2 with empty stdout and a small
JSON stderr error: file, pin, contract, UTF-8 or output-limit failure. The program
only reads inputs and writes its report to stdout. It never repairs or rewrites.

Retain sibling tools `jsonl-contract`, `source-locator`, `rule-locator`,
`bounded-contract` and `json-contract` as ordinary files when relocating; run
inside their workspace. Runtime uses only the Python standard library. No
network, environment lookup, account or coin is needed. The deliberate contract
subset is not full JSON Schema. Trusted regexes are required; byte limits are
not a CPU sandbox. No cross-file persistent deduplication or business semantics
are inferred from uniqueness.

## Checks performed

```sh
python3 -B line-2/tools/jsonl-unique/test_check.py
```

All **19 tests passed**, including exact decimal equality, large-number rounding,
extreme exponents, boolean separation, null/missing, deep anchors, escaped and
array pointers, independent fields, UTF-8/CRLF token slices, first occurrences,
malformed recovery, structural failures, pins, single capture, path refusal,
complete-output failure, exit codes, input immutability and the saved ZTO policy
with network disabled. The inherited JSON Lines suite's **18 tests** also passed.
These are local observations, not independent certification.
