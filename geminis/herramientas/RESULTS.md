# Phase 2 · replay against Ethereum's real history

**English** · [Español](RESULTS.es.md)

**The difficulty bomb and its six delays.** Run on 19/8/2026.

```
cd geminis
python herramientas/replay.py        # the complete report
python verificar.py replay           # the pass criteria
```

> **DATA VERIFIED on 19/8/2026, number by number.** The first version of this report ran with the
> data transcribed from memory and said so at the very top: *a remembered datum is not a third-party
> datum*, and this phase exists precisely so as not to confuse them. The verification pass was done
> and **all twelve numbers came out right**:
>
> | what | against what | result |
> |---|---|---|
> | the six **offsets** of the bomb | the text of each EIP on `eips.ethereum.org` | 6/6 |
> | the six **activation heights** | `MainnetChainConfig` in `ethereum/go-ethereum`, `params/config.go` | 6/6 |
> | the block of the **merge** | 15,537,394, 15/9/2022 06:42:42 UTC | ok |
>
> **And a trap turned up worth noting: the EIPs do not carry the activation height.** They use a
> placeholder (`BYZANTIUM_FORK_BLKNUM`, `FORK_BLOCK_NUMBER`), so whoever transcribes only from the
> EIP is left with half the datum. **Two** sources per fork are needed, and the second is the
> configuration the nodes run.

---

# Case 1 · the difficulty bomb

## Why this case first

The roadmap names three —blobs, gas limit, bomb— and the last on the list was implemented on
purpose. The other two need a **series**: how many blobs per block, how much gas used against the
limit. That cannot be written from memory.

The bomb needs none: its effect is a deterministic function of the height, written in the EIPs, and
the six human decisions are six heights. **The whole case is answered with discrete, citable facts.**

---

## Measurement 1 · the revealed threshold — zero free parameters

How much the bomb's term —`2 ** (floor((height − offset) / 100,000) − 2)`— was worth at the exact
moment the humans decided to delay it.

| fork | EIP | height | date | exponent | fork only because of the bomb? |
|---|---|---|---|---|---|
| Byzantium | EIP-649 | 4,370,000 | 2017-10-16 | **41** | no (it lowered the reward) |
| Constantinople | EIP-1234 | 7,280,000 | 2019-02-28 | **40** | no (it lowered the reward) |
| Muir Glacier | EIP-2384 | 9,200,000 | 2020-01-02 | **40** | yes |
| London | EIP-3554 | 12,965,000 | 2021-08-05 | **37** | no (EIP-1559) |
| Arrow Glacier | EIP-4345 | 13,773,000 | 2021-12-09 | **38** | yes |
| Gray Glacier | EIP-5133 | 15,050,000 | 2022-06-30 | **41** | yes |

**Range 2^37 – 2^41: the bomb's term varied 16× between the earliest and the latest decision.**
There was no consistent human threshold.

And the obvious hypothesis does not explain the dispersion: the forks that existed anyway for another
reason should have been able to delay the bomb earlier —it was free for them— and the exclusive ones
should have waited. Measured: exclusive `[38, 40, 41]`, mixed `[37, 40, 41]`. **They do not
separate.** With six points there is nothing to sustain that explanation, and it is noted as
discarded rather than repeated.

---

## Measurement 2 · the counterfactual per decision — one free parameter

The right comparison, and separating it matters: the humans took **two** different decisions each
time —*when* to delay the bomb and *by how much*— and a chained simulation mixes them, because the
step's error accumulates and contaminates the measurement of the firing. Here the offset is set by
the real history and the only thing measured is the moment.

Candidate rule: *when the bomb's term reaches `2^40`, delay it.*

| fork | human | the rule | difference | days |
|---|---|---|---|---|
| Byzantium | 4,370,000 | 4,200,000 | −170,000 | 27 |
| Constantinople | 7,280,000 | 7,200,000 | −80,000 | 12 |
| Muir Glacier | 9,200,000 | 9,200,000 | **±0** | **0** |
| London | 12,965,000 | 13,200,000 | +235,000 | 37 |
| Arrow Glacier | 13,773,000 | 13,900,000 | +127,000 | 20 |
| Gray Glacier | 15,050,000 | 14,900,000 | −150,000 | 23 |

**Maximum deviation 235,000 blocks (37 days). Mean, 127,000 (20 days). One exact coincidence.** With
a single number chosen in Geminis, and reading nothing but the height and the offset in force.

**The `2^40` threshold was not chosen by hand: it is the one that minimizes the maximum deviation in
a sweep from 2^35 to 2^45.** One degree of freedom against six points.

