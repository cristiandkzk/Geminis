# The node's budget, and what margin the loop asks for

**English** · [Español](RESULTS.es.md)

**Run on 18/8/2026.** Reproduce with `python medicion.py`. No external data.

**The question.** `θ*` was going to be fixed on three assumptions added up by eye —128 B of entry +
32 B of tree + 16 B of index = 176 B— and on a stability simulation. A measurement was asked for
before fixing it.

**The short answer: rightly asked.** Two of the three byte assumptions were wrong, and the C7.13
simulation was wrong in a way that invalidates its conclusion. **The control law, corrected, does
not converge** — and the cause is not one of tuning but economic.

---

## Assumptions, all declared

| assumption | value | why |
|---|---|---|
| hash | 32 B | addresses and metadata pointers are hashes: with post-quantum signatures the public key is not stored |
| hashing on the phone | 100 MB/s | conservative for the light layer |
| signature budget | ~640 tx/s | §6.1, measured in Test 2 |
| disk budget | 2 / 4 / 8 GB | swept |

---

## A · The layout: there are two classes of entry, not one

| OBJECT (the asset) | B | | BALANCE (one holder) | B |
|---|---|---|---|---|
| owner (public key hash) | 32 | | owner | 32 |
| asset identifier | 8 | | asset identifier | 8 |
| metadata pointer (hash) | 32 | | amount | 8 |
| permanence deposit | 8 | | permanence deposit | 8 |
| creation block | 8 | | creation block | 8 |
| supply | 8 | | | |
| divisibility + flags | 4 | | | |
| **sum → aligned** | **100 → 112** | | **sum → aligned** | **64 → 64** |

The 128 B were correct for the object. **For a balance they are too many: it is 64 B**, and that
distinction was not made in any previous measurement.

## B · The tree: the overhead is not a fact, it is a knob

Storing all the internal nodes (32 B per entry) was assumed. It is not needed: the levels above a
cut `d` are stored and the subtree of `2^d` leaves is recomputed. **The binding cap is updating, not
proving** — updating happens on every transaction.

| cut `d` | B per entry | hashing per operation | % of the hash budget |
|---|---|---|---|
| 1 (store everything) | 32.0 | 0.4 KB | 0.2% |
| **6** | **1.0** | 12 KB | **7.9%** |
| 9 | 0.125 | 96 KB | 62.9% |
| 12 | 0.016 | 768 KB | 503% |

> **The tree does not cost 32 B per entry: it costs ~1 B with the cut at `d=6`**, and the price is 8
> points of the node's hash budget. It is an implementation decision that has to be taken, not a
> cost that is suffered.

> **Note of 22/8/2026 — the byte table reproduced exactly, and the last sentence did not.** With the
> tree built (`geminis/estado/arbol.py`), the bytes per entry give 32.0 / 1.0 / 0.125 / 0.016 just
> as here. What does not hold is *"implementation decision"*: **the permanence floor of §8.5 is
> derived from the cost of updating the tree, and the floor is burned**, so two nodes with different
> `d` would not agree on how much was burned when creating an entry. `d` became a constant of
> Geminis (`CORTE_ARBOL`).
>
> And a third currency appears that this measurement was not looking at: **with `d=6` the floor is
> 77% of the maximum deposit, and with `d=7` it exceeds it.** The margin is finer than it looked
> looking only at disk and hashing. Development in `geminis/estado/RESULTS-TREE.md`.

## C · The eviction index

Binary heap of `(expiry, id)`: 16 B per entry. **Buckets per expiry epoch: 8 B** —the expiry is
implicit in the bucket, only the id is stored— and eviction also becomes O(k) over the k that
expire.

## D · The real capacity

| | entry | tree | index | total |
|---|---|---|---|---|
| active object | 112 | 1 | 8 | **121 B** |
| holder balance | 64 | 1 | 8 | **73 B** |

**31% less than the 176 B assumed.**

