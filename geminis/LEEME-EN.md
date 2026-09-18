# Geminis · the implementation

The code lives here. The design is in `../Geminis Paper EN.md` (translation of
`../Geminis Paper.md`, which is the source of truth) and the build plan in `../ROADMAP-EN.md`.
**`§X.Y` always cites the paper.**

```
python verificar.py            # the invariants and the pass criteria
python verificar.py -v         # with the name of each criterion
python herramientas/demo.py    # the commutation running, on one screen
python herramientas/replay.py  # Phase 2, case 1: the difficulty bomb
python herramientas/replay_blobs.py   # Phase 2, case 2: the blobSchedule
python herramientas/replay_gas.py     # Phase 2, case 3: the gas limit
python herramientas/cola.py           # Phase 3: the challenge queue under attack
python herramientas/techo.py          # the VM step ceiling, derived (§10.3)

cd predicado/vm && cargo test --release   # the machine: 20 criteria (Phase 4)
```

The Ethereum series the replay uses are already in the repo (`herramientas/datos/`,
144 KB), so **everything runs offline**. To refresh them:
`python herramientas/traer_datos.py blobs|gas|dificultad` — public endpoint, no key.

No dependencies: only the Python 3.11+ standard library. `pytest` also runs the
tests if it is installed, but nothing needs it.

---

## Where this stands

| phase | what it is | status |
|---|---|---|
| **0 · executable invariants** | I1–I5 as predicates that run against any state and any transition | ✅ **running** |
| **1 · succession engine** | `protocolo/` + `sucesion/` over synthetic state, with the real commutation | ✅ **all six criteria pass** |
| **2 · replay harness** | the external evidence: difficulty bomb, blobs, gas limit | ✅ **closed, 3 of 3.** All three run and written up, with the data verified against the EIPs and `config.go`. The verdict is in `herramientas/RESULTADOS-EN.md` |
| **3 · ordering and settlement** | double spend by lock, double signature, the queue of §6.3 with a real `N` | ✅ **all three criteria pass**, with a correction to the paper: the queue needs **11** nodes and not 10 — and with the rule anybody would write, no number is enough. See `liquidacion/RESULTADOS-EN.md` |
| **4 · the VM and the predicate** | the deterministic machine, in Rust — reuses the harness from `test2-interprete` | ✅ **closed** (21 Aug). Six criteria passed; the seventh failed by 23× and out of it came the second ceiling |
| 5 · state with a cost | — | partially blocked by the rate rule (§10.3) |
| 6 · disposable devnet | — | pending |

**§3 ran for the first time on 19/8/2026.** Before that the paper's central mechanism
had never been executed. What is seen in the demo —three generations, the two classes
of transition **overlapping**, the state crossing over intact— is that.

> **Everything here is disposable by declaration** (ROADMAP §4). The parameters are
> toys: it is not yet known what space Geminis has to anticipate, so these numbers
> exist so that the mechanism runs, not to be inherited.

---

## The map: module ↔ paper