### The two readings of measurement 1 — RESOLVED, and against the optimistic one

The term varied 16× and even so a fixed threshold reproduces the six dates within five weeks. Both
things are true because **the bomb is exponential**: 16× of dispersion is four exponent steps, that
is, about two months of calendar.

The first version of this report left open which of the two readings mattered and said what datum
would close it: the **difficulty series**. It was downloaded on 19/8/2026 (`traer_datos.py
dificultad`, 1,154 samples) and **it answered against the optimistic reading** — see Measurement 1b.

---

## Measurement 1b · the real pressure — with the difficulty series

The obvious denominator is the wrong one. Against difficulty alone, the bomb's term is 0.00%–0.07%
in all six forks: it looks like nothing. But difficulty **adjusts**, and what decides whether the
bomb is felt is how much of that adjustment capacity it consumes:

```
pressure = bomb × 2048 / difficulty     ← steps of the per-block adjustment
```

Below 1, the adjustment absorbs it within its normal band and **nobody notices**. Above, it can no
longer: blocks get slower.

| fork | exponent | pressure | floor s/block | was it felt? |
|---|---|---|---|---|
| Byzantium | 41 | **1.504** | 22.5 | **YES** |
| Constantinople | 40 | 0.761 | 15.9 | no |
| Muir Glacier | 40 | 0.916 | 17.2 | no (at the edge) |
| London | 37 | 0.037 | 9.3 | no |
| Arrow Glacier | 38 | 0.047 | 9.4 | no |
| Gray Glacier | 41 | 0.315 | 11.8 | no |

**One of the six forks happened with the bomb forcing slower blocks. The other five were
preventive.**

**And the calculation has external validation that was not sought.** Muir Glacier was an emergency
fork, in January 2020, because blocks climbed to ~17 s. The model —which knows nothing of that story
and was not fitted to anything— gives **17.2 s**. It is the only independent check this measurement
has and it passes it.

**The dispersion, measured in the unit that matters, is worse: 41×, not 16×.** From 0.037 to 1.504.
And it is not noise: there is a temporal trend. The first three forks (2017-2020) go from 0.76 to
1.50; the last three (2021-2022), from 0.04 to 0.32. **The humans learned to act earlier and
earlier**, and that is exactly what a rule written in Geminis cannot do.

> **This reinforces the problem, not the solution.** A fixed threshold chosen in 2015 would have been
> the wrong one at both extremes: too late for the 2017 criterion, too early for the 2022 one.
> Measurement 2 shows that **one** number reproduces the six dates within five weeks; 1b shows that
> that number does not correspond to a stable criterion, but to the average of a criterion that was
> moving. It is the first boundary of §10.1 with a measured case: *writing the rule in advance does
> not eliminate the fork, it moves it to the case in which the written rule is the wrong one* — and
> here you also see **how** it becomes wrong: not because the world changes, but because those who
> wrote it learn.

## Measurement 3 · the bound — where the difference can indeed be called *better*

| | peak of the bomb's term |
|---|---|
| under the human process | **2^41** |
| under the rule (threshold 2^40) | **2^40** |

The rule bounds **by construction**: it fires as soon as the threshold is reached, so the term cannot
go past it. The human process reached twice that bound, and could have reached anything — nothing
prevented it, only the attention of a group of people.

It is the only one of the four measurements where *better* means something verifiable: it is not that
the rule got it right more often, it is that **it has a guarantee and the human process had a
result.**

---

## Measurement 4 · the chained replay — two free parameters

Here the rule also chooses **how much** to delay, with a fixed step, and there it separates from the
history: the best combination in the sweep leaves errors of up to 2.2 million blocks (about 354
days).

The reason is visible in the increments the humans chose:

```
3,000k · 2,000k · 4,000k · 700k · 1,000k · 700k
```

**No fixed step reproduces them.** And it has a mechanical explanation: each delay was sized to reach
*up to the next already-planned fork*, which is a variable a `TRANSITION_RULE` does not read and
should not read.

> **A warning about how to read this table.** The sweep penalizes the rule firing more times than the
> humans did, and that penalty assumes a transition costs what a hard fork costs. **It does not, and
> that is the whole thesis of the design.** Firing more often keeps the bomb smaller and costs nobody
> a coordination. The measurement is here anyway, with the bias declared, because removing it would
> be choosing the metric that favours the conclusion.

---

## What the replay does **not** demonstrate

- **It does not demonstrate that the rule would have been better.** On timing it is a tie with a
  five-week advantage to either side, depending on the fork.
