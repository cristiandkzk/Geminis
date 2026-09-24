# Deterministic rule succession

**English** · [Español](Geminis%20Paper.es.md)

**A chain that carries written into block 0 how its own rules change, and that executes
that change with no vote, no political fork and no human intervention in the decision.**

---

## Abstract

Protocol evolution is, today, an act of governance: someone proposes, someone decides,
someone walks away. This document describes an alternative — that the succession rule live inside
Geminis and execute on its own when the state of the chain meets a verifiable condition.

The result is not a family of chains: it is **a single chain that commutes its ruleset by
generation**, preserving state intact and chaining every generation to its ancestor by
hash. The goal is not a blockchain that never needs a fork, but a blockchain **whose
fork is already part of the protocol**.

---

## 1. The problem

Every deployed protocol sooner or later meets a condition its original rules do not handle
well. The three answers that exist today all put a human in the loop at exactly the moment
of the change:

| Mechanism | Example | Who decides |
|---|---|---|
| Contested fork | Bitcoin / BCH | A faction writes new software; the market arbitrates afterwards |
| On-chain vote | Tezos, Polkadot | The holders, with all the politics that drags along |
| Forced obsolescence | Ethereum's difficulty bomb | The protocol forces the change, but humans write the successor |

All three work. None is deterministic: in all three, what comes next is a decision taken
in the moment, by people, under pressure. And that decision is exactly where a protocol
turns political.

---

## 2. The proposal

Geminis contains, besides the rules of the first generation, three more things:

- **`TRANSITION_RULE`** — the trigger condition, computable from the state of the chain.
- **The parameter space** of all its possible descendants.
- **The interpreter** capable of executing any point in that space.

When the condition is met, the node reads the rule, selects the parameters of the next
generation and **changes its own ruleset**. There is no new software to install, no state to
migrate, nobody to ask.

**How what follows should be read.** Those three pieces do not have the same backing, and saying
so here is more honest than leaving it for the end. The succession of **internal parameters**
—capacity, issuance, block times— is the half that went out looking for takers and found them
(§12, Test 1). The **interpreter** and the **chainable generations** —which are what makes
§6.6 possible and what separates this design from its precedents— are the half that pays the most
expensive boundaries of §10.1 and that **still has no case found outside**. They go together
because the mechanism is a single one; but the first is an application and the second is a bet, and
the document gains nothing by hiding which is which.

---

## 3. The mechanism: commutation

The piece that keeps this from being a fork in disguise is that **the node is not replaced, it is
commuted**. It is the same process running, with the same state in memory, executing
different rules from a given block onward.

<!-- FIGURA: figure-commutation.html -->

```
   ┌──────── ruleset A ────────┐ ┌─ F ─┐ ┌──── Δ ────┐ ┌─── ruleset B ───┐
                                                     ║
   ───▣───▣───▣───▣───▣───▣───▣───▣───▣───▣───▣───▣──╫──▣───▣───▣───▣───▶
                              ▲       ▲              ║
                              │       │              ║
                           block N   N final    activation
                       TRANSITION_    LOCK-IN   commutation in effect
                        RULE → TRUE  irrevocable
                        (advisory)   params_nuevos
                                      on-chain

   the SAME node · the SAME state · no migration, no bridge, no snapshot

   F = challenge window (§6.3) · Δ counts from lock-in, not from N

   H0_A ─────────────▶ H0_B = H( H0_A ‖ state_trigger ‖ params_nuevos )
                       computed at lock-in, with N already final
```

The node's track is not cut at the transition block: it changes rules. State crosses over
intact because it never leaves the process that holds it.

### The trigger is not the activation

Commuting in the same block in which the rule evaluates TRUE would turn every transition into
a surprise. The mechanism has three times, not two:

1. **Trigger.** At block `N`, `TRANSITION_RULE` returns TRUE. That commutes nothing and
   commits nothing yet: it is advisory, and a reorganization can undo it. Since I2 requires the
   trigger to publish how many blocks are left at the current rate, the trigger is simply the
   moment at which that distance reaches zero.
2. **Lock-in.** When `N` is final, the trigger becomes **irrevocable**: from then on, even if
   the state rolls back, the activation is already fixed. A schedule that switches on and
   off is worse than none at all, because nobody mobilizes a team against a date that can
   evaporate. Waiting for finality is not ceremony — `H0_B` commits `state_trigger`, and
   committing it earlier would leave the checkpoint pointing at a state that a reorganization can
   take out of the chain. Lock-in emits the on-chain event with the complete `params_nuevos` and
   the activation height: everything an integrator needs to know is on the chain, `Δ` blocks
   in advance, without anyone having to announce it or ask permission to read it.
3. **Activation.** `Δ` blocks after lock-in —not after the trigger, so that the notice is
   exactly `Δ` and does not depend on how long finality took— the node commutes.

`Δ` is fixed in Geminis **per transition class**, not globally: a circulation transition
tolerates a long window —issuance pauses for a few weeks and nothing happens—, whereas
a cryptographic migration under attack needs the opposite. The trade-off is real and is
declared in §10.1.

The hash of each generation is derived from that of its ancestor, from the state that triggered the
transition and from the selected parameters. Geminis A **does not know B's hash** —it cannot,
because B incorporates information that does not yet exist— but it deterministically knows how it
will be computed:

```
H0_B = H( H0_A ‖ state_trigger ‖ params_nuevos )

Verify( H0_B, H0_A, state_trigger, params_nuevos ) → TRUE
```

`H0_B` is not the genesis of a new chain: it is a **generational checkpoint marker** within
the same chain. And it makes the entire lineage verifiable with one hash, from any generation
backwards.

### More than one transition in flight

Between lock-in and activation there are `Δ` blocks in which the chain keeps running with the
old rules even though the new ones are already committed. That window is not an edge case:
it appears on its own as soon as there is an accumulation rule, because the state that triggered
stays above the threshold while the change has not yet taken effect.

**A rule does not trigger again until its own activation** — not until its lock-in. If it could
trigger in between it would be measuring a state that **does not yet reflect the change it has
itself just committed**, which is a control loop with dead time. Bitcoin Cash already paid that
bill: its 2017 EDA was an automatic rule written in advance that reacted faster than its own effect
became visible, oscillated, and had to be replaced by a human fork three months later.
What closes the loop is the effect, not the commitment.

**But the wait is per rule and not global.** Blocking every trigger while one is in flight would
put an urgent cryptographic migration behind a circulation transition, and that empties out the
reason why `Δ` is per class. Two different rules can be in flight at once, and the second locks
in without waiting for the first.

**What they do share is the activation order.** `params_nuevos` is a complete point of the
space and not an increment, so activating generation 2 before generation 1 would also apply the
changes of generation 1, and with generation 2's notice. Generations activate in the order in which
they locked in; if two coincide at the same height, they apply in the same block, one after another.

> **Declared residue.** An emergency transition may have to wait out the remaining `Δ` of whichever
> one is ahead of it. It is **bounded** —the ceiling is the longest `Δ` in the space— and **does
> not compose**: it does not grow with the number of generations. And what concurrency gains anyway
> is the irrevocable part: the urgent one stays committed and announced even if its activation has
> to queue up.

Hence **`params_nuevos` is computed at lock-in and not at the trigger**, which is also where
`H0_B` is computed. With two transitions in flight, parameters computed at the trigger would hang
off an ancestor that is no longer the last one, and the lineage would not close.

**And that is why lock-in verifies before committing.** A checkpoint is irrevocable: if it
committed a point outside the Geminis space, the node would reach activation unable to commute
and the chain would halt. The successor is verified against the space and against the
additivity of the interface **before** being emitted, and if it does not pass there is no
checkpoint but a **rejection**, also on-chain. A rejection does not trim the successor to the edge
of the space —that would change the rule silently— nor does it stop consensus: that transition does
not happen, it is recorded that it did not happen and against which ancestor, and the rule does not
retry against that same ancestor. That a rule is seen to have got stuck against the ceiling of the
space is information, not a failure: it is the bottom of the ladder of §10.1 announcing itself in
good time.

### The lock-in event is state, not an announcement

Lock-in emits on-chain the complete new ruleset and the activation height, and it does so in the
block in which `N` becomes final — a block which, **by being the last one, is not yet final
itself**. A legitimate reorganization can replace it.

There is no contradiction, but there is a consensus rule to be written: **the event is emitted as a
function of the height at which `N` becomes final, not of the node having just found out.** It is
a fact derived from the chain and not a notification: anyone who replays the same blocks produces
it identically, because its two inputs —the triggering state, already final, and the committed
ancestor, already irrevocable— do not depend on who was present. A node that published only *what
has just matured* would be left, after a reorganization, with a lock-in in force and no record in
the state, and its root would part company with that of a node that did not reorganize. **That is
not an unreadable notice: it is a fork**, and of the worst kind, because the two nodes agree on
everything else.

That the record lives **in the state** and not in the node's memory is paid for by two different
things. An integrator with a header and a proof has to be able to read the activation without
replicating the entire chain; otherwise the `Δ` notice exists only for whoever already runs a full
node, which is precisely the one who does not need it. And §5 rests on the same thing: *the chain
that did not commute has no valid generational checkpoint* is verifiable by a third party only
if the checkpoint is in the state the chain commits to.

A corollary worth keeping at hand: when finality is decided by the challenge window (§6.3) and
not by a fixed number of blocks, the lock-in height is also derived by the chain, and a
reorganization prior to it can move that height. That is why the notice is counted from lock-in and
not from the trigger — and why `H0_B` does not include heights: moving *when* does not change *what*.

---

## 4. Design invariants

Five non-negotiable properties. Each one eliminates a way of reintroducing the human into the
loop.

**I1 · The interpreter lives in Geminis and never changes.** A transition does not introduce node
code: it selects a point of a space the node **already knows how to execute**. What Geminis fixes
permanently is not a list of possible rules but the **machine that runs them**, and the
space of descendants is everything that machine can execute (§6.6). If the interpreter had to
be changed, it would not be a transition — it would be a plain ordinary fork.

The space is split into two halves with different rules. The **internal** parameters
—issuance, fees, block size, timings— can change in any transition. Those **visible in the
interface** —signature primitive, address format, serialization— only by way of I5.

*This invariant was weakened on purpose, and the cost is declared in §10.1: with an interpreter,
the set of possible futures stops being auditable from Geminis.*

**I2 · The trigger is computed only from the state of the chain, and nobody chooses the moment.**
No oracles, no signatures, no votes, no external inputs: a trigger that needs someone to declare it
has already reintroduced the governance the design exists to eliminate. But computable is not
enough, and it is not enough for two different reasons: a volatile variable is computable and
surprising at the same time, and *"the state says Alice sent 1 wei to address X"* is also computed
only from the state — and it is a gate with an owner.

There are **two ways** for nobody to choose the moment, and every rule has to declare which one it
is in. By **observable approach**: the quantity that triggers is monotone non-decreasing and the
chain publishes *how many blocks are left at the current rate*. Nobody chooses the moment because
the approach is aggregate and public, and no single actor moves it alone. A rule declared this way
**cannot trigger from rest**: if the previous block did not publish a distance, what happened was
not an approach but a step.

By **demonstrated capability**: there is no approach and there cannot be one. This is the case of
§6.6 —the break of a primitive is not approached, it happens— and it is admissible only if
**producing the fact requires exactly the capability the transition exists to react to**. Whoever
can choose the moment is, by construction, the one against whom the mechanism defends, and choosing
it costs them the advantage they had. The rule declares what that capability is, the declaration
goes on-chain, and the chain publishes *no observable approach* instead of inventing a date.

Both exclude the same thing: a fact that an identifiable party can produce at will and cheaply. And
both have their limit written down. No node can verify that the declared capability is the true
one: that is audited in Geminis, which is where the space of rules is fixed and in plain sight
(I1), and that is why the declaration is mandatory and explicit rather than implicit. And the
distance of the first form is a **projection at the current rate**, not a promise — the rate can
change. The promise is `Δ`, which counts from lock-in and does not depend on anyone having seen
anything coming.

**I3 · State is preserved intact across the transition.** There is no balance migration, no
reassignment, no snapshot — and therefore no bridge, which is the most attacked component in the
industry.

**I4 · Every generation commits to its ancestor.** The lineage is verifiable by hash and does not
depend on anyone attesting to it.

**I5 · Transitions are additive in the interface.** Every address and every transaction carries a
generation tag from block 0. A transition can **add** formats; it cannot remove them.
Retiring a format is a later transition, separated by at least one generation from the one that
deprecated it.

This is the invariant that decides the failure mode of every external integrator. With it, whoever
did not manage to support the new generation **keeps operating in the previous one** —old objects
remain valid— and degrades instead of stopping. And when it meets an object of the new
generation it fails closed and loud, *"a version I don't know"*, instead of misinterpreting it,
which is the failure that loses funds.

---

## 5. Canonicity

Commutation produces a consequence that is not obvious and that is, probably, the most
valuable property of the design: **it inverts the legitimacy asymmetry of a fork.**

In Bitcoin the conservative position —change nothing— is the default. Whoever wants to change the
rules has to write new software, and the chain that stays the same can claim to be the
original. Here it is the other way around: the standard client commutes on its own, so
**not commuting requires actively modifying the software** and disabling the transition rule.
Whoever stays on the old rules does not preserve the original chain — they deviate from Geminis,
and cannot invoke Geminis to justify it.

The practical consequence is that *"which one is the real one"* stops being a social question. An
exchange, a wallet or a light client run the lineage verification, and the chain that did not
commute simply has no valid generational checkpoint. It is an objective canonicity
criterion, and no contested fork in history ever had one.

---

## 6. Architecture: nodes, work and order

### 6.1 Two classes of node, with different economics

**Compute nodes.** GPU and RAM. They host the models that do the requested work. It is expensive
hardware and it is a competitive market, but **they do not take part in consensus**: their income
is the payment for the request they executed, not the protocol's issuance for producing blocks.

**PoD nodes.** They verify and settle, and charge a fee every time two contracts interact.
They run on any hardware — PoD verification reproduces bit for bit on x86-64, ARM64 and a
phone.

**The fee is ad valorem, not fixed per operation.** A fixed fee is regressive in the two directions
that matter: it makes the small request unpayable —which is the one an agent economy will make in
volume— and it makes the large request free, which is exactly where the burn of §7.1 has to
bite so that the withdrawal of circulating supply follows value and not the number of operations.
Proportional to value, the same parameter serves both scales without anyone having to decide which
is which.

**The rule has one exception and it is worth declaring it here:** a newly created asset is worth
~0, so an ad valorem fee does not bite on its creation. It is the only operation in the design
where the rule of §6.1 is not enough, and that is why the antispam of minting comes not from the
fee but from the floor and the permanence deposit of §8.5.

Portability also has a governance consequence. **What lets a miner or a validator hold a chain
hostage is not their conviction: it is the capital moat.** Replacing whoever refuses costs ASICs or
stake, and meanwhile the chain does not advance. A node that fits in a phone has no moat: if a
group refuses to commute, the marginal cost of replacing it is one mobile phone. **A blocking
coalition cannot last if entry is free.**

**There is a stronger argument than that one, and it does not depend on the cost of entry.** The
one above rests on entry being cheap, and Test 2 weakened it: the cost is asymmetric by platform,
up to 15× depending on the operating system (§10.1). The argument that does not weaken is another:

> **You can have 3,000 nodes or 3 million. If there is no external demand, they all compete for a
> pie that does not exist.** Since issuance does not depend on work (§7.1), adding nodes creates no
> income: it only splits the same fee among more hands. **Manufacturing identities is free and
> yields exactly the same**, which is a considerably more robust property than making it
> expensive.

**Measured (Test 2, §12).** On a Motorola Edge 40 Neo under Termux, an ML-DSA-44 verification from
bytes runs in **391 µs** as bytecode with JIT —3.51× native— and yields ~640 tx/s with a quarter of
a core dedicated to signatures. It is the same absolute time as on a desktop i5-9400. The
budget fits with room to spare.

With one caveat the argument above did not anticipate: **not all phones cost the same.** iOS does
not allow third-party JIT, and since here the bytecode arrives at runtime from the chain, it cannot
be precompiled before publishing the app either. A node on an iPhone is forced into the
interpreter: **~15× slower** than the same device on Android. The blocking coalition still cannot
last —entry is still cheap in absolute terms— but the cost of entry is asymmetric depending on
which side of the duopoly you are on, and that asymmetry belongs to the operating system, not to
the design (§10.1).

### 6.2 PoD verifies the predicate, not the inference

A model cannot pass the determinism gate that PoD rests on. Not even at temperature zero:
floating-point non-determinism across different hardware breaks bit-for-bit reproduction, and
without reproducible re-execution a dispute cannot be resolved without a human showing up to give
an opinion.

The split into two layers makes it irrelevant. **The GPU produces; the light node checks.**
The request does not say *"generate good code"* — it says *"deliver something that compiles and
passes these tests"*, and that is checked deterministically, cheaply, on any hardware. Inference is
not verified: what is verified is that **the output satisfies the predicate**.

Out of that comes a hard restriction on what a work request can be:

> **Every request carries a deterministic acceptance predicate, cheap enough to run on the light
> layer.** Whatever cannot be expressed that way is not work that issues coin.

That turns a fuzzy warning —*"not all work is provable"*— into a sharp boundary:
the settleable subset is exactly that of requests with a verifiable predicate. Code that compiles
and passes tests, an answer that satisfies a check, a transformation with a checkable inverse. That
this subset is large enough to sustain an economy is a hypothesis, and it is in §12.

**And there is a corollary that looks like a limitation and is the opposite: the client does not
choose which node executes their request, and does not need to.** In a normal services market,
choosing a provider *is* the quality mechanism: you research, compare reputations and place a bet.
Here quality is not secured by selecting in advance but **at acceptance** — if the output does not
satisfy the predicate, there is no payment. It is the same inversion the rest of the design makes:
do not trust who, verify what.

Out of that also comes a property §6.5 uses: since there is no channel through which to direct a
request to a particular node, there is no channel either through which a prior reputation —having
been there at block 0, for example— could turn into an economic advantage.

### 6.3 Order without global consensus

Verifying and ordering are not the same operation, and it is worth saying so because they are
easily confused. If Alice signs two transactions spending the same 100 tokens, **both are
individually valid**: any verifier looking at them separately says TRUE to both. Only order
decides which one wins. That is the problem consensus exists to solve, and validity does not touch
it.

But **global** order is not needed:

- **Queue per account.** Each account carries its own sequence and its owner is the only one who
  can append to it. Two interactions that do not share collateral do not need a relative order —
  and they do not have one, which is different from having it undefined.
- **The lock eliminates contention.** Committing funds into a contract takes them out of the
  available balance. They cannot be committed twice, so the only fact that crosses between accounts
  —*"these tokens are committed"*— does not need to be ordered against anything.
- **Finality by challenge window.** An interaction becomes firm when the window passes
  without anyone presenting proof of conflict. It is not a new mechanism: it is the optimistic
  verification of escrow, promoted to a finality layer.

Only one real conflict remains: that the owner of an account signs two things at the same index.

