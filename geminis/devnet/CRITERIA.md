# Phase 6 — pass criteria

**English** · [Español](CRITERIA.es.md)

**Written on 21/8/2026, before the first line of the devnet.**

## First, because the roadmap demands it in writing

> **A devnet with free tokens answers software questions, not economic ones.** With worthless tokens
> there is no income, there is no hoarding, the elasticity of storage demand is not measured and the
> antispam is not tested. Worse: manufactured activity is indistinguishable from real demand —and
> there, on top of that, it is free—.

**Everything built here is disposable by declaration**, and it gets rewritten once it is known what
parameter space Geminis has to anticipate. **Reset date: the day the permanence rate rule is chosen**
(§10.3), because that is the number that changes the space.

## And the phase is narrowed, because two of its four questions are already answered

The roadmap says Phase 6 closes four mechanism questions. Two are already measured:

| question | where it was answered |
|---|---|
| the queue with a real `N` | Phase 3, eleven nodes with 10% headroom |
| the budget under real blocks | Phase 4, C1 on the reference hardware |
| **the real commutation under load** | **here** |
| **the eviction cycle** | **here** |

Running again what has already been measured adds no evidence and does add the temptation to stare at
the number until it comes out right.

---

## B1 · Commutation under load does not break the state

Phase 1 commuted over a still synthetic state. Here the chain is doing things while it commutes:
entries being charged permanence, objects expiring, the queue with open challenges.

**Passed if** the state crosses over **bit for bit identical** (I3) with load running, the lineage
keeps verifying (I4), and **no entry changes state by the mere fact of the commutation** — it is
neither evicted nor revived because the ruleset changed.

---

## B2 · The eviction cycle runs at scale and across a commutation

Phase 5 tested the cycle entry by entry. Here it runs with thousands, over epochs, and with a
commutation in the middle.

**Passed if** the cycle closes for all of them: none is lost, none is evicted before its deposit runs
out, and the accumulator stays in the hundreds of bytes.

---

## B3 · A deposit bought before the commutation is worth the same afterwards *(the one that can fail)*

**Here is the real risk of integrating, and no single phase saw it.** The deposit is bought in
**byte-epochs**; the epoch is counted in **blocks**; and `tiempo_bloque_ms` is an **internal
parameter**, that is, a transition can move it.

If a commutation changes the block time, the same epoch comes to last a different amount of real time
— and then **an already-paid deposit buys more or less storage than it bought**, without anyone
touching it. I3 says the state crosses over intact, and it does: the bytes are the same. What changes
is what they are worth.

**Passed if** the real storage a deposit bought does not change when the block time changes. **Failed
if** it changes — and in that case it has to be decided whether the epoch stops being counted in
blocks, whether `tiempo_bloque_ms` leaves the space, or whether the deposit is repriced in the
transition. None of the three is free.

---

## B4 · Eviction and the queue share a budget, and they were never measured together

Phase 3 measured the queue without permanence running; Phase 5 measured permanence without the queue.
**In a real node both come out of the same budget**, and §6.3 depends on there being headroom left to
drain.

**Passed if the number gets written down**: what fraction of the block the eviction cycle takes in
steady state, and how much headroom is left for the queue. No threshold to pass — what fails is being
unable to measure it.

---

## B5 · The commutation cannot evict anyone by surprise

§8.5 asks for the countdown to be **public and computable in advance**, because *an announced
eviction does not generate pressure for a coordinated fix by hand, and a surprise does*.

A commutation that changes the ceiling, the capacity or the block time **cannot shorten the life of
an already-paid entry** without notice. **Passed if** for every live entry, the countdown published
before the commutation is honoured afterwards.

---

## What this phase does NOT answer, and must not be confused

- whether anyone leaves the GPU switched on;
- what the elasticity of storage demand is;
- whether the currency gets hoarded;
- whether the antispam holds.

**That needs real money or external review, and it goes down another track.**
