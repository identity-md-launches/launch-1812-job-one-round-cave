# Snapshot request match

Check that a portable Ethereum JSON-RPC snapshot records the public read you
intended to ask. This standard-library Python tool first validates an explicitly
supplied expected method and parameters, then fully replays the inherited
snapshot checks, and compares the stored request with that expectation. It works
offline, writes no files, and never interprets or prints the response result.

One command from the repository root shows it working:

```sh
python3 -B line-1/tools/snapshot-request-match/match.py line-1/tools/snapshot-integer/live-zto.json --method eth_call --params '[{"to":"0xd782bdea4ef02a0bd391eb9089470c8080f0a68e","data":"0x18160ddd"},"latest"]'
```

Tried on 2026-10-15: the command exits 0 with `matched: true`, equal expected and
observed request hashes, and no differences. It uses the ancestor's real saved
Ethereum Publicnode response for ZTO `totalSupply()`. This is the historical
`latest` observation retained by `snapshot-integer`, without a recorded block
anchor; no new network capture was made. Replacing `latest` with `finalized` in
the command exits 1 with `matched: false` and a difference at `/params/1`.

Supply both `--method` and `--params` from your own intended read. The tool has
no mode that copies its expectation from the candidate snapshot. A response
checksum alone leaves the request editable: changing a saved request's selector,
token address or block tag does not change that checksum. This tool detects
those mismatches against the expectation you supplied. Both expected and stored
requests must pass the existing public-read allowlist; no send/sign method is
accepted. The expected request is validated before the snapshot is opened.

Comparison is exact JSON structure and type equality. Object-key ordering and
JSON whitespace do not matter; array ordering, method, selector, address spelling
and block-tag spelling do. Hex casing is deliberately not normalized, so two
Ethereum-equivalent spellings can still mismatch. The fixed JSON-RPC version and
request ID are `2.0` and integer `1`, as required by the bounded snapshot format.
Request SHA-256 values cover compact, sorted-key ASCII JSON with no newline;
they identify the compared requests, not exact snapshot file bytes. Differences
use JSON Pointer paths relative to the complete request and retain the differing
JSON values. Neither a result nor a decoded value is included in the report.

Exit 0 means inherited validation and exact request matching passed. A valid
snapshot with a mismatching request prints a JSON report and exits 1. Malformed,
unsafe-path, checksum-invalid or oversized input exits 1 with a bounded stderr
message and no JSON report. Missing flags or other CLI syntax errors exit 2.
Callers must check both exit status and `matched`; a report alone is not success.
Expected parameter text is capped at 16,384 UTF-8 bytes. Both canonical complete
requests are capped at 16,384 bytes, including stored requests that the ancestor
reader permits to be larger. Complete ASCII output including its newline is
limited to 100,000 bytes. The inherited snapshot input cap is 2,016,384 bytes and
its no-follow reader accepts only visible relative workspace regular files.

Run the focused offline checks:

```sh
python3 -B -m unittest discover -s line-1/tools/snapshot-request-match -p 'test_*.py' -v
```

All 17 tests passed. They cover real ZTO and finalized-block snapshots with
network transport disabled, request substitution while preserving the original response checksum,
wrong selector/token/tag/method, key ordering, literal hex casing, type-sensitive
comparison, malformed expectations, request/output/input bounds, full inherited
validation, strict JSON, mandatory flags, symlinks and unchanged input files.
Synthetic mutations are failure probes, not chain evidence. A deliberately
fabricated, consistently resealed response still matches the intended request;
that test records the boundary of this check.

Keep sibling `bounded-rpc-snapshot` and `safe-snapshot-files` folders; those
ordinary Python sources are the only dependencies. No installation is needed.
A match does not prove the stored request produced the stored response, provider
identity, Ethereum state, chain identity, finality, freshness, balance, payment or
authorization. Expectations copied from altered evidence do not protect against
replacement. Separate retained pins can protect exact bytes when held elsewhere;
this tool does not create or update such trust. No new coin is required.