**The challenge window cannot be clogged, and the reason is not the price.** The obvious objection
is that if processing challenges has finite capacity, an attacker fills it with garbage so that a
legitimate proof does not make it in time — and with the hard ceiling on the delay to lock-in
(§10.1) that would be enough for a fraud to become firm. It is not enough, because of a structural
asymmetry:

> **Filling is serial; draining is parallel.** A challenge does not exist until it enters a
> block, so the ceiling for filling is the capacity of the chain — a single pipe. Draining is done
> by all PoD nodes **at once**, because verification reproduces bit for bit on any hardware and
> anyone can take any challenge.

The margin is `N · h / γ`, with `N` nodes, `h` the work each one does per block besides
verifying the block, and `γ` the cost of verifying a challenge measured in equivalent transactions.
With `γ ≈ 1` —which is what the VM step ceiling of §10.1 guarantees— and 10% headroom per node, the
formula gives **ten PoD nodes**; run with a real queue instead of calculated, **eleven** are needed,
and the reason why is in the third condition below. The 10% is conservative by an order of
magnitude: Test 2 measured 640 tx/s using a quarter of a core on a phone with eight.

**Three** conditions hold that up and they have to be written down, because none is automatic:

- **any PoD node resolves any challenge.** If the node that ordered the original interaction were
  required, there would be no parallel work to distribute and `N` would disappear from the formula;
- **arrival order, and a flat bond.** If the queue were ordered by bond size, capital would buy
  priority. With arrival order, the bond stops being a **bid** and becomes a **cost**: it is lost if
  the challenge does not verify, and *"does not verify"* is deterministic, so no judge is needed;
- **each node picks in its own order, and not in the queue's.** This is the condition that was
  missing, and it appeared when running the queue instead of calculating it. Arrival order solves
  **priority** —capital does not buy a turn—, but if on top of that every node takes **from the
  head**, the `N` nodes verify exactly the same challenge and parallelism evaporates: measured, with
  fifty nodes the margin is identical to that of a single one, the queue saturates with any `N`, and
  a legitimate challenge buried in garbage does not wait a fixed term but a ramp: the backlog grows
  by about ninety per block and drains at ten, so what arrives at height `T` waits on the order of
  `9·T` —the censorship attack working, and getting worse over time—. The rule that fixes it needs
  neither coordination nor knowing how many nodes there are: **each node walks the queue in a
  pseudorandom order derived from its own identity.** The cost is **one node**: the required `N`
  goes from ten to eleven, because two nodes sometimes coincide. The exact alternative —splitting
  the queue among the `N`— reproduces the ten on the nose and **requires knowing how many there
  are**, which is precisely what a design without a validator set cannot know.

And there is a property of the random case worth having written down, because it is what makes
eleven enough: **the backlog does not grow without a ceiling, it stabilizes.** The longer the queue,
the less the nodes step on each other, so the effective drain rises on its own until it matches the
tap. With eleven nodes the equilibrium settles at some four hundred challenges and a mean wait of
four blocks; with twenty, at twenty challenges and two tenths of a block. *The queue is long, not
infinite, and that is a different thing.*

**But a queue that does not saturate is not the same as every challenge landing in time, and the two
were read as one.** The mean wait of four blocks describes the queue's equilibrium, not what happens
to any particular challenge: since each node picks at random among everything pending, the wait has a
heavy tail. Measured with 19.6 million legitimate challenges under a sustained censorship attack,
against the finality window of the initial ruleset (12 blocks):

| PoD nodes | mean wait | maximum observed | wait longer than 12 blocks |
|---|---|---|---|
| 11 | 4.2 blocks | 89 | 6.2% |
| 13 | 1.2 | 28 | 0.04% |
| 15 | 0.6 | 16 | 0.0004% |

With the eleven nodes the design declares sufficient, **about one in sixteen legitimate challenges is
not verified inside the window, under the very attack this section exists to resist.** The queue does
not fail: what does not hold is the finality promised in 12 blocks against its own worst case. *This
is our own simulation, on the simulator that measured the rest of this section: evidence of the kind
§11 distinguishes from a customer found outside.*

**The fix is not to ask for more nodes**, because `N` is not a protocol parameter: there is no
validator set, and anyone runs a PoD node or none. The only dial that exists is the window, and it has
to be calibrated against the worst case the design already declared viable —eleven— and not against a
better `N` that may never be running. Lengthening it by a fixed amount closes the gap, on the order of
150 blocks, but charges that latency to **every** transfer even when nobody is attacking anything, and
attacking costs burned bonds: the normal state is calm.

> **Finality stretches only when there is a queue, and with a ceiling.** The window is the base while
> the challenge backlog has stayed below a threshold for an entire window of consecutive blocks;
> otherwise the only thing that matures the transition is the class's hard ceiling (§10.1). **There
> are no intermediate values, on purpose:** a window that grew gradually with the backlog would make
> any one-block difference between two queues move the maturation. With a threshold and a streak it
> takes a *sustained* disagreement.

Two measured things support the numbers. **The threshold is a plateau and not an optimum:** with a
sustained flood of 70 to 100 junk challenges per block over a capacity of 100, the probability of
waiting more than 12 blocks is negligible as long as the backlog does not pass about a hundred, and
only then grows fast —0.00006 with an equilibrium backlog of 70, about 0.06 with 383— so **any
threshold between 20 and 80 separates the harmless from what requires stretching the window**, and 40
was chosen. The reason is that detection and damage are coupled: delay cannot be created without
creating a proportional backlog, and that backlog is exactly what the threshold detects. And **the
flood that really creates risk requires filling 85% or more of the entire block capacity with junk,
sustained**, burning a bond for each one: near-total saturation, not a subtle attack. On the ceiling:
with 59.4 million samples at eleven nodes and the full flood, **zero waits above 88 blocks.**

**What is built and what is missing, stated whole.** The per-class hard ceiling of §10.1 is exactly
the ceiling of this rule, and it was already written into the schedule with nothing activating it: the
signal was missing. Now the node carries the backlog and a streak of calm blocks, and the maturation
of the lock-in uses the base or the ceiling depending on that streak. **That is the signal and the
reaction, not the source of the signal**: the challenge queue is not connected to the node's state, so
today the backlog arrives as a parameter and nothing produces it. And for the finality of ordinary
interactions the rule is specified and simulated, not implemented. Two things follow that have to be
written down:

- **As long as each node brings the backlog in from outside, it is not a fact of the chain.** A
  challenge does not exist until it enters a block, so with the queue inside the state it would be
  —every node would compute it the same—. Without that, two nodes with different views can mature at
  different heights, and since those heights do not enter `h0`, the lineage does not tell them apart.
  It closes one of two ways: the backlog comes out of the state, or the schedule's heights enter `h0`.
- **The cryptographic class's ceiling does not cover the worst case measured.** It adds up to
  12 + 32 = 44 blocks against an observed maximum of 89, and it is undecided on purpose: shortening
  it buys urgency in the emergency migration and costs legitimate challenges coverage under
  saturation, the same tension `Δ` already has (§3). The other classes' ceilings do cover it.

The bond does not have to be large, only non-zero, and the reason is an asymmetry that plays
entirely on the right side: **the honest challenger's bond comes back** —their proof verifies— **and
the attacker's is burned.** Sending ten thousand copies of a valid proof costs the honest party
nothing, and sending ten thousand false challenges is ten thousand bonds lost.

Below that dozen or so nodes the queue does saturate. That is the bootstrap regime, and there the
chain has bigger problems than this one.

**What happens in the transition block.** Nothing special, and for two different reasons. What is
in the mempool is not consensus state: the rules of the block that includes it apply, and whatever
becomes invalid simply does not get in — it is what any chain does in any hard fork and it needs no
mechanism of its own. And what is half-committed **in the state** —a signed and unaccepted offer, an
escrow with the window open crossing the activation— is resolved by I5: every object carries its
generation tag and old rulesets are never retired, so **an escrow opened in generation A settles
with the rules of A**. The new rules apply only to what is opened after activation, which is also
the fair thing: the parties agreed under known rules.

### 6.4 Getting it wrong is not forbidden: it is made suicidal

That a signature is unforgeable does not stop its owner from signing **two different messages**.
Both are genuinely theirs, neither is forged, and no signature scheme can prevent it. That
is why the answer is not to forbid but to make it not worthwhile — and there is a way of making the
punishment cryptographic instead of administrative.

In Schnorr and ECDSA, signing two different messages **with the same cryptographic nonce** allows
the private key to be solved for from the two signatures. It is a known accident: that is how the
PS3 key was lost, and that is how wallets with bad randomness generators were emptied.

Turned into a design rule: **the signature nonce is a deterministic function of the account
index.** Then signing twice at the same index is not an infraction that has to be proven and
sanctioned — **it is publishing one's own private key.** Anyone who collects the two signatures
takes everything the mistaken party has.

Three consequences, and the third is the one that closes the design:

1. The punishment needs no protocol rule, no bond, no arbiter to execute it.
2. It is verified on a phone: two signatures and one subtraction.
3. **The watchman funds himself.** The classic challenger problem —nobody has a reason to watch—
   disappears when the reward for catching the infraction is the infringer's balance. There is no
   need to invent an incentive: the incentive is the loot.

### 6.5 Every transfer is bilateral

Unilateral sending does not exist. Alice offers, Bob accepts, and only then does the transfer exist;
if Bob never answers, a timeout returns the funds.

**There are two classes of offer and the difference is by design, not by use.** An ordinary transfer
is **directed**: it names the receiver, because paying a specific someone is the point. A work
request is **open**: it names nobody, it is taken by whichever node can satisfy the predicate, and
the lock of §6.3 makes sure only one takes it. That second form is the entire work assignment
mechanism of the system, and it is worth saying because it is written nowhere else:

> **Nobody assigns requests.** The client publishes predicate, price and deadline with the funds
> already committed; the node that can fulfil it accepts it. It is *pull*, not *push* — the node
> selects itself because it knows its own hardware, and filters itself out on its own, because
> accepting a request it cannot fulfil means failing the predicate and not getting paid.

Out of that three things come for free. **There is no duplicated computation**, because acceptance
happens before computing and whoever loses the acceptance spent nothing. **A saturated node simply
does not accept**, so the request stays available for another one without anything having to route
it. And **the client cannot direct work to a chosen node**, which is the property the certificate of
§7.2 depends on in order not to turn into an advantage.

The deadline is declared by the client together with the price, and there is the tension that has to
be settled: long, and a node can accept and not deliver in order to block the request cheaply;
short, and the node with slow hardware does not make it and loses the electricity it already spent.
With the client declaring it, the node decides along three axes instead of one —*can I satisfy the
predicate, at this price, within this deadline?*— and the parameter is set by whoever pays the
consequences. **Whoever accepts and does not deliver does not get paid and releases the request**,
and since accepting is an on-chain act that accrues a fee, blocking requests costs money and buys
only a delay.

This does not prevent double spending —that is done by the lock and §6.4— but it does two other
things:

**It puts the watchman where he was already looking.** Whoever has to sign to accept is the one who
can lose. Bob is online, he is about to commit, and checking Alice's index before signing costs him
nothing extra. The interested observer stops being a role that has to be funded and becomes a
mandatory signer.

**And it turns prudence into structure.** Since acceptance is an on-chain act, *"wait for
finality"* stops being a discipline the receiver has to remember to follow: there is no transaction
until they signed. In Bitcoin, accepting with zero confirmations is an imprudence the protocol
allows; here there is nowhere to be imprudent.

The costs are in §10.1: you cannot pay someone who is offline, and finality is measured in minutes
or hours.

### 6.6 Cryptographic evolution with no bottom of the ladder

Every cryptographic primitive eventually gives way, and a chain that cannot replace its own has an
expiry date. The problem is that *"the primitive broke"* is not in the state of the chain, so it
cannot be a trigger (I2); and if Geminis carried a **list** of replacement primitives, the list would
run out and a human fork would be needed. Neither thing is acceptable, and both are solved with the
same loop.

**The canary turns the break into a fact of the state.** Geminis publishes a deliberately weakened
version of the primitive, with an on-chain reward. If someone breaks it and claims it, that **is**
state: there is a preimage or a forgery written in a block. The trigger does not read *"the
cryptography broke"* — it reads *"the canary was claimed"*, which is observable, deterministic and
oracle-free. The reward also makes someone actually try: it is the same pattern as §6.4, the
watchman funded by the loot.

**The weakened instance is derived; it is not generated.** It is the condition that makes the canary
admissible under I2 —the *demonstrated capability* form— and it is easy to overlook. If Geminis
**generated** the instance —a modulus, a key pair—, whoever generated it would keep their trapdoor
and could claim the canary whenever they felt like it. What I2 admits as demonstrated capability
would in fact be a secret somebody kept: the canary would stop being an alarm and become a gate with
a cryptographic disguise, that is to say the very governance the design eliminates, but much harder
to see. That is why the instance comes out of a **public seed** by a deterministic, nothing-up-my-
sleeve procedure, and anyone can rederive it from Geminis. A canary that cannot be rederived from
its seed is not a canary: it belongs to someone.

**The ladder of canaries grades the response.** A weak canary gives way years before a strong one,
so the weak one triggers a migration with a long `Δ` —planned, no emergency— and the strong one a
migration with a short `Δ`. By the time someone can break the strong one, the migration has already
happened. That is what avoids the case of a cryptographic surprise with a short grace window.

**The interpreter removes the bottom of the ladder.** Since Geminis fixes the machine and not the
list (I1), a new primitive is **bytecode**, not node code. The node never updates because it already
knows how to execute the machine, and the set of possible primitives stops being finite.

**Who writes that bytecode: it is a work request.** When the canary falls, the protocol publishes a
request —*"deliver an implementation that meets this interface and these vectors"*— and the agents
compete to deliver it. The acceptance predicate is deterministic and cheap to run on the light
layer, which is exactly what §6.2 demands of any request. There is no committee to choose: whoever
delivers gets paid like for any other work.

**Who says it is secure: nobody can, so it is tested the hard way.** Cryptographic security is not a
decidable property — there is no predicate that verifies it. What can be done is to make mechanical
the standard the real world uses, which is *"many attacked it and nobody could"*:

> **The gauntlet.** Every candidate enters with a weakened instance and an on-chain reward for a
> fixed window. If someone breaks it, it is discarded and the next one goes. The one that survives
> the window is installed. It is the same canary, used as an entrance exam instead of as an alarm.

**The gauntlet measures security; cost is measured by another clause.** An implementation can be
correct and unbreakable and still be ten times more expensive than the one it replaces: nobody can
break it —it is correct— so it survives the window and stays installed forever. At that moment the
budget of §6.1 breaks *from inside the protocol*: with no fork, no attacker and without any rule
being violated. That is why the acceptance predicate carries **three** clauses and not one:

> **Correctness, ceiling and locality.** The candidate has to pass the vectors, verify below a
> **ceiling of VM steps**, and do so touching fewer than a **ceiling of pages**. Both ceilings are
> measured in executed quantities, not in wall-clock time: they are deterministic and they reproduce
> across architectures (Test 2 measured the count as identical between x86-64 and ARM64), so they
> qualify as a predicate under §6.2 and as a fact of the state under I2. Wall-clock time would not
> qualify: it depends on the hardware, and that would be an oracle.

**The ceiling is not a free number, and it is not a performance decision.** On one side it is tied by
the budget of §6.1 —verification has to keep fitting into the light layer, which is where cheap node
entry comes from and with it the answer to the validator problem—; on the other it is **a security
condition of §6.3**, because it is what prevents a challenge from existing that is more expensive to
verify than to create (§10.1). A correct candidate that does not fit under the ceiling is not
rejected as insecure: it is rejected as unaffordable, which is the same criterion §6.1 applies to
everything else.

**And the ceiling is not chosen: it is derived.** It is what ties `§6.1` to `§6.6` in a single sum —
`ceiling = f* × tiempo_de_bloque × R_declarado / tx_por_bloque`, where `f*` is the fraction of the
light node that signature verification may occupy and `R_declarado` is the rate of the entry
hardware, both frozen in Geminis, and the other two are internal parameters of the generation. What
I1 freezes is **the formula**; the value is set by each generation. The derivation, the two constants
and what ends up decided are in §10.3.

### 6.6.1 · Why there are two ceilings and not one

A step ceiling assumes that one step is worth one step, and **that is false**. With the machine built
and measured against instruction mixes chosen to be slow, the worst runs at **twenty-three times
fewer steps per second** than the real workload `R_declarado` came out of. With that gap open, a
perfectly legitimate predicate spends its entire ceiling in 596 milliseconds instead of the 22 the
ceiling promises: **the chain falls behind deterministically, with no fork, no attacker and without
any invariant seeing it**. It is the same failure mode this section opens with, one layer further
down.

**And it is not fixed by weighting the instructions.** The obvious way out is to charge each step by
its class —what gas does—, but the mix that produces the gap is a memory read, and a read costs the
same as an addition when the data is in cache: 207 million steps per second against 11. **It is the
same opcode.** What separates them is not which instruction it is but where the data falls, and that
is not read off the binary: it is known only by running it. A per-class weight would have to charge
every read the price of the worst one, and then the reference primitive —which is full of accesses
that do hit cache— would stop fitting.

What can be counted while it runs is **how many distinct pages the program touches**, and that is the
second ceiling: 96 pages of four kilobytes. The reference verification touches 26.

**And the second ceiling came close to introducing into the design the one thing the design does not
admit: a wall.** Written as a constant, the page budget had a property the writing did not give
away. A ceiling derived from capacity can *raise the price* —a primitive that costs more steps fits
by lowering `tx_por_bloque`— but **a constant ceiling can only exclude**, because there is no price
the primitive can pay. And the three primitives of one same family do not touch the same memory:
26, 40 and 65 pages. A budget chosen with an eye on the first leaves the third out forever, and no
sum points it out.

**The way out is the same move that had already settled the step ceiling: stop freezing a point and
freeze the sum.** Here the sum is a curve —how much rate the reference hardware sustains for each
memory budget—, measured once and frozen in Geminis. The page budget becomes an internal parameter
like block time or capacity, and **asking for more memory lowers the declared rate, which lowers the
step ceiling, which is paid for in capacity**. With that, the two ceilings stop being two: they are
the same time bound seen from two sides.

```
ceiling = f* × tiempo_de_bloque × R_declarado(pages) / tx_por_bloque
```

What the curve charges could not be anticipated without measuring it, and it is the most useful
thing it left behind: **from 96 to 512 pages memory is almost free** —the rate falls by 4%— and
**between 512 and 1,024 it collapses by 7.4×**, which is where the TLB reach of the reference core
runs out. The mechanism charges that shape without anyone declaring it: quadrupling the budget costs
4% of capacity and the next step divides it by seven.

> **And the space stops needing a limit by decree.** The most expensive point of the curve is
> declared and it is ruinous: with a sixteen-megabyte working set the chain does one transaction per
> block. It is a legitimate choice and nobody is going to take it — which is exactly how a boundary
> has to look in this design.

**What this cost block 0 is declared.** `R_declarado` had been calibrated on the rate of a single
instruction mix, and the correction lowers it from 300 to 70 million steps per second — because what
it has to withstand is not the average but the worst admissible case, and the adversary does not run
the average. The ceiling in steps barely moves; what changes is how many guaranteed steps a second of
clock buys, and since the cost in steps of a verification is set by the ISA and not by the ruleset,
**the initial capacity drops from 67 to 15 transactions per block**. It is the same mechanism this
section describes for future primitives —entering costs capacity—, charged against the one that was
already there. The full measurement is in §12, Test 5.

