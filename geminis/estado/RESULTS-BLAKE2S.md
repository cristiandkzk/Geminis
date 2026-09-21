# The consensus hash becomes BLAKE2s — what changes in the §8.5 floor

**What changed.** On 2026-09-21 Genesis' hash (`H`, I4) moved from SHA-256 to BLAKE2s. The initial
signature is Ed25519, which hashes with SHA-512 inside, and an `H` from the SHA-2 family shares a core
with it; §10.1 forbids that (lineage and signature must not fall together). BLAKE2 is neither SHA-2
nor Keccak (the SHAKE family, which ML-DSA-44, the successor signature, uses).

**What was migrated.** `huella()` (lineage, state root, block hash), the state tree, the eviction tree
and the predicate digest: all hash through `protocolo.serializacion.hasher`, the single entry point,
and a test verifies that no other module imports `hashlib`. **Declared exception:**
`liquidacion/doble_firma.py`, a toy 127-bit Schnorr where SHA-256 is an internal part *of that
primitive*, not the chain's consensus hash.

## The measurement

Same as `steps_per_verify` (Test 2) and the SHA-256 one: a hand-written BLAKE2s (RFC 7693), compiled to
RV32IM (`predicado/vm/guest-blake2s/`), run on the §6.6 machine by subtracting two batches
(`cargo run --release --bin hash_blake2s`). **Before counting steps it is validated that it computes
BLAKE2s for real:** the digest of `"abc"` is the one in RFC Appendix B.

| | steps per compression | create + evict cycle (26 hashes) |
|---|---:|---:|
| SHA-256 (`guest-sha`, 2026-08-21) | 4,898 | 254,696 |
| **BLAKE2s (`guest-blake2s`, 2026-09-21)** | **2,529** | **131,508** |

BLAKE2s costs **0.52×**. The count is exact and architecture-independent. Both guests are hand-written
by the same method, so the ratio between them is comparable.

## What moves

The model reproduces the published SHA-256 table (row by row, before touching anything) and gives this
with BLAKE2s:

| cut `d` | hashes per update | floor with SHA-256 | floor with BLAKE2s |
|---:|---:|---:|---:|
| 1 | 26 | 6.03 (24% of `L_max`) | 3.11 (12%) |
| 4 | 37 | 8.58 (34%) | 4.43 (18%) |
| **6** | **83** | **19.25 (77%)** | **9.94 (40%)** |
| 7 | 146 | 33.86 (135%) | 17.48 (70%) |
| 9 | 528 | 122.44 (490%) | 63.22 (253%) |

Devnet B4 (what eviction takes from the block, `d = 6`): **9.62% with SHA-256, 4.97% with BLAKE2s**.
See `devnet/RESULTS.md`, which also records that the published 3.01% was already out of date.

### Which conclusions move and which do not

- **The original Phase 5 criterion is still not met:** it required the floor below 35% of `L_max`;
  with BLAKE2s it is 40%. The distance moves, the verdict does not.
- **Short life:** someone buying one epoch pays 91% at creation (95% with SHA-256). The criterion
  requiring more than 90% passes at **0.909**, with a thin margin.
- **The cut `d = 6` was not re-decided.** At `d = 7` the floor no longer exceeds `L_max` (70%, was
  135%), so the open decision of choosing the cut again has more room. It is a Genesis decision, not a
  side effect of changing the hash.
- **The floor dropping is not a merit of the tree:** it is the cost of a different hash.

## Limits

- **The model counts one compression per hash, and an internal node is two.** The message the tree
  hashes is the domain label (18 B) plus two 32 B children: 82 bytes, two 64-byte blocks in SHA-256 and
  in BLAKE2s. `PASOS_POR_HASH` is per compression and the computation multiplies by hashes, not by
  compressions. It is a simplification **prior** to this change, undocumented, and it **does not alter
  the 0.52 ratio**, but it does alter the absolute level: if corrected, the floors above would double
  for both algorithms. (BLAKE2s can separate domains with its personalization parameter, which is free
  and would leave each node at one compression; it is a design option, not done.)
- **One implementation per algorithm**, hand-written by the same method; x86-64 only (the count is
  deterministic by design and Test 2 measured it identical on ARM; not repeated here).
- **The earlier documents keep their numbers**, computed with SHA-256, as a record of what was measured
  then: `estado/RESULTS.md`, `estado/RESULTS-TREE.md`, `presupuesto-nodo/`.