| budget | objects | balances | old assumption |
|---|---|---|---|
| 2 GB | 17.7 M | 29.4 M | 12.2 M |
| **4 GB** | **35.5 M** | **58.8 M** | 24.4 M |
| 8 GB | 71.0 M | 117.7 M | 48.8 M |

And the threshold of §10.1 —creations per day that exhaust the budget in ten years— goes back up to
**~9,700/day**, very close to the original 9,200.

---

## E · The corrected simulation topples the result of C7.13

The C7.13 simulation recalculated the life of **all** cohorts in every epoch: on raising the price,
it retroactively shortened terms already paid for. That cannot happen — whoever paid has their term.
Corrected, each cohort expires when it bought expiring. Sustained ×3 shock, 4,000 epochs, reference
life 200 epochs:

| k | ε | peak | tail (min–max) | final `r0` |
|---|---|---|---|---|
| 0.05 | 1.0 | 1.98× | 0.00 – 1.97 | 3,338 |
| 0.125 | 1.0 | 2.04× | 1.19 – 1.97 | 9e19 |
| 0.25 | 1.0 | 2.08× | 0.00 – 2.08 | 2e17 |

> **It does not converge at any gain.** Occupancy keeps oscillating between almost zero and more
> than double the target after 4,000 epochs, and `r0` runs off to meaningless values. The *"absorbs
> a ×3 shock without oscillating"* of C7.13 was an artifact of the model.

## F · Why it does not close, and it is not the controller's fault

Measured over that same run: **`r0` fell to 0.22 and the maximum life bought reached 897 epochs**
against a reference of 200.

> When the loop cheapens in order to fill, the life bought for the same outlay **lengthens** — and
> those slots stay taken for centuries at bargain prices. The loop cannot recover them afterwards,
> because they are paid for and evicting early would be confiscation.

**It is not a tuning problem: it is intertemporal arbitrage.** Prepayment with a floating price is
equivalent to *buying long when it is cheap*. And it also explains the dead time: moving the price
is only felt when the cohorts expire, and a proportional controller with hundreds of epochs of dead
time oscillates by construction.

## G · The fix, and the ceiling it leaves for `θ*`

If the life that can be bought **at once** is capped at `L_max` —and to stay alive it is topped up at
the price of the time— the arbitrage disappears and the dead time is bounded by `L_max`:

| `L_max` | ε | peak | tail (min–max) | does it close? |
|---|---|---|---|---|
| 10 | 1.0 | 1.43× | 1.00 – 1.00 | **yes** |
| 25 | 0.5 | 1.25× | 1.00 – 1.00 | **yes** |
| 25 | 1.0 | 1.48× | 1.00 – 1.00 | **yes** |
| 50 | 1.0 | 1.88× | 0.17 – 1.88 | no |
| 100 | 1.0 | 2.04× | 0.00 – 2.04 | no |

With an `L_max` of 25 epochs or less the loop **lands exactly on target**; with 50 it is marginal and
with 100 it breaks again. The threshold is on the order of **an eighth of the reference life**.

> **The cap on the life that can be bought stops being an economic recommendation and becomes a
> stability condition of the mechanism.**

And only with the loop closing does `θ*` have a derived ceiling. The worst peak among the
configurations that close is **1.48×**:

| θ\* | occupancy peak | does it fit in the budget? |
|---|---|---|
| 25% | 37% | yes |
| **50%** | **74%** | **yes** |
| 65% | 96% | yes, at the edge |
| 75% | 111% | **no** |
| 90% | 134% | **no** |

> **`θ* ≤ 67%`**, and that is a ceiling, not a recommendation. The margin between θ\* and 100% is
> not slack: it is where the peak of the first sustained shock lives.

---

## H · The admission auction, simulated against the same shock

**Run on 1/9/2026**, added to `medicion.py` (`bloque_h`). A candidate to replace the
occupancy-indexed law, discussed in `CONTEXTO.md` C22.4: instead of moving `r0` by the error
`(θ − θ*)`, each epoch a **fixed quota** of new state is admitted —it does not depend on `θ`— and
that epoch's price is the one that makes desired demand exactly equal that quota: a uniform-price
auction read off the demand curve. Every admitted entry lives **exactly `L_max` epochs**, with no
variable life, so the intertemporal arbitrage channel of E/F is eliminated by construction and not
by an external cap.