```
canary broken  →  work request  →  candidates delivered
                                            ↓
                          predicate: vectors + step ceiling
                                            ↓
                                   gauntlet: weak instance
                                   + reward + fixed window
                                            ↓
                        the one that survives is installed as bytecode
                                            ↓
                                   new canary published ──┐
                                            ↑             │
                                            └─────────────┘
```

The loop repeats indefinitely, all on-chain and without anyone deciding anything. The four costs this
brings are in §10.1, and the one that decides whether it is feasible is in §12.

**Prior convergence.** The idea that a chain should carry preloaded from Geminis the mechanism of its
own cryptographic succession had already appeared: in February 2018, Justin Drake proposed
*cryptographic canaries* on Ethereum Research — a mechanism with a bounty, redeemable by means of a
proof of threat, which on activation automatically commutes to a backup cryptographic primitive.

This design was conceived independently of that discussion. The coincidence is, therefore, relevant
information: the premise that cryptographic evolution can be anticipated in the protocol, instead of
being decided after the threat appears, had already arisen naturally while addressing a different
problem. Convergence does not prove the design valid, but it does constitute evidence that the
premise deserves independent consideration.

The difference lies in the depth of the succession. Drake's backup is a prewired single-step
mechanism: one transition towards an alternative primitive. Here, by contrast, the successor is
derived within a space of transitions defined by Geminis, and the interpreter allows successive
generations to be chained.

In the original discussion it was objected —and it is the objection that left the idea without
follow-up— that calibrating a canary to fire *before* the cryptography in production is compromised
forces estimates so conservative that the automation ends up redundant with manual supervision.

The objection is correct for a single-step mechanism. A premature transition consumes the only
recovery resource available, so the trigger has to be nearly perfect; and a trigger that has to be
nearly perfect needs someone to judge it. There the automation dissolves.

A chainable succession changes that calculation. A premature transition does not destroy the future
capacity for recovery: it consumes a generation that can, in turn, generate the next one under the
rules of Geminis. The trigger no longer has to be perfect — and with that the reason why the
automation fell back on human supervision disappears.

The second objection from that same discussion —that whoever can break the primitive gains more by
keeping quiet than by collecting the reward— is not solved by this loop, and it is declared in §10.2.

### 6.6.2 · A scenario: migrating a classical signature to a post-quantum one

The above is the loop; this is what it does with a concrete signature change. A chain that was born with a
classical signature —Ed25519, or secp256k1 like Ethereum's accounts— can move to a post-quantum one **by
succession**, without a coordinated fork: the transition adds the successor format (ML-DSA-44) to those the
generation accepts, and from then on both are valid. What is preserved is what I3 and I4 promise: the state, the
Genesis root and a lineage that verifies end to end.

**Why the reference implementation starts with a classical signature.** It is not a position on what a chain should
use: Geminis' choice for a chain born new is still ML-DSA-44 (§10.1). It is that to show a *change* of signature you
have to start from one different from the destination, and classical → post-quantum is the migration that existing
chains have pending. **The initial signature is a parameter of Genesis, not a property of the mechanism.**

What was measured is in §12 (Tests 8 to 10) and has four caveats that matter:

- **The classical signature is not the cheap one.** Verifying secp256k1 costs 1.71× what ML-DSA-44 does (5.67 M
  against 3.32 M steps) and `ecrecover` does not fit under the initial ceiling. Migrating would give capacity back;
  what grows is size, about 38× per signature plus key.
- **The mechanisms are independent; the security is not.** The hash succession (BLAKE2s → SHA-3) and the signature
  one (Ed25519 → ML-DSA-44) advance one without the other and in any order, with the lineage verifying and the root
  intact. But Ed25519 hashes with SHA-2 and ML-DSA with Keccak: once both have happened, `H` shares a core with the
  successor signature. It is the limit §10.1 declares.
