# Test 7 · The budget of a composite signature

> Status: **partial. Desktop (x86-64) run on all three engines, preliminary verdict.** The phone
> (ARM64) is missing and Part A (velocity threshold on dormant value) is missing — see LEEME-EN.md,
> "What is missing". This is an order-of-magnitude signal, not a result citable as closed.

## 1. What was measured

`decode+verify` of ML-DSA-44 (the already chosen primitive, Test 2) and SLH-DSA-128s (a candidate
second family for a composite signature — hash-based, with no core shared with ML-DSA's lattice, a
condition of §10.1), in the same wasm module, under three engines: native, `wasmi` (pure interpreter
— the "chain VM" profile) and `wasmtime`/Cranelift (JIT — the engine that actually fit into the
budget of Test 2). Methodology identical to Test 2: a `measure` function that scales iterations up
to a 1.2 s run and takes the median of 5 repetitions.

Machine: x86-64 desktop (Windows), with no explicit vectorization (same criterion as Test 2: "the
native column is portable Rust, not AVX2" — the real penalty against the best possible native is
larger than the one in this table).

## 2. Results

**`decode+verify`** (µs per signature · signatures/s · penalty vs. native)

| | native | cranelift (JIT) | wasmi (int.) |
|---|---|---|---|
| **ML-DSA-44** | 124.0 µs · 8,065/s | 471.3 µs · 2,122/s · **3.8×** | 3.51 ms · 285/s · **28.3×** |
| **SLH-DSA-128s** | 1,265.4 µs · 790/s · **10.2× ML-DSA-44** | 1,158.1 µs · 863/s · **9.3× ML-DSA-44 · 0.9× its own native** | 10.18 ms · 98/s · **2.9× ML-DSA-44 · 8.0× its own native** |

Signature: ML-DSA-44 = 2,420 B; SLH-DSA-128s = 7,856 B (3.2× heavier).

*Variance:* three complete runs. `wasmi` and `cranelift` stayed within ~3% between runs for both
primitives — the table's figures are representative. `native` was noisier, above all ML-DSA-44
(124–160 µs between runs, ~25%): it is a single-pass measurement without the scaling of `measure`,
and at that time scale (tens of microseconds) the Windows scheduler and cache noise weigh more. It
changes none of this test's conclusions, which rest on `wasmi`/`cranelift`, not on `native`.

**Cost of installing the bytecode** (once, not per verification): wasmi 0.8–1.2 ms; cranelift ~146 ms
for a 142 KB module (this test's module carries both primitives, heavier than Test 2's). It is noise
against the cost of verifying; it does not enter the per-transaction budget.

## 3. The finding that matters

**The order between engines inverts between primitives.** ML-DSA-44 suffers a much larger interpreter
penalty than JIT penalty (28.3× against 3.8×) — the same pattern Test 2 already measured.
SLH-DSA-128s barely pays a JIT penalty (0.9×, practically tied with its own native) and pays a
considerably smaller interpreter penalty than ML-DSA (8.0× against 28.3×). It is consistent with
SLH-DSA being a cascade of SHA-2 compressions — a computation pattern a JIT optimizes almost as well
as the native compiler, and that an interpreter punishes less than the modular arithmetic with
scattered memory access of a lattice.

**Practical consequence:** measured natively, SLH-DSA-128s looks ~10× more expensive than ML-DSA-44.
Under Cranelift —the engine that actually decides the budget, because it is the one used on the phone
for Test 2's figure— the gap drops to **9.3×**, and the composite cost (both signatures verified
together) gives **471 + 1,158 ≈ 1,630 µs**, against the 391 µs a single ML-DSA-44 verification cost
on the real phone (Test 2). That is **~4.2×** the cost of a simple verification — not ~10× and not
~30×, which is what a naive extrapolation from the native number would have suggested.

With Test 2's figure of ~640 tx/s per quarter core for an ML-DSA-44 verification alone, a composite
verification at ~4.2× that cost would sustain on the order of ~150 tx/s — far above what the use case
demands, which is **only** the transactions that trip the velocity circuit breaker (§8.5), not the
chain's general traffic.

## 4. What this number does NOT say yet

- **It is not run on the phone.** Test 2's native/JIT/interpreter ratio was not identical between x86
  and ARM (§10.3 already measured that for ML-DSA); there is no guarantee that the composite ~4.2×
  holds the same way on the real reference hardware.
- **It does not include the size cost.** An additional 7,856 B per affected transaction is a block
  size and state budget cost (§10.1) this test does not quantify — it only measures verification
  time.
- **It does not say whether the complete mechanism is worth it.** That depends entirely on Part A
  —which velocity ceiling on dormant value does not brush against legitimate activity—, which is
  still unmeasured.

## 5. Reproducibility

Code in `codigo/`. Two crates: `guest/` (compiles to `wasm32-unknown-unknown`, exposes
`run_ml_dsa44` and `run_slh_dsa128s`) and `host/` (measures with `wasmi` and `wasmtime`, plus the
`nativo` binary for the reference row). Complete instructions in `LEEME-EN.md`. No dependencies outside
`crates.io`; the same RustCrypto crates `pqcore` from Test 2 already uses, plus `slh-dsa` 0.1.0.

*Method note:* `slh-dsa` 0.1.0 requires pinning `signature = "=2.3.0-pre.4"` by hand — the default
resolution (`2.3.0-pre.7`) breaks the crate's compilation because of an API change between two
pre-releases of the same major version. It is a real fragility of depending on a pre-1.0 crate in
someone else's pre-release; documented in the `LEEME-EN.md` so that it does not get lost if `slh-dsa`
moves version.
