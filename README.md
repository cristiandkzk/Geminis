# Deterministic rule succession

**English** · [Español](README.es.md)

**A chain that carries written into block 0 how its own rules change, and that executes
that change with no vote, no political fork and no human intervention in the decision.**

> **What this is and what I am asking of you.** It is the complete design (~19,500 words)
> compressed to a third: **about 25 minutes**. I took out the decision log, the history of what
> fell over along the way and the long justifications — what is left is the mechanism, the
> measured numbers and the boundaries.
>
> **If you are short on time:** §2 and §3 are the mechanism, §7 says what is measured and what is
> not, and §10 is the concrete ask. The rest is reference for when you want to hit something
> specific.
>
> **This is not a pitch. It is a request that you break it.** The design survived every attack
> that was run against it, and every one of them was run by the person who wrote it, which is
> exactly the kind of evidence that is worth nothing. At the end there is a list of **where to hit
> first**; if you only have time for one thing, go straight there.
>
> Everything listed as *measured* has a reproducible script and raw data.

**Where the rest is, if you want to get to the bottom of something.** This file is the summary.
The source of truth is **[Geminis Paper.md](Geminis%20Paper.md)** —~19,500 words, with the
boundaries developed and the record of what was discarded along the way—; the Spanish original it
was translated from is [Geminis Paper.es.md](Geminis%20Paper.es.md), and `Geminis-paper.html` is its
render, regenerated with `python render.py` and never edited by hand.

⚠️ **Careful with the section numbers: this summary has its own numbering.** It merged sections, so
it has 10 and the paper has 12, and **they do not line up** — the challenge queue is §5.3 here and
§6.3 there; asset creation is §6.4 here and §8.5 there. When you jump to the long paper, search by
title and not by number.

**And if you are here to write code:** [`ROADMAP.md`](ROADMAP.md) has the glossary of the concepts,
the module structure and the phases with their pass criteria.

And every number here has its measurement, with a `RESULTS.md` and scripts:

| directory | what it answers |
|---|---|
| [`test1-transicion/`](test1-transicion/RESULTS.md) | whether the mechanism has a customer outside — the cases of §7 |
| [`test2-interprete/`](test2-interprete/RESULTS.md) | the interpreter's budget on real hardware, with the benchmark package |
| [`test4-ventana-k/`](test4-ventana-k/RESULTS.md) | the self-payment attack, and the window that turned out to be empty |
| [`cola-impugnaciones/`](cola-impugnaciones/RESULTS.md) | whether the queue of §5.3 saturates — where the ten PoD nodes come from |
| [`expiracion-estado/`](expiracion-estado/RESULTS.md) | how much state is generated and what being able to revive it costs |
| [`amortizacion-mint/`](amortizacion-mint/RESULTS.md) | why the rate cannot go down by depositing more |
| [`parametros-mint/`](parametros-mint/RESULTS.md) | the parameters of §6.4, and which of them is really a decision |
| [`presupuesto-nodo/`](presupuesto-nodo/RESULTS.md) | how much an entry occupies, and where `θ*` and `L_max` come from |

---

## 1. The problem

Every deployed protocol sooner or later meets a condition its original rules do not handle well.
The three answers that exist today all put a human in the loop at exactly the moment of the
change:

| mechanism | example | who decides |
|---|---|---|
| contested fork | Bitcoin / BCH | a faction writes new software; the market arbitrates afterwards |
| on-chain vote | Tezos, Polkadot | the holders, with all the politics that drags along |
| forced obsolescence | Ethereum's difficulty bomb | the protocol forces the change, but humans write the successor |

All three work. None is deterministic: in all three, **what comes next** is a decision taken in the
moment, by people, under pressure. And that decision is where a protocol turns political.

The proposal: that the succession rule live inside Geminis and execute on its own when the state of
the chain meets a verifiable condition. The result is not a family of chains — it is **a single
chain that commutes its ruleset by generation**, preserving state intact and chaining every
generation to its ancestor by hash.

**How what follows should be read.** The design has two halves with very different backing, and
saying so early is more honest than leaving it for the end. The **succession of internal
parameters** —capacity, issuance, block times— went out looking for takers and found them (§7). The
**interpreter** and the **chainable generations** —which are what makes the cryptographic evolution
of §5.6 possible and what separates this from its precedents— pay the most expensive boundaries and
**still have no case found outside**. The first is an application; the second is a bet.

---

## 2. The mechanism: commutation

The piece that keeps this from being a fork in disguise is that **the node is not replaced, it is
commuted**: the same process, with the same state in memory, executing different rules from a given
block onward.

```
   ┌──────── ruleset A ────────┐ ┌─ F ─┐ ┌──── Δ ────┐ ┌─── ruleset B ───┐
                                                     ║
   ───▣───▣───▣───▣───▣───▣───▣───▣───▣───▣───▣───▣──╫──▣───▣───▣───▣───▶
                              ▲       ▲              ║
                           block N   N final    activation
                       TRANSITION_    LOCK-IN   commutation in effect
                        RULE → TRUE  irrevocable
                        (advisory)   params on-chain

   the SAME node · the SAME state · no migration, no bridge, no snapshot
```