- **Ethereum has not chosen ML-DSA-44.** According to [ethereum.org](https://ethereum.org/roadmap/security/quantum-resistance/)
  and [pq.ethereum.org](https://pq.ethereum.org/) (September 2026), its team is evaluating Falcon, Dilithium and
  SPHINCS+ for accounts, with account abstraction (EIP-8141), and leanXMSS —hash-based— for validators. This scenario
  shows that the mechanism can express that change; not that it should be the destination.
- **What comes after ML-DSA-44 remains open.** As §6.6 says, the successor is delivered by a work order as bytecode
  and accepted by the gauntlet; that path is not built. ML-DSA-87 is not a step: it is a cost level measured in
  Test 2.

### 6.7 The compute challenge: fast wins, better is not enough

§6.5 assigns each work request to a single node, before it computes — that is what eliminates
duplicated computation. But there is a class of work that needs exactly the opposite: many nodes
computing in parallel, most of them losing their computation, and only one getting paid. It is not an
oversight of §6.5, it is a different mechanism: the waste of those who lose is what makes the cost of
participating real and unfalsifiable, the same argument that sustains Bitcoin's subsidy (§9) — with
one difference: here the scarce resource is not hashing, it is inference from a model, bounded by the
protocol.

**The risk that has to be ruled out before writing a line of mechanism.** §6.1 declares that the
choice of model belongs to the node, not the protocol — a node can run any LLM and replace it
whenever it wants. If "who gets paid" were decided by how good the answer is, a node with a better
LLM would systematically win more challenges than one with a worse LLM, at equal hardware — and that
rebuilds the capital moat §6.1 exists to avoid, now on the model side instead of the silicon side:
capital buys the best model, the best model buys more fees, more fees buy more capital. The property
that has to hold is the opposite of the "let the best one win" intuition: **the LLM decides what to
attempt; the protocol decides how many times and in how much time it can attempt it, and neither of
those two things depends on how good the answer is.**

**The challenge predicate has two independent clauses, and both are needed.**

1. **Structural filter, cheap and deterministic** — it runs on the light layer just like any other
   predicate of §6.2: the output has to parse against a fixed schema and clear a floor of matching
   against a dictionary published on-chain. It does not measure quality: it measures "this was
   generated by something that understands language". Randomly generated noise fails it almost
   always; any LLM trying in good faith passes it almost always, whatever its size. Without this
   filter, the optimal strategy uses no LLM at all — it generates random bytes faster and more
   cheaply than any inference, and the challenge stops measuring what it is supposed to measure.
2. **Hash lottery** — the node chooses its own `nonce` and puts it *inside* the prompt, together
   with the challenge seed; the submission is valid if `hash(canonical output ‖ nonce)` falls below
   a difficulty target. That the `nonce` goes in the prompt and not stuck onto the output afterwards
   is no detail: it is what prevents computing the answer once and grinding nonces separately over a
   cheap hash — every attempt demands a fresh end-to-end inference pass, so "attempts per second" is
   real inference throughput and not hashing throughput.

No LLM can "guess" a hash better: if the hash function behaves like a pseudorandom function, being
smarter does not raise the probability that a particular output falls below the target. The only
thing that raises that cumulative probability is how many attempts per second the node makes — which
is hardware and inference efficiency, not model quality.

**One channel remains through which quality sneaks in anyway, and it has to be closed on purpose: the
fixed structural filter can be farmed with a narrow model, trained only to pass that filter and
nothing else** — not a general-purpose LLM, a few-megabyte shortcut built to beat an exam that never
changes. It is the same capital moat of §6.1, now in the form of a "model ASIC" instead of a silicon
ASIC.

**The way out is the same play §6.6 already uses against cryptographic obsolescence: do not fix the
exam, derive it from the state.** The schema, the language and the domain of the structural filter
are derived from the challenge seed — the same kind of value nobody can choose that the transition
nonce in I2 already uses — and they change from round to round. A narrow model trained for a fixed
domain falls over as soon as the domain rotates; a general LLM does not notice the difference.
Specializing stops paying, because there is no fixed target to specialize against.

```
semilla_ronda (chain state, ownerless)
        │
        ├──► domain of the structural filter (schema, language, vocabulary)
        │
        └──► range in which T falls (§6.7.1)

node picks nonce ──► prompt(semilla_ronda, nonce) ──► output
                                                          │
                                            structural filter (light layer)
                                                          │
                                              hash(output ‖ nonce) < target?
                                                    │            │
                                                    no           yes
                                                    │            │
                                              new nonce     enters the round's
                                            (if T remains)      lottery
```

### 6.7.1 · Rounds with an unpredictable window: why the clock cannot be fixed

Filter and hash lottery settle who may compete; they do not settle that the fastest always wins. If
"first to deliver" won the round without more, a model with a sustained throughput advantage —not a
narrow shortcut, a general-purpose LLM that is simply more efficient— would take a growing fraction
of the rounds forever, exactly like a miner with more hashrate in Bitcoin. There is no cheat to close
there: it is speed buying a result, and it is precisely what was decided must not happen.

**The solution is not to hurry or slow anyone down: it is that "arriving first" within the round stops
mattering.** The challenge is resolved in rounds of fixed duration in blocks —never in wall-clock
time, which would be an oracle (the same rule that already governs the two ceilings of §6.6)—, and
every valid submission received before the round closes enters a lottery with a fresh source of
randomness from the closing block. The node that delivers in the first block of the round and the one
that delivers in the last have the same probability of winning the lottery. It is the same play §6.3
already uses against capital in the challenge queue —pseudorandom order instead of arrival order—,
applied here against speed instead of against capital.

**The duration of the round cannot be a fixed and known number, for the same reason the exam cannot be
a fixed domain:** a constant value is a target to overfit the pipeline against —batch sizes, prewarmed
cache, calibrated exactly for that number—. The window `T` is drawn, in blocks, within a range
`[X, Y]` fixed by the protocol, using the seed of the block that opens the round — the same source
that already derives the domain of the filter:

```
T = X + (semilla_apertura mod (Y − X + 1))        [blocks]
```

Nobody knows `T` before the round begins, and once it begins everybody knows it at the same time —
nobody had an information advantage and nobody can ask afterwards for it to be moved.

**What this does not do: it does not lower the speed floor, it only prevents overfitting to a
number.** The short end of the range, `X`, ends up being the real requirement for anyone who wants to
qualify reliably round after round — sooner or later the draw is going to land there. What the range
avoids is someone building a pipeline tuned for a single known value; it does not relax how much has
to be withstood in the worst case.

> **Open problem — declared here, measured in §10.3.** `X` and `Y` cannot be fixed without measuring,
> and measuring them requires first deciding something that is not a measurement: what counts as the
> reference model whose legitimate worst case `X` protects. A floor calibrated on a large model on a
> datacenter GPU excludes any more modest node by design; one calibrated on the smallest admissible
> hardware stretches the round for everyone. The formula is frozen here; the two numbers are not.
> See §10.3.

---

## 7. Monetary policy

### 7.1 Three mechanisms that must not be fused

Every monetary rule has to answer a single question: **how much new money can exist, and as a
function of what.** The first version of this design answered *"as a function of work paid for and
verified"* —issuance indexed to settled work, bounded by a temporal curve— and that answer did not
survive its own test. It is worth saying how it died, because the corpse is the best argument in
favour of what replaces it.

**The theorem that killed it.** If issuance is indexed to settled work, then for whoever occupies
both sides of the operation —pays for the request and executes the request— the net issuance of the
system and their own profit **are the same quantity**:

```
net issuance  =  (k − β·φ) · W  =  the self-dealer's profit
```

They are not two numbers to be balanced carefully: it is an identity. **The network issues if and
only if paying yourself is profitable.** The only point where self-dealing stops paying off is
`k = β·φ`, and there net issuance is exactly zero — that is, the safe point is the one at which the
entire mechanism is equivalent to neither issuing nor burning. Measured in §12, Test 4.

> **Issuance indexed to work does not have a narrow window: it has a window of measure zero.**

The way out is not to calibrate better. It is to stop fusing into a single mechanism three things
that do different jobs:

| mechanism | what it does | what it depends on |
|---|---|---|
| **fees** | they remunerate the work delivered | on real demand |
| **issuance** | it sets the monetary state | **on nothing a node can manufacture** |
| **PoD** | it validates which work and which transition are valid | on the predicate, not on the intention |

> **No new unit is created because a node decided to do more work.**

The difference from the previous version is not one of degree. Before, manufacturing work produced
tokens and the whole design consisted in getting it to produce few; now **it produces none**.
Farming does not become barely profitable: it stops existing as a category. And that decouples two
things that were tied together and could not be —the friction against the farmer and the friction
against the real user—, which is exactly what made the window of Test 4 impossible.

Fees are split three ways. The percentages are illustrative and not design; what matters is that all
three exist:

```
request fee  ─┬─  70%  providers      (pays for the work)
              ├─  20%  burn           (withdraws circulating supply)
              └─  10%  reserve        (redistributed among nodes)
```

**The burn is the only irreplaceable piece.** With the burn at 0% the closed circuit is back within
reach and self-dealing becomes free. All the rest of the split is negotiable; that is not. The why
is in §7.3.

### 7.2 The day-1 distribution

Taking issuance out of the work equation leaves a question without which the rest does not start:
**who has tokens before the first fee exists.** It is the same question the three classic answers
get wrong.

- **Fixed supply created all at once.** Elegant, but it moves the problem to the split: who receives
  and by what criterion. It is a human decision at block 0.
- **Issuance by calendar.** It distributes over time, but it still does not say to whom.
- **Indexed to work.** It works only if the work has an external, physical cost — and then it is
  proof of work, which is what this design avoids in consensus.

There is no fourth, and the reason is the same theorem of §7.1 in another form: **a distribution of
new tokens indexed to an action yields at most what that action costs, or it is farmable.**
If it pays less than the cost, nobody claims it; if it pays more, it gets farmed. Bitcoin could
because hashing has an external, physical cost that is impossible to fake.

**The chosen form takes the third, bounded to block 0.** Geminis publishes pools with a cap per node
class, and **claiming is paid for by demonstrating the capability being claimed**:

| class | what the claim demonstrates | machinery |
|---|---|---|
| **compute** | solving a reference task with a deterministic predicate | §6.2 |
| **PoD** | verifying a reference batch within the VM step ceiling | §10.1 |

Four properties, and the last is the one that justifies the whole arrangement:

1. **It needs no identity.** The cost is external and physical. Geminis knows nobody, writes no
   list of recipients and does not choose.
2. **It makes the separation by class verifiable.** Declaring *"I am a compute node"* is free;
   solving the reference task of that class is not.
3. **The work is not thrown away.** Unlike hashing, claiming is **a rehearsal of the real
   product**: you do exactly what the network is going to ask of you afterwards. The cost of entry
   selects for the capability the network needs.
4. **What is not claimed is burned.** And out of that comes the property that answers the criticism
   this section opens with:

> **The initial supply is not set by the creator — it is set by how much real capacity showed up.**
> The published pool stops being a promise and becomes a ceiling. It does not eliminate the
> decision, because somebody chose the ceiling; but the number that actually ends up circulating is
> determined by the world.

**What has to be declared without ornament:** it is still **an auction paid in compute**, and
whoever has more hardware takes more. It is not an egalitarian split and it must not be sold as
one. It is **open**, which is a different thing, and it is the property Bitcoin's launch had.

**The certificate is not money.** Each claim also emits a transferable record of having taken part
in block 0. It carries no token allocation and no right to collect: if it gave a right to tokens it
would be money, and concentrating it would be concentrating the initial monetary base — the units it
was denominated in would change nothing. **Nor is it a licence**, and that variant has to be
discarded explicitly because it is the one that occurs to anybody first: if a certificate were
needed in order to collect fees, the number of nodes would become artificially scarce and precisely
the capital moat §6.1 exists to avoid would appear.

Four details of form:

- **it is emitted as a receipt of the claim, it is not claimed separately.** That way it is free and
  unfarmable at the same time: it inherits the cost of the claim, which does cost;
- **it is transferable only after a term, and the term runs from each claim**, not against a common
  date — a common date is a predictable wall of selling;
- **the protocol confers no right on it, nor any indirect advantage.** There is no channel through
  which an advantage could operate: the client does not choose which node executes their request
  (§6.5);
- **it can be free and perpetual because the set has a hard cap.** It occupies state forever like
  any other object, but the pool caps bound it to the order of 0.01% of a node's disk budget. What
  cannot be free is the **uncapped** creation of §8.5, which pays a floor and permanence: the
  variable that separates the two cases is the cap, not the nature of the object.

**What remains to be parameterized and is not decided:** the exact cost of the claim, the duration
of the window and the caps per class.

### 7.3 Why the closed circuit loses

The attack that has to be ruled out is the usual one, and it does not depend on anyone wearing a
disguise: Alice has her own nodes, sends work to herself and collects her own fees. The right
question is not whether the protocol can detect her —it cannot, and §10.2 explains why it never will
be able to— but whether it is worth her while.

It is not worth it, and at no scale. With the split of §7.1, each self-payment cycle leaves her:

```
net per cycle  =  −φ · ( 1 − providers − σ_A · reserve )
```

where `σ_A` is her fraction of the network. Measured:

| Alice's nodes | net per cycle | balance after 1,000 cycles, from 1,000,000 |
|---|---|---|
| 2 of 3,000 | −0.000900 | 406,486 |
| 99% of the network | −0.000603 | 547,068 |
| **100%** | **−0.000600** | **548,713** |

**She loses even while being the entire network.** The number of nodes only moves her slice of the
reserve; the burn stays out of her reach always, because it is not paid to anyone. Hence the burn
is the piece that cannot be removed: with the burn at zero, the last column becomes flat and the
attack becomes free.

It is worth noting what class of argument this is, because it is the methodological finding of the
whole design:

> **The protocol does not distinguish Alice from a real client. It does not try to.** It makes the
> closed circuit **lose money**, and the arithmetic does not need to know who anybody is.

And the same calculation closes the door next to it: **burning one's own money never benefits the
one who burns.** For any holding below 100%, burning lowers both their share and its value at the
same time, even at constant capitalization. The channel *"I burn to make mine worth more"* does not
exist.

### 7.4 A bounded supply banks unlimited activity

The natural objection to a ceiling on circulating supply is that it puts a ceiling on the economy.
No: it puts a ceiling on the **unit**, not on the **activity**. What limits how much economy fits is
not the quantity of money but the speed at which it can circulate, and here the only mechanical limit
is the escrow of §6.5 during the finality window — committed money cannot move again until the
interaction closes.

Measured with deliberately hostile assumptions —6-hour finality and only 20% of the circulating
supply tolerated in flight simultaneously— the velocity ceiling gives **292 turns a year**, against
1.2 for United States M2, 1.5 for M1 and ~12 for Bitcoin on-chain. Between 25× and 250× of headroom.

> **Issuance determines the monetary unit; fees determine the economic capacity of the network.**
> They are two separate questions, and confusing them is what makes people think a bounded supply
> needs a bounded economy.

### 7.5 Token concentration does not grant protocol power

It is worth saying here because it is the criticism this design borrows from Bitcoin, and in this
design it does not apply by construction.

In vote-governed chains —Tezos, Polkadot— holding **is** decision: whoever concentrates tokens
concentrates votes. In Bitcoin the separation between holding and power exists but it is custom, not
an invariant. Here it is an invariant: **I2 forbids the trigger from reading anything that is not
state**, and §10.1 closes the back door by declaring that signalling readiness is information and
never a gate.

An actor with 90% of the tokens has 90% of the money and zero power over the rules. That does not
solve wealth inequality nor the perception from outside —neither of the two is a problem a protocol
can solve— but it does separate the two things that in the rest of the ecosystem come glued
together.

### 7.6 The target is the quantity, not the price

The system fixes **circulation** and lets the price float. It is monetary aggregate targeting, and
the distinction from a peg is fundamental, not one of degree: a peg has its setpoint outside —a
parity against an asset the protocol does not control— and when the market does not want that price,
the loop runs in reverse and there is no bottom. A circulation ceiling has its setpoint **inside**:
the protocol measures exactly the variable it controls.

This is also the only thing compatible with I2. Price does not exist in the state of the chain; and
a trigger that read an on-chain market price would be worse than an oracle, because it would allow a
transition to **be bought** by moving a pool with borrowed capital.

> **Explicit prohibition, and it is a security condition.** The trigger reads `emitido − quemado`
> **of the native token** and nothing else. It does not read pool ratios, it does not read liquidity
> depth, it does not read volume, and it does not read the accounting of any other asset. This was a
> conclusion while there was no native market; with the market of §8 the pool comes to be in the
> state, within reach, and with the asset creation of §8.5 the attacker can manufacture **the asset
> and its pool** from scratch. A trigger that read just any `emitido − quemado` would be firable at
> will by whoever mints the asset that feeds it: it stops being a conclusion and becomes a written
> rule. It is the same promotion the VM step ceiling made, which came in as a performance budget and
> turned out to be a security condition of §6.3.

**A distinction the replay of §11 forced into writing.** There are prices that are not quotes: the
EIP-1559 base fee is **computed by the protocol** from a quantity —how full the blocks came in— and
is published by no market. A trigger that read it would not be reading a pool, so it does not fall
under the prohibition above; what does have to be seen is that pushing it costs filling blocks and
burning the fee, that is, it falls inside the burn channel §10.2 declares as a bounded boundary.
**What disqualifies it as a setpoint is not where it comes from: it is that it is nominal** —
Ethereum's base fee fell 650-fold in four years (§10.3). The rule still holds, then, but for two
different reasons that are worth not fusing: a market price is forbidden because it is **buyable**; a
price computed by the protocol is discarded because it **expires**.

### 7.7 The ceiling belongs to the family, not to the generation

Geminis fixes the total and each generation receives a portion of the same schedule. A transition
**relocates** issuance, it does not enlarge it: the next generation does not gain purchasing power
the previous one did not have, it gains room for manoeuvre within a total already fixed at block 0.

That is what keeps the anchor standing. The variant in which each generation brings its own ceiling
that adds to the previous one is defensible, but it is another design: it has no anchor, it has a
deterministic rule of expansion.

### 7.8 Circulating supply is `emitido − quemado`

It is the only definition compatible with I2. Discounting custody, locks or treasury requires
classifying addresses, and classifying is human judgement. The only thing excludable without
breaking anything are addresses Geminis itself defines.

**With more than one asset in the state (§8.5) it has to be made precise which circulating supply is
being spoken of: that of the native token.** Distinguishing one asset from another is not the same
operation as classifying addresses and does not fall under the same prohibition — the identity of an
asset is a fact of the state, written at its creation; that of an address is an interpretation about
who is behind it.

**That it carries no exceptions has a cost, and it is declared.** The permanence burn of §8.5 counts
like any other, so whoever occupies state moves everyone's measured circulating supply. It is the
boundary of §10.2, and the way out that would close it is precisely to open the first exception
here.

It is worth not confusing two things: that there is no premine means that Geminis grants no custody,
not that custody does not exist. Bitcoin did not premine either and today the exchanges hold
millions of BTC. Custody appears when a human hands over their keys, and no protocol can see it or
prevent it.

### 7.9 Dormancy, and a tension that has to be declared

A regime that targets the quantity has a problem one that issues by calendar can ignore: **lost
tokens.** Lost keys and dead contracts remain as *issued and not burned* forever —Bitcoin is
estimated to have ~20% permanently lost— and nobody burns a wallet whose key they lost. Over time
the measured circulating supply stays pinned against the ceiling while the living economy drains
away underneath.

The way out that respects I2 is **dormancy reclamation**: an address with no movement for `N`
generations is burned. It is deterministic, it is computed from the state and it classifies nobody.

**And it is worth saying what it is not**, because there is an apparent overlap with §8.5: dormancy
**is not the brake on state growth**. It runs in generations, that is, in years, and what it does
with a dormant balance is burn it, which is a monetary operation. What rations disk is the
permanence deposit, which runs in epochs and evicts without destroying. They are two rules with the
same apparent trigger and different jobs: one measures circulating supply, the other charges for
storage.

**But dormancy serves two different purposes that ask for opposite calibrations, and this design
cannot have both.**

| purpose | what counts as life | `N` | effect on hoarding | confiscates legitimate custody |
|---|---|---|---|---|
| **measurement** — that the measured circulating supply be the real one | any signed activity | above the cold-storage horizon | **none** | no |
| **velocity** — pushing money to circulate | only balance movement | below that horizon | real | **yes** |

**Separating issuance from work changed which of the two matters.** While issuance was indexed to
work and a circulation band could fire it, measuring circulating supply badly produced spurious
issuance: measurement was the urgent thing. With issuance decoupled, that channel closes and the
second problem is left standing, which is behavioural and not arithmetic — **if the currency
appreciates, hoarding it is rational and spending it is foolish**, and no circulation ceiling fixes
that. It is the Stage 2 problem of §9, and there dormancy stops being a measurement detail and
becomes the central mechanism.

> **What has to be said without ornament: the parameters written above are calibrated for the
> justification the redesign downgraded.** Counting *"any signed activity"* as life and setting `N`
> above legitimate cold storage makes dormancy **do absolutely nothing** against hoarding — a cheap
> signature every so often disables it completely. They serve for measuring; they do not serve for
> what now matters.

The velocity calibration is the opposite —only balance movement counts, and `N` below the
cold-storage horizon— and **its cost has to be declared, not hidden**: a custodian with cold storage
and a long-term holder become indistinguishable from a lost wallet, because the only thing that
separates them is intention, and intention is not state. That is the wall of §10.2 appearing again.

It is demurrage, and it has lineage: Gesell, the Wörgl experiment of 1932, Freicoin in 2012. It is
not an improvised idea, but it is a monetary decision with a real counterpart.

**The decision is not taken in this section**, because it is not monetary but about purpose: it
defines whether this is digital gold or circulating currency. It is set out in §9, Stage 2, and it
has to be taken early because it changes what class of asset this is from block 0.

### 7.10 What this section leaves open

Separating issuance from work solves farming and leaves a question this design **still does not
answer**: what governs issuance after block 0.

The pieces that are decided sketch a system in which circulating supply only goes down —the burn of
§7.1 withdraws, the dormancy of §7.9 withdraws, the permanence of §8.5 withdraws, and nothing
replenishes— with divisibility absorbing the deflation, just as Bitcoin's minimum units absorb its
ceiling. It is coherent and it may be the answer. But **it is not verified**, and presenting it as
decided would be exactly the error this document tries not to commit: taking an architecture on
paper as good before measuring it.

**What did get closed is one way out**, and it is worth saying because it is the first that occurs
to anybody: that issuance respond to demand. It cannot, and the reason is an asymmetry between the
two halves of a quantity regime.

> **Activity already determines how much circulating supply is withdrawn. What it cannot determine
> is how much is added.**

Withdrawing needs no recipient. Burning is a fact of the state, it verifies itself, and whoever
burns loses (§7.3): it is a lever that **only harms whoever pulls it**, so it can be left open to
anyone — and §8.4 ties it directly to economic activity. Adding does need a recipient, and choosing
it is either a human decision or an indexation to an action; in the second case the theorem of §7.2
comes back —it yields at most what that action costs, or it is farmable— and that is why §7.2 could
only solve it **bounded to block 0**, where the cost could be external and physical one single time.
A recurrent version of that is permanent proof of work, which is what this design avoids in
consensus.

And measuring demand in order to issue against it also fails along four independent paths, worth
enumerating because there is no single plug that closes them: on-chain, demand **is** activity, that
is, the `W` whose identity kills §7.1; the arithmetic of §7.3 assumes zero issuance, so with indexed
issuance the sign of self-payment becomes a calibration again; the channel of burning in order to
fire issuance and capture a fraction of it reappears, which yields `(σ_A − 1)·X` and tends to zero
when the attacker is the entire network; and if the signal were a price, with the pool of §8 inside
the state a transition would be bought with borrowed capital, which is exactly what §7.6 forbids.

**This does not answer the open question — it bounds it.** The two ways out that do not measure
demand remain standing: a deterministic rule of expansion, whose cost is already stated in §7.7 —it
loses the anchor—, and the dormancy of §7.9, which attacks hoarding without issuing anything.

---

## 8. Native liquidity

The design includes a **deterministic market as a piece of the protocol**, not as an application
built on top. The reason is not a product reason: it is survival across transitions.

### 8.1 Why the market goes inside

Without a native market, each exchange writes its own integration against the raw format of the
chain: address derivation, serialization, confirmation rules. They are N integrations maintained by
N teams that do not know each other, and in a transition all N break at once. A native market
**collapses those N surfaces into one**, and that one is part of the protocol — that is, it commutes
with it, without anyone doing integration work.

The strongest effect is on custody. **Tokens that are in a pool are state of the chain**, and by I3
state crosses the transition intact. A pool does not have to update anything in order to survive,
because it is not an integrator: it is state. Every unit that moves from an exchange's cold wallet
to an on-chain pool is a unit that stops depending on an external engineering team making it in
time.

### 8.2 Deterministic, and with the agents off the critical path

The market is an AMM: a closed formula, with no judgement inside. **No model takes part in price
formation or in execution.** A constant-formula market survived years of adversarial pressure
precisely because it has nothing to decide, and putting a model on that path would bring three
things incompatible with the design: non-determinism —same input, different output, and consensus
stops closing—, the impossibility of verifying that the output was correct, and the need for an
operator to run the model, which is the human who was shown out through the governance door coming
back in through the market-maker window.

There is also an indirect violation of I2: if the state the market produces depended on a
non-deterministic off-chain process, and the trigger reads state, the trigger would end up depending
on a disguised oracle.

**The agents go on top, as participants.** Market makers, arbitrageurs, liquidity providers. They
operate off-chain, permissionlessly, and if one of them gets it wrong they lose their own money
without touching consensus. It is the same criterion as §6.2: the mechanism is deterministic, the
strategy is free.

### 8.3 What the native market cannot do

**It does not close off the path of centralized custody.** If an exchange lists the native token and
people deposit, that exchange has an address with a balance, and the protocol cannot distinguish it
from any other. The native market offers a better path; it does not shut down the other one. It
shrinks the concentration, it does not eliminate it — and the residue is declared in §10.2.

**And it relocates the interface problem instead of eliminating it.** Whoever integrates against the
native market depends on the interface of the native market. The difference is that it is now **a
single surface, and it is our own**: I5 applies to it just as it does to the raw formats, and
whoever maintains it is the protocol.

### 8.4 The sink finds its place

§7.1 asks for a burn on consumption of the network's resources. A burn on every swap makes the sink
proportional to **real economic activity** and not to bare transfers — which is exactly what a
quantity regime needs: that circulating supply be withdrawn at the pace of activity, without anyone
deciding when.

### 8.5 Creating assets: the charge goes on permanence

A native market needs there to be something besides the native token to quote. The protocol admits
creating assets, and the way it admits it is narrower than is usual.

**A creation primitive of fixed shape is admitted, not a machine open to third-party state.** The
distinction matters and it is easy to lose: the chain **already** executes code written by third
parties —the acceptance predicate of §6.2 is written by the client and run by the light layer under
the VM step ceiling— but a predicate runs, answers and dies. What is admitted here is that an object
**persists** between transactions. Its structure is fixed by the protocol —owner, identifier,
pointer to metadata, prepaid balance, counters— and the creator's choice is the content, not the
form. What is ruled out is the open machine in which anyone defines what fields their object has,
and the reason is not that minting is dangerous: it is that with a free shape **the size of an entry
is chosen by the user**, and the state stops having a unit of measure. With a fixed shape the state
becomes a countable quantity again, which is the condition for being able to bound it.

**A single primitive covers fungible and non-fungible.** It is enough for the shape to carry
`supply` and divisibility: **a non-fungible is the case `supply = 1`, indivisible**. There is no
reason for two different objects, and with I1 fixing the machine, one shape fewer is one thing fewer
the machine has to know forever. Whether the issuer can enlarge the `supply` later is their own
business and the protocol has no opinion — the same stance §8.3 takes with custody: the better path
is offered, the other one is not shut down.

**The charge does not go on creation, and this is the least obvious part of the arrangement.**
Intuition says charge for minting. It does not work, and the precedent is fiscal: where a building
levy is charged when applying for the permit, what goes down is not the building but the permit.

> **A charge on creation does not reduce creation — it reduces the registration of creation.**

Translated here: if creating in the native layer carries a charge of its own, people do not mint
less, they mint **outside** —their own contract, a compressed format, a committed hash and the
object somewhere else— and there you lose exactly what §8.1 and §8.4 argue for over two sections: I3
only covers native state, the market only quotes what is inside, and the sink can only burn on swaps
that happen inside. The asymmetry is moreover not only one of incentives but of applicability: **the
charge on creation is evaded by minting outside; the permanence charge is not, because the state
that exists is seen by every node.**

**So the tariff has two parts, and neither of the two is a free decision.** On creation a **floor**
is paid, which is burned, and the floor **is not a knob: it is the fixed cost of the create + evict
cycle**. It is nailed down from both sides: from below, because less than that subsidizes the churn
of creating and letting die; from above, because everything charged beyond it is already the charge
on creation the previous paragraph ruled out. It has to be charged separately because the ad valorem
rule of §6.1 does not bite here — a newly created asset is worth ~0, so a fee proportional to its
value tends to zero.

**The sum is written by equating two fractions of the same node, and both are already declared.**
The cycle consumes a number of steps, and the node devotes `f*` of its rate to verifying: that is a
fraction of an epoch's computation. Storing the entry for that epoch occupies `size / state budget`
of the disk. The floor is the quotient — **how many epochs of disk are worth what the cycle spends
in computation**— and no new number appears, because `f*` and the state budget were already fixed by
Geminis. What does appear is an assumption worth stating: that the two fractions are equally tight,
that is, that the node saturates both. It is what §6.1 builds on purpose by fixing both against what
a phone has.

**And what enters the cycle are the two tree updates, not the signature verification.** The
distinction is not cosmetic: **the signature is already paid for by the ad valorem fee like in any
transaction**, so charging it again in the floor is charging it twice, and the error is not small
—with the signature inside, the floor comes out on the order of ninety epochs, several times the
maximum deposit `L_max` allows, and then nearly the whole cost of an entry is paid at creation,
which is exactly the charge on creation this section has just ruled out—. What creation adds on top
of an ordinary transaction is the tree work, and that is what the floor covers.

**With the two updates measured, the floor comes out on the order of nineteen epochs** —5% of what
it costs to hold the entry for a year, and **a little over three quarters of the maximum life
`L_max` allows to be bought at once**. That last ratio is the one that has to be watched: if the
floor were comparable to the maximum deposit, nearly the whole cost would be paid at creation and
the charge on creation would come back through the back door.

**And at this point it is already uncomfortably close.** Whoever buys the maximum deposit pays less
than half at creation, but **whoever only wants the entry for a short time pays nearly all of it**,
and this section's argument does not depend on the magnitude: a charge on creation does not reduce
creation, it reduces its registration. That the floor ended up where it did is not a comfortable
conclusion and it is declared as such.

> **The number depends on how the tree is stored, and that was not known when the sum was
> written.** A tree that stores all its internal nodes costs 32 bytes per entry and makes the update
> cheap; one that stores only the upper levels and recomputes the rest costs one byte and makes the
> update three times more expensive. **Both are the same tree and they give different floors**, so
> the cut is not an implementation decision: it enters the state by way of the floor, which is
> burned. It is one more constant of Geminis.

> **The two inputs of that sum are measured and neither is estimated**, which is what makes it
> assertible: the cost of a signature verification on the small machine (§12, Test 2) and that of a
> hash compression, measured the same way and for the same reason. The second one had to be gone
> after: an earlier version of this section took it as negligible against the first, and that
> reasoning held only while the signature was inside the cycle — with it taken out, it was the only
> term left.

**The floor is denominated in storage epochs, not in units of the token**, and that form does work.
If it were in units it would be a **second** price to set alongside the rate, with the same problem
the rate has and with none of its defences. In storage epochs it inherits whatever rate is in force
— and what §10.3 leaves open goes back to being a single number.

The second part is a **permanence deposit**, which is consumed by being burned epoch by epoch, at a
rate linear in size × time. **What the deposit buys is real storage time, not a number of epochs**,
and the distinction is not pedantic: the epoch is counted in blocks and block time is an internal
parameter, so a transition that moved it would change what an already-paid deposit bought — without
touching a single byte of the state, and without any invariant flagging it. It is avoided with the
same move the ceiling of §6.6 uses: **convert with the quantity the ruleset declares, not with one
that has to be measured.** Block time is not a clock reading —that would indeed violate I2— but a
number the chain itself fixed. While there is balance the object is in the active set; when it runs
out, it is evicted. To keep it alive it is topped up. **And it is the deposit, not the floor, that
acts as antispam**: creating N objects costs N deposits, so flooding the state is paid for at the
price of a flooded state.

**And the life that can be bought at once has a cap.** Up to `L_max` is bought per operation and
after that it is topped up, at whatever price is in force then. It looks like a nuisance and it is a
load-bearing beam, for two reasons that reinforce each other:

- **it closes the last door to bought permanence.** Without a cap, a finite but large enough payment
  buys centuries, which is exactly what this section exists to prevent. With a cap **a century
  cannot be bought even by paying for it**;
- **it is what keeps the price of storage governable.** The rate **cannot stay frozen in Geminis**:
  it is a nominal price on a real resource, so with the unit floating it breaks in both directions
  —if the currency appreciates, storing becomes prohibitive and the state empties out; if it
  depreciates, storing is free and it fills up—. Whatever the rule that moves it, **prepaying without
  limit is betting against that rule and leaving the state taken meanwhile**: when the rate falls,
  buying long captures slots at bargain prices that can no longer be recovered without confiscating.
  The cap is what prevents that purchase — and the adopted rule (§8.6) goes further: it did not leave
  the cap as an external defence, it made it the life of every admitted entry.

**The charge is per entry, not per object, and that is decided by the fungible.** A non-fungible is
one entry and does not grow; a fungible is one entry **plus a balance for each holder**, and that
count does grow with adoption. With a node's budget, a token with a million holders occupies **3%**
of the disk: **thirty-three successful tokens fill the chain**. So what has to be uniform is not the
shape but the charge — **every state entry pays permanence, and whoever creates it funds it**.
Transferring to an address that does not yet have an entry includes floor and minimum deposit,
charged to the sender; afterwards the holder tops it up if they want to keep it.

That rule also closes a door that had been open since before this section, and that is not about
minting: **native token accounts are state entries too**. Since the fee of §6.1 is ad valorem, on
dust it tends to zero, so filling every node's disk with minimal transfers cost **little more than
saturating the chain for half a day**, and nothing in fees. The dormancy of §7.9 did not cover it:
it runs in generations and its job is monetary, not disk.

> **The property all this buys, and it is the one that justifies the whole section: on the chain
> there is no object whose future cost does not have someone paying for it. Nobody can buy perpetual
> space with a finite payment.**

**What has to be declared, because it is a change of character and not a detail:** with the uniform
rule, **holding a balance stops being free**. It is demurrage on the state and not on the amount —a
small, still wallet ends up evicted, recoverable with a proof— and it pushes in the same direction as
the decision of §9, Stage 2. It is maintained knowingly.

> **You do not pay for creating — you pay for how long you want the network to store it.**

What is charged for is **size × time**, that is, cost and not utility, so the rule asks the protocol
for no opinion whatsoever about what an asset is worth.

**And the rate does not go down by depositing more.** The temptation is to reward whoever deposits a
lot by amortizing more slowly, and it falls down on arithmetic: with a power rule, life grows faster
than the deposit, so the price per year tends to zero — a hundred floors would buy ten thousand
years. That does not make just anything cheaper, it makes cheaper **the only operation that buys
permanence in volume**, which is filling every node's state and never letting go: it comes out an
order of magnitude cheaper than without the discount. It is the fixed fee §6.1 rejects as regressive
—*"it makes the large request free"*— in the dimension of time instead of that of value, and since
disk is capped the discount creates no capacity: it reassigns it to whoever has more capital, which
is the moat §6.1 exists to avoid. The only thing volume legitimately saves is paying the setup once
instead of once per period, and that already brings the average rate down — with a floor at the real
cost of storing, instead of heading for zero.

**Evicting is not destroying, and the residue has to be O(1).** The object leaves the active set and
the holder revives it with a proof, paying the cost at that time. That piece is what keeps eviction
from being confiscation, and that is why there is no final burn of the asset. But the commitment it
is proven against **cannot be one per evicted object**, or the attacker would have bought permanence
anyway, only more cheaply: a 32-byte tombstone per object is **1 GB per node forever**, a quarter of
the budget. Eviction **adds the object to a single append-only accumulator**, of the kind where
inserting needs barely the peaks of the tree: **some 800 bytes in total**, not per object.
Reactivation proves against that accumulator, and double reactivation needs no nullifier list — it is
checked against the **active** set, which is bounded by construction. The countdown is **public and
computable in advance** —a *pull* notice, the same form as §6.5— and that predictability is not a
convenience: an announced eviction does not generate pressure for a coordinated fix by hand, and a
surprise does.

**There is no debt, and there is no auction.** The natural variant —letting the balance go overdrawn
and executing against the asset— asks for two things the design cannot give. The first is a debtor:
the owner is a key, and against an empty account there is nothing to seize, so the only executable
thing would be the object. The second is worse: auctioning it forces the chain to know what it is
worth, that is, to read the pool, which is exactly what §7.6 forbids and is manipulable in the
obvious direction. Liquidation exists anyway, but it is done by the market and not by the protocol:
whoever cannot sustain the balance sells before the eviction and the buyer inherits what is left.

**The sink, to close.** The floor and the deposit are burned: they have no recipient, so there is
nobody to choose and nothing to farm. It stays on the *withdraw* side of the asymmetry of §7.10 —
activity can determine how much circulating supply is withdrawn— and it adds to the sink of §8.4 a
second source, continuous and proportional to how much state the network carries.

### 8.6 The permanence rate: admission auction, not an occupancy loop

§10.3 left two things about this tariff undecided: the level `r0` starts from —resolved there— and
the rule that moves it after Geminis. Indexing to **state occupancy** looked like the only way out
compatible with I2 —a fact of the state, not a market reading, the doctrine of §7.6 applied to disk—
and it has a flaw that only appeared when measuring it against a real case: **once a price already
rations the resource, occupancy stops saying whether that price makes sense.** Ethereum measures it
without meaning to: with the EIP-1559 base fee moving 650× in four years, gas occupancy stayed
pinned to its target by construction, correlation −0.02 against the price. A loop that adjusts `r0`
by looking at that same error inherits the blindness: it can hold occupancy at target and not know
whether it does so at an absurd price.

**The adopted rule does not look at occupancy: it makes the price discover itself, against a fixed
quota.** Each epoch a fixed amount of new bytes is admitted, `quota = θ*/L_max` —a sum, not a
decision, the same play as the step ceiling of §6.6—, and every admitted entry lives exactly `L_max`
epochs: there is no variable life to buy with the price. The epoch's price, `r0`, is the one that
makes demand to enter exactly equal the quota — a uniform-price auction: whoever is willing to pay
more gets in, the rest wait for the next epoch, and the one who marks the price is the last admitted
bid.

Fixing life at `L_max` instead of letting it depend on the price is not a detail: it is what closes
the channel that brought down the first version of this rule. With variable life (`life = reference
/ r0`), cheapening in order to fill lengthened the life bought for the same outlay, and those slots
stayed taken at bargain prices with no way for the loop to recover them without confiscating
—intertemporal arbitrage, measured: a sustained demand shock pushed the bought life to more than four
times the reference one, and occupancy oscillated without converging over thousands of epochs—. With
fixed life that lever does not exist: paying more or less changes how much it costs to get in, never
how long you stay.

**Measured against the same shock that brought down the previous law** —sustained ×3 demand—,
occupancy does not move from target at any moment: neither the peak nor the trough departs from it,
because the quota is fixed and so is the life, so `θ = quota × L_max` at all times from the first
`L_max` epochs onward. All the information of the shock is absorbed by the price: it jumps to the
clearing value in the same epoch as the shock and comes back in the same epoch in which it ends, with
no overshoot and no tuning parameter to choose. Against the same `L_max`, the previous law —even once
corrected with the life cap— still spiked up to 1.48× above target during the transition; here there
is no spike to absorb.

**And there is a consequence for the risk of §8.5 —the currency that appreciates or depreciates— that
was not sought and appears anyway.** A price the protocol computes from occupancy knows nothing about
the real value of the token; a price that comes out of bids does know it, even though the protocol
itself never reads it, because **whoever bids converts on their own**: if the token is worth more,
they offer fewer units for the same real value, and the clearing price falls in nominal units without
anyone asking it to; if it is worth less, they offer more. The protocol still reads no price —I2
intact—, but the level in units of the token stops being pinned to a fixed number and starts to
follow, with the lag of the bootstrap reserve described below, the real value assigned to it by those
who actually pay. It is not a guarantee —the conversion is done by the market of bidders, not by a
formula—, but it is a defence the occupancy-indexed law did not have at all.

**The price of an auction with few bidders is noisy, and getting more people together does not fix
it.** With real bids —not a known demand curve but candidates with their own valuation, drawn from a
heavy-tailed distribution— the noise of the clearing price depends on the **quota**, not on how many
bidders compete for it: doubling or multiplying by ten the number of candidates over the same quota
does not reduce it; multiplying the quota does. It is a result from extreme-value statistics: the bid
that marks the price converges by having more winners to average over, not by having more candidates
above the cut.

**The bootstrap reserve exists for that regime, and it touches nothing once the quota grows.** The
effective price of each epoch is an exponential moving average over the raw clearing price, with
adaptive gain `α = min(1, quota / quota_ref)`: with a large quota, `α → 1` and the raw price passes
through untouched; with a small quota —a newborn network, few admissions per day— it integrates more
epochs, borrowing bidders from the past instead of demanding more candidates now, which no longer
helps. It is I2-compatible because it uses only the protocol's own price series, nothing external.
The trade-off between noise and reaction speed does not have its optimum at either extreme of the
gain but at an intermediate point, measured; once the steady-state quota exceeds that reference by an
order of magnitude, the gain is capped at 1 and the reserve retires on its own.

**Under a transition that moves `θ*`, the mechanism needs nothing new.** The quota is recalculated on
its own, with the same move as any other parameter derived from Geminis. The only thing a reduction
of `θ*` leaves pending is a readjustment: entries admitted under the previous `θ*` cannot be evicted
before their `L_max` expires —evicting them earlier would be the same confiscation the life cap
exists to avoid—, so occupancy may stay above the newly declared target until those entries expire.
That never threatens the physical budget: the inherited occupancy was already, by construction, under
the previous generation's `θ* ≤ 67%`, always below the real ceiling. And if demand falls below the
quota there is nothing to resolve: the quota is a ceiling, not a floor, so whatever shows up is
admitted, the price falls to its floor, and occupancy stays below target that epoch without anything
left over to burn, accumulate or distribute.

---

## 9. Adoption

The expected bootstrap is Bitcoin's: nobody takes part because they believe in the currency, they
take part because there is an arbitrage window. The infrastructure arrives for the money and the
network stays. Nobody needs to understand the design, and counting on them not understanding it is
realistic.

### Stage 1 — the claim, not the subsidy

**This design had a different Stage 1 and it is worth telling how it fell, because the one that
remains is smaller and more honest.**

The original version was that of every yield farm: humans stand up infrastructure in order to
generate tokens and sell them for fiat. It had a structural difference from Bitcoin that decided
whether it was healthy or toxic. Bitcoin's subsidy **buys security**, and the work is defined by the
protocol: hashing *is* what secures the chain, the cost is external and physical, and nobody can pay
themselves for mining. Here the subsidy was paid **on top of a private transaction between two
parties**, and the protocol deliberately does not define what work is worth, because the moment it
defines it, it becomes a committee picking winners.

So the infrastructure that maximized token generation was not a mining farm: it was **an agent
paying itself**, the cheapest way to produce *"work requested, paid for and delivered"*.

**The arbitrage window and the self-dealing window were the same window**, and the only thing that
separated them was the parameter that grades the subsidy. Adoption needed it to be juicy; the health
of the currency, that it not be so juicy as to be farmable. Test 4 ran that hypothesis and **they do
not fit**: the parameter enters identically into both economies, and the margin between them is net
issuance, which is the same quantity as the profit of the one paying themselves. There is no way to
enlarge one without enlarging the other.

**The Stage 1 that remains is the claim of §7.2**, and it is smaller in every sense: a single window
at block 0 where claiming tokens costs demonstrating compute capability. It is still an arbitrage
—you spend electricity, you receive tokens, you sell them if you want— and it still requires nobody
to understand the design, which was the important property. But **it is bounded in time and cannot
be farmed after it closes**, because after that no action creates units.

**What is lost with that, and it has to be said:** the incentive paid by the protocol to run a node
**before demand exists** disappears. Bitcoin has a block subsidy for decades; here the claim buys
the day-1 cohort and after that the income is fees from real demand or nothing. The design does not
guarantee that demand will appear — it only guarantees that if it does not appear, nobody can
manufacture it in order to get paid anyway. It is a deliberate choice between two failures: the old
one started off safely and farmed itself; this one does not farm itself and may not start.

A corollary about autonomy, which survives the change intact: that the human stops intervening is
true of **the rules** and false of **the holdings**. A software agent has no keys; somebody operates
it, and that somebody controls the wallet. The human does not disappear — they move up one level,
from holder to operator.

### Stage 2 — that it settle into circulating currency

It has no example at all, and for a reason of design and not of luck: **a hard ceiling and
circulation pull in opposite directions.** If the holder expects appreciation, holding is rational
and spending is foolish. Bitcoin reached store of value and stayed there for exactly that reason. A
design that targets quantity and lets the price float inherits the same problem: if it is adopted it
appreciates, and if it appreciates it is hoarded.

This is where the dormancy of §7.9 stops being a measurement detail, and §8.4 gives it the volume it
needs to bite. A maintenance cost on the still balance makes hoarding stop being free and spending
rational again — which is literally what Gesell designed Freigeld for, what Wörgl tested in 1932
until the Austrian central bank shut it down the following year, and what Freicoin took to a
blockchain in 2012.

**Design consequence:** if the goal is circulating currency and not digital gold, dormancy is not
the price to pay for measuring well — it is the central mechanism. And it has to be decided early,
because it changes what class of asset this is from block 0.

---

## 10. Declared boundaries

What the design does **not** solve, written here and not in a footnote, because an implicit boundary
is a lie by omission. They are grouped by what has to be done with each one, which is not the same
in the three cases.

### 10.1 Assumed decisions

They are not problems to be solved: they are the price of properties the design wants. They are
maintained knowingly.

**Adaptation is bounded to what Geminis anticipated.** A direct consequence of I1 and with no fix
inside the design: if the condition that fires the transition is something unforeseen, there is no
ruleset to load. It is the price of there being no new code, which is what makes the transition
verifiable.

**Determinism also removes the emergency brake.** A badly anticipated transition is exactly the
scenario in which humans would want to refuse, and the design's answer is *"then you are a fork"*.
There is no override, by construction — which is the same property that eliminates governance, seen
from the uncomfortable side.

**The `Δ` window buys integration safety with reaction time.** A long window leaves the chain
running under rules already known to be insufficient; a short one passes the cost to everyone who
integrated. There is no value that solves both, which is why `Δ` goes per transition class (§3). The
worst case —an urgent cryptographic migration, where the chain needs a short `Δ` and the integrators
need a long `Δ`— is defused by the ladder of canaries of §6.6: the weak canary fires the migration
years in advance, so the emergency path is almost never used.

> **And building the mechanism showed that, at the values that are in Geminis, that tension does not
> exist.** `Δ` is declared in **blocks** —64 for circulation, 8 for a migration— and with the initial
> block time that gives **six minutes and forty-eight seconds** of notice. No integrator reacts in
> six minutes, so both values are on the same side of the curve, the *no notice at all* side, and
> the knob this paragraph describes is not on it.
>
> What really gives the integrator a tolerable failure mode is not `Δ` but **I5**: whoever did not
> manage to support the new generation keeps operating in the previous one and degrades instead of
> stopping (§4). That is what keeps the small number from being catastrophic — and also what shows
> that `Δ` is doing considerably less than this paragraph attributes to it.
>
> There is also a units problem, and it is the same one that appeared in the permanence deposit
> (§8.5): **`Δ` is in blocks and block time is an internal parameter**, so the real notice varies
> sixtyfold across the space, and a transition can move it while another one is in flight. The
> correction that worked for the deposit does not apply the same way here, because the activation
> height is announced at lock-in and moving it afterwards contradicts §3. **It stays open**, with
> the three possible ways out written in the units audit in the repo.

**The set of possible futures stops being auditable.** It is the price of the interpreter (I1). With
a finite list of rules, anyone could read Geminis and know what the chain can turn into. With a
machine, the space is infinite and that reading no longer exists. Evolution without a ceiling is
gained; being able to know today what this may end up being is lost.

**And the declared space may fall short.** It is the opposite face of the previous point and it was
found by the replay of §11, not by an imagined attack. Internal parameters do not live in the
infinite space of the machine: they live in a range declared in Geminis, auditable precisely because
it is finite. Ethereum took the blob target from 3 to 14 in twenty-two months, and the last two
raises were not possible because demand appeared —occupancy was at 43% and 31%— but because a data
availability technique appeared that changed how much the network can carry without degrading. A
ceiling of 6 declared in 2024 would have been correct in 2024 and would have fallen short in 2025,
and **I1 freezes it**. The difference from what this section already says is fundamental: it is not
that the written rule may be the wrong one, it is that **the range within which the rule chooses may
fall below what the network ended up being able to do**, and widening it is a fork — the mechanism
handing back exactly what it came to avoid. The mitigation is to declare the range with slack, and
the slack has its own cost: a generous ceiling is the one that lets through the case the ceiling
exists to block. It is the same tension §10.3 declares for the step ceiling, now measured on a real
parameter and not on a hypothetical one.

**The interpreter is a single point of failure that can never be patched.** If it has a bug, there
is no transition that fixes it, because every transition runs on top of it. It is the only piece of
the system where formal verification is not optional.

**Surviving the gauntlet is not surviving fifteen years of cryptanalysis.** A window with a reward is
a mechanical approximation to the real standard, not a substitute. It is mitigated with a long window
and a large reward; it is not eliminated.

**Activation does not wait for anyone to be ready.** The tempting way out of the integrator problem
is to condition activation on a percentage of the supply in custody signalling readiness. **That is a
vote**, and one of the worst kind: it gives veto power over the evolution of the protocol to the most
concentrated actors. Forbidden by I2. What is admitted is publishing the readiness signal as
**information with no protocol effect** — telemetry for the market to use, never a gate.

**You cannot pay someone who is offline.** The bilaterality of §6.5 turns every payment into a
two-round handshake. For an agent economy it is irrelevant —they are online—, for humans it is
friction, and it is the price of the receiver being the watchman.

**Finality is measured in minutes or hours, not in seconds.** It is the consequence of finalizing by
challenge window instead of by quorum (§6.3). Not having a validator set is gained; it is paid for
in latency. And it is not a number but a distribution: in calm it is the base window, and under
saturation of the queue it stretches up to the class's ceiling (§6.3).

**The work the protocol can pay for is a subset, not the whole.** Only requests with a verifiable
deterministic predicate (§6.2). Issuance no longer depends on this —§7.1 decoupled it from work— but
the fee does: what cannot be expressed as a predicate cannot be settled on the network, and
therefore generates no income for any node. It is a sharp boundary and it is narrow, and if it turns
out to be too narrow the system is a niche instead of an economy.

**The predicate's step ceiling is an I1 decision that has not been taken.** §6.6 closes the hole
Test 2 found —the gauntlet verifies correctness and not cost, so a correct but ten times slower
implementation passed, survived the window and stayed installed forever, breaking the budget of §6.1
from inside the protocol— by adding a VM step ceiling to the acceptance predicate. What the mechanism
does **not** say, and has to be chosen knowingly, is which half of the space that ceiling belongs to.
Frozen into the machine, it can leave out a legitimate primitive that the hardware of twenty years
from now would make cheap. As an internal parameter of the generation, raising it is exactly the path
by which the slow implementation gets in.

**The dilemma was false, and it was resolved without paying either side.** What is frozen into the
machine is not the number: it is **the sum that produces it**, and the value is determined by each
generation with its own parameters —block time and capacity—, which are already in the space. That
way the ceiling is neither frozen nor loose: **it is not a lever, because nobody can move it without
moving capacity or block time**, and that has its own consequences and its own trigger. The
derivation is in §10.3.

> **That ceiling does a second job that is not visible from here, and it is a security job, not a
> performance one.** It is what prevents a challenge from existing that is **more expensive to
> verify than to create** — the classic denial-of-service asymmetry against the verifier. Without a
> ceiling, an attacker would buy cheap verification work and the queue of §6.3 would come to need a
> thousand nodes in order not to saturate instead of ten. With a ceiling, verifying a challenge costs
> at most what creating the disputed interaction cost. **Whoever moves this parameter is moving a
> condition of §6.3, not a performance decision.**

**The machine forbids floating point, and that closes doors forever.** Bit-for-bit reproduction
between ARM and x86 only holds with `+ − × ÷` and without transcendentals — it is measured, not
assumed. If the gauntlet admitted candidates without restricting that, the loop of §6.6 could install
a primitive that breaks the determinism everything else depends on, PoD included (§6.2). So the
specification of the machine forbids or canonicalizes floating point **before the gauntlet runs for
the first time**, and since it is a condition on Geminis, it cannot be lifted afterwards. The cost is
concrete and not hypothetical: every primitive that needs floating point is out of the space of
descendants forever. Falcon / FN-DSA verifies with integers but signs with floating point, and with
this condition it never gets in.

**Lineage and signature cannot share a cryptographic core.** The ladder of canaries of §6.6 grades
the response, and that grading assumes primitives give way **one at a time and in order**. The
assumption breaks on its own if the function that chains the lineage (§3, I4) and the signature
primitive share a core — which is the default case, and not by chance: ML-DSA uses SHAKE inside, and
59% of a verification goes on expanding the matrix with it. Choosing Keccak for `H` couples the two
things, and then Keccak does not give way by one step: it gives way on the lineage and the signature
in force at the same time, and the migration would have to run over a chain whose lineage
verification is no longer trustworthy. Geminis chooses `H` from a different family than the one the
initial signature primitive uses. It is cheap on day one and impossible afterwards.

**With a classical initial signature, "a different family" stops being SHA-2, and the rule cannot be held at every
step.** Ed25519 hashes with SHA-512, so an SHA-2 `H` shares a core with it from block 0: the reference
implementation uses BLAKE2s, which is neither SHA-2 nor Keccak. But signatures are additive (I5: Ed25519 is not
retired) and the standard library only guarantees three hash families —SHA-2, Keccak and BLAKE—, so the hash and
signature successions cannot avoid coupling at some step: as soon as the successor hash is SHA-3 and the successor
signature ML-DSA-44, they share Keccak. A check (`protocolo/nucleo.py`) **reports that coupling at the step where it
appears and does not block it**, because blocking it would leave the hash chain with no successor. The rule is
enforced with teeth for generation 0's `H`, and for what follows it is a **declared limit**; §6.6.2 has the case.

**Choose the most scrutinized primitive, not the rarest, and knowingly accept the monoculture risk
that brings.** Almost the entire crypto industry today shares a core — secp256k1 for Bitcoin and for
Ethereum's accounts —, so a real mathematical break of the underlying problem does not threaten one
chain: it threatens almost everything that exists at once, and that enlarges the prize for keeping
quiet that §10.2 already declares. The temptation is to dodge it with a primitive nobody else uses.
It is not taken: a scheme without public scrutiny is not safer for being rare, it is more likely to
be broken already with nobody yet having tried seriously. Rainbow and SIKE —serious candidates from
the same NIST competition, with years of scrutiny behind them— fell completely in 2022 to a single
researcher with a laptop; no primitive, scrutinized or not, is exempt from this, but the scrutinized
one is the one with the best available evidence of not being broken already. Geminis chooses
ML-DSA-44 for that reason —the best candidate with years of public attempts to break it behind it—
and not in order to avoid the monoculture that is coming. What does solve the future monoculture is
not today's choice: it is not depending on it lasting forever, which is what §6.6 buys.

**Lock-in waits for finality, and that opens a delay that can be forced.** The separation between
trigger and lock-in (§3) is not ceremony: without it, a reorganization would leave `H0_B` committed
to a `state_trigger` the canonical chain no longer contains, and I4 would stop verifying precisely
where it matters most. The price is that every transition pays the challenge window of §6.3
up front, and that **delaying finality comes to delay the transition**: an adversary willing to pay
challenge bonds would try to stretch the lock-in. It points in the worst direction exactly in the
urgent cryptographic migration — the same worst case that already strains the `Δ` window.

**The fix is a hard ceiling on blocks of delay to lock-in, fixed in Geminis per transition class** —
the same form as `Δ` in §3, applied to the other half of the schedule. The ceiling is also the limit
the adaptive window of §6.3 stretches to when there is a queue. A hard ceiling was chosen over
a stepped challenge bond, and the criterion is worth more than the case:

| | stepped bond | **hard ceiling** |
|---|---|---|
| kills the delay attack | partially | **totally** |
| needs identity | no | no |
| punishes the honest challenger | **yes** | no |
| residue | **compounds** | flat and bounded |

> **A residue that compounds is not a fix, it is a loan.** The stepped bond leaves a residual delay
> that grows with the attacker's capital; the ceiling leaves a residue that is declared in one line
> and is the same on day 1 as in year 20.

**That residue, stated in full:** a fraud discovered after the ceiling does not stop the transition.
The ceiling turns *"delay"* into *"survive the ceiling"*, and the cheap way to survive it would be
flooding the challenge queue so that a legitimate proof does not get processed in time. It cannot be
done — §6.3 explains why, and it is not because it is expensive but because there is no geometry that
allows it.

And what makes it tolerable is still the usual thing: the weak canary fires years in advance, so the
emergency path almost never runs.

**Floating point is forbidden or canonicalized from Geminis onward.** Falcon / FN-DSA verifies with
integers but **signs** with floating point, and bit-for-bit reproducibility between ARM and x86 only
holds with `+ − × ÷` and without transcendentals. If the gauntlet of §6.6 admits candidates without
restricting that, the loop can install a primitive that breaks the determinism everything else
depends on. It is a condition on the specification of the machine (I1) and it has to be written
**before the gauntlet runs for the first time**: like every condition on Geminis, it is cheap on day
one and impossible afterwards. The price is that it narrows the space of eligible primitives before
knowing which ones are going to exist.

**The cost of entry to the light layer is asymmetric by platform.** Measured in Test 2: a node on an
iPhone runs **~15× slower** than the same phone on Android, because iOS does not allow third-party
JIT and the bytecode arrives at runtime (§6.1). It does not break the blocking-coalition argument
—entry is still cheap— but *"replacing it costs one phone"* is true only up to a factor of 15
depending on the device. It is a platform policy, not a property of the design, and there is nothing
the protocol can do about it.

**State expires, and that exchanges a guarantee for a dependency.** With a single asset no boundary
on the size of the state had to be declared; with the creation of §8.5 it does, and the threshold is
low. Counting the object, its part of the tree and the eviction index, an active entry weighs
**~120 bytes** —a holder's balance, half that—, so with a phone's disk budget some **9,700 creations
a day** exhaust it in ten years: 0.1 per second. Any real adoption crosses that threshold, so
expiring is not an optimization but what keeps standing the cheap entry of §6.1 and, through it, the
non-saturation of §6.3. What is gained is measured and it is large: evicted state goes from one
mandatory copy per node to a few voluntary ones, three orders of magnitude. What is paid is that
reactivation stops being guaranteed by the protocol (§10.2). And a residue is left with no fix:
**expiration does not distinguish the abandoned from the deliberately kept**, because intention is
not state — the same wall §10.2 declares for everything else.

**State targets half the declared budget, and not filling it.** The charge of §8.5 defends a **target
occupancy**, and that occupancy is measured against a disk budget Geminis declares —of the order of
the few gigabytes that sustain the argument of §6.1— and that only a transition can move, being an
internal parameter of I1. That way capacity grows by a generation's decision and not by hardware
drift. The chosen value is **half**, and the half left free is not wasted slack: it is where the peak
of a sustained demand shock lives, which in simulation reaches half again above target before the
price bites. Aiming at 75% or 90% goes over budget in the first shock.

That the value is conservative is deliberate, and the reason is the asymmetry of the two errors.
Falling short makes storage more expensive and hosts less, and it is corrected by raising it in a
transition. Overshooting expels the small nodes from the budget — and that **is not reversed by
lowering the number afterwards**, because whoever left does not come back and already-financed state
cannot be evicted early without confiscating. One error is reversible and the other is not.

### 10.2 Inherent limits

Neither this design nor any other solves them. They are declared so that nobody discovers them
afterwards.

**The protocol has no notion of identity, so every lever it moves, it moves for everyone.** It is
the limit that explains in one go why four different fixes attempted on this design failed, each one
against a different problem:

| attempt | against what | how it died |
|---|---|---|
| grade the subsidy with a parameter | self-payment | it enters identically for the self-dealer and for the honest party |
| block the subsidy for a time | farming | it discounts both equally |
| split the benefit by role | self-dealing | it is arbitraged by whoever occupies both roles |
| superlinear challenge bond | the delay to lock-in | it punishes the honest challenger along with the attacker |

It is not bad luck four times: it is a property. Any mechanism that wants to treat the honest party
and the attacker differently needs to distinguish them, and all the protocol sees are signatures and
amounts. **Every proposed fix of the form "let the good guy pay less" is, in this design, a proposal
to introduce identity** — and it is declared here so that it does not have to be discovered four
more times.

The same rule has a second instance, on the monetary side: **every proposal of the form "let it
issue when there is real demand" is also a proposal to introduce identity**, because separating real
demand from manufactured demand is separating two actors the protocol sees as identical —
signatures and amounts. The development is in §7.10.

The way out that does work is not distinguishing better but **giving up on trying**: making the
closed circuit lose money by arithmetic, as in §7.3. The same form reappears in §6.4 —whoever signs
twice publishes their private key, without anyone having to judge them— and in §6.3, where what
stops saturation is not a filter but that draining is parallel and filling is serial.

**The five invariants cover what the state *is*, not what it *means*.** It is a limit of the whole
framework and it was discovered by building: two different defects slipped underneath the five
without violating any of them. In one case a ceiling declared as a constant **excluded primitives
instead of making them more expensive**, contrary to what §6.6 promises; in the other, a prepaid
balance was denominated in a unit that a ruleset parameter redefines, so **a transition changed what
that balance had bought without touching a single byte**.

Both are the same form. I3 verifies that the state crosses over intact, and it did cross: the hashes
match and so does the identity of the objects. What changed was the value of what crossed over, and
**no invariant looks at that** — nor can it, without the protocol having a notion of what a quantity
is worth, which is precisely what the rest of this section declares impossible.

What replaces a sixth invariant is a question that can be asked mechanically and that is worth
asking again every time the parameter space grows: **for every quantity the protocol stores, does
its meaning depend on something a transition can move?** If it does, there are two ways out
—denominate it in something that does not depend on it, or recompute it in the transition— and
neither is free. What is not a way out is failing to notice.

**The split is illegitimate, not impossible.** The asymmetry of §5 is real: whoever does not
commute is the one who deviates, and that is verified with a hash. But legitimacy is not survival.
Ethereum Classic exists, nobody disputes that it is a fork, and it has a market and miners anyway.
The asymmetry does not kill the dissident chain — it makes it small. No rule written in Geminis can
prevent the split, because the rule lives inside the software the dissident decided not to run.

**The hash that chains the lineage cannot be replaced.** A new signature primitive applies going
forward and the old ones stay valid by I5. The lineage hash does not: `H0_B` chains backwards to
Geminis (§3, I4), and there is no way of re-hashing a history that is already written without
breaking the commitment that makes it verifiable. The only way out is to keep the old function for
the old links, whereby a broken function stays as structural load forever. A canary for `H` is
indeed constructible —a claimed collision is a fact of the state just like a preimage— but it does
not buy much: finding out that `H` gave way enables no migration, because what would have to be
migrated is the past. It is not a defect of this design; it happens to any chain that commits its
history with a hash. It is mitigated by choosing the most conservative function available and
declaring that that is the floor. It is not eliminated.

**The rule does not summon hardware.** The protocol can determine the next generation down to the
last byte, but it cannot force nodes to exist running it. Autonomy is true at the level of decision
and false at the level of execution.

**Nor can it force an archive to exist**, and it is the same boundary applied to the expiration of
§10.1:

> **The protocol can guarantee that an evicted asset *can* be revived. It cannot guarantee that
> anyone will have what it takes.**

The reactivation proof weighs less than a kilobyte, so storing it is free; what is not free is
**keeping it up to date**. The union of the siblings along a leaf's path is the whole tree minus that
leaf, so the proof expires at the first block that touches anything else: keeping it means following
the chain without ever breaking off. It is enough for a permanently online agent —which is the
declared audience of this design, and it is the same assumption that sustains *"you cannot pay
someone who is offline"*— and it is not enough for a person, who is going to depend on an archive
service, that is, on the market and not on the protocol. Paying the archive from the protocol is not
a way out: *"a node stored a file"* is passive state with no on-chain evidence, of the same family
as *"a node was switched on"*, so paying for it would be paying for a declaration. What the lack of
an archive produces, and it is worth being precise, is **unavailability and not divergence**:
eviction is deterministic and reactivation is verified against a commitment everyone has, so there
is nothing to fork over.

**Custody concentration is counterparty risk, not a property of the protocol.** An exchange that
lists the native token custodies an address like any other and the protocol cannot distinguish it —
classifying it would be human judgement (§7.8). Nor would it help to turn concentration into a
trigger: balance per address is measurable, but economic concentration is not, because splitting
custody across ten thousand addresses takes it to zero without anything real changing; and as a
trigger it would be **evadable by the one being targeted and forgeable by anyone** who wants to
force a transition by gathering balance.

And above all: **a transition redistributes nothing.** By I3 the state crosses over intact, so
whoever had 40% still has it afterwards. Forking against concentration is a loop that does not move
a single balance.

What makes it tolerable is that here **concentration does not buy protocol power**: there are no
votes, no weight by stake, no block production by holdings. A large holder cannot block a
transition, nor vote, nor censor, nor move the trigger —which only reads `emitido − quemado`—. All
it gives them is market power and the ability to strand their own clients, which is the same as
*"your exchange can go bust"*: true of every asset that ever existed, and no protocol ever solved it.
It is measured and published as telemetry; that is where it ends.

**It is possible to pay to bring a transition closer, though not to change which one.** It is the
flip side of the previous paragraph, and it appears only when indexing the permanence rate of §8.5
to state occupancy, which is the only variable it can be indexed to without violating I2 (§10.3).
Whoever occupies disk raises the price of storage for everyone; other people's deposits are consumed
by burning faster; and the burn enters `emitido − quemado`, which is exactly what the trigger reads.
None of that is an oracle or a forbidden reading —everything that happens is a fact of the state—, so
§7.6 does not reach it: the channel does not buy a different transition, it buys **anticipation**.

How much anticipation it buys is what changes the character of the problem. Pushing the trigger by
burning one's own money is already within reach of anybody who has money, and in the best case it
costs one to one —it is the arithmetic of §7.3, where the only thing that never comes back is the
burn—. What this channel adds is a **discount**. With `s` the fraction of the state the attacker
occupies and `ε` the elasticity of honest demand for storage, the control has to raise the rate by
`R = (1/(1−s))^(1/ε)`, and the other people's burn the attacker obtains for each unit of their own
burn is `((1−s)/s) · ((R−1)/R)`:

| `s` | `ε` = 0.25 | `ε` = 0.5 | `ε` = 1.0 | `ε` = 2.0 |
|---|---|---|---|---|
| 5% | **3.52** | 1.85 | 0.95 | 0.48 |
| 25% | 2.05 | 1.31 | 0.75 | 0.40 |
| 50% | 0.94 | 0.75 | 0.50 | 0.29 |

> **The lever is of the order of `1/ε`.** With elastic demand the attacker never burns more of other
> people's than of their own, and the channel is an expensive way of doing something they could
> already do cheaply. With inelastic demand —whoever needs their asset alive at whatever price— the
> discount appears, and occupying little it goes past threefold.

And `ε` cannot be known without a running network, so this is not closed with a number. Closing it
by definition can be done —excluding the permanence burn from the trigger's accounting— and it is
not free: it breaks *circulating supply is issued minus burned, with no exceptions* (§7.8), and the
expensive part is the first exception, not the exception itself, because from then on every burn
channel that is added has to argue whether it counts. That is exactly the growing list §7.8 exists
in order not to have.

The choice is to declare it, with two things that bound it and one that reopens it. It is bounded by
the fact that **what is bought is the date and not the content** —the successor is written in
advance and by I3 the state crosses over intact, so bringing the trigger forward does not change what
is transitioned to— and by the fact that this rule fires by **observable approach** (I2), so that a
sustained push is seen coming in the same telemetry that publishes how many blocks are left at the
current rate. It is reopened by a measurement: if with a running network the demand for storage turns
out to be markedly inelastic, the correct decision becomes the other one, and what has to be paid is
§7.8.

**The canary pays for telling, and whoever can break the primitive gains more by keeping quiet.**
The reward of §6.6 only attracts whoever values collecting it above what they would obtain by
exploiting the break in silence. For a genuinely new cryptographic capability —the case the canary
exists to detect— that comparison is not won by any reasonable reward: whoever can forge signatures
can take the entire chain, and that is worth more than any bounty the chain can pay. The objection
comes from the original 2018 discussion and the interpreter does not resolve it: the chainable ladder
fixes the cost of firing early, not the reason why somebody would fire.

What bounds it is that the canary does not need to attract the optimal adversary, but **anyone** who
gets there first — academic research, a team looking for reputation, a competitor. The assumption is
that the capability to break a primitive does not appear in a single place nor in perfect secrecy,
which is what historically happened with DES, MD5 and SHA-1. It is an empirical assumption about how
cryptanalysis spreads, not a property of the design, and it has to be declared as such: if the
capability appears concentrated and in silence, the canary does not fire and the loop of §6.6 does
not start.

**Freshness ties exploitation to the present; it does not prevent it.** Nothing above requires the
validity of a signature or of a transition to depend only on a fixed secret. If it also depends on a
value that does not exist until the moment of use —a public randomness beacon, revealed only in the
block that consumes it—, the attacker loses the option of breaking the primitive once, in private,
and accumulating precomputed forgeries to spend quietly over years: every use comes to demand live
computation, exposed at the instant it happens. It is a reduction of surface —it takes away from the
adversary the *break today, collect in secret later* mode—, not a closure. Against whoever breaks the
primitive in real time, as fast as the legitimate owner signs, freshness contributes nothing: there
is nothing to precompute in between, and the limit of this item stays intact for that case.

**It is not a cryptographic problem and an economic one separately — it is a single one, and the
economics depends on whichever fails first.** An incentive mechanism —the canary, any reward, any
punishment— can only be conditioned on what the state can observe. What would have to provide that
observability is the cryptography, and it cannot: an indistinguishable forgery leaves, by definition,
no difference a predicate could read. The economic mechanism never failed for being badly designed —
it never had anything to work with. In the form this takes in mechanism design, it is a problem of
**hidden action with an unobservable type**, the same family as the moral hazard of information
economics: when the designer cannot observe the agent's action, there is no contract that guarantees
the desired outcome for every type of agent, if the outside option —here, exploiting in silence— can
be worth more than anything the contract offers.

**And the property of "leaving no trace" is not a hole in the design: it is what a complete break
means.** Whoever recovers the private key —or its computational equivalent— does not produce a
signature similar to the legitimate one: they run exactly the same equation the owner would run.
There are not two processes generating two distinguishable results; there is only one, and the
attacker can now run it too. Asking that signature to give away how it was obtained is asking a
perfectly duplicated key to feel different in the lock. That is why a **partial** break —a
statistical bias, a leak that gets close without completing, the historical pattern of DES, MD5 and
SHA-1— can indeed leave a trace, and that is why the ladder of canaries exists to catch exactly that
stretch, years in advance (above in this section). What the ladder cannot touch is the direct jump to
a complete break without passing through a public version of the intermediate stretch — not for lack
of a better mechanism, but because at that point there is no longer any difference that any
mechanism, cryptographic or economic, could read.

**What is covered, stated in a single list and without exaggerating it:** the ladder of canaries
bounds when a spreading capability matures into a production attack; lineage and signature not
sharing a core bounds what falls together with what when something breaks; choosing the most
scrutinized primitive instead of the rarest (above, §10.1) bounds the probability that the break
already exists without anyone having looked for it seriously; and a composite signature from a second
family with no shared core, required only for transactions moving dormant value above a threshold, is
a candidate mitigation —measured in `test7-firma-compuesta/` (~3.5× the cost of a simple verification
in the same module, under the engine that actually fit into the budget of Test 2, and 3.9× on a real phone), still
without the speed threshold or the size cost that would make it adoptable— that would reduce the value of keeping quiet precisely
for the accounts most worth emptying. What none of the four covers is the lone adversary who reaches
the complete break without passing through any public intermediate phase: that case is not covered
because there is no information in the state with which to cover it.

**And there is a second frontier, that of key theft and not of primitive breakage.** The ladder of
canaries covers the mathematics giving way; it does not cover someone getting hold of an account's key
by another route —phishing, malware, a side channel, a compromised device—, and for the same reason: a
stolen signature is bit for bit the owner's signature, and no predicate reads the difference. We
explored what could be done on the network side, and where it ends:

- **A second secret that nobody knows cannot be born on the network.** If a node generates it, that
  node saw it; if the machine generates it, since it runs under deterministic rules anyone with the
  same data rederives it —determinism and secrecy exclude each other—; if it lives in the state, the
  state is public and can only hold a commitment, never the secret. It is the rule of §6.6 turned
  around: there the canary's instance is **derived** so that nobody keeps a trapdoor; here the secret
  must be one that **nobody** can derive, and only a device of the owner provides that.
- **Isolating a secret inside a compromised device does not exist without dedicated hardware**, and
  requiring it breaks §6.1 —PoD runs on any hardware—, of the same family as the iOS/Android asymmetry
  above but worse: it is not slower, it is being unable to use the protection. Geminis does not require
  it.
- **The way out that holds equally on any device is on the wallet's side:** splitting the secret
  across several of the user's own devices, with a threshold (two of three, say). It is mathematics and
  depends on no chip, so it is equally strong on Android, iPhone or PC. **But it is only as mature as
  the primitive it is applied to:** for Ed25519 there is FROST (RFC 9591, an IRTF document); for ML-DSA
  there is no standard —NIST's call for threshold schemes is in progress— though there are two schemes
  whose output verifies under an unmodified FIPS 204 verifier (Mithril and Quorus, both USENIX
  Security '26), so this way out depends on one existing for the primitive in force. What the chain
  sees was measured in `test11-umbral-mldsa/`: a 2-of-3 signature from Mithril's public prototype
  costs the §6.6 machine the same steps as an ordinary one (3,318,732 against 3,318,658 at the
  median), while the same protection without threshold cryptography —a 2-of-3 multisig on-chain, with
  loose signatures— spends 6.78 M steps, halves the capacity per block, and a 3-of-3 does not fit
  under the initial ceiling. The cost moves to the wallet, and that prototype is academic: its public
  code deals the keys from a seed (a dealer), with no distributed key generation. Which scheme, how
  many devices at minimum, and how a loss is recovered **is not defined.**

And what stays declared as a frontier, without looking for a way out:

- **The coordinated compromise of all of a wallet's factors** is indistinguishable from its
  legitimate use, by the same argument as the complete break.
- **Accounts that operate on their own** —contracts, automatic nodes— are left without a second
  factor. It is not impossible: an independent co-signer, on other infrastructure, that signs only if
  the transaction meets a policy, is a real second factor with no human. But it requires a second
  machine per account, that is, double the hardware, and collides with the zero entry moat of §6.1. It
  was decided not to go that way: it is a limit **by cost**, not by impossibility. For those accounts
  only the canary covers, and theft of the process stays open.

**Declaring this is stronger than promising the opposite.** A design that said "this chain is
unbreakable" would be promising something no cryptographic system can promise — section 6.6 already
says it for the primitive ("nobody can say it is secure, so it is tested the hard way"), and it holds
exactly the same for the succession mechanism that replaces it. The alternative to a declared limit
is not a solved limit: it is an undeclared limit, which is there anyway, only nobody wrote it down
before it was needed.

### 10.3 Open problems

Two remain. The rule that moves the permanence rate of §8.5 was decided in September 2026 —the
mechanism is in §8.6— and with that the first problem on this list is closed entirely: the step
ceiling, the initial level of the rate and the rule that moves it are all three at the end of the
section, among the resolved ones. What remains is an empirical question, not a decision, and it was
opened by building the machine of §6.6: which hardware is the worst case, and two machines are not
enough to answer it.

**Which hardware is the worst case, and it was opened by measuring.** The whole design assumes that
the light layer is the binding one: that is where the cheap node entry of §6.1 comes from, and on
that assumption the `R_declarado` that feeds the ceiling of §6.6 is calibrated. **Measured on the
real machine, the assumption is false for adversarial memory patterns.** A mid-range phone runs the
worst admissible program at 80.8 million steps per second and an x86-64 desktop runs it at 78.9 —
and with larger memory budgets the distance opens up to double, in the phone's favour. The cause is
that the two machines break at different places: the ARM core does not pay for the unpredictable
indirect jump that punishes the interpreter on x86, and the desktop does not withstand the page
dispersion the phone absorbs at no cost.

That does not invalidate the ceiling —it is calibrated against the hardware the protocol declares as
reference, and there it is measured— but **it does invalidate the claim that the cheapest hardware is
the worst case**, which appeared as obvious. And it is not closed by thinking: **two machines are not
enough to fix a hardware floor**, much less when one of the two has an 80% spread between runs of
the same measurement against the other's 1.6%. It needs more machines, which is work of a different
class from the rest of this section.

**A third machine, and the first that does not fit.** An Amlogic S805 (Cortex-A5, 32-bit ARMv7,
2015) —the simplest core of the three measured, with no division pipeline and no aggressive prefetch—
runs the complete reference block (fifteen ML-DSA-44 verifications) in 2,499 ms against a budget of
1,500: **1.67× over, failed**, against the phone's margin of 4.24×. And the mechanism that breaks it
is not the same one that separated the first two machines either: there, two memory patterns were
competing; here integer division (`divu`, with no special cost on the other two) ties with pointer
chasing as the most expensive mix, so the second ceiling of §6.6.1 —designed for the memory pattern—
neither sees it nor charges for it. Tables in `geminis/predicado/RESULTS.md`.

This does not close the question —more hardware is still needed, and this time, besides weaker
machines, what resource binds has to be varied— but it fixes a point: under the parameters in force,
a core of that class is **out of spec** for running the light layer, and the cheap node entry of §6.1
has, for now, that known floor and no other declared one.

**The second, and it was opened by §6.7: the edges `X` and `Y` of the round window of the compute
challenge.** The formula that draws `T` within the range is already closed; what is missing is the
range itself, and it is not just a latency measurement — it is, first, a decision no measurement can
take on its own: what counts as the reference node whose legitimate worst case `X` protects. A floor
calibrated on a large model on a datacenter GPU excludes any more modest node by design; one
calibrated on the smallest admissible hardware stretches the round for everyone, and there is no
third option that avoids deciding it. Unlike the hardware floor above —which asks what exists—, this
one asks what is to be admitted. And unlike `R_declarado`, there is not yet a real compute node
running a challenge to benchmark: it is a measurement pending something to measure.

> **Solved:** *the step ceiling of §6.6*. It was declared here as **a number and where it lives**,
> with a coupling that seemed to force a choice between two bad forms: frozen into the machine it has
> to be chosen generous —it has to survive primitives that do not yet exist— and generous is
> precisely what lets through the correct but ten times slower implementation; tight, it has to be an
> internal parameter, and an internal parameter is a lever somebody is going to want to move.
>
> **The dilemma was false.** This same section already said where the anchor had to be —*the only
> thing that does not derive is the light layer budget of §6.1*— and what was missing was writing the
> sum: `ceiling = f* × tiempo_de_bloque × R_declarado / tx_por_bloque`. What I1 freezes is **the
> formula**, not the number, and the value is determined by each generation with parameters that are
> already in the space. That way it is neither frozen nor loose: **it is not a lever, because nobody
> can move it without moving capacity or block time**. And since it does not depend on which
> primitive is installed, **it does not compose**: it avoids the loan the relative anchor charged,
> where 2× per transition is 1,024× by the tenth.
>
> **The edge of future primitives dissolves on its own.** A more expensive primitive is not left out:
> **it gets in by paying capacity**, and that sum is done by a transition of §3, with its `Δ` and its
> notice. It stops being a free and invisible decision and comes to have a price.
>
> **What does remain a decision, and is declared as such:** `f*` —the fraction of the light node
> that signature verification may occupy— and `R_declarado` —the rate of the entry hardware—.
> Neither comes out of a measurement. `f*` has a floor: §6.3 needs headroom to drain the queue, and
> it is measured at 10% with eleven nodes. `R_declarado` has to be **below** the real hardware, and
> erring low is the safe direction because the surplus is headroom. With `f* = 25%` and
> `R = 70 M steps/s`, a six-second block with 15 transactions gives a ceiling of **7 million steps**:
> double what the reference implementation of ML-DSA-44 costs, and a fifth of what the slow
> implementation Test 2 found would cost.
>
> The 2× margin is the only choice with discretion and it is bounded on both sides: at 1× the
> protocol ends up choosing the implementation instead of the interface, which is the opposite of
> what §6.6 wants; at 10× the case the ceiling exists to exclude comes back. **It is used only once,
> in Geminis, to choose the capacity** — if the protocol reapplied it at every transition, it would
> compose again.
>
> **And the first time this was written, `R_declarado` said 300 M and the capacity 67.** Building the
> machine falsified it: that number was the rate of **one** instruction mix, ML-DSA's, and the rate
> of the machine depends on the mix by 23×. The formula survived without a change; what was wrong was
> its calibration, and fixing it cost three quarters of the block's capacity. **That the ceiling was
> a sum and not a number is what made the correction one of a parameter and not of a mechanism** —
> and that a second ceiling was needed, on pages touched, is what §6.6.1 adds. Measured in §12,
> Test 5.
>
> **And the second ceiling repeated the history of the first in miniature.** It was born as a
> constant, and a constant in that place **excludes instead of making more expensive**: a primitive
> that needed more memory had no price to pay. It was closed the same way —freezing the curve instead
> of the point— and block 0 did not move: 96 pages, 15 transactions, seven million steps. **That the
> same play served twice is what gives the most confidence about its form:** in this design, a number
> that has to be chosen is usually a sum that has yet to be written.

> **Solved:** *the initial level of the permanence rate*. From the first open problem of this section
> a smaller number remained: not the rule that moves `r0`, but where it starts. A control law says
> how the rate moves, not where it begins, and where it begins is a price —how much a storage epoch
> is worth in units of the token— that the chain cannot read without violating I2. The rate has a
> physical side —bytes × epochs— and a monetary one —how many units that is worth—, and no sum
> crosses those two sides without reading a price: unlike the step ceiling, which had both its sides
> in the physical world and could therefore be closed with a formula, here one of the two sides is
> monetary and there is no formula that derives it. **That is not a sum that has yet to be written,
> it is a boundary**, of the same family as those of §10.2.
>
> The replay of §11 put a number on this boundary, on someone else's parameter: Ethereum rations gas
> with a price the protocol itself computes —the EIP-1559 base fee— and that price fell **650-fold in
> four years**; any nominal level fixed in Geminis would have stopped meaning what it meant. And the
> anchor that seemed to avoid the problem —the price against its own annual median, dimensionless, no
> oracle— was discarded with the same data: it gets it right where it matters (on the gas limit it
> would have fired fourteen months before human coordination did) but **it is left with no notion of
> expensive**, because without an absolute reference *expensive* is only *more than just now*. A
> relative setpoint is not a setpoint: it is a ratchet.
>
> **The way out was not to derive it: it was to declare it, with the same argument as `f*` and
> `R_declarado`.** It does not come from a measurement —it could not—, but the margin around the
> choice is measured. The representability floor of the chosen epoch (one day, §8.5) gives the
> minimum unit of token that can be charged per epoch; `r0(0)` is set at **a thousand times that
> floor**. The reason: at that scale, filling 100% of the state budget for the window of `L_max`
> starts to cost a non-trivial fraction of the supply (of the order of 1%) without normal use
> —creating a few entries— noticing it at all, because both costs scale the same way (linearly) with
> the multiplier: shrinking it does not buy adoption, it only subtracts the only defence that exists
> against whoever wants to fill the entire state while the control law has not yet reacted. Fixed on
> 1/9/2026.
>
> What this closure does not touch: **the rule that moves `r0` after Geminis**, resolved separately —
> see the next resolved item.

> **Solved:** *the rule that moves the permanence rate*. Indexing to occupancy —the only variable it
> can be indexed to without violating I2, the doctrine of §7.6 applied to disk— looked like the
> obvious way out, and it has a flaw that only appeared when measuring it against a real case: **once
> a price already rations the resource, occupancy stops saying whether that price makes sense.** The
> replay of §11 measures it without meaning to, on someone else's parameter: with Ethereum's base fee
> moving 650× in four years, gas occupancy stayed pinned to its target by construction, correlation
> −0.02 against the price. A loop that looks at that same error inherits the blindness: it can hold
> occupancy at target and not know whether it does so at an absurd price.
>
> **The adopted rule does not look at occupancy: it makes the price discover itself, against a fixed
> quota — the complete mechanism is in §8.6.** In summary: a fixed quota per epoch (`θ*/L_max`, a
> sum, not a decision, the same play as the step ceiling), life fixed at `L_max` for every admitted
> entry —which closes the intertemporal arbitrage channel that brought down the first version of this
> rule: measured, the bought life reached more than four times the reference one when the price fell
> in order to fill, and occupancy did not converge over thousands of epochs—, and a price from a
> uniform clearing auction. Against the same shock that brought down the previous law, occupancy does
> not depart from target at any moment, without the spike of up to 1.48× that the occupancy-indexed
> law still let through with the same `L_max`.
>
> **With few bidders the price is noisy, and getting more people together does not fix it** —the
> noise depends on the quota, not on how many bid for it, a result from extreme-value statistics and
> not from sample size—, so the rule carries a bootstrap reserve: a moving average over the
> protocol's own price series, with a gain that switches itself off when the quota grows with the
> network, without anyone retiring it by hand. Under a transition that moves `θ*` the quota is
> recalculated on its own, and a reduction within what `θ* ≤ 67%` already left as margin never
> compromises the physical budget. Fixed on 1/9/2026.

> **Solved:** *the cost of what the gauntlet installs*. The work request delivers an interface and
> some vectors, and for a while the predicate verified only that the implementation was **correct**,
> not that it was **cheap**. Test 2 found it and §6.6 closes it: the acceptance predicate now carries
> two clauses, and the second is a VM step ceiling. The hole was that the budget of §6.1 could be
> broken from inside the protocol, with no fork and no attacker.

> **Solved:** *the interpreter's verification budget*. It was the problem that could bring down a
> structural piece: if interpreted lattice mathematics did not fit into the light layer budget, §6.1
> broke and with it the answer to the validator problem. Measured on real hardware (§12, Test 2): it
> fits, and with margin. The key is that **determinism and interpretation are separate things** —
> wasm fixes the semantics, and for integer code the JIT reproduces it bit for bit just like the
> interpreter, so the penalty of the property §6.6 needs is **~3×** and not the ~29× the intuition of
> "interpreted is slow" suggests. On a phone the ceiling with JIT is the same as on a desktop.

> **Solved:** *cryptographic obsolescence against I2*. The canary turns the break into a fact of the
> state; the interpreter removes the bottom of the ladder; the work request writes the new primitive
> and the gauntlet decides whether it gets in. All in §6.6, with no human fork and no limit on
> generations.

> **Solved:** *in-flight transactions*. Half is adopted from what every chain already does —the
> ruleset of the including block applies, and the mempool is not consensus state— and the other half,
> the half-committed objects, comes out of I5 without adding anything (§6.3).

> **Solved, and it is recorded because the problem is the one almost everybody expects to find:** *a
> transition the validators do not want*. In PoW and PoS the block producer earns exactly what a
> transition can touch, so they can form a bloc with an interest aligned against it. Here the income
> of the consensus layer is a fee per verification on hardware with no capital moat (§6.1): whoever
> refuses does not block, they exclude themselves, and replacing them costs one phone.

---

## 11. Status

A concept with the four tests of §12 closed and, since August 2026, with the mechanism of §3
**running**: a succession engine over a synthetic state, the five invariants as predicates that
execute on every block, ordering and settlement from §6.3 to §6.5, and a harness that runs candidate
rules against Ethereum's real history. What has been built is not a network — it is §3 executing and
measuring itself.

**Building it corrected three things that reading had not corrected**, and all three are written
where they belong and not in an appendix: what happens with **more than one transition in flight**
(§3), that the lock-in event **is state and not an announcement** (§3), and that **I2 was written
wrong** — it left out the canary of §6.6, which is the shop-window section, and it let through a gate
with an owner (§4). To that was added the third condition of §6.3: **each node picks in its own
order**, without which the parallelism of the queue evaporates and the number of necessary nodes
ceases to exist.

**The replay comes first because it is the only evidence in this document its author did not
write**, and the first thing to say is that **two of its three cases went against.** Three real
parameters, with the heights and offsets verified against the EIPs and against the configuration the
nodes run:

- **the difficulty bomb.** A `TRANSITION_RULE` with a single number chosen in advance reproduces the
  six times Ethereum ran it, within 37 days, and one of them exactly. But that number is the average
  of a criterion that **was moving**: measured against the network's adjustment capacity, the
  pressure at which they forked varied **41×**, and five of the six forks were preventive. A
  threshold written in Geminis would have been the wrong one at both extremes;
- **the blobs.** Where the constraint was demand, the rule would have acted **383 days earlier**,
  with occupancy sustained at 129% of target. Where the constraint was **not** demand, it would
  never have acted: the last two raises responded to Fusaka bringing PeerDAS, and *"the network can
  now carry more without degrading"* is not a fact of the state;
- **the gas limit.** There is no admissible trigger, and not for lack of ingenuity. The quantity is
  empty by construction —EIP-1559 pins occupancy to the target: **correlation −0.02** with the base
  fee while the fee moves 650×—, the nominal price expires, and anchoring the price to its own
  history loses the notion of *expensive*.

**The replay produced no evidence that this design is better.** It produced the three places where it
breaks against the real world, each one with its number. All three are written where they belong
—§10.1, §10.3 and §7.6— instead of being left in an appendix. Reproduction in
`geminis/herramientas/`.

**Test 2 passed**: the interpreter's budget fits with margin, measured on real hardware, and the
§10.3 item that could bring down a structural piece was resolved. The hole the test found along the
way —the gauntlet bounded correctness and not cost— was also closed in the mechanism of §6.6. What
remains open there **is no longer a mechanism: it is a number and where it lives.**

**Test 3 run**: the gap exists, but narrower. Automatic firing without a vote has a precedent (Drake,
2018); what does not is the chainable succession within a space defined in Geminis. §6.6 was
rewritten to cite that convergence and to answer the objection that left that idea without
follow-up.

**Test 1 passed**, and it is the one that moves the design the most: the mechanism has a customer
—there are real transitions that meet the three conditions, and the main one is running today on
Ethereum—, but the customer asks for the cheap half. None of the cases found needs the interpreter or
the chainable generations, which are precisely the two pieces that pay the most expensive boundaries
of §10.1 and that sustain the differentiator of §6.6. The demonstrated demand is for §3 + I2 over a
finite space of internal parameters; cryptographic evolution, which is the shop-window section, is
the only application with no customer found.

**Test 4 run**, with the most expensive result of the four: the answer to its question was no. Net
issuance and the profit of whoever pays themselves are the same quantity, so there was no `k` that
created new money without creating exactly that opportunity. On top of that came a second failure
that did not depend on `k`: with `W` measured in tokens paid and with no premine, the loop started at
zero and could not issue the first unit.

**That result rewrote the whole of §7, and that rewrite is the newest and least tested part of this
document.** Issuance stopped depending on work, fees were left as the only payment for work, the
day-1 distribution was resolved by a claim with a compute cost and a burn of what is not claimed, and
the self-payment attack went from *"it has to be calibrated"* to *"it loses money at any scale"*.
Around that, four questions the redesign opened were closed: the initial distribution (§7.2), the
circulation band —eliminated—, work assignment (§6.5) and the saturation of the challenge queue
(§6.3).

What remains, then, is a concept split into two halves with different **evidence**, which is a more
precise way of saying what §12 anticipates:

- **the deterministic succession of parameters** has a customer found outside, in chains that exist,
  and does not depend on the currency;
- **the currency** has a specification that survives every attack that has been run against it, and
  none of those attacks came from outside.

**And the asset creation of §8.5 is newer still than that**, so it is worth saying what state it is
in: the mechanism —floor, deposit, cap on the life that can be bought, eviction with reactivation— is
complete and verified against the invariants, but **the rule that moves the rate is not chosen** and
was left in §10.3. The collision that blocked it —indexing the rate to occupancy opens a channel for
paying to bring a transition closer— was resolved in the only way available without a running
network: the lever was measured, compared against what closing it cost, and left **declared as a
boundary** in §10.2 instead of fixed. It serves as a sample of how fragile one's own evidence is: the
first version of that rule looked stable, and what brought it down was correcting a detail of the
model it had been tested with —it treated as shortenable some terms the protocol promises to
respect—. It is exactly the failure mode the previous paragraph describes, found this time from the
inside.

What comes next in the project is not more falsification of the same kind: the four tests §12
proposes are already run, and the fifth —the only one that required building— is too. For the first
half it is the scope decision Test 1 left on the table; for the second, getting someone who did not
write the design to try to break it.

---

## 12. How to falsify it before building anything

The dominant risk is not technical —the mechanism is implementable— but that it has no customer.
None of the four tests requires writing a line of protocol.

**There is a fifth, and it came later.** The four above were designed to falsify *before* building,
which is where almost all of their value comes from. Test 5 could not: it asks what the machine does
when the program is written by an adversary, and to answer that you have to have the machine. It is
written here because it **failed**, and what it failed was a number this same document took as
closed. It is worth having it in view alongside the others, with the warning that the lesson it
leaves —*there are things you only see by building*— is exactly the one this section exists to
minimize, not to deny.

**Test 1 · The concrete transition.** ✅ **Passed** (August 2026), with a correction to the scope.
Name *one* real transition that meets the three conditions at once: that its trigger be computed from
the state of the chain; that it be expressible as a selection within a parameter space definable
today; and that some real chain has needed it and not been able to have it. If none appears, the
mechanism has no customer and everything else is engineering with no recipient.

> **Result: three appear, and the customer is smaller than the shop window.** The main one is alive:
> Ethereum recalibrates the blob capacity parameters —`blobSchedule`: target, limit and adjustment
> fraction— and built a fork type dedicated to making that change cheaper (EIP-7892), because *"large
> and infrequent blob parameter changes generate costs and inefficiencies"*. The firing, however, is
> still a timestamp written by hand in the client's configuration. In May 2026 the pattern repeated
> on the gas limit (EIP-8261): a schedule per epoch that explicitly declares **not** to be a consensus
> rule. Two other cases corroborate it: the difficulty bomb, delayed by hard fork **six times** in
> five years —Muir Glacier was coordinated in less than three weeks, over the 2019 holidays, to
> install an integer the chain could compute on its own, and that a human had computed wrong—; and
> terminal issuance, which Monero wrote in advance and obtained with no fork and no decision, while
> Bitcoin, which did not write it, today cannot have it at any price. Method, discarded candidates and
> sources in `test1-transicion/RESULTS.md`.
>
> *August 2026 update, on verifying the replay data of §11.* EIP-7892 moved to **`Final`**, and its
> motivation is worth reading verbatim: *"the current approach of only modifying blob parameters in
> large, infrequent hard forks is not agile enough to keep up with L2 growth"*. Ethereum has already
> used it twice —mainnet's `blobSchedule` went from target 3 to 6, 10 and 14 in twenty-two months—,
> so the customer not only exists: it is acting, and accelerating. **And the other half has to be
> said just as loudly: it solved it by making the fork cheaper, not by making it unnecessary.** A
> parameters-only fork is still a coordinated fork. More still: the last two raises were announced
> **together and in advance**, that is, the next step the customer took on its own was *writing the
> schedule beforehand* — the form of BIP-103, one property away from what this document proposes, and
> that property is I2: the firing is still the clock and not the state.
>
> *The correction to the scope:* none of the three needs the interpreter, nor chainable generations,
> nor §6.6 — they are internal parameters over spaces of integers. What has demand demonstrated by
> third parties is **§3 + I2 with a finite space**, which is the half of the design that does **not**
> pay the expensive boundaries of §10.1. The other half, including the differentiator declared
> against Drake, still has no recipient found.

**Test 2 · The interpreter's budget.** ✅ **Passed** (August 2026). Measure how long a post-quantum
signature verification takes running as bytecode over a deterministic VM, on a phone. The loop of
§6.6 and the governance property of §6.1 both depend on that number fitting into the light layer's
budget. It is a benchmark, not a protocol: it is run with a VM that already exists and a reference
implementation. If the number does not work out, the light layer stops being light and the answer to
the validator problem falls.

> **Result: it fits with margin.** ML-DSA-44 from bytes on a Motorola Edge 40 Neo: 391 µs as bytecode
> with JIT (3.51× native), ~640 tx/s with a quarter of a core — the same ceiling as on a desktop.
> What decides it is that **determinism and interpretation are separable**: for integer code the JIT
> is as deterministic as the interpreter, and it costs ~3× instead of ~29×. The test also returned a
> clause of the predicate (§6.6), two conditions (§10.1, §10.3) and a correction to §6.1: the
> Android/iOS asymmetry is ~15×, not ~8× as had been estimated from a desktop. Method, tables and raw
> data in `test2-interprete/RESULTS.md`.

**Test 3 · Competitors.** ✅ **Run** (August 2026), with a correction to the declared gap. Tezos
self-amends by vote. Polkadot evolves by governance. Ethereum's difficulty bomb forces the fork but
humans write the successor. The declared gap is **deterministic succession without a vote**; it has
to be confirmed that it is real and not an artifact of not having searched hard enough.

> **Result: the gap exists, but it is narrower than this section said.** Tezos, Polkadot and Internet
> Computer are confirmed as vote-dependent. Cardano's hard fork combinator makes the transition
> without a split, but humans write the successor and the proposal goes signed. What was **not** new
> is the firing: *cryptographic canaries* (Drake, 2018) already combines a trigger from the state and
> automatic commutation without a vote, with a single prewired backup — see §6.6, *Prior convergence*.
> Nor was it new to write the succession of a **parameter** in advance: BIP-103 (Pieter Wuille, 2015)
> proposed replacing Bitcoin's block size limit with a deterministic function —+4.4% every ~97 days
> until 2063— without a miners' vote. It does not close the gap, and for three reasons worth keeping
> at hand: the firing is time and not state, the successor is a constant of a fixed curve instead of a
> point of a space, and there is no chaining. But it is deterministic succession without a vote, in
> Bitcoin, ten years earlier. What appears in no work found is the successor derived within a space
> defined in Geminis, with chainable generations. Concurrent work to watch: *Post-Quantum Blockchains
> with Agility in Mind* (Tectonic Labs, IACR 2026/609, March 2026), which solves agility by each
> user's operational choice, not by deterministic succession.
>
> *Limit of the search:* one pass, in English, over the web and indexed literature, with governance
> and crypto-agility vocabulary. The Drake finding came out of the second vocabulary and not the
> first, and BIP-103 came out of neither: it turned up only in Test 1, with parameter recalibration
> vocabulary. The two precedents this test had to find were found **outside** its own vocabulary. It
> does not rule out something in badly indexed documentation of a small project.

**Test 4 · The window of `k`.** ✅ **Run** (August 2026), and it is the only one of the four that
forced rewriting a whole section instead of pruning it. Simulate whether there was any `k > 0` where
paying yourself was not profitable and the subsidy was still significant for an honest operator. It
was the test with a double function —it decided at once whether the currency was healthy and whether
stage 1 of adoption was viable— and without that number the monetary policy and the adoption plan
rested on an unmeasured assumption. It is a simulation, not a protocol.

**The `k` of this test no longer exists in the document.** What §7 and §9 say today is a consequence
of having run it; the result should be read knowing that it describes the design presented to it, not
the one that remained.

> **Result: the window is empty, and by identity.** Net issuance and the profit of whoever pays
> themselves are **the same quantity**: `(k − β·φ)·W`, where `β·φ` is the fee times its burn
> fraction. They are not two conditions that have to be fitted into a window — **every unit of new
> money the protocol creates is, exactly, a unit available to whoever manufactures work.** The
> self-dealer collects that issuance by running their own PoD node, and §6.1 makes that entry cheap on
> purpose. At the maximum safe `k` the sum closes at zero and the income of the PoD nodes is exactly
> the fee: **the whole apparatus of issuance and burning does the same as a fee market with no
> issuance and no burning.** There is no third region. Model and simulation in
> `test4-ventana-k/RESULTS.md`.
>
> *Second finding, independent of `k`:* `W` was measured in tokens paid and that version forbade
> premining. At block 0 no token exists, so nobody can pay, so `W = 0` and `E = 0` forever. **The loop
> was closed and it started at zero.**

> **What this test forced, and it is the only time a negative result changed the design instead of
> pruning it.** The §7 that is read today is not the one that ran this test: issuance stopped being
> indexed to work and became a separate mechanism, the day-1 distribution was resolved by a claim with
> a compute cost, and fees were left as the only payment for work. **The redesign was subjected to the
> same attack that killed the original** —Alice cycles money between her own nodes in order to
> manufacture activity— and it loses at every scale, even while being 100% of the network (§7.3,
> `test4-ventana-k/ataque-alice.py`). The reason is that there is no longer anything to farm:
> manufacturing work produces no new units.
>
> It is worth being precise about what was demonstrated, because *"run"* is not *"it went well"*.
> **The question this test asked has a negative and definitive answer:** there is no healthy `k`, and
> no future calibration is going to find one. What replaces it is not a better `k` but a design in
> which `k` does not exist. The test did exactly its job —discard before building—, and the design
> that replaces it is simulated, not built or deployed.

**Test 5 · The machine under an adversarial program.** *(Of a different class from the four above:
this one could not be run before building, and that is why it arrived late.)* ⚠️ **Run** (August
2026), and **the central criterion failed**. Test 2 measured the interpreter with its own guest,
written by the same repo. This one measures the same interpreter running the program of the
counterparty to a challenge: someone who wants the node to hang or fall over. The criteria were
written before the first line of code, in `geminis/predicado/CRITERIA.md`, and seven of them are
operable with a number.

> **Result: six passed and the seventh uncovered that the ceiling of §6.6 was over-promising by 23×.**
> The criterion said: *passed if the worst instruction mix runs at ≥ 300 M steps/s*, which is the
> `R_declarado` the ceiling had been closed with. The worst mix runs at 11.3 M. **No per-class
> instruction weight fixes it**, because the mix that produces the gap is a memory read and a read
> costs the same as an addition when the data is in cache: it is the same opcode and what changes is
> where the data falls. Out of that came **a new ceiling on pages touched** (§6.6.1), a recalibration
> of `R_declarado` from 300 to 70 M steps/s, and three quarters of the block's initial capacity: from
> 67 to 15 transactions. Tables and method in `geminis/predicado/RESULTS.md`.
>
> *And three findings that were not about performance but about attack surface:* the loader reserved
> 64 MiB before validating a single header, and an altered section header could force 128 MiB of
> predecoding — **cheap input, expensive work, which is amplification by another name**. They were
> found by the mutation sweep taking minutes, not by a correctness test. The third is that the segment
> flags of an ELF do not distinguish code from constants, so the predicate format had to start
> requiring the binary to **declare where its code is**.
>
> *And a lesson of method that cost three published corrections.* The measurement that fixes
> `R_declarado` **was wrong four times, and all four towards the same side**: the unsafe one. Three
> were comparisons between numbers taken with different methods or at different times. The fourth is
> worse and nothing failed: **an adversarial mix degenerated into another one and went on reporting a
> credible number** —pointer chasing loaded its initial address wrong and ended up always reading the
> same position, in cache—. It was caught because it ran at exactly the speed of another mix, and two
> conclusions already written here had leaned on it. Now every mix **declares how many pages it has to
> touch and is verified on finishing**: a measurement has to declare what it is measuring.
>
> **And reproducibility across architectures was verified**: the seven vectors —verdict, steps, pages
> and register fingerprint— come out identical on x86-64 and on aarch64.

**Tests 6 and 7 are used where they belong, and then four more came.** Test 6 (`test6-desafio-computo/`) measures
the compute-challenge budget of §6.7.1 and Test 7 (`test7-firma-compuesta/`) the mitigation of §10.2. The four that
follow measure the signature, its succession and how an account is protected, and are of the same class as the
fifth: they could not be run without the machine.

**Test 8 · Ed25519 on the machine.** ✅ **Run** (September 2026). "Ed25519 is more efficient" was an intuition:
until then everything measured on the machine was ML-DSA. ed25519-dalek was compiled to RV32IM and run on the §6.6
machine untouched, with the same method as Test 2 (`test8-ed25519/`).

> **Result: between 1.02× and 1.11× fewer steps than ML-DSA-44, not an order of magnitude.** `verify_strict` costs
> 3.28 M steps and `verify` 3.01 M, against ML-DSA-44's 3.34 M; in capacity per block it is ~1.3×. Where Ed25519
> wins by a wide margin is bytes, which the test does not measure. RFC 8032 vector 1 verifies in the guest and an
> altered signature gives zero. One reference crate, untuned, x86-64 only.

**Test 9 · Ed25519 → ML-DSA-44 in the same chain.** ✅ **Run** (September 2026). Do the pieces compose? The format
succession had been tested with signatures that were labels, and the machine with each primitive on its own. A real
node crosses the canary transition and, in each generation, a signature is admitted by the format that ruleset knows
(I5) and actually verified on the machine under *that* generation's ceilings, with every verdict cross-checked
against native verification (`test9-ed25519-a-mldsa/`).

> **Result: they compose.** Generation 0 rejects ML-DSA-44 by format without invoking the machine; generation 1
> accepts both and the signature born in 0 stays valid. `H0_GENESIS` does not move and the lineage verifies.
> Rejecting a bad signature costs what accepting a good one does (~3.3 M steps). **The signature → machine routing
> is scaffolding of the test, not of the protocol**: the synthetic state has no accounts or signed transactions.

**Test 10 · secp256k1 → ML-DSA-44: the change Ethereum would make with a fork.** ✅ **Run** (September 2026). The
same with the signature Ethereum accounts use today, over an alternative Genesis that belongs only to the test
(`test10-secp256k1-a-mldsa/`). With two external anchors so that it is not the implementation agreeing with itself:
private key 1 gives the well-known address `0x7e5f…5bdf` and `ecrecover` run on the machine recovers that same
address; and a signature with a high `s` is rejected (EIP-2).

> **Result: the mechanism expresses the change, and Ethereum's signature is the most expensive of the three.**
> Verifying secp256k1 costs 5.67 M steps (1.71× ML-DSA-44) and `ecrecover` 11.33 M, which **does not fit under the
> initial ceiling** of 7 M. Migrating to ML-DSA-44 would give capacity back; what grows is size, ~38×. *And a finding
> about the node:* invariant I4 is checked against Geminis' `H0_GENESIS`, so today the node does not support another
> Genesis. One crate per primitive, untuned; **it is not claimed that Ethereum should choose ML-DSA-44**.

**Test 11 · Threshold ML-DSA-44: does the chain see anything other than an ordinary signature?** ✅ **Run**
(September 2026). §10.2 said that a threshold across the owner's own devices leaves the network seeing one ordinary
signature; that was an argument. The public prototype of Mithril (USENIX Security '26), unmodified, signs 2-of-3 with
each of the three possible pairs, and those signatures are verified on the §6.6 machine untouched, under the ceilings
of the initial ruleset, against a competitor with no threshold cryptography: a k-of-n multisig on-chain, with loose
signatures (`test11-umbral-mldsa/`).

> **Result: the chain sees an ordinary signature.** 90 of 90 verify at a median of 3,318,732 steps and 28 pages,
> against 3,318,658 for an ordinary one (0.002 %); altered ones give zero. The multisig without threshold costs 2× at
> 2-of-3 (6.78 M steps, 3.1 % of the ceiling left, 7 transactions per block instead of 15) and a 3-of-3 (10.1 M)
> **does not fit** under the initial ceiling. The cost moves to the wallet: ~1.7 attempts of three rounds each, ~27 KB
> per party per signature. *And a trap:* the same guest cost 46 % more steps after a patch bump of a transitive
> dependency (`keccak` 0.2.1 → 0.2.2): a cost belongs to a binary, not to a crate name. Signing in-process on one
> machine, without a network or a phone; keys dealt from a seed; **academic prototype, not audited here**; the security
> of the scheme is not tested.

**Tests 1 and 4 were independent and gave opposite results.** Test 1 decided whether the generational
mechanism has a customer and found one, smaller than the mechanism; Test 4 decided whether the
currency exists and found that it does not, with the specification presented to it. Exactly what this
section anticipated happens: **what survives is the corresponding half, not the whole.** The
deterministic succession of internal parameters survives —and its customers, moreover, already have a
currency of their own— and issuance indexed to work paid for does not.

**And there is an asymmetry between the two results worth not papering over.** Test 1 measured the
world: it found three real transitions, written by third parties, on chains that exist. Test 4
measured a model of its own with parameters of its own, and so did the redesign that came out of it.
**A simulation that survives the attacks its author managed to imagine is not evidence of the same
kind as a customer found outside**, and the difference between the two halves of this document is
still that one, even after the redesign.
