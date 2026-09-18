# Phase 4 — results

**English** · [Español](RESULTS.es.md)

**Run on 20 and 21/8/2026.** The criteria are in `CRITERIA.md`, written beforehand and untouched
afterwards. The protocol's reference hardware: the Test 2 phone (Motorola Edge 40 Neo, Cortex-A78,
Termux). **Every figure that decides anything is measured there**; the x86-64 desktop appears only
where the comparison between machines is the point.

| criterion | verdict |
|---|---|
| **C1** the budget fits under block load | **passed**, 354 ms out of 1,500 on the phone |
| **C2** floating point forbidden before the first run | **passed**, with two corrections |
| **C3** the count reproduces between x86-64 and ARM64 | **passed**, all 7 vectors identical |
| **C4** no input causes a panic | **passed**, with two amplifications corrected |
| **C5** the ceiling cuts, and cutting is a verdict | **passed** |
| **C6** out of range is a trap, not a wrap | **passed** |
| **C7** the step is an honest unit | **FAILED by 23×** |

**C7 is the result of the phase.** It moved three constants of Geminis, lowered the block's capacity
from 67 to 15 transactions, left open a problem the paper did not have, and uncovered **a wall in the
design**: the second ceiling, written as a constant, excluded primitives instead of making them more
expensive. That last one is the only thing that touched the core, and it was closed on 21/8.

---

## What ended up in Geminis

| what | before | now |
|---|---:|---:|
| `R_declarado` | 300 M steps/s, constant | **a measured curve**, 70 M at the Geminis point |
| page budget | — | **96**, and it is a ruleset parameter |
| `tx_por_bloque` | 67 | **15** |
| step ceiling | 6,716,417 | **7,000,000** |

| primitive | steps | margin in steps | pages | margin in pages |
|---|---:|---:|---:|---:|
| ML-DSA-44 | 3,339,364 | **2.10×** | 26 | **3.7×** |
| ML-DSA-65 | 5,379,218 | 1.30× | 40 | 2.4× |
| ML-DSA-87 | 9,111,691 | 0.77× — gets in by paying capacity | 65 | 1.48× |

**The ceiling in steps barely moved; what changed is how many guaranteed steps a second of clock
buys.** Since the cost in steps of a verification is set by the ISA and not by the ruleset, lowering
the declared rate leaves fewer transactions per block.

---

## C7 · The step was not an honest unit

### What was measured, on the reference hardware

Seven mixes, each an infinite loop that stops at exactly the step asked of it — **the measuring
instrument is the ceiling itself**. Worst of three passes.

| mix | M steps/s | vs ML-DSA |
|---|---:|---:|
| `mul` | 326.6 | 1.23 |
| `aritmetica-revuelta` (eight random opcodes) | 325.4 | 1.22 |
| `addi-uniforme` | 322.7 | 1.21 |
| **`ML-DSA-44` (the real load)** | **266.0** | **1.00** |
| `divu` | 197.7 | 0.74 |
| `lw-secuencial` (2 KiB, all in L1) | 186.3 | 0.70 |
| **`lw-persecucion` (96 pages)** | **82.1** | **0.31** |
| `lw-persecucion` (with no page ceiling) | *cut off* | — |

Without the page ceiling that last one ran at **11.3 M steps/s**: the ceiling promised 22 ms per
transaction and the mix took **596**. The chain falls behind deterministically and no invariant sees
it, because none of that is incorrect: it is slow.

### Why gas does not fix it

The obvious way out —weighting each step by instruction class— **does not work, and the table itself
says why**: `lw-secuencial` runs at 186.3 and `lw-persecucion` at 82.1, and **it is the same
opcode**. What separates them is not which instruction it is but where the data falls, and that is
not read off the binary: it is known only by running it. A per-class weight would have to charge
every read the price of the worst one, and then ML-DSA —which is full of accesses that do hit cache—
would stop fitting.

The only thing countable while it runs is **the distinct pages it touches**.

### The working-set curve