**There are three times, not two**, and the separation is what keeps every transition from being a
surprise:

1. **Trigger.** At block `N`, `TRANSITION_RULE` returns TRUE. It commutes nothing and commits
   nothing: it is advisory, and a reorganization can undo it.
2. **Lock-in.** When `N` is final, the trigger becomes irrevocable. It is not ceremony: `H0_B`
   commits `state_trigger`, and committing it earlier would leave the checkpoint pointing at a
   state a reorganization can take out of the chain. Lock-in emits on-chain the complete parameters
   and the activation height — everything an integrator needs is on the chain, `Δ` blocks in
   advance, without anyone having to announce it.
3. **Activation.** `Δ` blocks after lock-in —not after the trigger, so that the notice is exactly
   `Δ`— the node commutes.

`Δ` is fixed in Geminis **per transition class**: a circulation transition tolerates a long window,
a cryptographic migration under attack needs the opposite.

The lineage is chained by hash:

```
H0_B = H( H0_A ‖ state_trigger ‖ params_nuevos )
Verify( H0_B, H0_A, state_trigger, params_nuevos ) → TRUE
```

Geminis A **does not know** B's hash —it cannot, B incorporates information that does not yet
exist— but it deterministically knows how it will be computed. `H0_B` is not the genesis of a new
chain: it is a generational checkpoint marker within the same chain.

---

## 3. The five invariants

Each one eliminates a way of reintroducing the human into the loop. **They are the hard frame: an
attack that respects them is an attack against the design; one that violates them is a different
design.**

**I1 · The interpreter lives in Geminis and never changes.** A transition does not introduce node
code: it selects a point of a space the node **already knows how to execute**. What Geminis fixes
permanently is not a list of possible rules but the **machine that runs them**. The space is split:
the **internal** parameters —issuance, fees, block size, timings— change in any transition; those
**visible in the interface** —signature primitive, address format, serialization— only by way of I5.

**I2 · The trigger is computed only from the state, and nobody chooses the moment.** No oracles, no
signatures, no votes. But computable is not enough: *"address X received 1 wei"* is computed only
from the state and it is a gate with an owner. There are two ways of meeting it and every rule
declares which one it is in. By **observable approach**: the quantity that triggers is monotone, the
chain publishes *how many blocks are left at the current rate*, and the rule **cannot trigger from
rest** — if the previous block did not publish a distance, it was a step. By **demonstrated
capability**: there is no approach and there cannot be one —the break of a primitive happens, it is
not approached— and it is admissible only if producing the fact requires **exactly the capability
the transition reacts to**, declared on-chain. It is the canary of §6.6, and its condition is that
the weakened instance be **derived** from a public seed: if somebody generates it, they keep the
trapdoor and the canary is theirs.

*No node can verify that the declared capability is the true one; that is audited in Geminis, and
that is why the declaration is mandatory and explicit. And the distance is a projection at the
current rate, not a promise: the promise is `Δ`.*

**I3 · State is preserved intact across the transition.** There is no balance migration, no
snapshot — and therefore no bridge, which is the most attacked component in the industry.

**I4 · Every generation commits to its ancestor.** The lineage is verifiable by hash and does not
depend on anyone attesting to it.

**I5 · Transitions are additive in the interface.** Every address and every transaction carries a
generation tag from block 0. A transition can **add** formats; it cannot remove them.

It is the invariant that decides the failure mode of every **external integrator** — an exchange, a
wallet: software that reads the chain from outside, not a node. It does not mean it stays on an old
chain: **objects from the previous generation never stop being valid**, so the integrator that did
not update keeps processing them just as always. What it cannot do is understand the new ones — and
there, since every transaction carries a generation tag from block 0, it **fails closed and loud**
(*"a version I don't know"*) instead of parsing them under the old rules and producing a plausible
and wrong result, which is the failure that loses funds. That is degrading: it works for the old,
it stops dead at the new.

---

## 4. What comes for free: canonicity

It is probably the most valuable property of the design and it was not sought: **it inverts the
legitimacy asymmetry of a fork.**

In Bitcoin the conservative position —change nothing— is the default: whoever wants to change the
rules writes new software, and the chain that stays the same claims to be the original. Here it is
the other way around: the standard client commutes on its own, so **not commuting requires actively
modifying the software** and disabling the rule. Whoever stays on the old rules does not preserve
the original chain: they deviate from Geminis, and cannot invoke Geminis to justify it.

*"Which one is the real one"* stops being a social question. An exchange or a light client run the
lineage verification, and the chain that did not commute has no valid generational checkpoint. It is
an objective canonicity criterion, and no contested fork in history ever had one.

---

## 5. The architecture

### 5.1 Two classes of node

**Compute nodes.** GPU and RAM, they host the models that do the requested work. Expensive
hardware, a competitive market, and **they do not take part in consensus**: their income is the
payment for the request they executed.

**PoD nodes.** They verify and settle, and charge a fee every time two contracts interact. They run
on any hardware — verification reproduces bit for bit on x86-64, ARM64 and a phone.

