# Test 4 · The window of `k`

**English** · [Español](RESULTS.es.md)

> Status: **closed. It does not pass.** Corrected on 17/8/2026 — see §2.
> Net issuance and the self-dealer's profit are **the same quantity**, so there is no `k` that
> creates new money without creating exactly that farming opportunity. At the maximum safe `k`, the
> whole apparatus of issuance and burning is equivalent to a fee market with no issuance and no
> burning. And there is a second problem, independent of `k`: the loop cannot start.

What §12 asks for: *"simulate whether there is any `k > 0` where paying yourself is not profitable
and the subsidy is still significant for an honest operator"*. It is the test with a double
function: it decides at once whether the currency is healthy (§7.1) and whether stage 1 of adoption
is viable (§9).

Reproducible with `python simulacion.py`. There is no external data: it is arithmetic over the model
the paper itself writes.

---

## 1. The model, taken literally from the paper

§7.1 gives the formula:

```
E(t) = min( curva_temporal(t),  k · W(t) )
```

`W(t)` is settled and verified work, measured **in tokens paid** — it is the only thing the protocol
can count without judging utility (§7.1, rule 1). So `k` is dimensionless: subsidy per token of work
paid for. The subsidy is split pro rata, so the effective rate per token is `r = E/W = min(curve/W,
k)`.

**The self-dealer** (§9: *"an agent paying itself"*). It cycles `W` tokens: it deposits them into
escrow and collects them itself, so the net payment is zero. Its costs:

- the protocol fee, `φ·W`, of which a fraction `β` is burned and the rest goes to the PoD nodes
  (§6.1);
- if it also runs PoD nodes, it recovers a fraction `s` of that unburned part (`s = 1` is the
  vertically integrated attacker);
- the work itself: it chooses the cheapest predicate §6.2 admits. That cost is **fixed per
  settlement, not proportional to `W`**, so scaling `W` dilutes it to zero.

```
cost per cycle = φ · (1 − s·(1−β)) · W        profit = r · W
```

**The honest operator** collects `W` from a real client, spends real computation, pays the same fee
and receives **the same `r`**. The protocol cannot distinguish them from the self-dealer: it is not
an omission, it is rule 1 of §7.1 working as written.

**"Significant"** is measured as a fraction of the operator's gross income, `r/(1+r)`, against a
threshold `σ`. `σ = 10%` means *"the subsidy is at least 10% of what they bill"*.

---

## 2. Correction: who collects the issuance

**The error.** The first run measured the significance of the subsidy against the billing of the
node doing the work. §6.1 says the opposite, verbatim: the compute node's income is *"the payment
for the request they executed, **not the protocol's issuance**"*. The paper nowhere says who does
collect `E(t)`; by elimination, the PoD nodes. Redone in `correccion-destinatario.py`.

**The ceiling does not move.** The self-dealer runs their own PoD node to capture the issuance over
the work they themselves manufacture, and §6.1 makes that entry cheap *on purpose* — *"a node that
fits in a phone"*. So vertical integration stops being the worst case and becomes the normal case:
`s = 1`, ceiling `k ≤ β·φ`.

**What does change is that the result becomes an identity.** Per unit of settled work:

```
issuance created       k·W
burn                   β·φ·W
─────────────────────────────────
net issuance           (k − β·φ)·W
self-dealer's profit   (k − β·φ)·W        ← the same expression
```

> **The theorem.** `net issuance > 0` ⟺ `paying yourself is profitable`. They are not two conditions
> that have to be fitted into a window: they are **the same quantity**. Every unit of new money the
> protocol creates is, exactly, a unit of profit available to whoever manufactures work.

Out of that comes the sharpest form of the verdict. At `k* = β·φ`, which is the safe maximum:

| | with issuance and burning | with neither issuance nor burning |
|---|---|---|
| net issuance | 0 | 0 |
| PoD nodes' income | `(1−β)φW + kW = φW` | `φW` |