- **It does not demonstrate that Ethereum should have written it.** In 2015, the number `2^40` was
  not available: it is known now, looking backwards. Measurement 1 says precisely that — **the humans
  never converged on that number**, and a chain that had written the rule in Geminis would have had
  to choose it blind. It is the first boundary of §10.1 instantiated for the second time, after
  Bitcoin Cash's EDA: *writing the rule in advance does not eliminate the fork, it moves it to the
  case in which the written rule is the wrong one.*
- **The zero forks thing is not a finding, it is a definition.** The rule needs no fork because a
  transition is not a fork; counting it as a result of the replay would be passing off a tautology as
  a measurement.

## What is demonstrated

- **The candidate rule is a real `TRANSITION_RULE`**: it passes the same I2 predicates as the
  protocol's rules, it is computed from two numbers that are on the chain —height and offset— and it
  reads no prices, no clocks and no votes.
- **The approach of I2 is not a rhetorical figure.** Since progress advances one block per block, the
  distance to the trigger is **exact and not a projection**: Ethereum could have published a perfect
  countdown to the next bomb delay, years in advance. At block 10,000,000 —May 2020— the chain could
  say *3,200,000 blocks to go*, and the London fork arrived 235,000 blocks before that date.
- **One implementation decision was validated against a real case.** C9.3 decided that the threshold
  moves and the progress does not reset. Here you see why it was not a whim: the bomb's exponent
  **goes down** with each delay, so using it as progress would have violated I2 six times.

---

---

# Case 2 · Ethereum's `blobSchedule`

**Run on 19/8/2026** with the series downloaded the same day. `python
herramientas/replay_blobs.py`.

It is the case the roadmap names first and the one with the customer closest to the design. Four
verified decisions: target **3 → 6 → 10 → 14** in 22 months.

## Two warnings about the data, and both change the measurement

**`excessBlobGas` does not compare across Fusaka.** It was the natural observable —the accumulator
the chain itself keeps in order to charge the blob fee— and the fetcher downloads it for that reason.
But **EIP-7918** changed its update rule: when the blob fee falls below a floor tied to the cost of
execution, the excess stops decaying and starts growing by `blob_gas_used × (max − target) / max`. It
shows in the series: under target 14, with demand at 31%, **the excess rises anyway**. The
measurement therefore uses **occupancy** (blobs against target), which means the same thing before
and after.

**BPO1 and BPO2 are not two decisions: they are one schedule.** Both were announced together on
6/11/2025, in the Fusaka mainnet announcement, **before Fusaka activated**. Reading them as two
independent responses to demand would be misreading the data — and it explains half the result.

## Measurement A · occupancy under each target — zero free parameters

| target in force | from | samples | mean occupancy | peak (30 d) | % of the stretch saturated |
|---|---|---|---|---|---|
| Cancun, t=3 | 2024-03-13 | 601 | **83%** | 129% | 64% |
| Prague, t=6 | 2025-05-07 | 309 | **83%** | 106% | 66% |
| BPO1, t=10 | 2025-12-09 | 41 | **43%** | n/a | n/a |
| BPO2, t=14 | 2026-01-07 | 323 | **31%** | 48% | 0% |

*«saturated» = 30-day moving average ≥ 80%. «n/a» = the stretch lasts less than the window: BPO1
lasted 29 days and nothing sustained can be measured — which already says something.*

**The first two targets ran saturated; the last two, nowhere near.** Demand stopped being the
constraint exactly when the BPOs arrived.

## Measurement B · the counterfactual per decision — one free parameter

Candidate rule: *raise the target when sustained occupancy (30 days) goes past the threshold*. The
target in force is set by the history, so there is no second parameter contaminating the first.

| decision | human | the rule (≥80%) | difference |
|---|---|---|---|
| Prague | 2025-05-07 | 2024-04-19 | **the humans took 383 days longer** |
| BPO1 | 2025-12-09 | 2025-06-30 | the humans took 162 days longer |
| BPO2 | 2026-01-07 | **never fires** | the occupancy of t=10 was 43% |

**The result does not depend on choosing the threshold well**: between 70% and 90% the conclusion
does not change — only how much longer they took (390, 383 and 306 days for Prague).

## The reading, and it has two opposite sides

**Where the constraint was demand, the rule wins by a huge margin.** Occupancy reached 80% of target
**37 days after Dencun**, stayed saturated 64% of the time and reached peaks of **129% of target**
—that is, sustained demand above what the parameter was aiming at, which is exactly when the blob fee
punishes the rollups—. Ethereum took **383 days** to respond. That is the bill for the coordination,
measured, on the parameter whose own EIP says the current method *"is not agile enough"*.

