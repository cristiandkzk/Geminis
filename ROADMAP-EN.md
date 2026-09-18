# Roadmap — Geminis

**For whoever joins the project.** This says where the project stands, what the words you are going
to see in the file names mean, and in what order things get built. Read it before opening any code.

> **Citation convention.** `§X.Y` always refers to **`Geminis Paper EN.md`**, the translation of
> `Geminis Paper.md`, which is the source of truth. `README-EN.md` is a summary with **its own
> numbering** —it has 10 sections and the paper has 12—, so the numbers do not line up between the
> two documents. If a `§` does not add up, you are looking at the wrong file.

---

## 0. Where the project stands

**There is a complete design and there is not a line of code.** The paper has ~19,500 words, four
falsification tests run and five measurements with reproducible scripts. None of that is a protocol
running: **§3 —the central mechanism— never executed even once.**

And the project is split into two halves with **different classes of evidence**, which is the first
thing to understand so as not to build the wrong thing:

| half | what it is | evidence |
|---|---|---|
| **parameter succession** (§3 + I2 over a finite space) | the chain changes its own internal parameters with no vote | **customer found outside**: Ethereum recalibrates `blobSchedule` by hand (EIP-7892), the gas limit by schedule (EIP-8261), the difficulty bomb was delayed by fork six times |
| **the currency + the interpreter + §6.6** | its own economy, a deterministic VM, chainable cryptographic evolution | **own evidence only**: it survived every attack run against it, and every one of them was run by the person who wrote the design |

> **The top half gets built first, and it is not a preference: it is where the evidence is.** The
> bottom half pays the most expensive boundaries of §10.1 and still has no case found outside.

**What this roadmap deliberately does not cover:** the launch of block 0. It depends on two things
that are not code —finding a buyer for the verifiable work of §6.2, and closing the two open
problems of §10.3— and the claim is **unrepeatable**, so launching early spends the only
distribution event there is.

---

## 1. Glossary: the words you need before opening a file

They are in the order in which they are needed, not alphabetical.

**Generation.** A version of the ruleset. The chain does not branch into generations: **it is a
single chain that changes rules**. Generation 3 is the same chain as generation 1, with other
parameters.

**Ruleset.** The set of parameters in force in a generation: issuance, fees, block size, timings,
formats. It is *data*, not code — that is the whole difference from a hard fork.

**Commutation.** The act of changing ruleset. **The same process, with the same state in memory,
executing different rules from one block onward.** There is no restart, no migration, no snapshot,
no bridge. If your implementation needs to restart the node, it is not commutation: it is a fork by
another name.

**`TRANSITION_RULE`.** The trigger condition. It is computed **only from the state of the chain**
(I2). It does not read prices, does not read oracles, does not read votes, does not read anybody's
clock.

**The three times.** Never confuse them, and there are three and not two:

1. **Trigger** — `TRANSITION_RULE` returns TRUE at block `N`. **It commits nothing**: it is advisory
   and a reorganization undoes it.
2. **Lock-in** — when `N` is final, the trigger becomes **irrevocable** and the complete new ruleset
   is emitted on-chain with the activation height. Waiting for finality is not ceremony: `H0_B`
   commits the state that triggered, and committing it earlier would leave the checkpoint pointing
   at a state a reorganization can take out of the chain.
3. **Activation** — `Δ` blocks **after lock-in**, not after the trigger. That way the notice to the
   integrator is exactly `Δ` and does not depend on how long finality took.

**`Δ` (delta).** The notice window, fixed in Geminis **per transition class**. A circulation
transition tolerates a long `Δ`; an urgent cryptographic migration needs a short `Δ`.

**Lineage / `H0_B`.** `H0_B = H( H0_A ‖ state_trigger ‖ params_nuevos )`. It is not the genesis of a
new chain: it is a **generational checkpoint marker** within the same chain. It makes the lineage
verifiable with one hash from any generation backwards. Geminis A does not know B's hash —it
cannot— but it knows how it will be computed.

**The five invariants (I1–I5).** The hard frame. Each one eliminates a way of reintroducing the
human into the loop. **In this repo they are not documentation: they are executable assertions that
every phase has to keep passing** (see Phase 0).

- **I1** — the interpreter lives in Geminis and **never changes**. A transition selects a point of a
  space the node already knows how to execute; it does not introduce node code.
