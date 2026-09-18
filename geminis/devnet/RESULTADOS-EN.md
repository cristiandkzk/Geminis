# Phase 6 — results

**Run on 21/8/2026.** The criteria are in `CRITERIOS-EN.md`, written before the first line of the
devnet.

> **Disposable by declaration.** A devnet with free tokens answers software questions, not economic
> ones. **Reset date: the day the permanence rate rule is chosen** (§10.3), because that is the
> number that changes the parameter space Geminis has to anticipate.

| criterion | verdict |
|---|---|
| **B1** commutation under load does not break the state | **passed** |
| **B2** the eviction cycle at scale and across a commutation | **passed** |
| **B3** a deposit is worth the same after commuting | **FAILED**, and corrected |
| **B4** eviction and queue share a budget | **measured**: 3.01% of the block |
| **B5** the commutation does not evict by surprise | **passed** |

**B3 is the result of the phase, and it is exactly what the phase exists to find:** a coupling no
module test could see, because it requires a commutation to happen while there are live deposits.

---

## B3 · The deposit was bought in a unit the ruleset could reinterpret

The deposit was carried in **byte-epochs**. The epoch is counted in **blocks**. And
`tiempo_bloque_ms` is an **internal parameter**, that is, a transition can move it.

Measured, with an entry that bought ten epochs:

```
block of  6,000 ms  ->  240 hours of real storage
block of 12,000 ms  ->  480 hours, with the SAME deposit
```

**The same deposit bought twice the storage**, without anyone touching it.

### The uncomfortable part is that no invariant saw it

**I3 was met.** The state crossed over intact: the deposit's bytes are exactly the same before and
after, and the commutator verifies it by fingerprint and by object identity. What changed was not the
state but **what that state is worth** — and none of the five looks at that.

It is the same class of thing as the page ceiling (C18): the mechanism was doing something the design
forbids, and it was doing it silently because no sum pointed it out.

### The correction, which is the usual one in this design

**Denominate the deposit in declared byte-seconds**, converting with `tiempo_bloque_ms`.

And the fine point is why that does not violate I2: **`tiempo_bloque_ms` is not a clock reading, it is
a parameter the ruleset declares.** The chain does not measure time — it uses the number it fixed
itself, just as it uses `R_declarado` for the ceiling. It is the same move for the third time: **use
the declared quantity instead of the derived one.**

With that:

| | before | after |
|---|---|---|
| real storage a deposit bought | changes with the block time | **does not change** |
| countdown in epochs | fixed | **adjusts**, because the epochs last something else |
| `L_max` | 25 epochs | 25 days of real time |

That the countdown in epochs **does** change is correct and necessary: if blocks take twice as long,
the same real life is half the epochs. What cannot change is the real life.

`L_max` moved for the same reason: if it were in epochs, changing the block time would change how much
can be prepaid — and the cap exists precisely so that one cannot bet against the rate.

---

## B4 · What eviction takes away from the queue

Phase 3 measured the queue without permanence running; Phase 5 measured permanence without the queue.
**In a real node both come out of the same budget.**

Worst case: the state full and nobody topping up, so everything expires within `L_max` and the whole
set is evicted every 25 epochs.

| | |
|---|---:|
| evictions per block in steady state | **99** |
| steps per block | 12,661,007 |
| block budget | 420,000,000 |
| **fraction of the block** | **3.01%** |

**97% is left** for everything else, against the 10% of headroom Phase 3 measured the queue needs to
drain with eleven nodes. It does not bind.

> The number comes out of the Phase 5 measurement —4,898 steps per SHA-256 compression, 26 hashes per
> tree update— so **it is not an estimate**: it moves only if that one moves.

---

## B1, B2 and B5 · What held

- **the state crosses over with load running** and the commutator keeps verifying I3 by fingerprint
  and object identity;
- **no entry changes state by the mere fact of commuting** — it is neither evicted nor revived
  because the ruleset changed. The only thing that evicts is the deposit running out;
- **the cycle closes for all 500**: none is lost, none is evicted before running out, and the
  accumulator stays below a kilobyte;
- **revival works after the commutation**, with the proof against the accumulator, and double
  reactivation fails against the active set;
- **the countdown published before commuting is honoured afterwards**, for all of them.

---

## And the mutation harness found another criterion that proved nothing

It was possible to **walk the active set in hash order** when evicting, and no test fell over.

That is a fork: **two nodes would put the evicted ones into the accumulator in different orders and
their roots would not coincide.** And it is one of the ones that hide well, because a dictionary
traversal by hash **looks deterministic within one process** and is not between two.

It is the third time in two days that the harness has found an empty criterion —before it was the
float check with the escape in the wrong place (C17.7) and the revalidation of the reactivation proof
(C19.8)—. **All three were criteria that existed, had a name and proved nothing.**

---

## Status

**246 criteria in Python, 20 in Rust, 31 mutations, all caught.**

## How to reproduce

```
cd geminis
python verificar.py fase6      # this phase's criteria
python verificar.py            # all 246
python herramientas/mutar.py   # 31 mutations
```
