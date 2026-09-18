# Test 2 · The interpreter's budget

**English** · [Español](RESULTS.es.md)

> Status: **closed. x86 and ARM run, firm verdict.**
> Three cells of the ARM table are left without a clean measurement; none of them sustains a
> conclusion. See §7.

What §12 asks for: *"measure how long a post-quantum signature verification takes running as
bytecode over a deterministic VM, on a phone"*. No protocol written: an existing VM (wasmtime 47,
wasmi 2.0) + a reference implementation (RustCrypto `ml-dsa` 0.1.1, FIPS-204 pure Rust).

---

## 1. What exactly was measured

A single ML-DSA `verify` compiled from the **same source** to native, to wasm32 and to two RISC-V
ISAs. That isolates the variable that matters —the execution engine— and does not mix different
implementations.

Six engines, which are not six speeds but six **deployment regimes**:

| engine | what it represents in the design |
|---|---|
| `native` | the primitive as node code — exactly what §6.6 wants to avoid |
| `wasmtime-cranelift` | bytecode with an optimizing JIT — **equally deterministic** |
| `wasmtime-pulley` | wasmtime's portable interpreter — pessimistic bound |
| `wasmi` | pure register interpreter — the "chain VM" profile |
| `rv32im` | own RV32IM interpreter — the small ISA, 32 bits |
| `rv64imac` | the same interpreter at 64 bits |

The last three are pure interpreters, so their ratios compare ISA against ISA. And `rv32im` against
`rv64imac` isolates a single variable —the register width— over the same interpreter design.

Two paths, and the distinction turned out to have a protocol consequence:

- **`decode+verify`** — the node receives the public key and the signature as bytes and verifies. It
  is the honest number by default.
- **`verify_only`** — the key is already expanded in memory.

## 2. Results — x86_64, Intel i5-9400 @2.9 GHz, one core

**`decode+verify`** (µs per signature · signatures/s · penalty vs. native)

| | native | cranelift (JIT) | wasmi (int.) | pulley (int.) |
|---|---|---|---|---|
| **ML-DSA-44** | 107 µs · 9,332/s | 392 µs · 2,548/s · **3.7×** | 3.11 ms · 322/s · **29.0×** | 8.42 ms · 119/s · 78.6× |
| **ML-DSA-65** | 172 µs · 5,813/s | 591 µs · 1,691/s · **3.4×** | 4.82 ms · 208/s · **28.0×** | 12.88 ms · 78/s · 74.9× |
| **ML-DSA-87** | 279 µs · 3,586/s | 896 µs · 1,116/s · **3.2×** | 7.25 ms · 138/s · **26.0×** | 19.53 ms · 51/s · 70.0× |

**`verify_only`** (key already expanded)

| | native | cranelift | wasmi | pulley |
|---|---|---|---|---|
| **ML-DSA-44** | 43.7 µs · 22,888/s | 248 µs · 5.7× | 1.97 ms · 45.2× | 5.13 ms · 117× |
| **ML-DSA-65** | 60.7 µs · 16,475/s | 354 µs · 5.8× | 2.89 ms · 47.6× | 7.39 ms · 122× |
| **ML-DSA-87** | 86.9 µs · 11,504/s | 524 µs · 6.0× | 4.35 ms · 50.1× | 11.21 ms · 129× |

**Cost of installing the bytecode** (once per node, on commuting primitive — the moment of the loop
of §6.6): cranelift **221–243 ms**, wasmi **1.2–1.5 ms**, for a 223 KB module. It is noise. That
part of the loop has no budget problem.

*Variance:* a second complete run gave `wasmi`/ML-DSA-44 at 26.1× instead of 29.0×. The spread
between runs is on the order of **10%**; no digit of these tables means anything beyond that.

*Note on the baseline:* the `native` column is portable Rust, not AVX2. A hand-vectorized ML-DSA runs
~2–3× faster still, so the real penalty of bytecode against the best possible native is larger than
the table's. It does not move the verdict, but the table is the optimistic version.

