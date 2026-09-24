# Test 7 · The budget of a composite signature

**English** · [Español](RESULTS.es.md)

> Status: **partial. Desktop (x86-64) and phone (ARM64) run on all three engines, preliminary
> verdict.** Part A (velocity threshold on dormant value) and the size cost are missing — see
> README.md, "What is missing". This is an order-of-magnitude signal, not a result citable as
> closed.

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
| **SLH-DSA-128s** | 1,265.4 µs · 790/s · **10.2× ML-DSA-44** | 1,158.1 µs · 863/s · **2.5× ML-DSA-44 · 0.9× its own native** | 10.18 ms · 98/s · **2.9× ML-DSA-44 · 8.0× its own native** |

Signature: ML-DSA-44 = 2,420 B; SLH-DSA-128s = 7,856 B (3.2× heavier).

*Corrected on 24/9/2026, after closing it:* the SLH-DSA-128s cell under Cranelift said **9.3×**, and that
number compared SLH-DSA under Cranelift (1,158.1 µs) against **native** ML-DSA-44 (124.0 µs), that is,
two different engines. On the same engine, 1,158.1 / 471.3 = **2.5×**. Also corrected in section 3.

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
for Test 2's figure— the gap drops to **2.5×**, and the composite cost (both signatures verified
together) gives **471 + 1,158 ≈ 1,630 µs**. That is **~3.5×** a single ML-DSA-44 verification in
this same module and engine (471 µs) — not ~10× and not ~30×, which is what a naive extrapolation
from the native number would have suggested. *(Against Test 2's 391 µs it would be ~4.2×, but that
figure came from a different module, ~20% faster for ML-DSA-44; see section 5. Corrected on
24/9/2026: this section used the 4.2× as if it were this module's ratio.)*

At ~1,630 µs per composite verification, a quarter core sustains on the order of ~150 tx/s
(0.25 / 1,630 µs) — far above what the use case demands, which is **only** the transactions that
exceed the velocity threshold on dormant value (proposed, it does not exist yet in the paper or in
the code: it is Part A), not the chain's general traffic.

## 4. What this number does NOT say yet

- **The phone was run (section 5), but it is a single device** (Motorola Edge 40 Neo, MT6879). The
  composite came out at 3.9× under Cranelift, close to the desktop's ~3.5× (same module); but the interpreter costs
  ~2× more than on x86, and a single SoC does not say whether that holds on other mid-range phones.
- **It does not include the size cost.** An additional 7,856 B per affected transaction is a block
  size and state budget cost (§10.1) this test does not quantify — it only measures verification
  time.
- **It does not say whether the complete mechanism is worth it.** That depends entirely on Part A
  —which velocity ceiling on dormant value does not brush against legitimate activity—, which is
  still unmeasured.

## 5. On the real phone (ARM64)

Motorola Edge 40 Neo (MediaTek MT6879), Termux, aarch64. Three complete runs on 2026-09-20, each a
fresh process, with no charger plugged in and no pauses (Test 2's recipe, §6.1). The binaries were
cross-compiled from the PC with `--target aarch64-linux-android`, because Cranelift does not compile
inside Termux (see README.md, "On the phone"). Raw outputs in `resultados-telefono/`.

**`decode+verify`**, median of the three runs (µs per signature · signatures/s · penalty vs. its own
native)

| | native | cranelift (JIT) | wasmi (int.) |
|---|---|---|---|
| **ML-DSA-44** | 113.4 µs · 8,818/s | 469.8 µs · 2,129/s · **4.1×** | 7.35 ms · 136/s · **64.8×** |
| **SLH-DSA-128s** | 1,004.0 µs · 996/s | 1,363.3 µs · 734/s · **1.4×** | 20.21 ms · 49/s · **20.1×** |

**SLH-DSA-128s against ML-DSA-44 on the same engine:** native 8.9× · cranelift **2.9×** · wasmi 2.8×.

**Composite cost** (both signatures verified together):

| engine | ML-DSA-44 + SLH-DSA-128s | vs. ML-DSA-44 alone (same engine) | per core · per quarter core |
|---|---|---|---|
| cranelift | 469.8 + 1,363.3 = **1,833 µs** | **3.9×** | ~545/s · ~136/s |
| wasmi | 7.35 + 20.21 = **27.6 ms** | 3.75× | ~36/s · ~9/s |

**Against the desktop** (phone / PC, median of three runs each)

| | native | cranelift | wasmi |
|---|---|---|---|
| ML-DSA-44 | 0.91× | 1.00× | 2.09× |
| SLH-DSA-128s | 0.79× | 1.18× | 1.99× |

*Variance and validity.* Between runs (max minus min, over the median): cranelift 0.1% on ML-DSA-44
and 0.02% on SLH-DSA-128s; wasmi 0.7% and 1.8%; native 8% and 5% (the noisiest, for the same reason as
on the desktop). Cranelift's `compile_ms` came out at 184.0–186.7 ms in all six measurements; a run
contaminated by migration to the little cluster would give ~4× (Test 2, §6), and there is no trace of
it. Against Test 2: this test's module gives ML-DSA-44/cranelift ~20% slower than Test 2's *on both
machines* (PC: 471.3 vs. 392.5 µs; phone: 469.8 vs. 390.6 µs), with a phone/PC ratio of 1.00 in both.
It is a difference of the module and not of the phone; the cause was not investigated. That is why the
composite is compared against ML-DSA-44 inside this same module (3.9×) and not against Test 2's 391 µs
(which would give 4.7×).

**What shows:**

- **The interpreter costs ~2× more on ARM** (2.09× on ML-DSA-44, 1.99× on SLH-DSA-128s), the same
  pattern as Test 2 (5.96 vs. 3.11 ms on ML-DSA-44, 1.9×). Against native, that takes wasmi's penalty
  on ML-DSA-44 from 28.3× to 64.8×. The JIT, by contrast, performs the same on both architectures for
  ML-DSA-44.
- **SLH-DSA-128s no longer ties with its native under JIT:** 0.9× on the desktop, 1.4× on the phone.
  What moves is the native (0.79× of the PC's), not the JIT (1.18×). One possible cause, unverified:
  ARM's native code uses hardware SHA-2 instructions and the wasm guest cannot; the i5-9400 has no
  SHA-NI, so on x86 that advantage did not exist.
- **The desktop's order of magnitude holds under Cranelift** (composite 3.9×, ~136 tx/s per quarter
  core, against ~3.5× and ~150 tx/s). **What changes is the interpreter:** ~27.6 ms per composite
  verification, ~9 tx/s per quarter core, about 15× fewer than Cranelift. Which of the two numbers
  applies to the budget depends on which engine the real VM uses, and this test does not decide that.

## 6. Reproducibility

Code in `codigo/`. Two crates: `guest/` (compiles to `wasm32-unknown-unknown`, exposes
`run_ml_dsa44` and `run_slh_dsa128s`) and `host/` (measures with `wasmi` and `wasmtime`, plus the
`nativo` binary for the reference row). Complete instructions in `README.md`, including the route for
the phone (binaries cross-compiled from the PC). No dependencies outside
`crates.io`; the same RustCrypto crates `pqcore` from Test 2 already uses, plus `slh-dsa` 0.1.0.

*Method note:* `slh-dsa` 0.1.0 requires pinning `signature = "=2.3.0-pre.4"` by hand — the default
resolution (`2.3.0-pre.7`) breaks the crate's compilation because of an API change between two
pre-releases of the same major version. It is a real fragility of depending on a pre-1.0 crate in
someone else's pre-release; documented in the `README.md` so that it does not get lost if `slh-dsa`
moves version.
