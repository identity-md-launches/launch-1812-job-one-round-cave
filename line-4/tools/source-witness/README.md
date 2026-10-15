# Offline EIP-712 source–witness binder

This standard-library tool takes the **original typed-data JSON**, a complete
version-1 encoding witness, and a separately retained expected digest. It first
verifies the witness's hashes and structure with the copied `hash_witness.py` and
its independent Keccak implementation. Then it walks every source field and
checks that its type, array position, dynamic bytes or 32-byte atomic encoding
matches the corresponding witness node. It also checks the complete source type
declarations, including types that occur only behind empty arrays. No wallet,
key, network, installation, signing or sending is involved.

One command from the repository root shows the saved historical ZTO example:

```sh
python3 -B line-4/tools/source-witness/source_witness.py line-4/tools/source-witness/zto-payment.json line-4/tools/source-witness/zto-trace.json --expect 0xf33e2506e5c103f98dbfe3feb6d4b87d55f1fad4e423dbaa8462465ff4ab9774
```

**Tried:** exit 0 with `accepted: true`, `sourceTypedDataChecked: true`,
`sourceMatchesWitness: true`, 12 source/witness nodes, seven Keccak checks and
691 hash-input bytes. The captured report is `example-zto.json`. The fixture is an inherited historical real-ZTO payment
evidence commitment, containing token
`0xd782bdea4ef02a0bd391eb9089470c8080f0a68e` and transaction
`0xc4ca304c305cae326cab066639ab2156412eee7f5f774b41a2a136369f817ef7`.
It is an illustration, not a token signing interface, fresh chain observation,
approval or payment. Retain your own intended source and expected digest.

The published EIP-712 Ether Mail example and a recursive/array edge fixture
also pass. Changing the source token to IMD leaves the witness internally valid
but returns exit 1 with `/message/token` as the differing atomic word. Changing
the expected digest returns exit 1 even when source and witness agree. The
token-substitution report is `example-rejection.json`. Fifteen
new tests pass. Run them with:

```sh
python3 -B -m unittest discover -s line-4/tools/source-witness -v
```

Input files must be bounded regular no-follow files beneath the current working
directory, as enforced by the copied witness reader. Duplicate JSON keys, floats,
nonfinite numbers and invalid UTF-8 fail. JSON numeric literals outside the
JavaScript safe-integer range fail; use a decimal or `0x` string. A source with
unused declarations fails closed because those declarations cannot be witnessed.
This is a deliberate subset of the source shapes accepted by some wallets.
Exit 0 means all three inputs agree, exit 1 means a checked mismatch, and exit 2
means malformed or unsupported input; an error emits no JSON on stdout.

This binding establishes **encoding agreement only**. It does not verify the
signer's identity, intent, contract support, payment, settlement or replay
protection. A separately retained digest is essential: someone who can replace
the source, witness and expected digest together can make all three agree.
The source comparison uses the witness's already validated encoding nodes and
its atomic-word routine; it is not a second independent EIP-712 encoder. The
copied witness verifier uses its own Keccak implementation, separate from the
earlier typed-data encoder. See `provenance.json` for exact ordinary-file copies.

Encoding rules and the Ether Mail vector: [EIP-712](https://eips.ethereum.org/EIPS/eip-712).
