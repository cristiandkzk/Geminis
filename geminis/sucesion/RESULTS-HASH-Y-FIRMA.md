# Independent successions of hash and signature

**What is shown.** The chain can change its hash function and its signature primitive **independently**, in any
order, without restarting and without moving its root:

```
hash:       BLAKE2s  →  SHA-3 (Keccak)  →  …
signature:  Ed25519  →  ML-DSA-44       →  …
```

Each succession has its own canary, its own rule (`ReglaCanarioHash`, `ReglaCanarioCriptografico`) and its own
format. Run it with `python herramientas/independencia.py`; it is pinned by 31 tests
(`pruebas/test_sucesion_de_hash.py` and `pruebas/test_sucesion_independiente.py`).

## Result

Real chain (`NodoPoD`), `H0_GENESIS` `6175777756bd3f8c`:

| order | step | gen | hash in force | signatures in force | core coupling |
|---|---:|---:|---|---|---|
| hash first | 0 | 0 | BLAKE2s | Ed25519 | — |
| | 1 | 1 | **SHA-3 (Keccak)** | Ed25519 | — |
| | 2 | 2 | SHA-3 (Keccak) | Ed25519 + **ML-DSA-44** | **H with ML-DSA-44 (Keccak)** |
| signature first | 0 | 0 | BLAKE2s | Ed25519 | — |
| | 1 | 1 | BLAKE2s | Ed25519 + **ML-DSA-44** | — |
| | 2 | 2 | **SHA-3 (Keccak)** | Ed25519 + ML-DSA-44 | **H with ML-DSA-44 (Keccak)** |
| both at once | 0 | 0 | BLAKE2s | Ed25519 | — |
| | 1 | 2 | **SHA-3 (Keccak)** | Ed25519 + **ML-DSA-44** | **H with ML-DSA-44 (Keccak)** |

In all three orders: the lineage verifies end to end (2 checkpoints), `H0_GENESIS` does not move, the block chain
crosses everything without breaking and the final state is the same. **The history is not the same**: the
checkpoints differ depending on the order, and that is what keeps the test from being vacuous.

**Each checkpoint is computed with its ancestor's hash, not the one it introduces.** With the hash first, the
checkpoint that introduces SHA-3 comes out of BLAKE2s and the next one already comes out of SHA-3; with the
signature first, both come out of BLAKE2s because the ancestor does not use SHA-3 yet. Verifying A→B does not
require trusting B's primitive.

## What is NOT independent: the coupling is reported, not blocked

The independence is one of **mechanism**, not of **security**. Ed25519 hashes with SHA-2 (SHA-512) and ML-DSA with
Keccak (SHAKE), so as soon as both transitions happen `H` (SHA-3) shares a core with the successor signature,
which is what §10.1 wants to avoid. The check (`protocolo/nucleo.py`) **reports it at the step where it appears
(right-hand column) and does not block it**, for a structural reason:

- signatures are additive (I5: Ed25519 is not retired), so after the first signature step SHA-2 and Keccak are in
  force at the same time;
- the standard library only guarantees three hash families (SHA-2, Keccak, BLAKE), and the signatures already use
  two;
- blocking would leave the hash chain with no successor. The limit is declared instead of hidden.

Generation 0 **is** enforced with teeth: `H` (BLAKE2s) shares no core with Ed25519, not even after a signature
succession alone (`pruebas/test_nucleo_compartido.py`).

## Limits, all declared

- **The "…" are open and not built.** §6.6 says there is no replacement list: the successor is delivered by a work
  order as bytecode and accepted by the gauntlet. Here each chain has two steps and they are formats Genesis
  already knows.
- **ML-DSA-87 is not a step**: it is not in the paper or in Genesis. It is a cost level measured in Test 2.
- **"SHA-3 (Keccak)" and not "Keccak-256":** it is `hashlib.sha3_256`, the same permutation as Ethereum's
  Keccak-256 with different padding; it does not give the same digests.
- **`Geminis`' signature canary is still a counter** (`("gastar_canario",)`, unverified); the hash one requires
  work (`CANARIO_HASH_BITS = 16`, an uncalibrated demonstration value). The verified signature version only exists
  in `Colosseum App`.
- **The state tree, the eviction tree and the predicates do not follow the hash succession:** they always hash
  with Genesis' hash, because migrating a Merkle tree to a new hash means re-hashing all of it and that is not
  built.
- The synthetic state has no accounts or value: the protocol's state is preserved, not funds under keys.
