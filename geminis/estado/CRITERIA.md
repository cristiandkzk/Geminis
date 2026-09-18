# Phase 5 — pass criteria

**English** · [Español](CRITERIA.es.md)

**Written on 21/8/2026, before the first line of `permanencia.py`.** It is the rule of section 4 of
`ROADMAP.md`, and in this phase it weighs more than in any other: **the only control law for the rate
this project wrote fell over, and it was not toppled by an attack — it was toppled by correcting a
detail of the model it had been tested with.** A criterion written after seeing the result
accommodates itself to the result.

This file **is not edited after running**. What gets measured goes into `RESULTS.md`, beside it.

---

## The three from the roadmap

### A1 · The cycle closes completely

**Passed if** `create → pay → exhaust → evict → reactivate` runs all the way through and the object
comes back **byte-for-byte identical** to the one that went in. **Failed if** the reactivation returns
something different, however slightly: that would be partial confiscation by another name.

### A2 · The accumulator is hundreds of bytes **in total**, not per object

It is the condition that keeps eviction from being permanence bought more cheaply. A 32-byte
tombstone per object is 1 GB per node forever — a quarter of the budget.

**Passed if** the accumulator occupies **≤ 1 KiB with any number of evictions**, verified over three
orders of magnitude (10, 10,000, 1,000,000). **Failed if** it grows linearly, even with a small
constant.

### A3 · What it costs to keep the proof up to date, measured

It is the dependency §10.2 declares and cannot guarantee: the proof weighs less than a kilobyte and
storing it is free, but **the union of the siblings along a leaf's path is the whole tree minus that
leaf**, so it expires at the first block that touches anything else.

**Passed if the number gets written down, whatever it is** — how many updates per block, and what it
costs a permanently online agent. There is no threshold to pass: what fails is being unable to
measure it.

---

## The ones that are added, and why

### A4 · Double reactivation is stopped without a nullifier list

A nullifier list would be exactly the O(n) residue A2 forbids, coming in through another door.
**Passed if** reviving the same object twice fails, and fails **by checking against the active set**
—which is bounded by construction— and not against a list of spent ones.

### A5 · Nobody buys perpetual permanence with a finite payment

It is the property §8.5 declares as the justification for the whole section.

**Passed if** both:

- at most `L_max` can be bought at once, and buying again requires another operation at the price of
  the time;
- **the price per epoch does not fall on depositing more.** With a power rule, life grows faster than
  the deposit and the price per year tends to zero — a hundred floors would buy ten thousand years.
  The only thing volume can legitimately save is **paying the setup once instead of once per
  period**.

### A6 · The countdown is public and computable in advance

The same form as the distance to the trigger of I2, and for the same reason: **an announced eviction
does not generate pressure for a coordinated fix by hand, and a surprise does.**

**Passed if** how many epochs any entry has left can be queried, the answer is deterministic, and it
is **monotone** as long as there is no top-up.

### A7 · Evicting is not confiscating

**Passed if** all three: there is no burning of the asset on eviction; there is no overdrawn balance
—the protocol has no debtor to seize from—; and there is no auction, because auctioning forces the
chain to know what the object is worth, which is exactly what §7.6 forbids.

---

## The two that come from C18.5, and are the ones that can fail

Phase 4 closed the same ceiling twice with the same play: **the number is not chosen, it is derived;
what is frozen is the sum.** Out of that came a suspicion worth running against this phase before
calling any parameter free.

### A8 · The floor: knob or sum?

§8.5 already declares it derived —*"it is not a knob: it is the fixed cost of the create + evict
cycle"*— but the sum with measured numbers was never written. Now it can be: Phase 4 measured what
verifying a signature costs, and this phase measures what the two tree updates cost.

**Passed if** the derivation is written and gives the order of magnitude §8.5 claims —**some sixteen
hours of storage, 0.2% of a year**—. **Failed if** the number has to be chosen by eye, or if the sum
gives another order: in that case the one that is wrong is the paper, and the paper gets corrected.

### A9 · The rate: why can this one not be closed the same way?

It is the open problem of §10.3, and the roadmap says this phase is built with the rate
parameterized. Fine — but **leaving it at *"we don't know"* is forbidden**.

**Passed if** one of the two happens:

- the sum is written, as happened twice with the ceiling; **or**
- **why this one is not of that class** is written, with an argument that distinguishes it from the
  step ceiling verifiably, not by feel.

**Failed if** the result is that more thinking is needed. After two closures with the same play, not
knowing whether the third applies is information that can be produced.

---

## What this phase does NOT answer

- **What the initial level of the rate is.** It is a price, and §10.3 already says the chain cannot
  read it without violating I2. If A9 passes by the second route, this is closed as a boundary.
- **Whether anyone is going to run an archive.** §10.2 declares it: the protocol guarantees that an
  evicted entry *can* be revived, not that anyone will have what it takes.
- **Whether the control law is stable.** There is nothing to calibrate it with and that is the
  declared blockage.