## 3. Results — ARM64, Motorola Edge 40 Neo (Dimensity 7030, Cortex-A78 @2.5 GHz)

Under Termux. The table is **assembled from clean cells of several runs**; the cleanliness criterion
is in §6 and the raw CSVs are listed at the end.

**`decode+verify`**

| | native | cranelift (JIT) | wasmi (int.) | pulley (int.) | rv32im | rv64imac |
|---|---|---|---|---|---|---|
| **ML-DSA-44** | 111 µs · 8,994/s | 391 µs · 2,560/s · **3.51×** | 5.96 ms · 168/s · 53.6× | 9.83 ms · 102/s · 88.4× | 10.57 ms · 95.1× | 11.67 ms · 105.0× |
| **ML-DSA-65** | 180 µs · 5,556/s | 589 µs · 1,697/s · **3.27×** | 9.12 ms · 110/s · 50.7× | 15.17 ms · 66/s · 84.3× | 16.75 ms · 93.1× | 18.09 ms · 100.5× |
| **ML-DSA-87** | 307 µs · 3,259/s | 905 µs · 1,105/s · **2.95×** | 14.16 ms · 71/s · 46.2× | 23.64 ms · 42/s · 77.1× | 28.49 ms · 92.8× | 33.09 ms · 107.8× |

**`verify_only`**

| | native | cranelift | wasmi | pulley | rv32im | rv64imac |
|---|---|---|---|---|---|---|
| **ML-DSA-44** | 52.5 µs · 19,054/s | — | 3.76 ms · 71.7× | — | 3.56 ms · 67.2× | 5.05 ms · 96.1× |
| **ML-DSA-65** | 75.0 µs · 13,349/s | 370 µs · **4.93×** | 5.49 ms · 73.2× | — | 4.77 ms · 63.7× | 6.82 ms · 91.0× |
| **ML-DSA-87** | 109 µs · 9,195/s | 554 µs · **5.09×** | 8.35 ms · 76.8× | 13.23 ms · 121.7× | 7.08 ms · 65.1× | 10.38 ms · 95.4× |

**Cost of installing the bytecode on ARM:** cranelift **335–344 ms** (x86: 221–243), wasmi
**1.5–2.1 ms**. Still noise.

### 3.1 The phone against the PC, engine by engine

| engine | ARM / x86 |
|---|---|
| `native` | 1.02–1.22× |
| `wasmtime-cranelift` | **1.00–1.06×** |
| `wasmtime-pulley` | 1.17–1.21× |
| `rv32im` | 0.82–1.07× per step |
| `rv64imac` | 1.46–1.74× per step |
| **`wasmi`** | **1.86–2.21×** |

Cranelift on the phone runs at **1.00× of the i5-9400** in the cells measured cleanly: 390,614 ns
against 392,462, 589,377 against 591,224, 905,159 against 895,815. It is not a fit, it is the same
absolute time on two architectures.

### 3.2 `steps_per_verify` is identical across architectures

The count of instructions executed by the RISC-V interpreters coincides **byte for byte** between
x86 and ARM in all six configurations, in every run. It is the only number in the whole test that no
contamination can touch, because it does not depend on the clock.

That is property I1 measured directly: the fixed machine does not degrade when changing host
architecture. It is also what makes the step ceiling of §5.1 viable.

## 4. The verdict

**The number fits, and it fits with margin — but not for the reason the paper assumes. The phone
confirms it.**

§10.3 says *"interpreted lattice mathematics is much slower than native"*. That is true: **26–29×**
under an interpreter on x86, **46–54×** on ARM. What the paper does not consider is that
**determinism and interpretation are separate things**. Wasm fixes the semantics; the JIT reproduces
it bit for bit on x86-64 and ARM64 just like the interpreter —for integer code there is no freedom
the compiler can take. The real penalty of the property §6.6 needs (I1: the fixed machine, the open
list) is:

- **3.2–3.7×** on x86
- **2.95–3.51×** on ARM