**The fee is ad valorem.** A fixed fee is regressive in both directions: it makes the small request
unpayable —which is the one an agent economy makes in volume— and the large request free, which is
where the burn has to bite.

Portability has a governance consequence: **what lets a validator hold a chain hostage is not their
conviction, it is the capital moat.** A node that fits in a phone has no moat. But there is a better
argument and it does not depend on the cost of entry:

> **You can have 3,000 nodes or 3 million. If there is no external demand, they all compete for a
> pie that does not exist.** Since issuance does not depend on work (§6.1), adding nodes creates no
> income: it splits the same fee among more hands. **Manufacturing identities is free and yields
> exactly the same**, which is more robust than making it expensive.

**Measured.** On a Motorola Edge 40 Neo under Termux, an ML-DSA-44 verification from bytes runs in
**391 µs** as bytecode with JIT —3.51× native— and yields **~640 tx/s** with a quarter of a core.
It is the same absolute time as on a desktop i5-9400. With one caveat: iOS does not allow
third-party JIT and the bytecode arrives at runtime, so a node on an iPhone is forced into the
interpreter, **~15× slower**. That is platform policy, not a property of the design.

### 5.2 PoD verifies the predicate, not the inference

A model cannot pass the determinism gate. Not even at temperature zero: floating-point
non-determinism across different hardware breaks bit-for-bit reproduction.

The split into two layers makes it irrelevant. **The GPU produces; the light node checks.** The
request does not say *"generate good code"* — it says *"deliver something that compiles and passes
these tests"*. Inference is not verified: what is verified is that **the output satisfies the
predicate**.

Out of that comes a hard restriction:

> **Every request carries a deterministic acceptance predicate, cheap enough to run on the light
> layer.** Whatever cannot be expressed that way is not work the network can settle.

That turns a fuzzy warning into a sharp boundary — and **that this subset is large enough to sustain
an economy is a hypothesis, not a result.**

A corollary that looks like a limitation and is the opposite: **the client does not choose which
node executes their request, and does not need to.** Quality is not secured by selecting in advance
but at acceptance: if the output does not satisfy the predicate, there is no payment.

### 5.3 Order without global consensus

Verifying and ordering are not the same operation. If Alice signs two transactions spending the same
100 tokens, **both are individually valid**; only order decides which one wins.

But **global** order is not needed: each account carries its own sequence and its owner is the only
one who can append to it; committing funds into a contract takes them out of the available balance,
so they cannot be committed twice; and an interaction becomes firm when a **challenge window**
passes without anyone presenting proof of conflict.

**The window cannot be clogged, and the reason is not the price:**

> **Filling is serial; draining is parallel.** A challenge does not exist until it enters a block, so
> the ceiling for filling is the capacity of the chain — a single pipe. Draining is done by all PoD
> nodes **at once**.

The margin is `N · h / γ`. With `γ ≈ 1` —which is what the VM step ceiling guarantees— and 10%
headroom per node, the formula gives **ten PoD nodes**; run with a real queue, **eleven** are needed.
Three conditions hold it up and none is automatic: **any PoD node resolves any challenge**; the queue
is **by arrival order with a flat bond** —if it were ordered by bond size, capital would buy
priority—; and **each node picks in its own order and not in the queue's**. This last one appeared on
running it: if they all take from the head, the `N` nodes verify the same challenge, parallelism
evaporates —with fifty nodes the margin is that of one— and the wait of a legitimate challenge is not
a fixed term but a ramp of `9·T`. It is fixed with no coordination: each node walks the queue in a
pseudorandom order derived from its identity, and that is the cost from ten to eleven. At random the
backlog **stabilizes** —with eleven nodes, ~400 challenges and a mean wait of four blocks— instead of
growing. **But the mean is not the promise:** with eleven nodes, about one in sixteen legitimate
challenges waits longer than the 12-block window under sustained censorship (simulated), so the
window stretches by itself when there is a queue, up to a hard per-class ceiling. The mechanism is
implemented; the real queue that would feed it is not.

The bond does not have to be large, only non-zero: **the honest challenger's comes back** and **the
attacker's is burned**.

### 5.4 Getting it wrong is not forbidden: it is made suicidal

That a signature is unforgeable does not stop its owner from signing **two different messages**. No
scheme prevents it. But in Schnorr and ECDSA, signing two messages with the **same nonce** allows the
private key to be solved for from the two signatures — that is how the PS3 key was lost.

Turned into a design rule: **the nonce is a deterministic function of the account index.** Signing
twice at the same index is not an infraction that has to be proven and sanctioned — **it is
publishing one's own private key.**

The punishment needs no protocol rule and no arbiter, it is verified on a phone, and **the watchman
funds himself**: the reward for catching the infraction is the infringer's balance.

### 5.5 Every transfer is bilateral

Unilateral sending does not exist: Alice offers, Bob accepts, and only then does the transfer exist.
There are two classes of offer. An ordinary transfer is **directed**. A work request is **open**: it
names nobody, and there lies the entire assignment mechanism of the system:

> **Nobody assigns requests.** The client publishes predicate, price and deadline with the funds
> already committed; the node that can fulfil it accepts it. It is *pull*, not *push* — the node
> selects itself because it knows its own hardware, and filters itself out on its own, because
> accepting a request it cannot fulfil means failing the predicate and not getting paid.

Out of that three things come for free: **there is no duplicated computation**, **a saturated node
simply does not accept**, and **the client cannot direct work to a chosen node**.

The cost is declared: you cannot pay someone who is offline, and finality is measured in minutes or
hours, not in seconds.

### 5.6 Cryptographic evolution with no bottom of the ladder

Every primitive eventually gives way. The problem is that *"the primitive broke"* is not in the
state, so it cannot be a trigger (I2); and a **list** of replacements runs out and demands a human
fork.

**The canary turns the break into a fact of the state.** Geminis publishes a deliberately weakened
version with an on-chain reward. If someone breaks it and claims it, that is state. The trigger does
not read *"the cryptography broke"* — it reads *"the canary was claimed"*. A **ladder** of canaries
grades the response: the weak one gives way years earlier and fires a migration with a long `Δ`.

**The interpreter removes the bottom of the ladder.** Since Geminis fixes the machine and not the
list, a new primitive is **bytecode**, not node code.

**Who writes it: it is a work request.** When the canary falls, the protocol publishes the request
and the agents compete. **Who says it is secure: nobody can**, so it is tested the hard way:

> **The gauntlet.** Every candidate enters with a weakened instance and an on-chain reward for a
> fixed window. If someone breaks it, it is discarded and the next one goes. The one that survives
> is installed. It is the same canary used as an entrance exam.

**The gauntlet measures security; cost is measured by another clause.** A correct and unbreakable
implementation that is ten times more expensive survives the window and stays installed forever —
and there the budget of §5.1 breaks *from inside the protocol*. That is why the predicate carries
**three** clauses: pass the vectors, verify below a **VM step ceiling**, and do so touching fewer
than a **page ceiling**. Both bounds are executed quantities, not wall-clock time: the count is
identical across architectures (measured) and the clock would be an oracle.

**The third clause was added by building the machine, and it was not in the design.** A step ceiling
assumes one step is worth one step, and it is not: the worst instruction mix runs **23× slower** than
the real workload, so the ceiling promised 22 ms per transaction and the mix took 596. It is not
fixed by weighting instructions —what gas does— because the mix that opens the gap is a memory read,
and a read costs the same as an addition when the data is in cache: **it is the same opcode**, and
what changes is where the data falls. The only thing that can be counted while it runs is the
distinct pages it touches.

**Prior convergence.** Justin Drake proposed *cryptographic canaries* on Ethereum Research in
February 2018: bounty, proof of threat, automatic commutation to a backup. This design was conceived
independently. The difference is the depth: Drake's backup is prewired and **single-step**; here the
successor is derived within a space defined in Geminis and the interpreter allows **chaining
generations**. That answers the objection that left that idea without follow-up —that calibrating the
canary forces estimates so conservative that the automation becomes redundant with manual
supervision—: with a single step, a premature transition consumes the only recovery resource and the
trigger has to be nearly perfect; chainable, it only consumes a generation that can generate the next
one.

---

## 6. The currency

### 6.1 Three mechanisms that must not be fused

| mechanism | what it does |
|---|---|
| **fees** | they remunerate work — demand → fee → nodes |
| **issuance** | it regulates the monetary state, **independent of work** |
| **PoD** | it validates which work and which transition are valid |

> **No new unit is created because a node decided to do more work.**

The fee split, with illustrative and not design percentages: 70% providers / 20% burn / 10% reserve.
**The burn is the only irreplaceable piece.**

### 6.2 The day-1 distribution

Taking issuance out of the work equation leaves a question without which the rest does not start:
**who has tokens before the first fee exists.** The three classic answers get it wrong, and the
reason is a theorem:

> **A distribution of new tokens indexed to an action yields at most what that action costs, or it
> is farmable.** If it pays less than the cost, nobody claims it; if it pays more, it gets farmed.
> Bitcoin could because hashing has an external, physical cost that is impossible to fake.

**The chosen form takes the third, bounded to block 0.** Geminis publishes pools with a cap per
class, and **claiming is paid for by demonstrating the capability being claimed**: the compute class
solves a reference task with a deterministic predicate; the PoD class verifies a reference batch
within the VM step ceiling.

It needs no identity —the cost is external and physical—, it makes **the separation by class
verifiable** —saying *"I am a compute node"* is free, solving its task is not—, and **the work is not
thrown away**: claiming is a rehearsal of the real product. **What is not claimed is burned**, and
out of that comes the best property:

> **The initial supply is not set by the creator — it is set by how much real capacity showed up.**

**Without ornament: it is still an auction paid in compute**, and whoever has more hardware takes
more. It is not an egalitarian split and it must not be sold as one. It is **open**, which is a
different thing, and it is the property Bitcoin's launch had.

