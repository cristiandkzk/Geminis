# Phase 5 — results

**Run on 21/8/2026.** The criteria are in `CRITERIOS-EN.md`, written before the first line of mechanism
and untouched afterwards.

| criterion | verdict |
|---|---|
| **A1** the cycle closes completely | **passed**, and the object comes back byte for byte |
| **A2** the accumulator is hundreds of bytes in total | **passed**, 232 bytes with a million |
| **A3** what it costs to keep the proof up to date | **measured**: once per someone else's eviction |
| **A4** double reactivation without nullifiers | **passed** |
| **A5** nobody buys perpetual permanence | **passed** |
| **A6** the countdown is public | **passed** |
| **A7** evicting is not confiscating | **passed** |
| **A8** the floor: knob or sum? | **FAILED against the paper, by 9×** — and closed |
| **A9** the rate: why does it not close the same way? | **passed by the second route** |

**A8 is the result of the phase**, and it fails against §8.5 and not against the code.

---

## A8 · The floor is a sum, and the sum does not give what the paper says

§8.5 declares that the floor *"is not a knob: it is the fixed cost of the create + evict cycle"* and
claims a value: **some sixteen hours of storage, that is, 0.2% of a year**. The sum was never
written. Written, it does not give that.

### The sum

It equates two fractions of the same node, and **Geminis already declares both**:

- **of the computation** — the cycle consumes `C` steps and the node devotes `f*` of its rate to
  verifying, so it spends `C / (f* × R × epoch_duration)` of an epoch's computation;
- **of the disk** — storing the entry for one epoch occupies `size / state_budget`.

The floor is the quotient: **how many epochs of disk are worth what the cycle spends in
computation.**

> **There is no new number, but there is an assumption:** that the two fractions are equally tight,
> that is, that the node saturates both. It is what §6.1 builds on purpose by fixing both against
> what a phone has. If one had slack, the sum shifts towards the other.

### What it gives

| what goes into the cycle | steps | floor |
|---|---:|---:|
| signature + two updates (as the paper said) | 3,594,060 | **91.4 epochs** |
| **only the two updates** | **254,696** | **6.03 epochs** |

§8.5 claimed **0.67 epochs**. The sum gives **9× more**, and with the signature inside it gave 137×.

### Why the signature does not go in the cycle

**The signature is already paid for by the ad valorem fee of §6.1**, as in any transaction: charging
it again in the floor is charging it twice. And the error was not cosmetic — with the signature
inside, the floor came out at **3.7× the maximum deposit** `L_max` allows, that is, nearly the whole
cost of an entry would be paid at creation. It is exactly the charge on creation §8.5 discards two
paragraphs earlier, and for the reason it explains itself: *it does not reduce creation, it reduces
the registration of creation.*

With it taken out, the floor comes to **24% of the maximum deposit** and the structure of §8.5 holds.

### And the input that was missing, measured

The dominant term became how many steps a SHA-256 costs, and it was **estimated at 10,000**.

> **That estimate had been declared harmless for a circular reason.** The first version of
> `permanencia.py` said it did not matter *"because the signature verification dominates it"*. That
> held only while the signature was inside the cycle — and taking it out is precisely the correction.
> **The term discarded for being small became the only one left.**

It was measured the same way as `steps_per_verify`: a hand-written SHA-256, compiled to RV32IM
(`predicado/vm/guest-sha/`) and run on the machine of §6.6, subtracting two batches so that the call
frame does not count.

| | |
|---|---:|
| **steps per SHA-256 compression** | **4,898** |
| hashes per tree update | 26 |
| steps of the create + evict cycle | 254,696 |
| that, against one signature verification | 8% |

The estimate was **2× too high**, that is, in the conservative direction. The count is exact and
architecture-independent, and it is fixed as a regression in `predicado/vm/tests/criterios.rs` for
the same reason as `steps_per_verify`: **the floor hangs off that number**, and if the machine's
semantics moved without anyone noticing, the floor would be badly calibrated and there would be no
way of knowing.

> **Incidentally, the SHA-256 guest is the second independent load to pass through admission.** C2
> and C4 had been tested against the Test 2 guest, which another repo produced; this one is produced
> by ours. A criterion verified against a single binary proves less than it looks — and the two
> corrections C2 needed came precisely from hitting a real binary.

---

## A9 · Why the rate does not close with the same play

Phase 4 closed the same ceiling **twice** with the same play —*the number is not chosen, it is
derived*— and out of that came the suspicion of C18.5. Run against this phase, it separates the two
numbers cleanly, and **the reason is verifiable and not a feeling**:

> **The step ceiling could be closed because both its sides were physical**: steps on one side,
> seconds on the other, and the chain can count both without asking anyone anything. **The rate has a
> physical side —bytes × epochs— and a monetary one —how many tokens that is worth—, and no sum
> crosses those two sides without reading a price.** Reading a price is exactly what I2 forbids, and
> it is the same wall §7.6 declares for the pool.

The proof that the argument is not rhetoric is that **it is visible in the types**: everything
`permanencia.py` computes is in byte-epochs or in epochs, and nowhere does a monetary unit appear.
The day one appears, it appears with an oracle beside it.

### And out of that comes a decision of form that was not in the paper

**The floor is denominated in storage epochs, not in tokens.** If it were in tokens it would be a
**second** free parameter alongside the rate, and two prices would have to be chosen instead of one.
In storage epochs it inherits whatever rate is in force, and stops being a separate decision.

That reduces the open problem of §10.3 to a single number: **the rate, and only its level.**

---

## A2 and A3 · The accumulator, and what the archive costs

| evictions | peaks | bytes in the state |
|---:|---:|---:|
| 10 | 2 | 72 |
| 10,000 | 5 | 168 |
| 1,000,000 | 7 | **232** |

It grows with the logarithm. The contrast that justifies it: **a 32-byte tombstone per object would
be 1 GB per node forever**, a quarter of the budget of §10.1.

And A3, with no threshold to pass because §10.2 promises none: **the proof expires on every other
eviction, with no exception.** With the initial capacity —15 tx per block, 14,400 blocks per epoch—
the ceiling is **216,000 rebuilds per epoch**. It is enough for a permanently online agent, which is
the declared audience, and it is not enough for a person.

> **This criterion existed and proved nothing, and the mutation harness found it.** The revalidation
> against the current peaks could be deleted and no test fell over. A proof that does not prove is
> worse than not having one, because it also gives confidence.

---

## Two things that were fixed for being slow

1. **`desalojar` built the proof on every insertion** — O(n) per object. A million evictions took 32
   seconds and made the mutation harness unrunnable. But the problem was not one of performance: **a
   node evicts and proves nothing**; building the proof is the work of whoever archives (§10.2). Taken
   out, the same million takes 2.9 s.
2. **The mutation harness leaves mutated files if it is interrupted.** It happened, and the suite
   started failing for a reason that was not the real one. A `finally` is not enough when the process
   is killed from outside, so now it can be asked: `python herramientas/mutar.py --limpio`.

---

## Status

**230 criteria, 20 in Rust and 28 mutations, all caught.** What remains of the phase, and it is what
the roadmap declares: the rate's control law is not chosen and there is nothing to calibrate it with.

## How to reproduce

```
cd geminis
python verificar.py fase5           # this phase's criteria
python verificar.py                 # all 228
python herramientas/mutar.py        # 28 mutations
python herramientas/mutar.py --limpio   # did anything stay mutated from an interrupted run?
```
