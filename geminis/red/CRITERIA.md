# `red/` — pass criteria

**English** · [Español](CRITERIA.es.md)

**Written on 22/8/2026, before the first line.** It is not a roadmap phase: the roadmap lists `red/`
in its structure (§3) and did not include it in any of the six phases. One can truthfully say *"we
finished the phases"* and be far from *"the network works"*, and this closes that distance.

## What you need to know before starting

**Until today there was never a second node.** Everything that says *"N nodes"* —the queue draining
in parallel, the eleven nodes of Phase 3, that everyone sees the same commutation— is modelled as
objects in one process.

And there is something more specific, verified before writing this:

> **There is no validation path at all.** `NodoPoD` only produces. Every state transition in the
> project happened **by construction, never by verification** — and a chain where nothing can be
> invalid is not a chain, it is a program keeping a list.

That is the asymmetry these criteria attack.

---

## R1 · Producing and validating are different paths

**Passed if** there is a function that receives a block this node **did not produce**, recomputes
the state from its transactions and **compares** against the root the block declares. And if they
differ, rejects it.

**Failed if** validating is producing again and trusting. The difference is exactly the comparison: a
validator that cannot say *"no"* is not validating.

---

## R2 · Syncing from scratch reaches the same state, bit for bit

**Passed if** an empty node that receives the entire chain ends up with **the same state
fingerprint** as the one that produced it, and that includes **crossing a commutation**: whoever
syncs has to activate the new ruleset at the same height without anyone telling them to.

---

## R3 · The lineage is verified against someone else's chain (I4)

Until now `verificar_linaje` ran over checkpoints the same process had created.

**Passed if** whoever syncs verifies the chain of `H0_B` from Geminis over checkpoints they
received, and **fails if any of the three inputs is altered** —`H0_A`, `state_trigger` or the
parameters—.

---

## R4 · A lied-about root is rejected

**Passed if** a block with `raiz_estado` altered by a single byte is rejected on validation.

It is the simplest case and that is why it matters most: if this one does not work, none of the
others means anything.

---

## R5 · A commutation at the wrong height is rejected *(the one that can fail)*

**Here is the real risk.** A malicious producer can activate the new ruleset early, or late, or not
activate it. Whoever validates **cannot read from the block when to commute**: they have to derive it
from the state they computed themselves, exactly like the producer.

**Passed if** a chain in which the commutation happens at a height different from the one the
validator derives is rejected. **Failed if** the validator takes the height from the producer —
because then the whole of §3 rests on the good faith of whoever produces, and the whole design exists
in order not to rest on that.

---

## R6 · Two independent nodes produce the same chain

**Passed if** two nodes started separately, with the same rules and the same transactions, produce
**identical block hashes** at every height.

It is determinism **between nodes** and not within one, which is the only thing proved so far. The
parallel is C3 in Phase 4: the machine reproduced bit for bit across architectures, and that counted
because it was run on two sides for real.

---

## What this does NOT answer

- **There is no transport.** There are no sockets, no peer discovery, no gossip. Blocks are passed as
  objects between two nodes in the same process. What is proved is **the separation between producing
  and validating**, which is the protocol property; transport is engineering and does not change any
  invariant.
- **There is no network adversary** — partitions, out-of-order messages, eclipse.
- **There is no incentive to validate.** Why a node would spend on verifying instead of trusting is a
  question for §6 and is not touched here.
