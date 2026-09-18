# The predicate inside a node — pass criteria

**English** · [Español](CRITERIA-PREDICATE.es.md)

**Written on 22/8/2026, before the first line.**

## The gap

`predicado/aceptacion.py` exists. The machine of §6.6 exists, in Rust, measured on two architectures
and with seven vectors that reproduce bit for bit. **And no node ever ran a predicate.**

The two ceilings —steps and pages— were measured standalone in Phase 4 and were never applied inside
a chain. The verdict was made canonical *so that it would enter the block hash* and it never entered
any. All the plumbing between *"the machine gives a verdict"* and *"that verdict is a fact of the
state"* does not exist.

---

## P1 · A verdict enters the state and changes the root

**Passed if** a transaction that evaluates a predicate leaves the verdict in the state, and the
block's root changes with it. **Failed if** the verdict stays outside the state — because then two
nodes could disagree about the result of a challenge without the chain noticing.

## P2 · Both ceilings are charged, and exceeding either one rejects

**Passed if** a predicate that goes over on steps and another that goes over on pages **are both
rejected**, with different verdicts and both deterministic. It is what Phase 4 measured standalone.

## P3 · The ceiling applied is that of the generation in force

`techo_vigente` is derived from the ruleset. **Passed if** the node uses the ceiling of the
generation in which the block runs, not a stored one.

## P4 · What happens to a predicate that crosses a commutation *(the one that can fail)*

**Here is the risk, and it comes straight from the units audit.**

The step ceiling is derived from `tx_por_bloque`, `tiempo_bloque_ms` and `paginas_vm` — all three
internal parameters. That is, **a commutation changes the ceiling**, and that is on purpose (§6.6).

But a work request of §6.2 is published with its predicate and **accepted later**. If there is a
commutation between the two, the predicate that was admissible may stop being so — or the other way
round. **Nobody touched the request and what it is worth changed**: it is exactly the form B3 found
with the permanence deposit, and the one the units audit says to look for in every stored quantity.

**Passed if** the request carries which generation it belongs to and the node can decide
unambiguously. **Failed if** the result depends on when it is evaluated without anything declaring it
— and in that case a choice has to be made: either the predicate is judged with the ceiling of when
it was published, or the request expires at the commutation, or the boundary is declared.

## P5 · The cost of running predicates comes out of some declared budget

`f*` is the fraction of the node **for verifying signatures**; §6.2 asks for the predicate to be
*cheap to run on the light layer* without saying charged to what.

**Passed if the number gets written down**: how many predicates per block fit and what budget they
come out of. No threshold — what fails is being unable to say it.

---

## What this is NOT

- **The machine is not reimplemented in Python.** The node invokes it; that it is Rust is the I1
  decision and it is not touched. Where running the real binary is expensive for a test, a double
  **that returns canonical verdicts** is used, and which is which is declared.
- **There is no work market.** Who publishes requests and who takes them is §6.2 and §6.5, and here
  only the evaluation matters.
