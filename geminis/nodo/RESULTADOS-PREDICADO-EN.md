# The predicate inside a node — results

**Run on 22/8/2026.** Criteria in `CRITERIOS-PREDICADO-EN.md`, written beforehand.

| criterion | verdict |
|---|---|
| **P1** the verdict enters the state and moves the root | **passed** |
| **P2** both ceilings are charged and each one rejects | **passed** |
| **P3** the ceiling is that of the generation in force | **passed** |
| **P4** a request that crosses a commutation | **found and decided** |
| **P5** what budget the predicates come out of | **measured** |

---

## What was missing: the plumbing

The machine of §6.6 was measured on two architectures, with seven vectors that reproduce bit for bit
and two calibrated ceilings. `predicado/aceptacion.py` modelled the predicate. **And no node ever ran
one**: the ceilings were measured standalone and the verdict was made canonical *to enter the block
hash* without entering any.

Now the verdict goes into `eventos`, which was already the canonical list where lock-ins are
published. **No new field was needed**, and that says something: a verdict is a published fact, of
the same class as a lock-in.

### The property that buys

**The verdict is computed by the node, not carried by the transaction.** If it came in the
transaction, whoever sends it would choose the result. By computing it:

- two nodes with the same machine arrive at the same fact and the same root;
- **whoever arrives at another produces a different root and their block is rejected**
  (`red/sync.py`).

Measured: a validator that did not produce the block reproduces it and arrives at the same
fingerprint. That is where the determinism of the machine —which Phase 4 measured across
architectures— stops being a property of the interpreter and becomes a property of the chain.

---

## P4 · A request that crosses a commutation

**Found with the units audit in hand, which is what it was done for.**

The ceiling of §6.6 is derived from `tx_por_bloque`, `tiempo_bloque_ms` and `paginas_vm` — all three
internal parameters. That is, **a commutation moves it, and that is on purpose**.

But a work request of §6.2 is published and accepted later. If there is a commutation in between,
**the predicate that was admissible may stop being so without anyone touching it.** It is exactly the
form of B3: the quantity did not change, what it means changed.

### The chosen way out

**The request carries the generation in which it was published and is judged with the rules of the
time.** A request evaluated against another ruleset raises `GeneracionEquivocada` instead of silently
giving a different result.

The opposite —judging it with the ceiling in force— would make accepting the same work give a
different answer depending on when the response arrives. The node keeps the history of rulesets, so
recovering the one from then is a read.

> **And this opens a question that does not belong to this piece:** a request published under
> generation 1 could stay alive indefinitely if nobody takes it. That it be judged with old rules
> forever is coherent but is declared nowhere, and §6.2 does not talk about expiry. It is a decision,
> not a bug.

---

## P5 · What budget they come out of

`f*` is the fraction of the node **for verifying signatures**, and §6.2 asks for the predicate to be
*cheap to run on the light layer* without saying charged to what.

| | steps per block |
|---|---:|
| of the whole block | 420,000,000 |
| for signatures (`f*` = 25%) | 105,000,000 |
| **outside `f*`** | **315,000,000** |
| predicates the size of the ceiling that fit in there | **45** |

That 75% is shared by the predicate, the network, the settlement of §6.5 and —since Phase 6— the
eviction cycle, which takes 3%. **The sum does not choose a new fraction**: it writes down what they
compete against.

---

## What this is not

**The machine was not reimplemented in Python.** The node invokes it through an interface; for the
tests there is a double that **returns canonical verdicts**, not simplified ones. What is tested here
is the plumbing —that the node charges both ceilings and publishes the fact—, not the machine, which
is tested in `predicado/vm/tests/criterios.rs` and on seven vectors over two architectures.

And there is no work market: who publishes requests and who takes them is §6.2 and §6.5.

## Status

**302 criteria in Python, 20 in Rust, 39 mutations, all caught.**