**Where the constraint was not demand, the rule is blind — and it would have got it right for the
wrong criterion.** BPO1 and BPO2 raised the target to 10 and to 14 with demand at 43% and 31%. It was
not a response to demand: it was possible because Fusaka brought PeerDAS. And *"the network can now
carry more without degrading"* **is not a fact of the state**: I2 says the trigger only reads state,
so a demand rule would have raised nothing. It would have been right by its own criterion and wrong
about the network.

> **And the true edge comes before that.** Could the rule have raised the target to 6 in April 2024?
> Only if the 6 was in the space declared in Geminis **and was safe**, and it was not safe until
> PeerDAS existed. The ceiling of the space of descendants is bounded by a technology that did not
> yet exist. It is the first boundary of §10.1 in its hardest form for this case: **it is not that
> the written rule may be the wrong one — it is that the declared space may fall short because of
> something nobody could anticipate.**

## What is visible looking at the four decisions together

In 22 months, Ethereum went through three stages on this same parameter:

1. **recalibrating inside a large fork** (Dencun, Pectra);
2. **a lightweight fork mechanism** so as not to have to wait for the next large fork (EIP-7892,
   `Final`);
3. **a schedule of raises written in advance** and executed by calendar (BPO1 and BPO2, announced
   together).

**The third step is one property away from this paper's design**: the schedule is written in advance,
yes, but the firing is **the clock and not the state**, and executing it still needs a fork. It is
exactly the form of BIP-103, which §12 already analyses and discards as a closure of the gap for the
same reason.

## Status of case 2

**Passed as an explained difference, not as a tie.** The criterion asked for *either it reproduces
the decision, or it is written down exactly where it differs and whether it was better or worse*: it
differs in all three decisions, the difference is measured in days, and the *better or worse* has a
different answer depending on what was constraining — speed in the rule's favour, capacity against,
and both with the number beside them.

---

---

# Case 3 · Ethereum's gas limit

**Run on 19/8/2026.** `python herramientas/replay_gas.py`.

**It is the only one of the three where the paper's mechanism does not compete against a fork.** The
gas limit is already a parameter **every validator votes on block by block**, with a cap of 1/1024 of
change per block: a lightweight, decentralized, fork-free coordination that already works. And the
result is the most uncomfortable of the phase: **for this parameter there is no admissible trigger**,
and not for lack of ingenuity.

## Measurement A · the human trajectory — zero free parameters

| from | to | limit | duration |
|---|---|---|---|
| 2022-09-15 | 2025-01-31 | 30.0M → 30.6M | **870 days** |
| 2025-01-31 | 2025-02-05 | 30.6M → 35.8M | 4 days |
| 2025-02-05 | 2025-07-18 | 35.8M → 36.5M | 164 days |
| 2025-07-18 | 2025-07-22 | 36.5M → 44.9M | 4 days |
| 2025-07-22 | 2025-11-25 | 44.9M → 48.8M | 126 days |
| 2025-11-25 | 2025-11-27 | 48.8M → 59.6M | 1 day |
| 2025-11-27 | 2026-08-19 | 59.6M → 60.0M | 265 days |

**28 months frozen at 30M, and then double in 300 days.** The shape of an off-chain coordination:
nothing, nothing, nothing, and then all at once.

## Measurement B · occupancy carries no information — zero free parameters

| | |
|---|---|
| mean occupancy | **50.9%** |
| range of the moving average (60 samples) | 42.8% – 59.3% |
| median base fee | 36.43 → 0.056 gwei (**650× fall**) |
| **correlation occupancy / base fee** | **−0.021** |

EIP-1559 fixes the target at half the limit and moves the base fee until usage comes back there.
**With the fee moving 650×, occupancy does not move.**

> **This closes a door the paper had open.** C7.13 concluded that `r0` could not be a nominal number
> and that the way out was **a control law indexed to occupancy**. Here you see that that way out is
> not available when the resource is already rationed by a fee market: occupancy is pinned by
> construction and **indicates nothing**. It is not that the correlation is weak — it is zero, over
> 1,026 samples and four years.

## Measurement C · the only signal is the fee, and neither of its two forms works

**Nominal form.** The median fee fell **650×**. Any threshold in gwei chosen in Geminis stops meaning
what it meant. It is literally the finding of C7.13, confirmed on another parameter and with
third-party data.