Not 29×, and not 50×.

Translated into what §6.1 needs: if a light node can spend **a quarter of a core** verifying
signatures —the rest goes to the acceptance predicate of §6.2, the network and the bilateral
settlement of §6.5—, the ceiling in transactions per second is:

| regime | ML-DSA-44 from bytes, x86 | ML-DSA-44 from bytes, **phone** |
|---|---|---|
| bytecode + JIT | ~640 tx/s | **~640 tx/s** |
| interpreted bytecode (wasmi) | ~80 tx/s | **~42 tx/s** |
| pessimistic interpreter (pulley) | ~30 tx/s | **~25 tx/s** |

The ceiling with JIT is **the same on the phone as on the desktop PC**. The interpreted ceiling is
cut in half, for the reason in §5.5.

Against a chain that in §10.2 **already accepted finality in minutes or hours**, even the worst row
is more than enough. A chain of that class is not fighting for 10,000 tx/s. **The open problem of
§10.3 does not topple §6.1, and it drops to §10.1** with the conditions of §5.1 and §5.4 written
down.

## 5. What the test found and was not looking for

Five things, and the first is a protocol hole, not a measurement.

### 5.1 The gauntlet of §6.6 does not bound the cost of what it installs — and it should

The work request says *"deliver an implementation that meets this interface and these vectors"*. The
predicate verifies **correctness**. Nothing verifies **cost**. A correct but ten times slower
implementation passes the gauntlet, survives the window (nobody breaks it: it is correct) and stays
installed forever. At that moment the budget of §6.1 breaks *from inside the protocol*, with no fork,
no attacker and without any rule being violated.

The fix is cheap and needs no new machinery: **the acceptance predicate has to include a VM step
ceiling**, not a wall-clock one. The count of executed instructions is deterministic and reproducible
—§3.2 confirms it across architectures—, so it qualifies as a predicate under §6.2 and as a trigger
under I2. Wall-clock time would not qualify; VM steps would.

Without that, the loop that solves cryptographic obsolescence can kill the governance property the
same chapter uses to solve the validator problem.

### 5.2 The hard limit is not cryptographic, it is a platform policy — and it costs twice what it said

Android allows JIT; **iOS does not allow it to third parties**. And since here the bytecode arrives
*at runtime* from the chain, it cannot be AOT-precompiled before publishing the app either. A light
node on an iPhone is forced into the interpreter.

The previous version of this section estimated that cost at ~8×, with x86 data. Measured on the
phone, it is **double**:

| | x86 (previous estimate) | ARM (measured) |
|---|---|---|
| ML-DSA-44 | 7.9× | **15.3×** |
| ML-DSA-65 | 8.2× | **15.5×** |
| ML-DSA-87 | 8.1× | **15.7×** |

(wasmi / cranelift ratio; with pulley instead of wasmi the gap is larger still)

That breaks nothing, but it corrects a sentence of §6.1. *"Replacing whoever refuses costs one
phone"* is true; what is not true is that all phones cost the same. The blocking coalition still
cannot last —entry is still cheap— but the cost of entry is **~15×** depending on which side of the
duopoly the device is on. It goes to §10.1 as an assumed decision, not to §10.3.

It is the finding that justifies having run the phone stage: it was a claim about phones made with
desktop data, and the real number is twice as bad.

### 5.3 Expanding the key weighs more than verifying the signature

In ML-DSA, 59% of a verification from bytes goes on expanding the matrix Â from ρ with SHAKE128 (107
µs total against 44 µs of pure verify, level 44, x86). On ARM the proportion is similar: 111 µs
against 52.5 µs. It is the operation `decode` does and `verify_only` skips.

Caching expanded keys per account **multiplies the ceiling by 1.6×** and is free: it does not touch
consensus, it is node-local state. It is the only large performance lever that appears without
touching a single rule, and the paper does not mention it.

### 5.4 A corollary already measured in `Chain`