**They are identical.** At the maximum safe `k`, the whole monetary apparatus of §7.1 does exactly
what a fee market with no issuance and no burning would do. There is no third region: either the
issuance is a no-op, or it is a subsidy to farming of exactly the size of the net issuance.

**And the significance question dissolves instead of being answered.** At `k*` the "subsidy" *is*
the fee, so asking whether it is enough for a PoD node is a fee-market question, not a monetary
policy one. The answer, with nodes that cost a phone (US$ 100/year amortized) and free entry down to
zero profit:

| annual settled work | φ=0.1% | φ=0.3% | φ=1.0% |
|---|---|---|---|
| US$ 1 M | 10 nodes | 30 | 100 |
| US$ 100 M | 1,000 | 3,000 | 10,000 |
| US$ 1,000 M | 10,000 | 30,000 | 100,000 |

With US$ 100 M settled annually and a 0.3% fee, the network banks ~3,000 PoD nodes — on the order of
Ethereum's execution nodes. **The fee market does sustain a large light layer.** What is not needed
for that is the issuance: those numbers come from the fee, not from `k`.

### 2.1 The cold start (independent of `k`)

`W(t)` is measured in tokens paid, and §7.1 says *"there is no premine, no treasury, no team
allocation. Every unit that exists was born against work delivered."*

At block 0 no token exists. So nobody can pay, so `W = 0`, so `E = min(curve, k·0) = 0`, and the
circulating supply stays at zero forever. **The loop is closed and starts at zero.** Issuing the
first unit demands an initial issuance that does not depend on `W`, which is exactly what the same
section forbids.

It is not a `k` calibration problem: no value of `k` moves it. It is a contradiction between two
sentences of §7.1, and we had not seen it because the first simulation took `W_h` as an exogenous
input.

### 2.2 What is left standing of §3 to §5

The tables of §3 to §5 were computed with the wrong recipient, so **the significance numbers against
the compute operator's billing (0.15%, 334×–2001×) no longer describe anything in the design** and
must not be cited. What survives intact:

- the ceiling `k ≤ φ·(1−s(1−β))` and its normal form `k ≤ β·φ` (§2, §3);
- that above the threshold `k` stops being a control variable and free entry pins the effective rate
  to the self-dealer's cost (§3);
- the escape route of the real cost floor `γ` and its price (§5);
- the corollary of the *ad valorem* fee (§6).

---

## 3. The main result: the window reduces to an inequality

Since the subsidy and the self-dealer's cost **both scale with `W`**, the profitability of
self-dealing is scale-invariant: it does not depend on the capital, on the volume, or on the curve.
The whole test collapses into comparing two rates:

```
do not farm   ⟺   k ≤ φ · (1 − s·(1−β))          ← safety ceiling
be juicy      ⟺   k ≥ σ / (1 − σ)                ← adoption floor
```

**The window exists if and only if `σ ≲ φ_effective`.** Neither the temporal curve, nor the size of
the network, nor the price of the token enters the condition.

| φ | β | s | ceiling on `k` | σ=1% | σ=5% | σ=10% | σ=20% |
|---|---|---|---|---|---|---|---|
| 0.1% | 0.50 | 1 | 0.00025 | · | · | · | · |
| 0.3% | 0.50 | 1 | 0.00150 | · | · | · | · |
| 0.3% | 1.00 | 0 | 0.00300 | · | · | · | · |
| 1.0% | 1.00 | 0 | 0.01000 | · | · | · | · |
| 3.0% | 1.00 | 0 | 0.03000 | **yes** | · | · | · |
| 10.0% | 1.00 | 0 | 0.10000 | **yes** | **yes** | · | · |

The window only opens —and only for the laxest threshold, 1%— when the protocol charges **3% per
settlement**. §6.1 asks for *"a small fee"*. Stripe charges 2.9%.