| pages | region | M steps/s | vs ML-DSA |
|---:|---:|---:|---:|
| 4 | 16 KiB | 163.6 | 0.63 |
| 16 | 64 KiB | 125.5 | 0.48 |
| 32 | 128 KiB | 101.1 | 0.39 |
| 48 | 192 KiB | 86.2 | 0.33 |
| **96** | **384 KiB** | **80.8** | **0.31** |
| 256 | 1 MiB | 79.3 | 0.30 |
| 512 | 2 MiB | 77.6 | 0.30 |
| 1024 | 4 MiB | 10.9 | 0.04 |

It falls sharply up to ~64 pages, then is almost flat, and **collapses between 2 and 4 MiB** —the
reach of that core's TLB—. That is where the hole the ceiling closes is.

### That counting pages is enough: measured, and this time properly

| layout (96 pages) | aarch64 | x86-64 |
|---|---:|---:|
| contiguous | 81.4 | 78.9 |
| scattered over 64 MiB | **81.4** | 65.4 |

**On the reference hardware, scattering costs nothing: 1.00×.** Counting pages is enough and there is
no need to bound the dispersion as well.

### And the text is not the binding lever

| text | M steps/s | vs ML-DSA |
|---:|---:|---:|
| 4 – 32 KiB | 246.1 | 0.94 |
| 128 KiB | 196.2 | 0.75 |
| 512 KiB | 166.6 | 0.64 |
| 1 MiB | 163.3 | 0.63 |

A large binary walked with unpredictable jumps makes the **host's** cache miss without touching a
byte of the guest's memory. It is a real lever but a weak one: 163.3 against memory's 82.1. Noted and
left open.

---

## The page ceiling: why 96, and why it stopped being a constant

**This is the design finding, and it does not depend on any time measurement.**

| primitive | pages | with a ceiling of 48 | with a ceiling of 96 |
|---|---:|---|---|
| ML-DSA-44 | 26 | fits | fits (3.7×) |
| ML-DSA-65 | 40 | fits | fits (2.4×) |
| **ML-DSA-87** | **65** | **out** | fits (1.48×) |

With 48, ML-DSA-87 was not left expensive: **it was left excluded, with no price to pay.** The step
ceiling is derived from the capacity, so an expensive primitive gets in by lowering `tx_por_bloque`;
**the page ceiling is a constant, so it can only exclude**. That contradicts §6.6, which is the whole
mechanism.

With 96, ML-DSA-87 fits in pages (1.48×) and **not** in steps (0.77×) — that is, it gets in by
lowering the capacity from 15 to 11 transactions. A price, not a wall.

> **The page counts are exact and coincide across architectures**, so no run can move this criterion.
> It is the only one that survived: there was a second —*the highest ceiling for which the reference
> hardware is still the binding one*— that gave the same number and **fell**, because it rested on a
> broken measurement. See below.

> **Closed on 21/8/2026.** While the budget was a constant, a primitive that needed more than 96
> pages had no price to pay. Now Geminis freezes **the curve** of rate against memory and the budget
> is a ruleset parameter: asking for more pages lowers `R_declarado`, which lowers the step ceiling,
> which is paid for in capacity. **The Geminis point did not move** —96 pages, 15 tx, 7,000,000
> steps—; what changed is that now every point has a price:
>
> | pages | KiB | declared `R` | tx at 2× |
> |---:|---:|---:|---:|
> | 32 | 128 | 87 M | 19 |
> | **96** | **384** | **70 M** | **15** |
> | 512 | 2,048 | 67 M | 15 |
> | 1,024 | 4,096 | 9 M | 2 |
> | 4,096 | 16,384 | 3 M | 1 |
>
> **From 96 to 512 pages memory is almost free and the next step divides the capacity by seven** — it
> is the TLB cliff, and the mechanism charges for it without anyone declaring it.

---

## Where `R_declarado = 70 M` comes from, and the three times it was wrong