Same shock as in E: sustained ×3 from epoch 100, 4,000 epochs, quota calibrated for `θ* = 1.0` with
`L_max = 25` (`quota = 1/25`):

| `ε` | pre-shock `r0` | `r0` in shock | occupancy (min–max) |
|---|---|---|---|
| 0.25 | 1.00 | **81.00** | 1.0000 – 1.0000 |
| 0.50 | 1.00 | 9.00 | 1.0000 – 1.0000 |
| 1.00 | 1.00 | 3.00 | 1.0000 – 1.0000 |
| 2.00 | 1.00 | 1.73 | 1.0000 – 1.0000 |

**Occupancy does not move from target at any moment** —neither the minimum nor the maximum
post-shock departs from 1.0000—, because the quota is fixed: `θ = quota × L_max` at all `t` from
`L_max` onward. All of the shock's signal is absorbed by the **price**, not the quantity — the
opposite of the old law, where the quantity absorbed the signal and the price was left with no
information about whether the level made sense (C14.3).

**Compared against G with the same `L_max = 25`:** there the tail also closes at 1.00–1.00, but the
**peak** during the shock reaches 1.25×–1.48× — there is real overshoot, though transient, and
`θ* ≤ 67%` exists precisely to absorb it. Here there is no peak to absorb: the quantity never moves.

**Nor is there a time to return to the band or a tuning parameter** (`k`, clamp): the price jumps to
the clearing value in the same epoch as the shock and comes back in the same epoch in which the
shock ends, because there is no integrator and no memory — that epoch's equation is solved, an
accumulated error is not corrected.

> **It avoids the failure of C14.3** (occupancy pinned to target, with no reading of whether the
> level of `r0` makes sense) **and that of E/F** (arbitrage through variable life). **What it does
> not solve —and cannot—** is the absolute level: the result is still a number in units of
> normalized `r0`, just like the old law. That is fixed by C22 (`CONTEXTO.md`), not by this.

**What remains to be simulated before proposing it as a replacement rather than a candidate:** this
assumes a continuous and known aggregate demand curve (the same simplification E/F already used, not
a new one); a real auction coordinates discrete bids from individual bidders, and it would be worth
running a version with discrete bids and seeing whether the clearing result holds with few
participants. It also remains to be decided what the quota is when `θ*` changes through a transition
—here it stayed constant for the whole run— and what happens if desired demand falls **below** the
quota (the leftover quota: is it burned, accumulated, given away?).

---

## I · The auction with discrete bids — the noise is not controlled by oversubscription

**Run on 1/9/2026** (`bloque_i`). H assumes a continuous and known demand curve. Here each epoch
there are `N_cand` candidates with their own valuation —Pareto(`x_min`, `ε`), calibrated so that the
clearing price with no shock gives ~1.0 on average, same convention as H— and that epoch's price is
the **k-th highest** bid among those who showed up: no curve, just sorted bids and a cut at the
quota. Same ×3 shock from epoch 100, a 100-epoch post-shock window, 40 runs per cell.

| `k` | oversub | `ε` | theoretical `r0` | measured `r0` | cv |
|---|---|---|---|---|---|
| 10 | 2 | 0.50 | 9.00 | 12.13 | 0.71 |
| 10 | 5 | 0.50 | 9.00 | 12.59 | 0.85 |
| 10 | 20 | 0.50 | 9.00 | 12.53 | 0.91 |
| 10 | 2 | 1.00 | 3.00 | 3.32 | 0.32 |
| 40 | 2 | 0.50 | 9.00 | 9.74 | 0.30 |
| 40 | 20 | 0.50 | 9.00 | 9.69 | 0.33 |

**The hypothesis this section started with —"with more candidates per quota the noise goes down"— is
false, measured.** For `k=10, ε=0.50` the `cv` stays at 0.71–0.91 both with oversub=2 and with
oversub=20: there is no trend. What does bring it down is **the quota `k` itself**. Confirmed by
isolating the variable, same `ε=0.50`, oversub fixed at 5:

| `k` | measured `r0` | cv |
|---|---|---|
| 10 | 12.37 | 0.77 |
| 40 | 9.69 | 0.32 |
| 200 | 9.15 | 0.14 |
| 1,000 | 9.04 | 0.06 |

**Why it is like this, and not the other way round:** it is a result from extreme-value statistics,
not from sample size. The k-th bid of a heavy-tailed distribution (Pareto, small `ε`) does not
converge by having more candidates above the cut — it converges by having **more winners to average
over**. With `ε=0.5` the tail is heavier than with `ε=1.0`, and that is why the noise is
systematically worse at equal `k`.

> **With the creation rate already calculated for steady state (~9,700/day, block D), `k` is on the
> order of thousands per epoch and price noise should not be a real problem.** Where it is: **the
> bootstrap**, when the network has little activity and real `k` can be just a few per day — there
> the measured `cv` is 0.7–0.9, a price that can jump several times its value from one epoch to the
> next. And the way out is not "get more candidates" —it has already been measured that this does
> not help—: it is the same one TLM uses in RN-12 §15 problem 2 (*thin markets*): **a protocol
> reserve that damps the price when the organic quota is small, not more participants.**

**What holds just as in H:** occupancy still does not move from target whatever happens with the
price —the admitted quota is a sum, not the result of the auction— and that does not change with
discrete bids. The only risk the real auction adds to the design of H is price noise at the
bootstrap, with a fix already known in the literature that motivated this.

---

## J · The bootstrap reserve — smoothing over time what is missing in winners

**Run on 1/9/2026** (`bloque_j`). I measured the problem (price noise with small `k`) and discarded
the obvious way out (more candidates does not help). TLM (RN-12 §11) solves the same problem with a
protocol reserve on a published curve, which damps the price without displacing price discovery when
there are participants. The version of this for an admission auction needs no extra capacity — it
needs **to average over more epochs** when averaging over few winners is not enough: the same
statistics I found, moved from the participants axis to the time axis.

**Mechanism:** `r0_effective(t) = α·r0_raw(t) + (1−α)·r0_effective(t−1)`, with `α = min(1, k/k_ref)`.
With large `k`, `α→1` and the raw price passes through almost untouched; with small `k`, a small `α`
integrates more epochs — it borrows "winners" from the past instead of asking for more candidates
now, which has already been measured not to work. It is I2-compatible: it uses only the protocol's
own price series.

**Part 1 — the noise/lag trade-off**, `k=10` fixed, `ε=0.50`, ×3 shock at epoch 100, a 700-epoch
window, 40 runs:

| `α` | pre-shock cv | post-shock cv | epochs of lag |
|---|---|---|---|
| 1.00 | 0.71 | 0.84 | does not settle |
| 0.50 | 0.39 | 0.45 | does not settle |
| 0.30 | 0.28 | 0.31 | 464.0 |
| 0.15 | 0.18 | 0.22 | 225.1 |
| 0.10 | 0.15 | 0.17 | 231.1 |
| 0.05 | 0.10 | 0.11 | 128.3 |
| **0.02** | **0.07** | **0.05** | **39.6** |
| 0.01 | 0.06 | 0.04 | 77.1 |

**The lag does NOT grow monotonically as `α` falls — it measures two mixed things.** How long the
smoothed mean takes to move (falls with high `α`) and how long it takes to stay inside the ±20% band
with the noise that remains (falls with low `α`, because there is less noise to push it out). An
intermediate `α` can lose on both: it moves more slowly than a high one and is still noisy. The
measured optimum is at **`α ≈ 0.02`** (minimum lag, ~40 epochs, with `cv` already down to
0.05-0.07) — not at either extreme, and it could not be assumed without the complete table: with
only `α ∈ {0.30; 0.15; 0.05}` (the first run) it looked monotonically decreasing and the conclusion
would have been the opposite.