- **I2** — the trigger is computed only from the state, **and nobody chooses the moment**.
  Computable is not enough: *"address X received 1 wei"* is computed from the state and it is a gate
  with an owner. It is met in two ways and every rule declares which one it is in: by **observable
  approach** —it publishes *how many blocks are left at the current rate* and cannot trigger from
  rest— or by **demonstrated capability** —there is no approach and there cannot be one, and
  producing the fact requires exactly the capability the transition reacts to: the canary of §6.6—.
  *(Reformulated on 19/8/2026: the previous wording left out the canary itself. See C9–C11.)*
- **I3** — the state crosses the transition **intact**. No migration, no reassignment.
- **I4** — every generation commits to its ancestor.
- **I5** — transitions are **additive in the interface**. Formats can be added, never removed, and
  every object carries a generation tag from block 0.

**PoD node.** It verifies and settles, and charges a fee when two contracts interact. It runs on any
hardware —verification reproduces bit for bit on x86-64, ARM64 and a phone—. **It is the consensus
layer.**

**Compute node.** GPU and RAM, it hosts the models that do the requested work. **It does not take
part in consensus.** Its income is the payment for the request it executed.

**Acceptance predicate.** Every work request carries one: deterministic and cheap to run on the
light layer. Inference is **not verified** — what is verified is that the output satisfies the
predicate. Whatever cannot be expressed that way, the network cannot settle.

**The predicate's two ceilings.** Besides passing the vectors, it has to verify below a cap on
**executed steps** and touching fewer than a cap of **4 KiB pages** (never wall-clock time — the
clock would be an oracle). **They are security conditions, not performance ones:** they are what
prevents a challenge from existing that is more expensive to verify than to create.

The step one **is not a chosen number: it is a sum** —`f* × tiempo_de_bloque × R_declarado /
tx_por_bloque`—, and what Geminis freezes is the formula, not the value. *(Closed on 20/8/2026; it
was the first open problem of §10.3.)*

The page one **is also derived**, since 21/8/2026: it is a ruleset parameter —96 pages of 4 KiB in
Geminis— and what Geminis freezes is the **curve** of rate against memory. **Phase 4 added it and it
was not in the design:** a step ceiling alone assumes that one step is worth one step, and the worst
instruction mix runs 23× slower than the real workload. It is not fixed by weighting instructions
—`lw` costs the same as `addi` with the data in cache and 23× more without it, **it is the same
opcode**—, so what has to be counted is the only thing visible while it runs: the distinct pages it
touches.

**And that was the most important correction of the phase, because it touched the core:** a derived
ceiling *raises the price* —an expensive primitive gets in by lowering `tx_por_bloque`— and a
constant one **can only exclude**. The three primitives of the ML-DSA family touch 26, 40 and 65
pages, so the first number chosen (48) left the third one out forever. **In this design, a number
that has to be chosen is usually a sum that has yet to be written** — it happened twice with the
same ceiling. *(21/8/2026, `geminis/predicado/RESULTADOS-EN.md`.)*

**Compute challenge (§6.7).** A third class of work, different from the request of §6.5: instead of
being assigned to a single node before computing, several nodes compute in parallel and only one
gets paid per round. The waste of those who lose is what makes the cost real and unfalsifiable —the
same argument as Bitcoin's subsidy, with inference bounded by the protocol instead of hashing as the
scarce resource—. It exists so that a node with a better LLM does not systematically earn more than
one with a worse LLM: the LLM chooses what to attempt, the protocol sets how many times and in how
much time.

**Rotated-domain structural filter (§6.7).** The clause of the challenge predicate that rules out
generating random bytes instead of using an LLM: cheap, deterministic, it runs on the light layer
like any predicate of §6.2. Its domain —schema, language, vocabulary— is derived from the round's
seed and changes in every round, so that a narrow model cannot be trained to farm a fixed exam (the
model-side equivalent of the capital moat §6.1 avoids in hardware).

**Round and window `T` (§6.7.1).** The challenge is resolved in rounds of fixed duration in blocks —
never in wall-clock time, which would be an oracle—. Every valid submission before the close enters
an even lottery, so arriving first within the round buys nothing: it is the same play §6.3 uses
against capital in the challenge queue, applied here against speed. The duration `T` is drawn within
a range `[X, Y]` with the seed of the block that opens the round, so that nobody can tune their
pipeline to a fixed and known number. `X` and `Y` remain an open problem in §10.3: the formula is
closed, the two numbers are not yet.

**Challenge window.** How finality happens: an interaction becomes firm when the window passes
without anyone presenting proof of conflict. There is no quorum and no validator set. What prevents
it from saturating is an asymmetry: **filling is serial —you have to get into a block— and draining
is parallel —all PoD nodes do it at once—.**

**Lock.** Committing funds into a contract takes them out of the available balance. It is what
eliminates contention: they cannot be committed twice.