It is a **requirement on implementations**, not a measurement: whichever runs slower is out of spec.
It has to stay below what the reference hardware sustains with the worst admissible program, and that
is now measured directly: **80.8 M steps/s**, with three independent measurements within 1.6% of each
other (`mezclas` 82.1, `conjunto` §4 81.4, `conjunto` §1 80.8). The lowest is taken and 70 is
declared, **13% below**.

**It was not raised to 75 on seeing that the measurement came out better than the estimate.** The 70
was fixed before that run; raising it after a favourable result is what section 4 of the roadmap
forbids.

The three previous versions, and what was wrong with each:

| value | where it came from | what was wrong |
|---:|---|---|
| 300 M | `steps_per_verify` ÷ 10.57 ms on the phone | the rate of **one** mix, ML-DSA's |
| 120 M | 316 M × ratio measured on x86-64 | **two different interpreters** —the 316 is from the unhardened one— and the desktop is not the reference |
| **70 M** | worst mix measured on the phone | — |

**The two ceilings and the range checks cost 1.19×** on the real load: the 10.57 ms of Test 2 became
12.55 on the same phone. That is the price of having a consensus machine instead of a benchmark
interpreter, and it was not measured.

---

## C1 · The budget under block load, on the phone

| stage | total ms | ms per tx | % of the budget |
|---|---:|---:|---:|
| admission | 26.2 | 1.01 | 1.7 |
| verification | 327.4 | 12.59 | 21.8 |
| **chargeable** | **353.6** | | **23.6** — margin **4.24×** |

### The penalty the criterion anticipated does not exist

The criterion said that measuring one verification and multiplying is no good, because *"a single
verification lives in a warm cache"*. **Measured on both architectures, it costs nothing:** the same
warm verifications in one instance give 12.55 ms/tx against the block's 12.59 — **1.00×** on the
phone, and 0.99×–1.06× on the desktop.

The explanation is in the number C7 gave: **one verification touches 104 KiB**, and that fits in
cache even if it arrives cold. What the criterion feared was the key, and the key is the small thing
beside the algorithm's working set.

> **The measurement cannot detect the effect the criterion named, and that has to be said.** They all
> use the same key/signature pair, because the Test 2 guest manufactures its material with a fixed
> seed. **The only thing that would distinguish the block from the warm loop —different material per
> transaction— is precisely what was held constant.** About cold memory the result is conclusive;
> about the other it says nothing.

---

## C3 · Closed

The seven vectors give identical results on x86-64 and aarch64: canonical verdict, steps, pages and a
fingerprint of the 32 registers plus 4 KiB of memory. The fingerprint is there because the count
alone is not enough —two different semantics can retire the same number of instructions and leave
different registers, and those are the ones that fork without anyone seeing them—.

The large vector is a stream of 200,000 pseudorandom instructions over the whole ISA, with operands
that feed back; `division-bordes` separately pins down the cases RV32M defines and other ISAs leave
as traps. It is reverified with one command:
`cargo run --release --bin vectores verificar`.

---

## C2 · Floating point, and two corrections that came from running it

Passed, but **the first implementation bounced the real binary twice**, and both times the correction
was to the check and not to the binary:

1. **rejecting every word that does not decode** bounces on the alignment padding of `.text`, which
   is zeros. Padding is not an offence → it is rejected by **opcode space**;
2. **sweeping the executable pages** bounces it on a `.rodata` constant: the linker puts `.text` and
   `.rodata` into the same read-only-executable `PT_LOAD` → the **sections** with `SHF_EXECINSTR` are
   swept, and **the predicate format requires the binary to declare where its code is**.

Eight major opcodes are frozen —`0x07`, `0x27`, `0x2F`, `0x43`, `0x47`, `0x4B`, `0x4F`, `0x53`—: all
of F, D and Q plus A's atomics. **Closing the space is stronger than not implementing it:** the day
someone wants to add floating point they have to break a declared constant, not add a branch. And it
is not forbidden for being expensive: **rounding is the only operation of an ISA where two correct
implementations can differ**, and one ulp between two nodes is a fork.

