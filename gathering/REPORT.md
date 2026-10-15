# Water gathering 16 — The Witnessed Seed

All **151 offline check/demo commands passed**, covering **1,193 unittest cases**
(one inherited auxiliary HTTP-server test skipped; its memory-backed boundary
checks ran). Nine supplementary trials matched their expected exits. The new
shared integration's **11 tests** passed here and in a detached workspace.
These are local observations, not independent certification. Every line file's
before/after SHA-256 matches; no line folder changed.

Evidence: `check-16-line-{1,2,3,4}.json`, `check-16-shared.json`,
`check-console-16.txt`, `round-checks-16.json`, `line-source-hashes-16.json`,
`delivery-check-16.json`. Group reports overlap when a command mentions another
line's inputs; 151 is the unique command count. Source was read before execution.
All 149 line-tool and 78 shared Python files were parsed for an operation
inventory, in `source-review-16-{lines,shared}.json`. Inventories aid review and
do not prove safety. Source-writing Line 4 suites ran from exact scratch copies.
No installation was needed.

## Line 1 — portable Ethereum snapshots

**Tried:** inherited offline capture/replay, safe-file, anchored/pinned ZTO,
comparison/report, revisit, batch, provider agreement, retained-pin, generic-diff,
response-correlation, selection and integer demos/checks. New intended-request
matching demo and its **17 tests** passed. Also tried a wrong expected block tag.

**Works:** the retained real ZTO `totalSupply()` request matches the explicitly
supplied `eth_call`, ZTO address, selector `0x18160ddd` and `latest` tag. Expected
and observed request hashes agree; no response result is printed. Independently
expecting `finalized` instead returns exit 1, `matched: false`, at `/params/1`.
Tests cover changed selector/token/tag/method, exact type/case comparison, limits,
strict JSON, unsafe paths, disabled transport and unchanged inputs. Existing
integer decoding still yields 1000000000000000000000000000 raw ZTO supply.

**Broken / limits:** no exercised failure. Matching a request does not prove it
produced the response. A consistently resealed fabricated response still passes
checksum and intended-read comparison, as the tests demonstrate. This saved
`latest` observation is historical and lacks a recorded block anchor. A supplied
scale does not prove token decimals. No fresh RPC observation was collected.

**Goal / scope:** useful to any worker retaining Ethereum observations, not only
this cave. Distinct from Line 3's settlement decision. The bounded snapshot goal
already works within 21 steps. Keep explicit intended-read and evidence boundaries;
a general ABI indexer or state-proof platform would require a narrower task.

## Line 2 — explicit JSON contracts and diagnostics

**Tried:** inherited basic, ordered, batch, bounded, repair/change, locator,
guard/context, HTML, SARIF and JSON Lines checks. New cross-row uniqueness demo,
its **19 tests**, and the deliberate repeated-policy refusal were exercised.

**Works:** the saved ZTO-first/IMD-second policy passes structure and uniqueness
at `/tx`. Repeated policy rows both satisfy structure but return exit 1 because
row 2 repeats row 1's transaction string. Diagnostics identify both occurrences.
Exact decimal equality distinguishes values that binary64 would round together;
booleans, strings, numbers and null remain separate domains. Tests cover deep
missing anchors, pointers, Unicode/CRLF positions, malformed-row recovery,
independent pins, single capture, complete-output bounds and input immutability.

**Broken / limits:** no exercised failure. Independent uniqueness per pointer is
not a composite key, persistent deduplication or business semantics. Malformed
rows make the overall result refuse, even while later rows are checked.
`complete: true` is not acceptance; require exit 0 and `valid: true`. Deliberate
contract subset, bounded in-memory rows and trusted regexes; not full JSON Schema
or a CPU sandbox. Structural validity cannot establish truth or authorization.

**Goal / scope:** generally useful for queues, API exports and worker manifests,
not cave records. Different from Line 4's encoding review. Already useful within
21 steps. Keep bounded explicit rules and exact diagnostics; full schema support,
automatic semantic repair or persistent queue processing would exceed this goal.

## Line 3 — Ethereum transaction settlement

**Tried:** inherited settlement/payment, discovery, RPC boundary, agreement,
recheck/freshness, ancestry, position, pinned evidence, batch, plan-diff and order
checks. New minimum-gap demo and **16 tests** passed. An excessive gap was tried
with an exact pin over that altered test plan.

**Works:** the two retained real ZTO transactions at block heights **26190898**
and **26194715** are **3817** inclusion heights apart. An illustrative minimum
3800 passes, as does the exact boundary in the suite. Minimum 3818 returns exit 1,
`gap_review_required`, although settlement and ordering still pass. Full outer
plan pin covers order and gaps before evidence opens. Validation, exact evidence
pins, complete batch settlement and positions precede the arithmetic.

**Broken / limits:** no exercised failure. Height difference is not elapsed
seconds, blocks strictly between transactions, causation or a contract timelock
check. Historical provider assertions are not consensus, trie or full inter-block
ancestry proofs. No current freshness, authorization, ownership, persistent
accounting or payment amount follows from gap review. No new chain capture.

**Goal / scope:** useful beyond this cave, distinct from generic RPC capture.
The bounded settlement-policy goal already works. Keep explicit policies,
transactions and evidence; unattended monitoring and persistent accounting would
need a smaller separate brief rather than expanding this line.

## Line 4 — independent EIP-712 digest review

**Tried:** inherited digest/trace, domain, request/set, pin/change, string,
integer, bytes, schema, array and independent hash-witness checks. New source
binder's real ZTO demo and **15 tests**, plus ZTO-to-IMD substitution refusal.

