# Creation floor and amortization rate — calculation

**Run on 18/8/2026.** Reproduce with `python amortizacion.py`. No external data.

**The question.** The proposal to be measured: minting cannot be free —there is a **creation
floor**, and the floor has to be **raisable**— and **the more you deposit, the lower the
amortization rate**. How much volume discount can be given without giving away the disk?

**The short answer: all three parts of the proposal are correct, but the third only in one of its
two possible forms.** The floor goes in; that it be raisable goes in; and the decreasing rate
**already comes out on its own** from a two-part tariff, with a hard floor at the real cost.
Written as a power rule, it does not: it sends the price of storage to zero and makes exactly the
attack that matters cheaper.

---

## Assumptions, all declared

| assumption | value | why |
|---|---|---|
| unit of account | **multiples of the floor** `D0` | so as not to invent a price for the token |
| unit of time | `L0` = life at the floor, normalized to 1 year | normalization, not a claim |
| state entry | 64 / 128 / 256 B | the same ones as `expiracion-estado/`, swept for the same reason |
| disk budget of a node | 2 / 4 / 8 GB | it sustains the cheap-entry argument of §6.1 |
| cost of creating | one signature verification: **391 µs** (Test 2, ARM64 with JIT) | against a quarter of a core — the same pair that gives the ~640 tx/s of §6.1 |
| replication | 3,000 nodes | the figure the paper uses when discussing concentration |
| cap on the receipt of §7.2 | 3,500 (3,000 PoD + 500 compute) | what was decided in C7.6 |

**The rule being measured**, which is the natural way of writing *"more deposit, less
amortization"*:

```
r(D) = r0 · (D0/D)^α        burned per epoch
L(D) = D / r(D)             life of the asset
```

with `k = D/D0`, it comes out `L(k) = L0 · k^(1+α)` and `price per entry-year = D0/L0 · k^(−α)`.
`α = 0` is no discount; `α = 1` is the strong version of the intuition.

---

## A · What each deposit buys

**Life bought, in years:**

| k | α=0 | α=0.25 | α=0.5 | α=1 |
|---|---|---|---|---|
| 1 | 1 | 1 | 1 | 1 |
| 10 | 10 | 18 | 32 | 100 |
| 100 | 100 | 316 | 1,000 | **10,000** |
| 1,000 | 1,000 | 5,623 | 31,623 | **1,000,000** |

**Price per entry-year, as a % of what whoever deposits the floor pays:**

| k | α=0 | α=0.25 | α=0.5 | α=1 |
|---|---|---|---|---|
| 10 | 100% | 56.2% | 31.6% | 10.0% |
| 100 | 100% | 31.6% | 10.0% | 1.0% |
| 1,000 | 100% | 17.8% | 3.2% | **0.1%** |

With `α = 0` a century can also be bought — but a century is paid for. **The difference between the
rules is not that one sells permanence and the other does not: it is the price per year.**

> **With any α > 0 the price per year tends to zero as the deposit grows: permanence stops costing
> what it costs.**

And that is exactly the defect §10.1 already names in other words — *a residue that compounds is not
a fix, it is a loan*.

---

## B · What exactly the discount makes cheaper

Occupying **all** the chain's slots for 100 years, buying one entry per slot with the minimum
deposit that withstands that horizon (4 GB / 128 B → 33,554,432 slots):

| α | floors per slot | total capital (floors) | vs α=0 |
|---|---|---|---|
| 0 | 100.0 | 3,355,443,200 | 1.0× |
| 0.25 | 39.8 | 1,335,825,998 | 2.5× |
| 0.5 | 21.5 | 722,908,323 | 4.6× |
| **1** | **10.0** | **335,544,320** | **10× cheaper** |

The discount does not make everything cheaper equally: **it makes cheaper precisely the only
operation that buys life in volume**, which is filling every node's state and never letting go.

It is the same form as the fixed fee §6.1 rejects as regressive —*"it makes the large request
free"*— but in the dimension of time instead of that of value. And the resource is capped: **the
discount creates no disk, it only reassigns it to whoever has more capital.** That is a capital
moat, which is what §6.1 exists to avoid.

