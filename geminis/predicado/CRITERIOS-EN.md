# Phase 4 — pass criteria

**Written on 20/8/2026, before the first line of the machine.** That is the rule of section 4 of
`ROADMAP-EN.md` and it is not bureaucracy: in this project the price of a criterion written after seeing
the result has already been paid once.

This file **is not edited after running**. What gets measured goes into `RESULTADOS-EN.md`, beside it.
If a criterion fails, it is written down that it failed and what is done about it — it is not
softened.

---

## The three from the roadmap

They come verbatim from Phase 4. Here they are made operable: each with a number and with the exact
way of measuring it, so that there is nowhere to accommodate.

### C1 · The budget fits under real block load, not in an isolated benchmark

`f* = 25%` of a 6 s block is **1,500 ms** to verify the 67 transactions of the initial ruleset. In
steps, that is already stated: `ceiling = 6,716,417` per transaction.

**Passed if** a block of 67 ML-DSA-44 `decode+verify` verifications runs in ≤ 1,500 ms of clock time
on the reference machine, measured **as a block**: 67 different key/signature pairs, one after
another, in the same process. **Failed if** one verification has to be measured and multiplied by 67
for it to work out.

> **Why the distinction matters.** A single verification lives in a warm cache with the key already
> in L2. Sixty-seven different 1.3 KB keys do not fit, and that is the difference between the
> benchmark and the block. It is exactly the error the roadmap's criterion names.

### C2 · Floating point forbidden before the gauntlet runs for the first time

It is a condition **on Geminis**, so it is not enough for floating point to fail: it has to be
impossible for it to get to run.

**Passed if** both things hold:

- the machine is RV32IM and **has neither F nor D**: there is not a single floating-point opcode to
  decode, verifiable by reading the integer decoder's `match`;
- a program containing a single floating-point word **is rejected at admission**, with **zero steps
  executed**. It is not rejected on reaching that instruction: it is rejected before starting.

**Failed if** floating point is only detected at execution time. A rejection at execution is a late
verdict: block budget has already been spent to discover it.

### C3 · The step count reproduces bit for bit between x86-64 and ARM64

**Passed if** the same ELF with the same inputs gives **the same number of steps and the same output
hash** on x86-64 and on aarch64. Exact equality; there is no tolerance.

---

## The four that were added on reading the interpreter that was going to be reused

The harness of `test2-interprete/telefono` measures an ISA with a **trusted** guest. A consensus
machine runs an adversary's programs, and that is four more properties. **Adding criteria is allowed;
softening them is not.** They are written here before running, just like the others.

### C4 · No input causes a `panic`

The harness's ELF loader indexes without checking. A truncated ELF makes it `panic`, and a `panic` in
a node is a crash — **a malformed transaction costs one transaction and takes down a node**.

**Passed if** a sweep over the real ELF —every truncation and a battery of altered bytes in the
headers— always returns `Ok` or `Err`, and **never** aborts the process.

### C5 · The ceiling cuts, and cutting is a verdict and not an error

A program that does not terminate has to stop at **exactly** `ceiling` steps, and both parties to a
challenge have to read the same thing.

**Passed if** a program in an infinite loop stops at exactly `ceiling` steps, with verdict
`TechoExcedido`, and that verdict enters the block hash like any other result. **Failed if** the
result depends on a clock, a timeout or a signal.

### C6 · Out of range is a trap, not a wrap

The harness does `address & MASK`: every invalid address wraps within memory. It is deterministic —so
it does not fork— but the behaviour **depends on the size of memory**, and the size of memory is a
parameter. The same program would give different results in two generations, and that breaks I1 in
the one place where it cannot be broken.

**Passed if** every access outside the declared region is a deterministic trap, and the size of
memory is a constant of Geminis and not a parameter of the internal space.

### C7 · The step is an honest unit *(the one that can fail)*

`R_declarado = 300 M steps/s` was derived from **one** instruction mix: ML-DSA's. If all steps are
worth one and a division costs twenty times an addition, an adversarial predicate made of divisions
and cache misses runs much more slowly per step — and then the ceiling promises a budget it does not
meet. The chain falls behind, deterministically, and no invariant sees it.

**Passed if** the slowest mix that can be constructed runs at **≥ 300 M steps/s**.

**Failed if** any runs below that. In that case the ceiling was over-promising and there are two ways
out, chosen after seeing the number and not before: lower `R_declarado` to the worst case —simple,
and it charges everyone the cost of the worst— or **weight the step** by instruction class with
weights frozen in Geminis, which is what gas does and costs a more expensive decoder.

> This criterion exists because the ceiling was closed yesterday with the data of a single mix. It is
> the most likely place for yesterday's sum to be wrong, so it is measured first and the result is
> written down whatever it is.

---

## What this phase does NOT answer

- **Whether the predicate of §6.2 is good for anything anyone would buy.** That is section 6 of the
  roadmap and it is not code.
- **What the predicate costs on a real node under a network.** There is no network here.
- **Whether the small machine is the right one at twenty years.** That is the I1 decision and it is
  not falsified with a measurement.
