# The parameters of §8.5 — calculation

**English** · [Español](RESULTS.es.md)

**Run on 18/8/2026.** Reproduce with `python parametros.py`. No external data.

**The question.** §8.5 was left written with three parameters unfixed: the **floor `F`**, the **rate
`r0`** and the **duration of the epoch**. Of each one the same thing is asked: is it a decision, or
is it a consequence of something already measured?

**The short answer: none of the three is what it looked like.** The epoch almost dissolves, `F` is
derived, and `r0` is not a number — it is a control law. What remains to be decided is **a single
policy number**, and **a new collision** appears that had not been seen.

---

## Assumptions, all declared

The same ones as `expiracion-estado/` and `amortizacion-mint/`, plus three about hardware:

| assumption | value | why |
|---|---|---|
| state entry | 128 B; budget 4 GB → **33,554,432 slots** | those of the previous measurements |
| signature verification | 391 µs, against a quarter of a core | Test 2, ARM64 with JIT |
| hashing on the phone | 100 MB/s | conservative for the light layer |
| sequential write | 200 MB/s | likewise |
| divisibility / supply | 1e8 / ~1e6 tokens | Bitcoin's; the supply on the order of the pools of C7.6 |

**What is deliberately not assumed: any price of the token in an external currency.** Everything
that depends on that is marked as *not computable by the protocol*, and that mark is half the
result.

---

## A · The epoch: what binds it, and what does not

**The charge does not bind it.** Discounting the balance of each entry by sweeping the state costs
rewriting and rehashing the whole thing:

| operation | cost per epoch |
|---|---|
| writing 4 GB at 200 MB/s | 21.5 s |
| rehashing 4 GB at 100 MB/s | 42.9 s |
| **total** | **64.4 s** |

With a ten-minute epoch that is 10.7% of the node's time — and worse: **it expires every
reactivation proof in every epoch**. It is not needed: by storing the deposit and the creation
block, the balance is computed **on read**, in O(1), with no writes and invalidating nothing.

**The eviction queue does not bind it.** In steady state, evictions happen at the rate of creations:
9,193/day = **0.11 per second**, with a `pop` in 25 comparisons. It is not a load.

**One single thing binds it: the floor of representable price.** The rate per epoch has to be an
integer number of minimum units, or rounding has to be defined — a determinism surface not worth
opening. That minimum integer fixes how cheap storage can be:

| epoch | minimum `r0` (token/year) | full state, % of supply/year |
|---|---|---|
| 10 minutes | 0.00052560 | **1.76%** |
| 1 hour | 0.00008760 | 0.29% |
| **1 day** | **0.00000365** | **0.0122%** |
| 30 days | 0.00000012 | 0.0004% |

With a ten-minute epoch the floor already costs 1.8% of the supply per year, which is too much for a
floor. **With a one-day epoch there are three orders of margin left.**

> **The epoch is still a choice, and it is the only one of the three — but it is cheap: one day
> settles it.**

---

## B · Why `r0` cannot be a fixed number

`r0` is a **nominal** price; the resource it rations —disk over time— is **real and constant**. With
the token floating, the real price of storage goes in the wrong direction both times. Real price of
an entry-year with `r0` frozen:

| year | +50%/year | +20%/year | −20%/year | −50%/year |
|---|---|---|---|---|
| 3 | 3.38× | 1.73× | 0.51× | 0.12× |
| 5 | 7.59× | 2.49× | 0.33× | 0.03× |
| 10 | **57.67×** | 6.19× | 0.11× | **~0** |

If the token appreciates, storing becomes prohibitive and the state empties out; if it depreciates,
storing is free and it fills up. In both cases the protocol lost control of the only variable it
cares about, which is **occupancy**.

It is the same defect that already killed the nominal floor of the auction in C7.10 —*nominal in a
currency that appreciates*— and it is why every chain with a fixed fee ended up in a fee market.

> **A fixed nominal price cannot ration a real resource under a floating currency.** `r0` has to
> move, and there is only one variable it can be indexed to without breaking I2: **state
> occupancy**, which is a fact of the state and not a market reading. It is the doctrine of §7.6
> applied to disk — target the quantity, let the price float.

---

## C · `r0` as a control law

```
r0(t+1) = r0(t) · (1 + k · (θ − θ*) / θ*)     bounded to ±clamp per epoch
```