Falcon / FN-DSA verifies with integers but **signs with floating point**. PoD's `ARCHIVO.md` already
measured that bit-for-bit reproducibility between ARM and x86 only holds with `+ − × ÷` and without
transcendentals. If the gauntlet admits candidates without restricting that, the loop of §6.6 can
install a primitive that breaks the determinism everything else depends on. **The specification of
the machine (I1) has to forbid or canonicalize floating point before the gauntlet runs for the first
time** — it is a condition on Geminis, and Geminis is the only thing that cannot be changed
afterwards.

### 5.5 The ratios between engines do depend on the hardware

The previous version of this document claimed that *"the ratios between engines do not depend on the
hardware; the magnitudes do"*. Measured, **it is false in general** — and true only where the verdict
needs it, which is luck and not design.

Penalty against native, same cell (`decode+verify`, ML-DSA-44), both machines:

| engine | x86 | ARM | change in the ratio |
|---|---|---|---|
| `cranelift` | 3.66× | 3.51× | **0.96×** |
| `pulley` | 78.6× | 88.4× | 1.13× |
| `rv32im` | 112.8× | 95.1× | 0.84× |
| `rv64imac` | 69.5× | 105.0× | **1.51×** |
| `wasmi` | 27.4× | 53.6× | **1.96×** |

Only `cranelift` keeps its ratio. `pulley` stays within 13%. The other three move between 0.84× and
1.96×, in both directions.

Two consequences:

**For the verdict:** §4 rests exactly on the only stable row of the table. That makes it firm, but it
was not predictable before measuring — and there is no reason of principle why Cranelift had to be
the stable row. If the paper had bet on the interpreter, extrapolating from x86 would have been wrong
by 2×.

**For the design:** `pulley` is also a pure interpreter and only loses 13%, so `wasmi`'s degradation
is not a property of interpretation but of its dispatch on ARM64. **The choice of interpreter —not
the decision to interpret— is what has to be measured on the target hardware** before committing. And
`rv32im` against `rv64imac` over the same interpreter design separate by 1.8× on changing host, which
means the choice of register width for the small ISA cannot be decided on a desktop either.

## 6. How the dirty cells were detected

A good part of the phone runs came out contaminated, and separating signal from artifact required two
invariants. They are written down because they are needed for reproduction.

**Invariant 1 — ns per step.** `steps_per_verify` is deterministic, so `ns_per_verify /
steps_per_verify` has to be constant per engine. On ARM: **3.11–3.19 ns/step** for `rv32im` and
**5.85–6.00** for `rv64imac`. Any cell outside that range is contaminated, with no exception. One
cell gave 14.7 ns/step and another 19.7.

**Invariant 2 — `compile_ms`.** Clean gives 335–344 ms for cranelift and 364–381 for pulley.
Contaminated gives 1310–1450: exactly 4×, which is the ratio between a Cortex-A78 and a Cortex-A55.
It is the trace of migration to the small cluster. Careful: `compile_ms` is measured at the start of
the cell, so a clean value does not guarantee the later measurement is clean too.

**An internal consistency check** that caught an entire run: `rv32im` level 65 `verify_only` (1.47 M
steps) came out slower than level 87 `verify_only` (2.22 M steps). Less work, more time. Impossible.

### 6.1 Two different causes, and one of them is not thermal

The contamination has two origins that behave the opposite way from each other:

**(a) Migration to the small cluster.** Variable between runs, ~4× factor, given away by
`compile_ms`. It is thermal and scheduler-related.

**(b) Degradation from a long process.** **Reproducible to four significant figures** —`native · 65 ·
decode+verify` gave 696,591 and 696,761 ns in two different runs— and therefore **not thermal**: a
run with 45 s of cooling before each block did not move it by 0.02%. It affects only `decode+verify`
at levels 65 and 87, which are the paths that reserve the largest matrix Â on each call. The
best-fitting hypothesis is memory fragmentation —wasmtime reserves enormous virtual regions per
store, and bionic's allocator degrades with many VMAs— but **it is unproven**. It is a defect of the
harness, not a result about the system being measured.