**Part 2 — why `α` should be adaptive and not fixed.** Simulated: `k=10` for 200 epochs (bootstrap)
and afterwards `k=1,000` (steady state), with no demand shock —only organic growth—, `k_ref=200`:

| epochs | `k` | cv of the window |
|---|---|---|
| 0–200 | 10 | 0.10 |
| 200–400 | 1,000 | 0.06 |

With `k=1,000`, `α = min(1, 1000/200) = 1.0`: the reserve stops touching the price on its own as
soon as the network grows, without anyone switching it off by hand. It is the property a fixed `α`
lacks: one that is enough for `k=10` keeps on smoothing —and lagging— the price long after it
stopped being needed.

> **The bootstrap reserve is specified, not just named:** an EWMA over `r0`'s own series,
> `α = min(1, k/k_ref)`, with `k_ref` on the order of 200–500 for the measured case (`k=10`,
> `ε=0.50`, ×3 shock) — not at the smoothest extreme, which worsens the lag again. **It is not extra
> capacity and not more participants: it is memory, and it retires on its own.** The sweep still has
> to be repeated for other `k` and other shock sizes before fixing a single `k_ref` — this number
> was measured for one case, not for all.

---

## K · Generalizing `k_ref` — the ratio `α/k` holds, the naive argmin does not

**Run on 1/9/2026** (`bloque_k`). J measured the optimum for a single case (`k=10`). Before proposing
`k_ref` as a protocol constant, it has to be seen whether the optimum in **ratio `α/k`** holds when
`k` changes. Same `ε=0.50`, ×3 shock, a 600-epoch window, 25 runs per cell, four `α/k` ratios for
each `k`:

| `k` | best `α/k` | `cv` at that point | implicit `k_ref` (raw argmin) |
|---|---|---|---|
| 10 | 0.0020 | 0.061 | 5,000 |
| 20 | 0.0020 | 0.058 | 10,000 |
| 40 | 0.0040 | 0.092 | 10,000 |
| 80 | 0.0020 | 0.064 | 40,000 |

**The implicit `k_ref` of the last column is an artifact and is not the result.** It is the argmin of
a noisy metric (lag, 25 runs) over a fairly flat minimum between `α/k=0.002` and `0.004` — inverting
it (`k_ref = k/ratio`) amplifies any tie into a number that jumps from 5,000 to 40,000 with no real
pattern. **The column to read is the `cv` at a fixed ratio of `0.002`: 0.061 / 0.058 / — / 0.064 for
`k=10/20/—/80`** — practically the same value over a range of `k` that varies 8×. It confirms the
sum: the effective memory of the EWMA is ~`k/α` accumulated "winners", so `cv ~ sqrt(α/k)` depends on
the **quotient**, not on `k` separately.

> **`k_ref` does generalize over the range tested (`k=10` to `80`):** a ratio `α/k ≈ 0.002–0.004`
> (`k_ref ≈ 250–500`) works for that whole range — no function of `k` is needed, a constant is
> enough.

**Why there is no need to test steady-state `k` (thousands) to close this — it is resolved by
analysis, not by a new simulation:** with `k_ref≈250-500` and steady-state `k` (~9,700/day, block D),
`α = min(1, k/k_ref) = 1` — the reserve is **switched off by design**, passing the raw price through
untouched. And "raw price with large `k`" is exactly what block I already measured (`cv≈0.06` at
`k=1,000`). The question of whether `k_ref` "holds up" in steady state does not apply: there the
reserve does not act, and the behaviour without the reserve is already measured. The range that did
matter to test —where `α<1`— is the one this block already covered.

**Initial condition, so that it does not stay implicit:** `r0_effective(0) = r0(0)`, the constant
declared in C22 — the EWMA starts at the same number as the raw law, with no ambiguity.

> **With this the bootstrap reserve is closed as a piece:** mechanism, optimum of the noise/lag
> trade-off, generalization over `k`, behaviour in steady state and initial condition — all measured
> or resolved by direct analysis of what was already measured, nothing assumed. What remains open
> (the quota under a `θ*` transition, demand below the quota) belongs to the auction in general, not
> to the reserve.