Each claim also emits a **transferable certificate** of having taken part. **It is not money and it
is not a licence**: if it gave a right to tokens it would be concentrating the initial monetary base;
if it were needed in order to collect fees, the number of nodes would become artificially scarce.

**Undecided: the exact cost of the claim, the duration of the window and the caps per class.**

### 6.3 Why the closed circuit loses

The attack to be ruled out does not depend on anyone wearing a disguise: Alice has her own nodes,
sends work to herself and collects her own fees. The right question is not whether the protocol can
detect her —it cannot— but whether it is worth her while.

| Alice's nodes | net per cycle | balance after 1,000 cycles, from 1,000,000 |
|---|---|---|
| 2 of 3,000 | −0.000900 | 406,486 |
| 99% of the network | −0.000603 | 547,068 |
| **100%** | **−0.000600** | **548,713** |

**She loses even while being the entire network.** The number of nodes only moves her slice of the
reserve; the burn stays out of her reach always. With the burn at zero, the attack becomes free.

> **The protocol does not distinguish Alice from a real client. It does not try to.** It makes the
> closed circuit **lose money**, and the arithmetic does not need to know who anybody is.

**A bounded supply banks unlimited activity.** With hostile assumptions —6-hour finality and only 20%
of the circulating supply in flight— the velocity ceiling gives **292 turns a year**, against 1.2 for
US M2 and ~12 for Bitcoin on-chain. Between 25× and 250× of headroom.

**Token concentration does not grant protocol power.** I2 forbids the trigger from reading anything
that is not `emitido − quemado` of the native token, and signalling readiness is information, never a
gate. An actor with 90% of the tokens has 90% of the money and zero power over the rules.

### 6.4 Creating assets: the charge goes on permanence

**A creation primitive of fixed shape** is admitted, not a machine open to third-party state. The
chain already executes someone else's code —the predicate of §5.2— but a predicate runs, answers and
dies; here an object is admitted to **persist**. With a free shape, the size of an entry is chosen by
the user and the state stops having a unit of measure. A single primitive covers fungible and
non-fungible: **a non-fungible is `supply = 1`, indivisible**.

**The charge does not go on creation, and it is the least obvious part of the arrangement:**

> **A charge on creation does not reduce creation — it reduces the registration of creation.**

If creating inside carries a charge of its own, people mint **outside**, and there everything the
native market argues for is lost. The asymmetry is one of applicability, not only of incentives:
**the charge on creation is evaded by minting outside; the permanence charge is not, because the
state that exists is seen by every node.**

So the tariff has two parts. A **floor** that is burned, and it is not a knob: it is the fixed cost of
the create + evict cycle, measured against a node's budget, some **sixteen hours of storage** (0.2%
of what it costs to hold the object for a year). And a **permanence deposit** that is consumed by
being burned epoch by epoch, linear in **size × time**. It is the deposit, not the floor, that acts
as antispam.

**The life that can be bought at once has a cap, `L_max`, and it is a stability condition and not a
recommendation.** Without a cap, a large finite payment buys centuries. And since the rate cannot
stay frozen —it is a nominal price on a real resource—, prepaying without limit is betting against
whatever rule moves it: when the rate falls, buying long captures slots at bargain prices that cannot
be recovered without confiscating. **Measured: with `L_max` = 25 epochs the loop lands on target;
with 50 it is marginal; with 100 it breaks.**

**The charge is per entry, not per object.** A fungible is one entry plus a balance for each holder,
and that count grows with adoption: a token with a million holders occupies **3%** of a node's disk —
**thirty-three successful tokens fill the chain**. So **every state entry pays permanence, and
whoever creates it funds it**. That also closes a hole that was not about minting: **native token
accounts are state entries too**, and since the fee is ad valorem, on dust it tends to zero.

> **On the chain there is no object whose future cost does not have someone paying for it. Nobody can
> buy perpetual space with a finite payment.**

**A change of character that has to be declared: holding a balance stops being free.** It is
demurrage on the state and not on the amount — a small, still wallet ends up evicted, recoverable
with a proof.

**Evicting is not destroying, and the residue has to be O(1).** The object leaves the active set and
the holder revives it with a proof, paying the cost at that time. But the commitment it is proven
against cannot be one per object: a 32-byte tombstone per object is **1 GB per node forever**, a
quarter of the budget. Eviction **adds to a single append-only accumulator** — some **800 bytes in
total**, not per object.

**There is no debt and no auction.** Auctioning forces the chain to know what the asset is worth,
that is, to read the pool, which is exactly what I2 forbids and is manipulable in the obvious
direction. Liquidation is done by the market: whoever cannot sustain the balance sells before the
eviction.

**Target occupancy `θ* = 50%`** of a declared disk budget —of the order of a few GB— that only a
transition can move. The derived ceiling is `θ* ≤ 67%`, because the peak of a sustained shock reaches
**1.48×** before the price bites. The conservative bias is deliberate: falling short is corrected by
raising the number; overshooting expels the small nodes and **that is not reversed**, because
whoever left does not come back.

---

## 7. What is measured and what is not

This section is the one that decides how much everything above is worth.