**Directed vs. open offer.** Every transfer is **bilateral** (Alice offers, Bob accepts). An
ordinary transfer names the receiver; **a work request names nobody** and is taken by whichever node
can fulfil it. It is *pull*, not *push*: **nobody assigns requests.**

**Epoch.** The unit of time of the permanence charge (§8.5). Not to be confused with generation,
which runs in years.

**Permanence / eviction.** Every state entry pays to keep existing: a **floor** that is burned at
creation, plus a **deposit** that is consumed by being burned, linear in size × time. When it runs
out, the entry is **evicted** —it leaves the active set, it is not destroyed— and it is revived with
a proof. **Holding a balance stops being free**, and that includes native token accounts.

**Claim.** The day-1 distribution: claiming tokens **is paid for by demonstrating the capability
being claimed**. It happens only once, at block 0, and after that no action creates units.

---

## 2. If you come from Bitcoin or Ethereum, this is different in five points

It is the section that saves the most time, because these are five assumptions you arrive with and
here they do not hold.

1. **There is no proof of work in consensus.** There is no mining, no difficulty, no block nonce, no
   hashrate. The only computation with an external cost appears **once**, in the block 0 claim, and
   it is not hashing but the reference task. **If you write a `proof_of_work.py` inside
   `consenso/`, you are building a different protocol.**
2. **There is no global order.** Each account carries its own sequence. Two interactions that do not
   share collateral **have no relative order**, and that is different from having it undefined. The
   "longest chain" is not the criterion for anything.
3. **Finality is by challenge window**, not by quorum and not by confirmations. It is measured in
   minutes or hours, and it is a declared boundary, not a defect to be optimized.
4. **There is no unilateral sending.** You cannot pay someone who is offline. The receiver signs to
   accept, and that is why *"wait for finality"* stops being a discipline and becomes structure:
   there is no transaction until they signed.
5. **The fork is not resolved, it is prevented by construction.** The standard client commutes on
   its own, so **not commuting requires actively modifying the software**. Whoever stays on the old
   rules does not preserve the original chain: they deviate from Geminis, and that is verified with
   a hash. No "pick the good branch" logic is needed.

---

## 3. The structure

**Why the generic proposal is no good.** The one that circulates in the tutorials
(`core/ consensus/ network/ api/` with PoW and a mempool) models a different protocol: it puts
mining at the centre, fork resolution in `blockchain.py` and has no place for **the one thing that
makes this project what it is** — the succession. A dev who opens `consensus/proof_of_work.py` has
already misunderstood the system.

The structure follows the pieces of the paper, so that the document ↔ code mapping is direct:

```
geminis/
├── protocolo/            # what Geminis freezes and never changes (I1)
│   ├── genesis.py          # block 0: initial ruleset, space of descendants,
│   │                       #   Δ per transition class, θ*, L_max
│   ├── invariantes.py      # I1–I5 as executable assertions — not comments
│   ├── generacion.py       # generation tag on every object (I5), ruleset in force
│   └── linaje.py           # H0_B = H(H0_A ‖ state_trigger ‖ params) and its Verify (I4)
│
├── sucesion/             # §3 — the heart, and the first thing built
│   ├── regla.py            # TRANSITION_RULE evaluated against the state (I2)
│   ├── distancia.py        # "how many blocks are left at the current rate" — I2 demands it
│   ├── cronograma.py       # trigger → lock-in (waits for finality) → activation (+Δ)
│   └── conmutador.py       # the hot ruleset change: same process, same state
│
├── estado/               # I3: what crosses over intact
│   ├── cuentas.py          # queue per account, index, balance
│   ├── entradas.py         # every entry pays permanence: objects and balances alike
│   ├── arbol.py            # tree with cut d; the binding cap is updating, not proving
│   ├── permanencia.py      # floor, deposit, rate, L_max, epoch
│   └── desalojo.py         # append-only accumulator and reactivation with a proof
│
├── liquidacion/          # §6.3–6.5: how an interaction is closed
│   ├── oferta.py           # bilateral; directed vs. open (pull); declared timeout
│   ├── lock.py             # committing takes it out of available — eliminates contention
│   ├── impugnacion.py      # window, flat bond, arrival order, parallel draining
│   └── doble_firma.py      # nonce = f(index): signing twice publishes the private key
│
├── predicado/            # §6.2 — what the network can pay for
│   ├── aceptacion.py       # vectors + step ceiling
│   └── vm/                 # the deterministic machine. Rust, not Python — see §5
│
├── nodo/
│   ├── pod.py              # verifies, settles, charges a fee. It is the consensus layer
│   └── computo.py          # accepts requests, executes, delivers. Outside consensus
│
├── red/
│   ├── p2p.py              # transport between nodes — DOES NOT EXIST, and it is engineering
│   └── sync.py             # ✅ validation and synchronization: the first node that does not produce
│
├── api/
│   └── server.py           # HTTP: query state, publish requests, see the distance to the trigger
│
└── herramientas/
    └── replay.py           # the harness against Ethereum's real history (Phase 2)
```