---

## Verdict

1. **The 176 B were wrong on two counts.** The tree is ~1 B with `d=6`, not 32; the index is 8 B with
   buckets, not 16. The 128 B layout was correct for the object, but **a balance is 64 B**. Real
   capacity with 4 GB: **35.5 M objects**.
2. **The control law of C7.13 does not close**, and its previous result was a simulation artifact.
3. **The cause is economic:** prepayment with a floating price is intertemporal arbitrage — lives of
   897 epochs get bought when the price falls, and those slots cannot be recovered without
   confiscating.
4. **The fix is `L_max`**, a cap on the life that can be bought at once. With 25 epochs the loop
   lands exactly.
5. **`θ*` has a derived ceiling at ~67%**, and 50% leaves real margin against the estimation error
   this very measurement has just proved to be possible.
6. **The admission auction with a fixed quota and life fixed at `L_max` (block H) avoids both known
   failures**, in the same simulation: occupancy stays pinned to target with no overshoot
   (eliminating the 1.25×–1.48× peak of G) and the price, not the quantity, carries all the
   information of the shock (avoiding the failure of C14.3). It does not solve the absolute level of
   `r0` —that is still C22.
7. **With discrete bids (block I) the mechanism holds, with a new and measured limit:** the price
   noise depends on the **quota `k`**, not on how many people bid for it —a prior hypothesis the
   measurement discarded—. With `k` on the order of thousands (steady state) the noise is small (`cv`
   ~0.06); with small `k` (bootstrap) the `cv` is 0.7–0.9. The fix is a protocol reserve, not more
   participants — the same mechanism TLM uses for the same problem (RN-12 §15.2).
8. **The bootstrap reserve (block J) is specified, not just named:** an EWMA over `r0`'s own series
   with adaptive gain `α = min(1, k/k_ref)` — it retires on its own when `k` grows, without switching
   it off by hand. The noise/lag trade-off **is not monotone**: sweeping only three values of `α`
   would have given the opposite conclusion to the one the complete table gives. The measured optimum
   for `k=10` is at `α≈0.02`, not at the smoothest extreme.
9. **`k_ref` generalizes (block K), but not by the obvious route:** the naive argmin of the lag per
   row gives numbers that jump from 5,000 to 40,000 with no pattern —it is amplified noise, not a
   real dependence on `k`—. The stable column is the `cv` at a fixed `α/k` ratio: practically
   identical (0.058–0.064) over an 8× range of `k`, confirming that the noise depends on the
   **quotient** `α/k` and not on `k` separately. `k_ref ≈ 250–500` works for the whole range tested.
10. **The bootstrap reserve is closed as a piece.** The only item that had been left pending —`k_ref`
    in steady state— is resolved by analysis: with `k` in the thousands, `α=min(1,k/k_ref)` is capped
    at 1, the reserve switches itself off by design, and that case was already measured by block I
    (`cv≈0.06`). Explicit initial condition: `r0_effective(0)=r0(0)` (C22). Still open, but no longer
    about the reserve and about the auction in general: the quota under a `θ*` transition and what
    happens if demand falls below the quota.
11. **And those last two also close by analysis, with no new simulation.** The quota under a `θ*`
    transition is not a decision: it is the sum `quota=θ*/L_max`, recalculated on its own at every
    activation —the same play as the step ceiling—; the readjustment after a change lasts at most
    `L_max` epochs and never compromises the physical ceiling, because the inherited occupancy was
    already, by construction, under the previous generation's `θ*≤67%`. And demand below the quota is
    not a special case: the quota is a ceiling, not a floor — if demand does not fill it, `r0` falls
    to its floor and occupancy stays below `θ*` that epoch, with nothing to burn, accumulate or give
    away. **With this the admission auction is completely specified as a candidate** —fixed quota and
    fixed life (H), discrete bids (I), bootstrap reserve (J, K), transition and insufficient demand
    (11)—; all that is missing is adopting it, which is the author's decision, not a pending sum.