**Only the burned part bounds it.** With `s = 1`, the ceiling drops from `φ` to `β·φ`: the attacker
running PoD nodes recycles the part of the fee that is not burned. The paper already intuited this
—§7.1 says *"the burned fee"*— but the consequence was not written down: **the ceiling on `k` is not
the fee, it is the fee times the burn fraction.**

---

## 4. What breaks the claim of §9

§9 says, verbatim:

> *"The arbitrage window and the self-dealing window are the same window. The only thing that
> separates them is `k`."*

**`k` does not separate them, because `k` enters identically into both.** The self-dealer and the
honest operator receive the same rate `r` on the same `W`, and they have to: distinguishing them
would require the protocol to judge whether the work was real, which is exactly what rule 1 forbids.
What separates the two is `φ_effective` against `σ` — two numbers the design fixes for other reasons
and that `k` cannot move.

And there is a second consequence, more uncomfortable: **above the threshold, `k` stops being a
control variable.** With free entry, self-dealers enter until the dilution brings `r` down to their
own cost. Ten periods with `k = 0.10` —67× the threshold— and organic demand growing 60% per period:

| period | organic `W_h` | farmed `W_f` | `r` | capture | significance |
|---|---|---|---|---|---|
| 1 | 10,000 | 66,656,667 | 0.00150 | 100.0% | 0.15% |
| 5 | 65,536 | 66,601,131 | 0.00150 | 99.9% | 0.15% |
| 10 | 687,195 | 65,979,472 | 0.00150 | 99.0% | 0.15% |

`r` does not move from `0.00150` = `β·φ`. **Raising `k` does not raise the honest operator's subsidy
by a single basis point**: it only determines how many self-dealers come in to dilute it. And they
capture between 99% and 100% of the issuance.

Out of that comes the only defensible `k`:

> **`k* = φ · (1 − s·(1−β))`, exactly.** It is the maximum that does not invite self-dealing, and it
> is also the maximum attainable subsidy. Above it, the market returns it to that same value,
> charging the toll that the issuance is taken by the farmers.

---

## 5. The intensity, against the example §9 says it follows

§9: *"the expected bootstrap is Bitcoin's"*. In Bitcoin 2009–2012 the subsidy was practically 100%
of the miner's income; fees were noise.

| φ | β | s | `k*` | subsidy / income | vs. Bitcoin |
|---|---|---|---|---|---|
| 0.1% | 0.50 | 1 | 0.00050 | 0.05% | **2001×** weaker |
| 0.3% | 0.50 | 1 | 0.00150 | 0.15% | **668×** |
| 0.3% | 1.00 | 0 | 0.00300 | 0.30% | **334×** |
| 1.0% | 1.00 | 0 | 0.01000 | 0.99% | **101×** |
| 3.0% | 1.00 | 0 | 0.03000 | 2.91% | **34×** |

*(Measuring against the margin instead of against gross income improves these numbers by the inverse
of the margin — with a 10% margin, a subsidy of 0.3% of income is 3% of the margin. It is still an
order of magnitude short of "juicy", but it is the most favourable reading and it is right to
declare it.)*

§9 says that stage 1 *"is almost certain: every yield farm in history proves it"*. The yield farms
offered two- and three-digit returns. Here the ceiling is **0.15%**.

---

## 6. The only escape route, and what it costs

The ceiling is low because manufacturing fake work is **free except for the fee**. The only
structural way to raise it is for producing a token of work to cost something real and irreducible,
`γ`, besides the fee. The ceiling becomes `φ_effective + γ`.

| σ | φ | β | s | current ceiling | `γ` needed |
|---|---|---|---|---|---|
| 1% | 0.3% | 0.50 | 1 | 0.00150 | 0.86% |
| 5% | 0.3% | 0.50 | 1 | 0.00150 | 5.11% |
| 10% | 0.3% | 0.50 | 1 | 0.00150 | **10.96%** |
| 10% | 1.0% | 1.00 | 0 | 0.01000 | 10.11% |