**Dimensionless form** —the fee against its own annual median, which is scalable and comes from the
state—. With `k = 1.5` it fires **four times, all between December 2023 and April 2024**, with the
limit still at 30M and the fee between 31 and 35 gwei: **fourteen months before** the humans moved it
for the first time. There it gets it right.

But it loses the notion of *expensive*:

```
k = 1.0 · 2026-05-01 · fee 0.261 gwei · limit 60M · ratio 1.06
```

**It fires again because the fee doubled from 0.08 to 0.26 gwei**, which is economically absurd:
without an absolute reference, *expensive* is only *more than just now*. With a higher `k` the
ratchet disappears — and with it the 2023 firings disappear too, which were the correct ones.

## On reading a price, which is the obvious doubt

§7.6 forbids the trigger from reading **on-chain market prices** —pool ratios, depth, volume— because
it would allow a transition to *be bought* by moving a pool with borrowed capital. **The base fee is
not that:** it is computed by the protocol from occupancy, and pushing it requires filling blocks and
burning the fee, so it falls on the side of the burn channel §10.2 already declares as a bounded
boundary. What disqualifies it is not where it comes from — it is that it is **nominal**.

And the candidate rule **passes the protocol's I2 predicates**. The problem is not in the provenance
of the datum nor in the form of the trigger: it is that **the only observable with information about
this resource is a price, and no nominal price works as a long-term setpoint.**

## Status of case 3

**Passed as an explained difference, and it is the hardest difference of the phase.** Where the
signal existed, the rule would have acted 14 months before an off-chain coordination that was already
working without forks. But **the trigger that would be needed does not exist in the paper's
framework**: the quantity is empty by EIP-1559's design, the nominal price expires, and the
dimensionless form ratchets.

It is §10.3, open problem 2 —*the nominal level `r0` starts from*— appearing in a second, independent
parameter, with third-party data, and with the way out proposed in C7.13 empirically discarded.

# Status of Phase 2 — CLOSED, three of three

The three cases run and written up, all three passed by the route the criterion admits when there is
no tie: **the difference is measured and explained.**

| case | does it reproduce? | where it differs |
|---|---|---|
| **1 · difficulty bomb** | **yes**, all six decisions within 37 days with a single parameter, and one exact | the threshold that achieves it is the **average of a criterion that was moving**: 41× of dispersion, five of six forks preventive |
| **2 · blobSchedule** | **no, and in both directions** | **383 days faster** where the constraint was demand; **blind** where it was capacity (PeerDAS) |
| **3 · gas limit** | **there is no admissible rule** | the quantity is empty by EIP-1559 (correlation −0.02), the nominal price falls 650×, and the dimensionless form ratchets |

## What the phase produced, which is what §11 asked for

**Evidence the author of the design did not write.** Five things, and three go against:

1. **the bill for coordination is real and has a number**: 383 days of delay on blobs saturated at
   129% of target; 870 days with the gas limit frozen. It is not a rhetorical figure of the paper —
   it is what happened to a chain that bills billions;
2. **the mechanism is structurally better at reacting and structurally incapable of anticipating.**
   Cases 1 and 2 show it from different sides: the human criterion was moving as they learned; and the
   last two blob raises responded to a new capacity that is not a fact of the state;
3. **§10.1 now has measured cases, and a harder form than the written one**: not only can the written
   rule be the wrong one — **the space declared in Geminis can fall short** because of a technology
   that did not exist when it was declared;
4. **§10.3, open problem 2, has a second independent instance**, and the way out C7.13 had proposed
   —indexing to occupancy— is **empirically discarded** for any resource already rationed by a fee
   market;
5. **the customer is approaching on its own.** In 22 months Ethereum went from recalibrating inside a
   large fork, to a lightweight fork mechanism (EIP-7892, `Final`), to a schedule written in advance
   and executed by calendar. **What it is missing to get here is exactly I2**: firing from the state
   and not from the clock.

## What the phase did **not** produce

**It produced no evidence that the design is better.** Two of the three cases give findings against,
and the third gives a tie with an asterisk. What it did produce is something more useful at this
stage: **the three exact places where the mechanism breaks against the real world**, each with its
number beside it and its test anchored, so that none can be forgotten without the suite falling over.

## Reproducing it

```
cd geminis
python herramientas/replay.py        # case 1 · the bomb
python herramientas/replay_blobs.py  # case 2 · the blobSchedule
python herramientas/replay_gas.py    # case 3 · the gas limit
python verificar.py replay           # the pass criteria for all three
```

The three series are in `datos/` (144 KB, with provenance inside), so **everything runs offline**. To
download them again: `python herramientas/traer_datos.py blobs|gas|dificultad` — public endpoint, no
key.