**Two decisions worth knowing are decisions:**

- **The module names are in Spanish** because each one maps to a concept defined in a paper in
  Spanish, and the onboarding cost here is the doc ↔ code mapping, not the language. **If at some
  point this opens to the public, it is worth translating them** — and the sooner, the cheaper.
- **`api/` is a development convenience, not a piece of the protocol.** A real node speaks p2p. Do
  not put protocol logic in there.

---

## 4. The principle that governs every phase

> **Every phase declares its pass and fail criteria BEFORE running it.**

It is not bureaucracy, it is the most expensive lesson already paid for in this project: the first
control law for the permanence rate looked stable and absorbed a 3× shock. What brought it down was
not an attack — it was **correcting a detail of the model it had been tested with**. A criterion
written after seeing the result accommodates itself to the result.

And its corollary, which applies to everything that follows:

> **A devnet with free tokens answers software questions, not economic ones.** With worthless tokens
> there is no income, there is no hoarding, the elasticity of storage demand is not measured and the
> antispam is not tested. Worse: manufactured activity is indistinguishable from real demand —and
> there, on top of that, it is free—. **Everything built here is disposable by declaration**, and it
> has to be rewritten once it is known what parameter space Geminis has to anticipate.

---

## 5. The phases

### Phase 0 · The scaffolding and the executable invariants

**Goal.** That I1–I5 stop being prose. Before the first line of mechanism.

`protocolo/invariantes.py` is built with the five as predicates that run against any state and any
transition, plus the test harness and CI that execute them on every commit.

**Pass:** every later phase keeps passing them with no exceptions and no *skips*. The day one has to
be marked as an exception, you stop and discuss the design, not the test.

### Phase 1 · The succession engine

**It is the half with a customer found, it needs no token and no VM and no economy, and it depends
on neither of the two open problems of §10.3.**

`protocolo/` and `sucesion/` are built complete, over a minimal synthetic state. A toy chain with
toy parameters, but **the real commutation**.

**Pass —written before running—:**

- a chain with synthetic state commutes and **the state crosses over bit for bit identical** (I3);
- `Verify(H0_B, H0_A, state_trigger, params)` returns TRUE for the whole chain of generations, and
  fails if any of the three inputs is altered (I4);
- a reorganization **before** lock-in undoes the trigger; **afterwards**, it does not undo it;
- the notice between lock-in and activation is exactly `Δ`, **independent** of how long finality
  took;
- the distance to the trigger is queryable and **monotone** in the approach (I2);
- **the node does not restart.** If a restart is needed, the phase is not passed.

### Phase 2 · The replay harness — the only external evidence that code produces

**Goal.** To answer with third-party data: *if `blobSchedule` had been a `TRANSITION_RULE` written in
advance, what would have happened?*

The real history is reproduced: Ethereum's blob parameters, the gas limit of EIP-8261 and the
difficulty bomb with its six delays. The deterministic rule is run against the historical state and
compared with what the humans actually decided.

**Pass:** for each case, either the rule reproduces the human decision, or it is written down
**exactly where it differs and whether that difference was better or worse**. A tie counts as a
pass; what does not count is being unable to explain the difference.

> **This phase is worth the most per unit of work in the whole roadmap**, because it is the only one
> that produces evidence the author of the design did not write. It is also the one that can be
> shown outside without asking anyone to believe anything.

### Phase 3 · Ordering and settlement

`estado/cuentas.py`, all of `liquidacion/` and `nodo/pod.py` are built. No economy yet: fees in
abstract units.

**Pass:**

- double spend impossible thanks to the lock, with no global order;
- **the double signature publishes the private key** and anyone can sweep the balance — verified
  with two signatures and one subtraction;
- under adversarial load with `N` nodes, the queue **drains faster than it fills**, and the measured
  margin is compared against the ten PoD nodes §6.3 predicts. If a hundred are needed, the paper's
  prediction is wrong and that has to be said.

### Phase 4 · The VM and the predicate — ✅ closed