The form of EIP-1559 applied to disk instead of to gas. A **×3** demand shock at epoch 100, with the
elasticity `ε` declared and swept because it cannot be measured without a network:

| k | clamp | ε | overshoot | return to ±5% |
|---|---|---|---|---|
| 0.05 | 12.5% | 1.0 | 1.16× | 172 epochs |
| 0.125 | 12.5% | 0.5 | 1.09× | 88 epochs |
| 0.125 | 12.5% | 1.0 | 1.07× | 90 epochs |
| 0.25 | 12.5% | 1.0 | 1.04× | does not leave the band |

The loop absorbs the shock **without oscillating**. The gain `k` moves the speed, not the stability;
the clamp is what prevents a one-epoch spike from moving the price.

> **`r0` is not a number computed once: it is a control variable.** What has to be chosen is `θ*`,
> and that one is policy.

---

## D · The floor `F`, derived

The fixed cost an object imposes on the network besides disk is the **create + evict** cycle,
measured against the node's budget and expressed in hours of storage, which is the unit `r0` is
denominated in:

| component | hours of storage |
|---|---|
| verifying the creation's signature | 14.6 |
| updating the tree on creation | 0.6 |
| updating the tree on eviction | 0.6 |
| **F** | **15.8 h = 0.18% of an entry-year** |

And `F` is nailed down **from above** too, by §8.5's own argument: everything charged for creating
**beyond** the cost of creating is a charge on creation, and a charge on creation is evaded by
minting outside.

> **`F` is not a knob: it is a number.** No more —that would be a charge on creation— and no less
> —that would be subsidized churn.

**It corrects C7.11.** There the floor was described as *"an antispam parameter, that is, policy"*.
With §8.5 written it is no longer that: **the antispam is done by the deposit**, because creating N
objects costs N deposits. The floor only covers the cycle.

---

## E · The new collision: the burn channel

With `r0` indexed to occupancy, **an attacker who fills state raises the price for everyone** — and
since the deposit is consumed by being burned, that accelerates third parties' burn. The burn enters
`emitido − quemado`, which is what the trigger reads (§7.6). That is: **it is possible to pay to
accelerate**.

The right question is not whether the channel exists —it does— but how much **leverage** it gives.
With `s` the fraction of the state the attacker occupies and `ε` the elasticity of honest demand,
the control has to raise `r0` by `R = (1/(1−s))^(1/ε)`:

```
leverage = ((1−s)/s) · ((R−1)/R)
```

| s | ε=0.25 | ε=0.5 | ε=1.0 | ε=2.0 |
|---|---|---|---|---|
| 5% | **3.52** | 1.85 | 0.95 | 0.48 |
| 25% | 2.05 | 1.31 | 0.75 | 0.40 |
| 50% | 0.94 | 0.75 | 0.50 | 0.29 |

> **The leverage is of the order of `1/ε`.** With elastic demand the attacker never burns more of
> other people's than of their own. With **inelastic** demand —people who need their asset alive at
> whatever price— the leverage grows and the channel becomes real.

And `ε` cannot be known before having a network. So **this is not closed with a number**: either it
is declared as a boundary, or the channel is cut by excluding the permanence burn from the trigger's
accounting — the second with its own cost, because it breaks the clean definition of §7.8,
*circulating supply is issued minus burned, with no exceptions*.

---

## Verdict

1. **The epoch almost dissolves.** It is bound neither by the charge (lazy reading is O(1) against
   64 s of sweeping) nor by the queue (0.11 evictions/s). It is bound only by the floor of
   representable price, and **one day settles it with three orders of margin**.
2. **`F` is derived:** ~15.8 hours of storage, 0.18% of an entry-year. Nailed from below by the cost
   of the cycle and from above by the anti-evasion argument of §8.5. **It corrects C7.11:** the
   antispam is done by the deposit, not the floor.
3. **`r0` is not a number.** A fixed nominal price cannot ration a real resource under a floating
   currency. It has to be a control law over occupancy — stable with a 12.5% clamp per epoch.
4. **A single policy decision remains: `θ*`**, the target occupancy. How much disk the chain wants
   to occupy on the entry hardware.
5. **And a collision remains that had not been seen**, and it is the only thing that can topple the
   control law: the burn channel, with leverage ~`1/ε`. It has to be decided **before** adopting the
   indexation, not after.