For the subsidy to be 10% of the operator's income, the protocol has to guarantee that
**manufacturing work costs ~11% of its value in real resources**.

And there is the knot: **guaranteeing a cost floor is defining what counts as work.** It is literally
rule 1 of §7.1 —*"the protocol never decides what work is useful"*— which exists to avoid becoming
*"a central bank with a committee inside"*.

> **The structural finding: rule 1 of §7.1 and a significant subsidy are incompatible.** It is not a
> `k` calibration problem: it is that `k` has no authority over either of the two quantities that
> decide the result. Bitcoin can pay a 100% subsidy because the protocol **does** define the work
> (hashing) and its cost is external and physical. This design gave that up on purpose, and the price
> is the ceiling of §2.

Ways of imposing the floor without defining work were looked for. They all die on Sybil, because the
protocol has no notion of identity: requiring payer and worker to be different —identities are free—;
per-account caps —it is split across accounts—; a superlinear fee per account —likewise—; a bond or
stake —the capital comes back, the cost per cycle is the interest rate times the duration of the
escrow, ~0.001% with hourly finality.

---

## 7. A corollary the paper does not have written down

**The fee has to be proportional to the value of the work, not fixed per operation.**

If the fee were a fixed amount per settlement, the self-dealer inflates `W` against a constant cost
and the subsidy `k·W` exceeds any fee for a large enough `W`. The ceiling disappears and self-dealing
is profitable for every `k > 0`.

This whole analysis assumes an *ad valorem* fee. The paper nowhere says so —§6.1 only says *"a small
fee every time two contracts interact"*, which sounds like a per-operation fee. It is a condition on
Geminis, and like all those of that class, it is cheap on day one.

---

## 8. What survives

§12 anticipated this exact case: *"one can pass and the other not — and in that case what survives
is the corresponding half, not the whole."*

With Test 1 passed and Test 4 not:

- **The mechanism survives:** deterministic succession of internal parameters with a trigger from
  the state. Test 1 found it real and living customers, and none of those customers needs the chain
  to have its own currency — Ethereum already has one.
- **The currency as specified does not survive:** §7.1 (issuance indexed to work paid for), §9 stage
  1 (farming the subsidy) and, by dependency, the argument of §6.1 about who pays the nodes.

That is a scope decision and it belongs to the author, not to the test. The options the result
leaves open, with none recommended:

1. **Separate the mechanism from the currency.** Publish the deterministic succession as a mechanism
   applicable to an existing chain. It is where Test 1 found the demand.
2. **Change the base of the issuance** to something whose cost is external and physical, accepting
   that this reintroduces a definition of work — that is, revise rule 1 knowingly instead of by
   accident.
3. **Accept the weak subsidy** and look for the bootstrap somewhere other than §9 stage 1.

---

## 9. Limits of the simulation

- **The significance metric is a modelling choice.** Measuring against the margin instead of against
  income improves the numbers by the inverse of the margin (§4). It does not change the order of
  magnitude, but it is right to say that the exact number depends on that choice.
- **The price of the token is not modelled.** It is the biggest omission. Self-dealers selling the
  issuance sink the price, and that does bound farming in practice — but it bounds it by destroying
  the value of the token, which is not a defence.
- **The burn of §8.4** on swaps is not modelled. It raises the cost of *exiting*, not of farming: the
  self-dealer cycles without touching the AMM and only pays that burn when they sell.
- **`ε = 0`** (cost of manufacturing work trivial). It is the pessimistic hypothesis for the design,
  and it is justified because the attacker scales `W` per settlement. If there were a maximum
  settlement size, `ε` would matter again — and that is, once more, a parameter that defines work.
- **Free and instantaneous entry.** In reality there is friction and delay, so the 99% capture is a
  limit, not a forecast for the first month.
- **A single decision period.** There is no intertemporal strategy and no accumulation.
