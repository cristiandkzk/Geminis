# The challenge queue — does it saturate?

**English** · [Español](RESULTS.es.md)

**Status: closed (17/8/2026). It closes, and with the strong condition.**

Script: `saturacion.py`. No external data, reproducible.

---

## 1. What was being asked

The hard ceiling on the delay to lock-in (§7.4 of `CONTEXTO.md`) had been noted down with this
condition: *"for it to close, the challenge queue must **not be saturable**"*. Later the form of
per-node queues with overflow appeared, which gives a **bounded** delay and not an impossible one —
two different things. The question was whether the ceiling closes anyway with the weak version.

**The attack that has to be killed is not delaying.** Delaying is already bounded by the ceiling
itself: whatever happens, lock-in occurs after `F_max` blocks. The real attack the ceiling *creates*
is **censoring**: filling the verification capacity with garbage challenges so that a **legitimate**
challenge does not get processed within `F_max`, and then the fraud becomes firm. That is exactly
the residue §7.4 declares: *"a fraud discovered after the ceiling does not stop the transition"*.

So the computable question is: **can an attacker keep the queue full for `F_max` blocks?**

## 2. The result, and it is not the expected one

**It cannot, and the reason is structural, not parametric.**

> **Filling is serial. Draining is parallel.**
>
> A challenge does not exist until it enters a block, so the ceiling for filling is the capacity of
> the chain, `T` transactions per block — a single pipe. Draining is done by the `N` PoD nodes **in
> parallel**, because PoD verification reproduces bit for bit on any hardware (§6.1) and anyone can
> take any challenge.

```
fill  ≤ T                        (one chain, one block at a time)
drain = N · h · T / γ            (N nodes, each with headroom h)

margin = drain / fill = N · h / γ
```

with `h` = extra work a node does per block besides verifying the whole block, and `γ` = the cost of
verifying a challenge measured in equivalent transactions.

**The queue cannot accumulate backlog while `N · h > γ`.** It is not that the attacker loses money
saturating: it is that **they cannot saturate**, because the drain is `N` times wider than the tap.

### Critical N (Table B)

| γ | h=0.05 | h=0.10 | h=0.25 | h=1.00 |
|---|---|---|---|---|
| **1** | 20 | **10** | 4 | 1 |
| 2 | 40 | 20 | 8 | 2 |
| 10 | 200 | 100 | 40 | 10 |
| 100 | 2,000 | 1,000 | 400 | 100 |

With `γ = 1` and `h = 0.10`, **ten PoD nodes** are needed for the queue to stop being saturable. And
`h = 0.10` is conservative by a large factor: Test 2 measured 640 tx/s with **a quarter of a core**
on an 8-core phone, so the real headroom is several multiples of the block, not a tenth.

> **Note of 20/8/2026 — Phase 3 ran this formula with a real queue, and found an assumption in it.**
> Nothing above is rewritten: the model is correct and so is its arithmetic. What the implementation
> showed is that **`drain = N·h·T/γ` assumes the `N` nodes do not step on each other**, and this
> measurement does not say so because it had no reason to — it is a model of capacities, not of
> assignment.
>
> Run with nodes that choose: with **partition by hash** it gives the ten on the nose, but that
> requires knowing how many nodes there are, which is exactly what a design without a validator set
> does not have. **At random, with no coordination, eleven are needed**, and the backlog stabilizes
> instead of growing. And with the rule anybody would write —*oldest first*— the `N` nodes verify the
> same challenge and **no number of nodes is enough**.
>
> The ten of this table is still the correct theoretical floor. What was missing was a condition on
> how each node chooses, and **it was written into §6.3 the same day**. Detail in
> `geminis/liquidacion/RESULTS.md` §3.

## 3. The piece that holds it all up: the VM step ceiling

`γ` is the deciding parameter, and it is not free.