| module | what it implements |
|---|---|
| `protocolo/serializacion.py` | canonical encoding. **Floating point is forbidden from the very first file** — Phase 4 demands it before the gauntlet runs, and a condition on Geminis cannot be lifted afterwards |
| `protocolo/genesis.py` | block 0: the machine, the space of descendants, `Δ` per class, the finality window, `θ*`, `L_max`, **the formula of the step ceiling** —which is what gets frozen, not the number (§10.3)— and **the page ceiling**, which is a number and is not derived |
| `protocolo/generacion.py` | ruleset, generation tag, decoding that **fails closed** (I5) |
| `protocolo/linaje.py` | `H0_B = H( H0_A ‖ state_trigger ‖ params )` and its `Verify` (I4, §3) |
| `protocolo/invariantes.py` | **I1–I5 executable.** They are not comments (Phase 0). Includes the two ways of meeting I2 and the check of the derived canary |
| `sucesion/regla.py` | `TRANSITION_RULE` against the state (I2). Two rules, one for each way of meeting it: observable approach and demonstrated capability |
| `sucesion/distancia.py` | *how many blocks are left at the current rate* (I2), in integers |
| `sucesion/cronograma.py` | trigger → lock-in → activation, the hard ceiling of C7.4, and §3 *More than one transition in flight*: waiting per rule, activation order, successor computed at lock-in, and rejection |
| `sucesion/conmutador.py` | the commutation. It is short on purpose: if it had to move data, it would not be commuting |
| `estado/sintetico.py` | the minimal state of Phase 1 |
| `estado/cuentas.py` | **Phase 3**: queue per account, balance, committed. `disponible = saldo − comprometido` is what prevents the double spend |
| `liquidacion/oferta.py` | bilateral; directed vs. open (pull); the lock happens on publication, and that is what makes it exclusive |
| `liquidacion/doble_firma.py` | the nonce is derived from the index: signing twice publishes the private key |
| `liquidacion/impugnacion.py` | the queue of §6.3, with the three ways of choosing what to verify — and the one that collapses |
| `nodo/pod.py` | applies blocks, evaluates the rule, commutes, reorganizes. **It does not settle anything yet** |
| `pruebas/` | Phase 0 and the six criteria of Phase 1, one per class, with the text of the criterion in the docstring. `test_transiciones_en_vuelo.py` and `test_eventos_y_reorganizacion.py` pin down the two new subsections of §3; `test_i2_quien_elige_el_momento.py`, the reformulation of I2 |
| `herramientas/demo.py` | see the mechanism running, with the two classes **overlapping** — which is the uncomfortable case |
| `herramientas/techo.py` | the derivation of the step ceiling with the data from Test 2, and what is left as a decision |
| `predicado/aceptacion.py` | the predicate of §6.2: the vectors and **the two ceilings**. The machine is not here |
| `predicado/vm/` | **the machine, in Rust.** The only directory that changes language, and `LEEME-EN.md` says why |
| `predicado/CRITERIOS-EN.md` | the seven criteria of Phase 4, written before the first line and untouched afterwards |
| `predicado/RESULTADOS-EN.md` | what came out: six passed, one failed, and the three constants of Geminis it moved |
| `herramientas/traer_datos.py` | the only thing that touches the network: downloads the Ethereum series to `datos/*.csv`, with the provenance inside the file |
| `herramientas/replay.py` · `replay_blobs.py` · `replay_gas.py` · `historial.py` | **Phase 2**: the candidate rule against the six times Ethereum ran the difficulty bomb. Every datum carries **where it came from and what it was verified against**. The result is in `herramientas/RESULTADOS-EN.md` |

**What is deliberately not here:** token, split fees, offer, lock, challenge, VM,
permanence, p2p. None of that is Phase 1, and building it earlier would be building
the other half with no evidence (ROADMAP §0).

---

## What showed up while building, and what was done about it

None of these things is a bug in the code: they are holes in the design that are only
visible when the mechanism runs. **All three were closed and all three are in the
paper.**

### ✅ Solved and written into the paper · more than one transition in flight

Between lock-in and activation there are `Δ` blocks with the old rules still in force
and the new ones already committed. **It is not an edge case: it happens on the very
first run** with an accumulation rule. §3 now has the subsection *More than one
transition in flight*, and the mechanism is in `sucesion/cronograma.py` with its tests
in `pruebas/test_transiciones_en_vuelo.py`. Four decisions:

1. **a rule does not trigger again until its own activation**, not until its lock-in.
   Otherwise it measures a state that does not reflect the change it has itself just
   committed — a control loop with dead time, which is how Bitcoin Cash's EDA fell
   over in 2017;
2. **the wait is per rule, not global.** Blocking everything while a transition is in
   flight puts an urgent cryptographic migration behind a circulation one, and that
   empties out the reason why `Δ` is per class;
3. **activations go in lock-in order**, even when the `Δ`s differ. This appeared while
   writing the test for (2) and it is deeper than it looks: `params_nuevos` is a
   **complete point** of the space and not an increment, so activating generation 2
   before generation 1 would also apply the changes of generation 1, with generation
   2's notice. **Declared residue:** an urgent transition may have to wait out the
   remaining `Δ` of whichever one is ahead of it — bounded by the longest `Δ` in the
   space, and it does not compose;
4. **`params_nuevos` is computed at lock-in**, where `H0_B` was already computed. And
   lock-in **verifies before committing**: an irrevocable checkpoint with a point
   outside the space would leave the node unable to commute and would stop the chain.
   If it does not pass, there is an on-chain **rejection** — it is not trimmed to the
   edge and consensus is not stopped.

**A note on the Phase 1 criterion.** *"The notice between lock-in and activation is
exactly `Δ`"* still holds as written when there is a single transition in flight,
which is the case that criterion contemplated. With a queue, the notice is **more**
than `Δ`, never less — and that is not a relaxation of the written criterion: it is a
case the criterion did not contemplate, and its behaviour is declared above and tested
in `test_ningun_aviso_es_menor_que_su_delta`.