**The language changes here, and it is on purpose.** The deterministic machine **is not written in
Python**: the six-engine harness of `test2-interprete/telefono` already exists in Rust, with
`steps_per_verify` measured identical across architectures. It gets reused.

**Pass:**

- the interpreter's budget fits **under real block load**, not in an isolated benchmark;
- floating point is forbidden or canonicalized **before the gauntlet runs for the first time** — it
  is a condition on Geminis and it cannot be lifted afterwards;
- the step count reproduces bit for bit between x86-64 and ARM64.

**Run on 20/8/2026, with six criteria passed and the seventh failed** —and the failed one is what
made the phase worth it—. Four criteria were added to the roadmap's three on reading the interpreter
that was going to be reused: the Test 2 harness runs a trusted guest and this runs an adversary's
program. Adding criteria is allowed; softening them is not.

> **The finding:** the step ceiling promised a budget it did not meet **by 23×**, because a step is
> not worth a step. Out of that came a second ceiling on pages touched, `R_declarado` from 300 to
> 70 M steps/s, and the initial capacity from 67 to 15 tx per block. Plus two amplification holes in
> the loader that no correctness test would have found —what found them was a sweep taking minutes—.
> All of it in `geminis/predicado/RESULTADOS-EN.md`.

**Closed on 21/8/2026**, with all seven criteria resolved: the vectors reproduce bit for bit between
x86-64 and aarch64, and C1 is measured on the reference hardware (354 ms out of 1,500, margin
4.24×).

> **And it left an open problem the paper did not have:** which hardware is the worst case. The
> design assumes the light layer is the binding one, and measured, that is false for adversarial
> memory patterns. **Two machines are not enough to fix a hardware floor** — closing it needs more
> machines, not more analysis.

### Phase 5 · State with a cost — ✅ run

`estado/permanencia.py`, `arbol.py` and `desalojo.py` are built.

**Pass:** the create → pay → exhaust → evict → reactivate cycle closes completely; the accumulator
stays on the order of hundreds of bytes **in total** and not per object; and what it really costs to
keep a reactivation proof up to date is measured, which is the archive dependency §10.2 declares and
cannot guarantee.

**Run on 21/8/2026**, with eight criteria passed and one failed — and the one that failed did so
**against the paper**: §8.5 claimed the floor came out at sixteen hours of storage, and the sum,
once written, gives another order. Development in `geminis/estado/RESULTADOS-EN.md`.

**Still blocked where it was:** the rule that moves the rate is not chosen and there is nothing to
calibrate it with. What did get closed is **why that is not a sum that has yet to be written but a
boundary** —the ceiling had both its sides physical and the rate has one monetary side, and no sum
crosses that without reading a price—. Out of that came denominating the floor in storage epochs,
whereby **the open problem became one number instead of two**.

### Phase 6 · The disposable devnet — ✅ run

Only here does everything come together and a token appear — **with the warning of section 4 put in
writing and with a reset date declared in advance.**

**What it is good for:** closing the four mechanism questions nothing else answers —the real
commutation under load, the queue with a real `N`, the budget under real blocks, the eviction
cycle—.

**What it is not good for, and this must not be confused:** knowing whether anyone leaves the GPU
switched on, what the elasticity of storage demand is, whether the currency gets hoarded, or whether
the antispam holds. **That needs real money or external review, and it goes down another track.**

**Run on 21/8/2026, bounded to two of the four questions** — the queue with a real `N` was answered
by Phase 3 and the budget under real blocks by Phase 4, and running again what has already been
measured adds no evidence but does add the temptation to stare at the number until it comes out
right.

> **The finding (B3):** the permanence deposit was bought in byte-**epochs**, the epoch is counted in
> blocks and block time is an internal parameter — so a commutation that moved it made **an
> already-paid deposit buy twice the storage**. I3 was met: the bytes crossed over identical. What
> changed was what they were worth, and **none of the five invariants looks at that**. Corrected by
> denominating in declared byte-seconds. Development in `geminis/devnet/RESULTADOS-EN.md`.

---

## 6. What runs in parallel and is not code

Two things that decide more than any phase above, and that if they wait for the code to be ready,
arrive late:

- **Looking for a buyer for the verifiable work of §6.2.** It is the most expensive hypothesis of
  the design and it is the only one nobody ever went out to falsify: the four tests measure the
  succession half and none of them asks whether anyone would buy this. **It needs no protocol** — a
  manual broker with real payment is enough. Ten real transactions say more than ten thousand from a
  devnet.
- **External adversarial review.** The design survived only the attacks of whoever wrote it. It
  costs little and comes back fast, and `README-EN.md` is already set up for it: it ends in a list of
  where to hit first.
