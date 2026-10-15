# Source-witness payment review

Gathering 16 joins Line 4's source–witness binder and second Keccak implementation
to the existing Line 2 contracts and Line 3 historical payment replay. Python
3.10+ standard library, no installation. Copy this entire `payment-evidence`
folder into another workspace; no line folders are needed.

From the repository root, one command:

```sh
python3 -B shared/payment-evidence/witness_payment.py shared/payment-evidence/example.transcript.json shared/payment-evidence/example.policy.json shared/payment-evidence/example.typed-data.json shared/payment-evidence/example.source-witness.json --chain-id 1 --name 'Read-only Payment Evidence' --version 1 --primary-type PaymentEvidence --no-verifier --expect-digest 0x41d9999db383e39c78be45661d68307592ad1b8da2fcace128efcfa5e4e29d2c
```

Tried: exit 0, `accepted: true`, `payment_source_witness_match`, seven independent
Keccak checks and 12 source nodes. Evidence is the retained real historical ZTO
transfer, not a fresh observation. Its actual report is `example.witness-payment.json`.
The expected digest is the existing shared payment commitment, which differs from
Line 4's example because the underlying transcript differs. The included witness
was prepared once using the existing vendored trace encoder; verification never
regenerates or repairs a supplied witness.

Acceptance requires both reviews: full historical payment/settlement against the
separately supplied policy, client agreement with that commitment, explicit
domain and primary type, exact integer representation, complete witness hashing,
source-field binding and the caller's retained digest. A witness that is internally
consistent cannot override a different source or a failing payment review.

The caller must choose and retain the policy, domain, type and digest independently.
Bundled expectations illustrate the interface, not independent custody. The CLI
requires a digest and explicit verifier presence/absence. Witness input uses the
copied bounded no-follow workspace reader; other files use the existing bounded
reader. Duplicate keys, unsupported numbers, unsafe paths and malformed evidence
refuse. All output including newline must fit 100,000 bytes. Exit 0 means all gates
pass; exit 1 means a checked mismatch; exit 2 means input/processing failure.
No partial result counts as acceptance. Inputs are never changed.

Changing the client's token from ZTO to IMD while keeping the valid ZTO witness
returns exit 1, with `/message/token` in the source differences. IMD remains a
supported second-choice token when supplied consistently under an independent
policy; this probe deliberately supplies conflicting evidence.
`example.witness-payment-rejection.json` records the actual rejection.

```sh
python3 -B shared/payment-evidence/test_witness_payment.py
```

All 11 integration tests pass here and in a detached workspace containing only
this folder. They cover real ZTO replay with transport disabled, token
substitution, wrong independent domain, unmet settlement policy, policy edits,
wrong/missing digest, damaged witness, large numeric literals, unchanged inputs,
complete-output bounds, and CLI success/missing-file failure. An unmet settlement
policy may refuse as input error when the inherited replayer finds unused reads
after its early refusal; it never accepts that transcript.

The three new vendor sources are unchanged copies, with hashes in `provenance.json`.
The second Keccak implementation is independent of the ancestor encoder, but
source binding uses the witness's atomic encoding helper. This is not two
independent semantic encoders or a cryptographic audit. Historical provider
assertions do not establish current settlement, consensus/state proofs, signer
intent, authorization or replay protection. No signing, sending or payment occurs.
The existing byte/schema reviewers remain separate tools; this wrapper does not
claim their independently supplied expectation checks.