---

## C · What creating really costs, measured in storage time

To know whether the floor covers a cost or is policy, **creating** (one signature verification
against the node's CPU budget) is measured against **storing** (the entry against the disk budget),
and the first is expressed in units of the second. Signature budget: 639 verifications/s.

| budget | entry | creating is equivalent to storing |
|---|---|---|
| 2 GB | 256 B | 3.6 hours |
| 4 GB | 128 B | **14.6 hours** |
| 8 GB | 64 B | 58.3 hours |

> **The fixed cost of creating is real but tiny: less than one day of storage**, against assets that
> claim to live for years.

**Consequence for the floor:** the floor **is not a costing**, because there is no fixed cost to
cover. It is an **antispam parameter**, and it has to be one — point 4 of C7.10 had already
anticipated it: the ad valorem fee of §6.1 does not bite on a mint, because a newly created asset is
worth ~0. **That it can be raised is correct: it is the only antispam knob minting has.** But it has
to be called by its name.

---

## D · The version that keeps the intuition without giving away storage

A two-part tariff, which is how any resource with a fixed setup cost and a linear permanence cost is
priced:

```
price(L) = F + r0 · L         F = floor, r0 = real linear cost
average rate = F/L + r0       ← falls with L, and never goes below r0
```

**The intuition comes out of this on its own and does not have to be postulated**: what falls when
buying more life is the floor spread over more time. With the floor equivalent to 10 years of
storage:

| life bought | average rate | vs paying for 1 year |
|---|---|---|
| 1 year | 11.00 · r0 | 100% |
| 10 years | 2.00 · r0 | 18% |
| 100 years | 1.10 · r0 | 10% |

**The rate falls 10× — and never goes below `r0`.**

> **The discount has a floor, and that floor is the real cost of storing.** The only thing volume
> saves is paying the setup once instead of once per period. That saving is **bounded by the
> floor**; the power rule's is `k^α` and has no cap.

Life bought with a capital of 1,000 floors, to see both families together:

| rule | years of life |
|---|---|
| power α=0 | 1,000 |
| power α=0.5 | 31,623 |
| power α=1 | 1,000,000 |
| two-part (floor = 1 year) | 999 |
| two-part (floor = 10 years) | 9,990 |

The two-part tariff is also linear —just like α=0— but with the advantage that **the floor stays
explicit and separate from the price of storage**, so it can be raised for antispam without touching
the permanence rate. Which is literally what was asked for: *a floor, and that it be raisable*.

---

## E · The block 0 receipt does not conflict

| | |
|---|---|
| receipts of §7.2, hard cap | 3,500 |
| slots of the node (4 GB / 128 B) | 33,554,432 |
| occupancy | **0.0104%** |
| weight across the whole network (3,000 nodes) | 1.25 GB |

C7.6 decided that the claim receipt is **free**; this decides **floor + deposit** for open minting.
They do not contradict each other, and the reason is quantitative and not one of framing: **the
variable that separates the two cases is the cap.** With a hard cap the set is negligible and can be
free and perpetual; without a cap, it cannot.

---

## Verdict

1. **The floor goes in, and it has to be called by its name.** It does not cover a cost —creating
   costs 14.6 hours of storage— but rations: it is pure antispam, and it is the only knob minting
   has, because the ad valorem fee of §6.1 does not bite on an asset worth ~0. **That it be raisable
   is correct for the same reason.**
2. **"More deposit, lower rate" is correct as an observation and dangerous as a rule.** It comes out
   on its own from amortizing the floor over more time; postulating it as a power rule does
   something else entirely.
3. **Any α > 0 sends the price per year to zero**, and makes occupying every node's disk forever 10×
   cheaper (with α=1). It is the fixed fee §6.1 rejects as regressive, in the dimension of time.
4. **The form that closes is the two-part tariff:** a floor on minting (antispam, burned, raisable)
   **+** a permanence deposit consumed by being burned, at a linear rate. The average rate falls
   with the life bought —which is what was asked for— but with a floor at the real cost, and with
   the discount bounded instead of growing without a cap.
5. **The genesis receipt can still be free**, and not by exception: because of its hard cap.