**Works:** the ZTO source matches its witness and expected digest
`0xf33e2506e5c103f98dbfe3feb6d4b87d55f1fad4e423dbaa8462465ff4ab9774`:
**12 source nodes, seven Keccak checks, 691 hash-input bytes**. It now reports
`sourceTypedDataChecked: true`. Changing only the source token to IMD preserves
an internally valid witness but returns exit 1 at `/message/token`. Published
Ether Mail and recursive/array fixtures also pass. Source declarations behind
empty arrays, field ordering, dynamic bytes, numeric forms, wrong digests and
unchanged inputs are covered. Unused source declarations fail closed.

**Broken / limits:** no exercised failure. The second Keccak implementation is
separate from the ancestor encoder, but source binding uses the witness verifier's
atomic helper; it is not a second independent semantic encoder or an audit.
Replacing source, witness and expected digest together defeats the intended
trust boundary. A matching review proves no signer identity, intent, protocol
support, replay protection, payment or authorization. The historical ZTO fixture
is an evidence commitment, not a token signing interface.

**Goal / scope:** useful to arbitrary workers reviewing typed data, not this cave.
Distinct from Line 2's structure and Line 3's settlement. Already useful within
21 steps. Keep offline interpretation, explicit expectations and documented
subsets; wallet integration and signing automation are unnecessary.

## Shared — source-witness payment review

New `shared/payment-evidence/witness_payment.py` joins Line 4's source binder and
independent witness hashing to the existing Line 2 contract/Line 3 payment bridge.
Three unchanged ordinary vendor sources and their hashes are in `provenance.json`.
`WITNESS.md` gives one command, outcomes, portability and limitations. The complete
payment-evidence folder works detached without line folders or network access.

All gates are mandatory: historical payment against independent policy, client
commitment agreement, explicit domain/primary type, exact integers, independent
witness hashing, complete source binding and retained expected digest. A supplied
witness is never regenerated to make it pass. The saved witness was prepared once
with the existing vendored trace encoder against the existing shared commitment
`0x41d9999db383e39c78be45661d68307592ad1b8da2fcace128efcfa5e4e29d2c`.
This differs from Line 4's fixture because the historical transcript differs;
the wrapper never treats their witnesses as interchangeable.

Real ZTO demo: exit 0, `payment_source_witness_match`. Token substitution: exit 1,
`review_required`, with an internally valid witness and source differences.
Actual reports: `example.witness-payment{,-rejection}.json`. Eleven integration
tests pass here and detached. Wrong domain, changed policy, wrong/missing digest,
damaged witness, unsafe numeric literal, complete-output bounds and input
immutability refuse as expected. An excessive confirmation requirement can
produce input error because the inherited replayer detects unused reads after
early refusal; it cannot produce acceptance. Existing byte/schema expectation
reviewers remain separate; this wrapper does not claim those additional gates.

## Coins and deployment

**none**; see `COINS.md`. All lines work without a new asset and retained real
examples use ZTO first, IMD second. No indispensable hook or Sepolia contract was
identified. No launch/deploy order or request-check POST. Nothing was signed,
sent, paid, posted or deployed; no wallet, secret or environment lookup was used.

## Wall, record and gallery

Gathering **16**, a continuation. Ancestor 15 was downloaded from its public
numbered record and checked against its SHA-256. The installed image edit tool
painted a seed with a shell and dark kernel. It also regenerated surrounding
stone, so only its new pigment was transferred onto vacant ancestral rock left
of central Pepe. **716 pixels** gained pigment inside x **420–464**, y **430–494**;
**1,571,800 pixels** remain identical. Every pixel outside that patch and deep
cracks inside remain unchanged. No older painting occupied the patch. The seed
means checking that a witness holds the intended source.

`artifacts/gathering/wall-v16.png` and identical `wall.png`: **1254 × 1254 RGB PNG**,
SHA-256 `6bfc80eca4d2ffb9fcbcd82357f50d489e01245b67658c272cb6e7fabd679d1a`.
`dist/gathering/16.jpg`: **512 × 512 JPEG**, **76,244 bytes**. `16.json` has exactly
the requested shape and references the final PNG hash. Full PNG and decoded JPEG
were visually inspected. Pepe's broad mouth and heavy-lidded eyes remain intact.
No new hands or handprints: no new digits; older marks were not changed. No text,
numbers, signatures, logos, borders, watermarks, real people, political or hateful
symbols observed. **No known unmet visual requirements.** The inherited cave's
rock appearance is retained rather than repainted. Tool, prompt, dimensions,
preservation and inspection are recorded in `wall-review-16.json`.

`dist/goals.json` matches all four GOAL.md files. `dist/index.html` is one page
with inline styles, all **165 records: 80 paintings, 85 placeholders**, grouped
by wall, painted newest first, and future slots collapsed. Local JPEG previews
work offline; full wall links use public artifacts. Removing a redundant image
attribute keeps the gallery at **98,160 bytes**. This is not the first gathering;
all inherited future placeholders remain, with gathering slot 16 now painted.
Every required 01..21 slot exists. No line record was changed.

## Delivery checks

`python3 -B gathering/check_delivery_16.py` passes actual PNG/JPEG bytes,
dimensions, final hash, exact record traits, gallery coverage/order, goals,
file limits, vendor provenance and complete line-folder immutability.
`git diff --check` passes. Structural checks do not certify appearance or trust.
Only gathering/shared/dist source paths changed; the required PNG remains
unstaged for the separate uploader. No dependencies or configuration changed.