---

## C4 · No input causes a panic — and two amplifications

Passed: every truncation of the real ELF and 6,660 mutations of its headers return `Ok` or `Err`,
none aborts. But the sweep took minutes, and **that was the finding**:

1. **`admitir` reserved 64 MiB before validating a single header.** A three-hundred-byte ELF with the
   right signature and the rest garbage cost that reservation;
2. **an altered section header could force 128 MiB of predecoding**, declaring megabytes of code that
   do not exist.

Both are amplification: cheap input, expensive work. **A `panic` takes down a node; this stalls it**,
which in a network of light nodes is almost the same. No correctness test would have found either —
what found them was the test being slow.

---

## How it was measured wrong, four times

The whole `R_declarado` sum is **a ratio between two rates**, and every way of measuring one worse
than the other corrupts it. All four pushed in the same direction: the unsafe one.

1. **the reference was measured with a single short call** while the mixes calibrated up to half a
   second. It gave 268 M in one run and 194 in the next;
2. **the reference was measured at the end**, with the processor already hot: ~20% slower;
3. **C1 compared the block against a rate from another execution**, and reported a cache penalty of
   1.20× that was entirely noise;
4. **the pointer chasing was not chasing anything.** `addi`'s immediate is twelve bits signed: with
   the low twelve bits of the address ≥ 2048, adding them subtracts 4096. The chain started on the
   previous page, read a zero, and from there every `lw` followed the zero pointer — **always reading
   the same address, always in L1**. It reported 194 M steps/s, which is exactly the rate of
   `lw-secuencial`.

**The fourth is the worst and the most instructive.** Nothing failed: a mix degenerated into another
one and kept reporting a credible number. It was caught by crossing two tools that had to coincide
and did not, and two already-written conclusions had rested on it —*"scattering costs 1.07×"* and
*"48 pages is where the curves cross"*—, both false.

What was put in place so that it does not repeat silently:

- **each mix declares how many pages it has to touch and is verified on finishing.** It is what would
  have caught this on the first run: a measurement has to declare what it is measuring;
- the address-loading idiom was moved into a function with the correct rounding;
- **each mix runs three times and the worst is reported**;
- the reference is measured **first and cold**, and in the form a node uses —one batch the size of a
  block, not a long loop—.

---

## What this phase left open

**It is not known which hardware is the worst case.** The whole design assumes the light layer is the
binding one —that is where the cheap node entry of §6.1 comes from— and on that assumption
`R_declarado` is calibrated. Measured, it is false for adversarial memory patterns:

| pages | aarch64 | x86-64 | who is worst |
|---:|---:|---:|---|
| 48 | 86.2 | 122.2 | phone |
| 96 | 80.8 | 78.9 | **desktop** |
| 512 | 77.6 | 40.6 | **desktop, by 1.9×** |

From 96 pages upward the desktop runs the worst mix more slowly than the phone. **Two machines are
not enough to fix a hardware floor**, much less with the spread the desktop has: the same measurement
gave between 44 and 79 M steps/s depending on when it was run, against 1.6% on the phone.

That is why it is declared as a boundary and **not absorbed into `R_DECLARADO`**, which is calibrated
on the hardware the protocol declares as reference. Closing it needs more machines, not more
analysis.

---

## Update 12/9/2026 — a third point, and this time it breaks C1

**Machine:** Amlogic S805 (Cortex-A5, 32-bit ARMv7), generic MXQ board, DDR3, Android 4.4.2.
Cross-compiled (`armv7-unknown-linux-musleabihf`, static) from a PC with `cross`, run directly on the
board without Termux (Android 4.4 does not support it).

### C1 — it is no longer a question of margin, it breaks

| run | admission + verification | % of the budget |
|---|---:|---:|
| 1 | 2,499 ms | 167% |
| 2 | 2,486 ms | 166% |
| 3 | 2,479 ms | 165% |

**Worst of three: 2,499 ms out of 1,500 (1.67× over). FAILED.**