### ✅ Solved and written into the paper · the lock-in event is state, not an announcement

Lock-in is irrevocable, but the block that publishes it on-chain **is not final** —it
has only just been produced—, so a legitimate reorganization can replace it.

On writing it up, it became clear that the failure was not the one it looked like. It
is not that the integrator is left unable to read the notice: it is that a node that
published only *what has just matured* would end up with a lock-in in force and no
record in the state, and **its root would part company with that of a node that did
not reorganize**. That is a fork, and of the worst kind, because the two nodes agree
on everything else.

The rule, now in §3: **the event is emitted as a function of the height at which `N`
becomes final, not of the node having just found out.** It is a fact derived from the
chain —its two inputs are final and irrevocable—, so anyone who replays the blocks
produces it identically. And it lives **in the state** and not in the node's memory for
two different reasons: so that an integrator can read it with a header and a proof,
without replicating the chain; and because §5 —*the chain that did not commute has no
valid checkpoint*— is only verifiable by a third party if the checkpoint is in the
state the chain commits to.

It is tested by `pruebas/test_eventos_y_reorganizacion.py`, and it is tested in the
only way that fits a consensus problem: **two nodes, one that reorganized the lock-in
block and one that did not, have to arrive at the same root** — plus a third that
resyncs from scratch and arrives there too.

### ✅ Solved and written into the paper · I2, and who chooses the moment

The canary of §6.6 is not seen coming, and the old wording of I2 said that this is not
admissible. Which means that **the shop-window section of the paper did not meet one of
the five invariants.**

What became visible on looking closely is that the invariant was written wrong, and it
fails **in both directions**: it leaves out the canary, which has to be inside, and it
lets through a back door —*"when address X receives 1 wei"*—, which has monotone
progress and a publishable distance just like the canary. The shape of the curve does
not distinguish them: **both are steps.**

What does distinguish them is **who can produce the fact and what it costs them**, and
that is the reformulation that ended up in §4. Two ways of meeting I2, declared by each
rule and verified in every block:

- **by observable approach** — and then the rule *cannot trigger from rest*: if the
  previous block did not publish a distance, it was a step. It is the check that
  catches the back door;
- **by demonstrated capability** — there is no approach and there cannot be one, and it
  is admissible only if producing the fact requires exactly the capability the
  transition reacts to. It forces declaring which one, on-chain, and **not inventing a
  date**.

**And out of that came a condition on §6.6 that was not written down.** *"Geminis
publishes a weakened version of the primitive"* leaves open who generates it — and if
somebody generates it, that somebody **keeps the trapdoor** and can claim the canary
whenever they want. There *demonstrated capability* is *a secret somebody kept*, and the
canary stops being an alarm and becomes a gate with a cryptographic disguise. The
instance is **derived** from a public seed (`protocolo/genesis.py`), and the node
verifies it in every block: **a canary that cannot be rederived from its seed is not a
canary, it belongs to someone.**

**The limit, declared and tested as such:** no node can verify that the declared
capability is the true one. The same back door, declared by capability, passes — and
`test_declarada_por_capacidad_pasa_y_queda_a_la_vista` leaves that written down. What
the protocol does guarantee is that the reason is on-chain and in plain sight for the
audit of Geminis, which is where the space of rules is fixed (I1).

---

## How the tests are tested

A criterion that is only run against working code does not distinguish a predicate from
a `return`. `python herramientas/mutar.py` breaks the engine on purpose in twelve ways
the paper declares impossible and verifies that the suite catches them:

| fault introduced | criteria that fail |
|---|---|
| the commutation touches the state (breaks I3) | 30 |
| the successor is computed over Geminis and not over the committed ruleset | 24 |
| `Δ` is counted from the trigger and not from lock-in | 8 |
| activations do not respect lock-in order | 6 |
| a rule rearms at lock-in and not at activation (open loop) | 8 |
| the lock-in event is published on maturing and not by height | 6 |
| lock-in can be undone in a reorganization | 1 |
| an approach rule can trigger from rest | 1 |
| the capability trigger publishes an invented countdown | 1 |
| the canary instance is not verified against its seed | 1 |
| the replay counterfactual uses the wrong offset | 3 |
| a rejected rule retries against the same ancestor | 1 |

**When adding a mechanism, add its mutation.** It costs one entry in the list and buys
knowing that the new criterion tests something. If a mutation says `ANCLA PERDIDA`
(*anchor lost*), the code moved underneath it and it has to be rewritten — not ignored:
a mutation that does not apply is not testing anything.