**Measured against the world (external evidence):**

- **The mechanism runs and was measured against Ethereum's real history** (August 2026), with the
  heights and offsets verified against the EIPs and against the configuration the nodes run. **Two of
  the three cases went against**, and that is why it comes first: in the **difficulty bomb**, a rule
  with a single number chosen in advance reproduces the six human decisions within 37 days —but that
  number is the average of a criterion that moved **41×**, and five of the six forks were
  preventive—; in the **blobs**, the rule would have acted **383 days earlier** where the constraint
  was demand and **never** where it was capacity; in the **gas limit** there is flatly **no
  admissible trigger**, because EIP-1559 pins occupancy (correlation **−0.02** against a price that
  moved 650×), the nominal price expires and the relative one becomes a ratchet.
- **The mechanism has a customer, and it is approaching on its own.** Ethereum recalibrates the blob
  capacity parameters (`blobSchedule`) and built a fork type dedicated to making that change cheaper
  —EIP-7892, today **`Final`**: *"the current approach of only modifying blob parameters in large,
  infrequent hard forks is not agile enough to keep up with L2 growth"*—. It has already used it
  twice: the target went from 3 to 6, 10 and 14 in twenty-two months, and the last two raises were
  announced **together and in advance**. Which means the customer got as far on its own as *writing
  the schedule beforehand*, which is the form of BIP-103; what it is missing to get here is I2 — the
  firing is still a timestamp written by hand. In May 2026 the pattern repeated on the gas limit
  (EIP-8261), with a schedule that explicitly declares **not** to be a consensus rule. Corroborated
  by the difficulty bomb —delayed by hard fork **six times in five years** to install an integer the
  chain could compute on its own— and by terminal issuance, which Monero wrote in advance and
  obtained with no fork, while Bitcoin today cannot have it at any price.
- **Precedents.** Drake 2018 (cryptographic canaries) and Pieter Wuille's BIP-103, 2015
  —a deterministic function for the block size limit, with no miners' vote—. Neither closes the gap:
  in Drake the backup is single-step; in BIP-103 the firing is time and not state, and there is no
  chaining. **Concurrent work to watch:** *Post-Quantum Blockchains with Agility in Mind*, Tectonic
  Labs, IACR eprint 2026/609, March 2026.
- **The interpreter's budget fits**, measured on real hardware (§5.1). What decides it is that
  **determinism and interpretation are separable**: for integer code the JIT is as deterministic as
  the interpreter and costs ~3× instead of ~29×.

**And now what has to be said without ornament.** The correction to the scope of the first point:
**none of the three customers found needs the interpreter, nor the chainable generations, nor the
cryptographic evolution.** They are internal parameters over spaces of integers. What has demand
demonstrated by third parties is the half that does **not** pay the expensive boundaries. The other
half —including the differentiator declared against Drake— still has no recipient found.

**Measured only against itself (own evidence, which is of a different class):** the entire currency.
The self-payment attack, the velocity of circulation, the challenge queue, the permanence parameters,
`θ*` and `L_max`. They survived every attack that was run against them, and **every one of them was
run by the person who wrote the design**.

A sample of how fragile that class of evidence is is worth giving, because it happened in here: the
first version of the rule that moves the permanence rate looked stable and absorbed a 3× shock. What
brought it down was not an attack — it was **correcting a detail of the model it had been tested
with**: it treated as shortenable some terms the protocol promises to respect. With the terms
respected it oscillates between almost zero and more than double the target, at any gain.

**Nothing is built.** The design never ran.

---

## 8. Declared boundaries

They are not problems to be solved: they are the price of properties the design wants, and they are
maintained knowingly. The ones that weigh most:

- **Adaptation is bounded to what Geminis anticipated.** If the condition that fires the transition
  is something unforeseen, there is no ruleset to load. **And determinism removes the emergency
  brake**: a badly anticipated transition is exactly the scenario in which humans would want to
  refuse, and the design's answer is *"then you are a fork"*.
- **The set of possible futures stops being auditable.** It is the price of the interpreter. With a
  finite list, anyone could read Geminis and know what the chain can turn into.
- **The interpreter is a single point of failure that can never be patched.** If it has a bug, there
  is no transition that fixes it, because every transition runs on top of it. It is the only piece
  where formal verification is not optional.
- **Surviving the gauntlet is not surviving fifteen years of cryptanalysis.**
- **The protocol has no notion of identity, so every lever it moves, it moves for everyone.** It
  explains in one go why four different fixes died —grading the subsidy, blocking it for a time,
  splitting by role, a superlinear challenge bond—: each one needed to distinguish the honest party
  from the attacker, and all the protocol sees are signatures and amounts. **Every proposal of the
  form "let the good guy pay less" is a proposal to introduce identity.**
- **The split is illegitimate, not impossible.** Ethereum Classic exists. The asymmetry does not kill
  the dissident chain — it makes it small.
- **The hash that chains the lineage cannot be replaced**, because what would have to be migrated is
  the past. It happens to any chain that commits its history with a hash.