Against the phone's margin of 4.24× (353.6 ms), this is the first machine where the budget **does not
fit at all** — not a smaller margin, a real breach. The steps per verification (3,339,442) coincide
with those already measured on another architecture: the interpreter is still deterministic, the only
thing that changed is the clock.

### C7 (`mezclas`) — which mix is the worst changes

| mix | phone (M steps/s) | MXQ (M steps/s) | ratio MXQ/phone |
|---|---:|---:|---:|
| addi-uniform | 322.7 | 26.9 | 0.083 |
| scrambled arithmetic | 325.4 | 27.0 | 0.083 |
| mul | 326.6 | 26.1 | 0.080 |
| divu | 197.7 | **8.1** | 0.041 |
| lw-sequential | 186.3 | 15.6 | 0.084 |
| lw-chasing (96 pp.) | 82.1 | **8.2** | 0.100 |
| ML-DSA-44 (real) | 266.0 | 21.8 | 0.082 |

On the phone the worst admissible mix is `lw-chasing` by a good margin (82.1 against the second
worst's 197.7). On the MXQ, `divu` (8.1) comes in **below** `lw-chasing` (8.2) — almost tied, with
`divu` in front. Phase 4's page ceiling was designed to make the memory pattern more expensive; it
does not touch division, which does not step on a single extra page. It is a candidate second
bottleneck the current design does not charge for, on in-order cores with no division pipeline.
**Small margin (1.2% between the two): confirm with more runs before treating it as established — it
was not repeated three times as §4 of the roadmap asks.**

The binary itself also computes a "translated" C7 —this machine's worst/ML-DSA ratio (0.370) applied
to the phone's real rate (266)— and gives "passed" with 29% of margin. **That sum is not a second
opinion on whether the MXQ is good enough: it answers a different question** (whether the relative
risk would stay bounded running on the phone) and it does not contradict that C1 has already failed
here in absolute terms.

### `conjunto` — there is no cliff

On the phone, between 2 and 4 MiB of region the machine falls 86% (77.6 → 10.9 M steps/s): its TLB
limit. On the MXQ, the same range falls by barely 2% (4.2 → 4.1) — because it comes in flat already
from much smaller regions (16 KiB: 15.1 M steps/s, already an order of magnitude below the phone's
peak). **The worst case is not a slower version of the same pattern: the shape of the curve changes
with the class of hardware**, not only the scale.

### `paginas` — the count holds

| primitive | steps | pages | KiB |
|---|---:|---:|---:|
| ML-DSA-44 | 3,339,442 | 26 | 104 |
| ML-DSA-65 | 5,379,293 | 40 | 160 |
| ML-DSA-87 | 9,111,768 | 65 | 260 |

It coincides between the runs made on this same machine; the determinism of steps and pages is not in
question, only the clock speed.

### What this leaves

Three machines and one already breaks the budget. The problem declared on closing Phase 4 —*"it is
not known which hardware is the worst case... closing it needs more machines, not more analysis"*—
remains open, but now with a concrete point: **an Amlogic S805 is out of spec** under the parameters
in force, and the mechanism that gives it away (division, not memory) is different from the one that
motivated the second ceiling. It is still not absorbed into `R_DECLARADO` — it is a boundary, and the
boundary moved.

---

## How to reproduce

```
cd geminis/predicado/vm
cargo test --release                 # C2, C4, C5, C6 and the regression — 18 criteria
cargo run --release --bin mezclas    # C7
cargo run --release --bin conjunto   # what it depends on, and the working-set curve
cargo run --release --bin paginas    # the page count of the three levels
cargo run --release --bin bloque     # C1
cargo run --release --bin vectores verificar   # C3

cd geminis && python verificar.py    # 197 criteria, including that the two languages agree
python herramientas/mutar.py         # 21 mutations, all caught
```

On the phone, `python herramientas/empaquetar_vm.py` assembles the package: the crate is not
self-contained, because the ELF of the Test 2 guest lives outside its folder.
