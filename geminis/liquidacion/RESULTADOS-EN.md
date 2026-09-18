# Phase 3 · ordering and settlement

**Run on 20/8/2026.** The three roadmap criteria, written before running them.

```
cd geminis
python verificar.py fase3       # the three criteria
python herramientas/cola.py     # the measurement of the queue under attack
```

---

## 1 · The double spend is prevented by the lock, with no global order — ✅

Two different properties, and the second is the one that gets forgotten.

**The lock.** Committing takes it out of the available: `disponible = saldo − comprometido`.
Publishing an offer commits in the same act, so an open offer already taken **has nothing left to
pay a second party with**. Nobody arbitrates which transaction goes first — the second one simply
does not have enough.

**And with no global order does not mean with the order undefined.** It means that two interactions
that do not share collateral **give the same state in any order**, and that is falsifiable with two
fingerprints: `(alice→carol, bob→carol)` and its inverse are run, and the ledger's fingerprint
coincides. Each account carries its own sequence; advancing Alice's index does not touch Bob's.

---

## 2 · The double signature publishes the private key — ✅

`s₁ = k + e₁·x` and `s₂ = k + e₂·x` with the same nonce give `x = (s₁ − s₂)/(e₁ − e₂)`. **One
subtraction and one division**, with what is on the chain and nothing else.

The mechanism is that **the nonce is derived from the account index**. If it were random, signing
twice at the same index would be an accident with no consequence and the fraud would have to be
detected and punished from outside; derived, the punishment is executed by any third party moved by
the loot — the same pattern as the canary of §6.6 and the challenger of §6.3.

What the tests pin down, besides the recovery: that **different indices leak nothing**, that signing
the same message twice is not a double signature —it is the same signature—, and that the group is
**rederived** rather than trusting the constants, with the same discipline as the canary:
`q = 2¹²⁷−1`, `p = 2·j·q+1` with the smallest `j` that gives a prime, `g` with the smallest `h` that
gives order `q`.

> **It is not production cryptography and does not claim to be**: the group is 134 bits, chosen so
> that the mechanism runs and can be read. The real primitive is chosen by Geminis (§6.6). What this
> demonstrates is **the property**, which is what the criterion asked for.

---

## 3 · The queue does not saturate — ✅, with a correction to the paper

The criterion said: *the measured margin is compared against the ten PoD nodes §6.3 predicts. If a
hundred are needed, the paper's prediction is wrong and that has to be said.*

**A hundred are not needed. One more is needed — or infinitely many, depending on a rule §6.3 did
not specify.**

`cola-impugnaciones/` had closed this **as a formula**: `margin = N·h/γ`, and with `γ = 1`,
`h = 0.10` ten nodes are enough. The formula assumes the `N` nodes **do not step on each other**, and
§6.3 does not say how they divide up — it cannot, because there is no validator set and no node knows
how many there are. Run with a real queue:

| how each node chooses | critical N | backlog in steady state (N=11) | mean wait |
|---|---|---|---|
| partition by hash | **10** = the formula | 0 | 0 |
| at random (no coordination) | **11** | 424 | 4.2 blocks |
| **oldest first** | **never** | grows ~90 per block | ramp of `9·T` |

**The natural rule is the one that collapses the mechanism.** *Oldest first* is what anybody would
write, and it makes the `N` nodes verify exactly the same challenge: with fifty nodes the same is
verified as with one.

**And in the only thing that really matters —whether the legitimate challenge is processed in time—
the failure is not a fixed term but a ramp.** With FIFO the backlog grows ~90 per block and drains at
10, so what arrives at height `T` waits on the order of `9·T`. Measured:

| arrives at height | 5 | 10 | 20 |
|---|---|---|---|
| wait (blocks) | 45 | 90 | 180 |

If the hard ceiling on the delay to lock-in (§10.1) falls below that ramp, the fraud becomes firm. It
is the residue §10.1 declares, happening for a reason that was not written down.

### The property that makes eleven enough

With random selection **the backlog does not grow without a ceiling: it stabilizes.** The longer the
queue, the less the nodes step on each other, so the effective drain rises on its own until it
matches the tap. With eleven nodes the equilibrium settles at ~424 challenges and a mean wait of four
blocks; with twenty, at 24 and two tenths. *The queue is long, not infinite.*

> **And there was a measurement trap there worth not stepping on again.** The first pass measured
> critical `N` with 80-block runs and gave **13**. It was an artifact: at 80 blocks the system had
> not yet reached equilibrium, so a backlog that was going to stabilize read as one that was growing.
> Measured by comparing **two run lengths** —250 and 500 blocks—, the real number is **11**. It was
> written into `satura()`'s docstring, and the tests compare two lengths and not one.

### What was written into the paper

§6.3 went from **two** conditions to **three**, and the third is this one: *each node picks in its own
order, and not in the queue's*. Arrival order solves **priority** —capital does not buy a turn— but
it does not say **what each node takes**, and there two sentences of the same section were colliding.
The rule that fixes it needs no coordination: each node walks the queue in a pseudorandom order
derived from its identity. **The paper's number changed from ten to eleven**, it was written that the
backlog stabilizes, and also why the exact alternative —dividing up the queue— is not available: it
requires knowing how many there are.

## Status of Phase 3

**Passed, three of three.** With a correction to the paper that did not come from an imagined attack
but from running the mechanism: **the measured margin is smaller than the calculated one, and the
difference depends on a rule that was not written down.**

What this phase does **not** cover, and it is declared: there is no economy —fees are abstract
units—, there is no VM (Phase 4), there is no permanence (Phase 5) and the queue is measured with a
model of nodes, not with nodes on a network. Going from this to a network is Phase 6, and with free
tokens it answers software and not economics.