- **The protocol cannot force an archive to exist.** It can guarantee that an evicted asset *can* be
  revived; not that anyone will have what it takes. It is enough for a permanently online agent and
  not enough for a person, who is going to depend on an archive service — that is, on the market and
  not on the protocol.
- **It is possible to pay to bring a transition closer, though not to change which one.** On indexing
  the permanence rate to occupancy, whoever occupies disk accelerates other people's burn, and the
  burn is what the trigger reads. With `s` the fraction of the state the attacker occupies and `ε`
  the elasticity of honest demand, the other people's burn per unit of their own burn is
  `((1−s)/s)·((R−1)/R)` with `R = (1/(1−s))^(1/ε)`:

  | `s` | `ε` = 0.25 | `ε` = 0.5 | `ε` = 1.0 | `ε` = 2.0 |
  |---|---|---|---|---|
  | 5% | **3.52** | 1.85 | 0.95 | 0.48 |
  | 25% | 2.05 | 1.31 | 0.75 | 0.40 |
  | 50% | 0.94 | 0.75 | 0.50 | 0.29 |

  **The lever is of the order of `1/ε`**, and `ε` is not known without a running network. It is
  declared instead of closed: it is bounded by the fact that **what is bought is the date and not the
  content** —the successor is written in advance and by I3 the state crosses over intact—. It is
  reopened by a measurement: if the demand for storage turns out to be markedly inelastic, it has to
  be closed by definition and the first exception to *circulating supply is issued minus burned* has
  to be paid.
- **The canary pays for telling, and whoever can break the primitive gains more by keeping quiet.**
  Whoever can forge signatures can take the entire chain, and that is worth more than any bounty.
  What bounds it is that the canary does not need to attract the optimal adversary but **anyone** who
  gets there first — which is what historically happened with DES, MD5 and SHA-1. **It is an
  empirical assumption about how cryptanalysis spreads, not a property of the design.**
- **Resistance to censorship by whoever assembles the block grows with the honest population and is
  minimal at launch.** With the proposer drawn without replacement and the 12-block window, an
  attacker can hold 19–23% of the seats at a 1% annual risk, and with a third the first run of 12
  blocks arrives in ~64 days. Seats cost almost nothing (10⁻⁵ token per day), and neither a longer
  window nor a dearer rate fixes it: **cheap entry stops a coalition that refuses from lasting, but
  not someone who dilutes.** It is declared without looking for a way out. Measured in
  `sorteo-proponente/`.
- **There is no incentive paid by the protocol to run a node before demand exists.** The claim buys
  the day-1 cohort and after that the income is fees from real demand or nothing. It is a deliberate
  choice between two failures: the old design started off safely and farmed itself; this one does not
  farm itself and **may not start**.

---

## 9. The open problem, and the ones that were closed

**Closed in August 2026 · the VM step ceiling.** It was declared as *a number and where it lives*,
with a coupling that seemed to force a choice between two bad forms: frozen, it has to be chosen
generous —it has to survive primitives that do not exist— and generous lets through the correct but
10× slower implementation; tight, it has to be an internal parameter, that is, a lever.

**The dilemma was false: the ceiling is not chosen, it is derived.**

```
ceiling = f* × tiempo_de_bloque × R_declarado(pages) / tx_por_bloque
```

What is frozen into the machine is **the formula**; the value is set by each generation with
parameters that are already in the space. It is not a lever —moving it demands moving capacity or
block time— and **it does not compose**, because it does not depend on which primitive is installed.
And the edge of future primitives dissolves: a more expensive one is not left out, **it gets in by
paying capacity**, and that is charged by a transition with its `Δ` and its notice.

Two constants remain that **are decisions and are declared as such**: `f*` (the fraction of the light
node for verifying signatures, with a floor measured in the headroom §5.3 needs) and `R_declarado`
(the rate of the entry hardware, declared below the real one because the surplus is headroom). With
25% and 70 M steps/s, a 6 s block with 15 tx gives **7 million steps** — double the reference
implementation of ML-DSA-44 and a fifth of the slow one Test 2 found.

> **And building the machine falsified the first calibration of those numbers.** They said 300 M
> steps/s and 67 transactions. That rate was the rate of **one** instruction mix, and the machine's
> rate depends on the mix by 23×. **The formula survived without a change** —which is exactly what is
> gained when a ceiling is a sum and not a number—, but the calibration cost three quarters of the
> block's capacity, and a second ceiling was needed, on pages touched: **96 pages of 4 KiB**.
>
> And that second ceiling brought its own lesson, which ended up being the most useful of the phase.
> A ceiling derived from capacity **raises the price**; a constant one **can only exclude**, because
> there is no price the primitive can pay — and the three primitives of the family touch 26, 40 and
> 65 pages, so the first number chosen left the third one out forever without any sum pointing it
> out. **It was closed with the same play that had closed the first: freezing the curve instead of
> the point.** Geminis fixes how much rate the reference hardware sustains for each memory budget,
> the budget becomes a parameter, and asking for more memory is paid for in capacity like everything
> else. The measurement is in `geminis/predicado/RESULTS.md`.