`γ > 1` means a challenge costs **more to verify than to create** — the classic
denial-of-service asymmetry against the verifier. If it existed, the attacker would buy cheap
verification work and critical `N` would grow linearly with `γ`.

**The VM step ceiling of §10.1 is exactly what forbids it.** A challenge that exceeded the ceiling
is invalid on its face, so verifying it costs at most what creating the disputed interaction cost:
`γ ≈ 1`.

> That ceiling was in the paper for another reason —bounding the cost of verification on light
> hardware—. It turns out to be **the condition the challenge queue's non-saturation depends on**.
> It is worth writing down, because nobody would guess it reading §10.1.

The `γ = 10` and `γ = 100` rows of Table B are there to see the counterfactual: what would happen
**without** the ceiling. It is the difference between needing 10 nodes and needing 1,000.

## 4. The other two pieces, and what each one does

The three conditions that had been proposed have different jobs and are not interchangeable:

| piece | what it kills |
|---|---|
| any PoD node resolves any challenge | it enables parallel draining — without this there is no `N` in the formula |
| **FIFO + flat bond** | *"capital buys priority"* |
| **VM step ceiling** (§10.1) | `γ ≈ 1`, which is what makes critical `N` small |

**The bond does not have to be large, only non-zero.** It is a cost and not a bid: it is lost if the
challenge does not verify, and *"does not verify"* is deterministic —§6.3/§6.4—, so no judge and no
administrative criterion is needed.

And there the asymmetry of Table D appears, which is the one that turns the problem around:

| | valid challenge | garbage challenge |
|---|---|---|
| verifies | yes | no |
| bond | **comes back** | **is burned** |
| cost of 10,000 | **0** | 100 (at b = 0.01) |

**The honest challenger can flood for free; the attacker cannot.** The honest one can send a
thousand copies of a valid proof and it costs them nothing, because the bonds come back. It is the
first time in the whole session that an asymmetry plays entirely on the right side without needing
identity.

## 5. The regime where it does saturate, and why it does not matter

Below critical `N` —with `γ = 1` and `h = 0.10`, fewer than ten PoD nodes— the queue does saturate,
and there Table C holds: censoring `F_max = 100` blocks (~17 min) costs sustaining 6,400 challenges
per block, that is, 640,000 burned bonds.

But that regime is the bootstrap one, and with fewer than ten PoD nodes the chain has bigger
problems than this. **It is not a hole in the mechanism, it is the same family as the cold start**,
and it closes the same way as the rest: with the day-1 distribution, which puts nodes in place
before there is anything to attack.

## 6. Verdict

**The hard ceiling closes, and it does not need the weak version of the condition.** The original
condition —*"the queue must not be saturable"*— **is met**, only not by the design of the queue but
by the geometry of the system: serial fill against parallel drain, with `γ` bounded by the ceiling of
§10.1.

Corrections this calculation forces in the previous note:

1. The form is not *"per-node queues with overflow"* — that is an implementation detail. **What
   closes it is that verification is parallel and injection is serial.** Overflow between nodes is
   the consequence, not the cause.
2. The condition was not weakened from *"not saturable"* to *"bounded delay"*. **The strong one is
   met.**
3. The VM step ceiling (§10.1) goes from being a performance decision to being **a security
   condition of §6.3**.

## 7. Assumptions, declared

- `T = 6,400` tx/block, from Test 2 (640 tx/s measured on a Motorola Edge 40 Neo) with a 10 s block.
  The paper does not fix block time; the result does not depend on it, because `T` appears in fill
  and in drain and cancels out in the margin.
- The attacker can use **100% of the block space** for garbage. That is generous: in reality they
  compete for space with real transactions and pay a fee for each one.
- `h ≥ 0.10` per node. Conservative by at least an order of magnitude according to Test 2.
- It is not modelled that the attacker runs PoD nodes that refuse to drain. There is no need: a node
  that does not work does not censor, it just does not work — the challenge remains available to any
  other. That is the reason why the first condition (any node resolves any challenge) is necessary.