What was proven in the negative: **level 87 has no special behaviour whatsoever**. Isolated and cold,
`native · 87 · decode+verify` gives 306,884 ns, that is 1.06× the x86, in line with all the other
cells. The 1.18–1.23 ms of the long runs were an artifact.

**And the pause was counterproductive.** Inserting 45 s of sleep between blocks makes Android's
governor lose track of the process and relocate it to the small cluster on waking. The run with
pauses came out *worse* than the run without pauses.

**The recipe that works: one cell per process, no pauses, charger unplugged.**

## 7. What is missing

Three cells of the ARM table without a clean measurement: `cranelift · 44 · verify_only`, `pulley ·
44 · verify_only` and `pulley · 65 · verify_only`. None sustains a conclusion —Cranelift is measured
cleanly in five cells and they all say the same thing— so it is table tidiness, not missing evidence.

They are completed with two passes per cell, taking the minimum per row (this system's noise has a
single sign: it can only make things slower, never faster):

```bash
~/host-jit 44 decode+verify > celdas-1.csv
for c in "44 verify_only" "65 decode+verify" "65 verify_only" "87 decode+verify" "87 verify_only"; do
  ~/host-jit $c | grep -vE '^#|^engine|^$' >> celdas-1.csv
done
```

What is **not** needed: nothing more to decide. The verdict of §4 does not depend on those three
cells.

Out of scope and noted in case it comes back: the cause of §6.1(b) is still undiagnosed.

---

## Reproduce

`telefono/` is the complete and self-contained package: `pqcore/` (the verification, shared),
`guest/guest.wasm` (223 KB), `guest-rv/` and `guest-rv64/` (the RISC-V ELFs) and `host/` (the
six-engine harness). The three guests are **embedded in the binary** with `include_bytes!`, so the
executable is a loose file with no path dependencies. It calibrates iterations up to passing 1.2 s
per measurement and reports the median of 5.

The harness accepts filters to measure a single cell:

```
host                        the complete matrix
host 87                     only ML-DSA-87
host 87 decode+verify       only that cell
host --pausa 45             cooling between blocks (DO NOT USE, see §6.1)
```

### On x86

```
cargo run --release --features jit
```

### On the phone

The interpreter alone (`wasmi` + native + RISC-V) compiles under Termux without a problem:

```
pkg install -y rust
bash telefono/correr.sh
```

**With JIT it does not compile under Termux.** `cranelift-codegen` overflows rustc's stack —in the
*parser*, not in codegen: the ARM64 backend that generates ISLE has blocks nested to a depth
`rustc_parse` cannot take— and raising `RUST_MIN_STACK` up to 1 GB is not enough. It has to be
cross-compiled from the PC:

```
rustup target add aarch64-linux-android
cargo build --release --target aarch64-linux-android --features jit
```

The linker configuration is in `telefono/host/.cargo/config.toml`, and it points at `clang.exe`
directly rather than at the NDK's `aarch64-linux-android30-clang.cmd` wrapper, which has a bug: it
computes the binary's directory and then overwrites it with empty just before using it, so it ends up
looking for `clang.exe` in the PATH.

Afterwards the executable is copied to the phone and `chmod +x`'d **inside `~`**: shared storage
(`/storage/emulated/0`, which is what Termux exposes at `~/storage/`) is mounted `noexec` and does
not accept the execute bit. Compiling or running from there does not work, with or without root.

### The raw CSVs

| file | what it is |
|---|---|
| `resultados_pc.csv` | x86, four engines with JIT |
| `resultados_rv_pc.csv` | x86, with both RISC-V interpreters |
| `test2.csv` | ARM, no JIT |
| `test2-jit.csv` | ARM, six engines |
| `test2-87dv-frio.csv` | ARM, cell 87 `decode+verify` isolated and cold |
| `test2-limpio.csv` | ARM, run with pauses — **contaminated**, see §6.1 |