**Open · which hardware is the worst case.** The whole design assumes the light layer is the binding
one —that is where cheap node entry comes from— and on that assumption `R_declarado` is calibrated.
**Measured, it is false for adversarial memory patterns:** a mid-range phone runs the worst
admissible program at 80.8 M steps/s and an x86-64 desktop at 78.9, and with more memory the distance
opens up to double in the phone's favour. The two machines break at different places. It does not
invalidate the ceiling —it is calibrated against the hardware declared as reference— but it does
invalidate the claim that the cheapest hardware is the worst case. **Two machines are not enough to
fix a floor**, and closing it needs more machines, not more analysis.

**Closed in September 2026 · the initial level of the permanence rate.** A control law says how the
rate moves, not where it begins, and where it begins is a price the chain cannot read without
violating I2 — unlike the step ceiling, here one of the two sides of the sum is monetary and there is
no formula that derives it. The replay of §11 put it in numbers: Ethereum's base fee fell 650× in
four years, and even the anchor that seemed to avoid the problem —the price against its own annual
median— is left with no notion of *expensive* once the absolute level is lost from view.

**The way out was to declare it, with the same argument as `f*` and `R_declarado`: it does not come
from a measurement, but the margin around the choice is measured.** `r0(0)` is set at a thousand
times the representability floor of the epoch — the point at which filling 100% of the state for the
window of `L_max` costs a non-trivial fraction of the supply (~1%) without normal use noticing it,
because both costs scale the same way with the multiplier.

**Closed in September 2026 · the rule that moves the permanence rate.** Indexing to occupancy looked
like the only way out compatible with I2, and it has a flaw that only appeared when measuring it
against a real case: once a price already rations the resource, occupancy stops saying whether that
price makes sense —measured on Ethereum, correlation −0.02 against a price that moved 650×—. A loop
that adjusts `r0` by looking at that same error inherits the blindness.

**The adopted rule does not look at occupancy: it makes the price discover itself, against a fixed
quota (§8.6 of the paper).** Each epoch a fixed quota of new bytes is admitted (`θ*/L_max`, a sum,
not a decision) and every admitted entry lives exactly `L_max` epochs —with no variable life to buy
with the price, which closes the arbitrage channel that brought down the first version of this
rule—, with the price coming out of a uniform clearing auction. Against the same shock that brought
down the previous law, occupancy does not move from target at any moment, without the spike of up to
1.48× that the occupancy-indexed law still let through. With few bidders the price is noisy —it
depends on the quota, not on how many people compete for it— and that is why it carries a bootstrap
reserve that switches itself off when the quota grows with the network.

---

## 10. Where to hit

What helps most is for you to attack here. They go in order of how much it would cost to find out
too late.

**A · Is the subset of verifiable work an economy or a niche?** All of the network's income depends
on there being requests with a cheap deterministic predicate (§5.2). Today most of the economic value
of a model is in outputs with no cheap predicate. **It is the most expensive hypothesis of the design
and it is the only one nobody ever went out to falsify.** Concrete question: would you pay for this,
against a centralized provider that answers in seconds, with finality in hours?

**B · Does the claim recruit operators or claimants?** The optimal claimant of §6.2 is a fleet of GPUs
rented for the duration of the window and returned when it closes. The design proves that the
hardware **existed**, not that it **stays** — and since issuance is decoupled from work, holding
tokens gives no reason to keep working. The claim is moreover **unrepeatable**.

**C · Is the reference task replayable?** If the instance is fixed and published in Geminis, the first
to solve it publishes the solution and the cost of the claim collapses to zero for everybody else. It
would be fixed by deriving the instance from the claimant's key — that is not written.

**D · At `t = 0` every defence is still denominated in a unit with no real price.** The fee is ad
valorem, the floor and the deposit are nominal, and the initial level of the rate now has a declared
number (§10.3) — but no number can have a real price before a market exists. What the declaration
buys is that filling the entire state costs a non-trivial fraction of the supply, not that it is
known whether that fraction is a lot of real money or a little.

**E · The dangerous scenario was success, not failure — and it now has a partial defence.** If the
currency appreciates, a fixed nominal price makes storage prohibitive in real terms and the state
empties out; the first version of the rule that was supposed to avoid that fell over. The adopted
rule (§8.6 of the paper) reads no price —that would still violate I2— but it takes the level from an
auction price instead of a loop over occupancy, and whoever bids does convert to real value without
the protocol having to know it. It is not a guarantee, it is a defence that did not exist before.

**F · The gauntlet installs consensus cryptography written by an anonymous bidder**, with *"nobody
broke a weakened instance in a fixed window"* as the only filter. Is that enough?

**G · The interpreter can never be patched.** Is it realistic to formally verify a complete
deterministic VM, and what happens the day a bug appears?

**H · The design cannot correct an economic error from day 1**, by construction, and a launch is
exactly the moment at which you find out what was not anticipated. Every other chain fixes that by
governance. Is that sustainable?

If any of this is already answered in the long document and is not visible here, that is the
summary's fault: ask for the complete section and I will send it.
