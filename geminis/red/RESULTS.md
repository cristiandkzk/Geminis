# `red/` — results

**English** · [Español](RESULTS.es.md)

**Run on 22/8/2026.** The criteria are in `CRITERIA.md`, written before the first line. It is not a
roadmap phase: it closes the gap between *"we finished the six phases"* and *"the network works"*.

| criterion | verdict |
|---|---|
| **R1** producing and validating are different paths | **passed** |
| **R2** syncing reaches the same state, bit for bit | **passed**, crossing a commutation |
| **R3** the lineage is verified against someone else's chain | **passed**, all three inputs weigh |
| **R4** a lied-about root is rejected | **passed** |
| **R5** the commutation is not read from the block | **passed** |
| **R6** two independent nodes produce the same chain | **passed**, hash by hash |

---

## What there was before: nothing

**`NodoPoD` only produced.** Every state transition in the project happened by construction, and
there was no function capable of saying that a block was wrong. A chain where nothing can be invalid
is not a chain — and the whole property §5 attributes to commutation, *whoever does not commute is
the one who deviates and that is verified with a hash*, presupposes that somebody verifies.

Now `validar_bloque` exists, and the difference from producing is exactly one thing: **the
comparison, and the ability to reject.**

## R5 · What the validator does not read from the block

It is the criterion that mattered and the one that carried risk. A malicious producer can activate
the new ruleset early, late, or not at all.

**The validator does not believe them.** It derives the activation height from the state it computed
itself, with the same rules. If the producer commuted one height early, the state the validator
computes is a different one, the root does not close and the block is rejected entirely.

Measured: a chain with a block removed before the commutation **is rejected**, because the trigger
falls at a different height. And a node that only saw empty blocks does not reach generation 2 no
matter how many blocks claiming it are sent.

> **That is where §3 stops resting on the good faith of whoever produces**, which is what the whole
> design exists for.

## R1 · A rejection cannot leave the node moved

If an invalid block left the validator half-applied, sending garbage would be enough to poison it. It
backs up before re-executing and restores if the comparison fails.

**And the backup is not a `deepcopy` of the node**, because it cannot be: the rules hold references
that do not copy. The containers that production mutates are copied by hand — which has a useful side
effect, namely **making it visible which ones they are**.

## R6 · Determinism between nodes

Two nodes started separately, with the same rules and transactions, produce **identical block hashes
at every height**, and each one validates the other's chain.

It is the parallel of C3 in Phase 4: the machine reproduced bit for bit across architectures and that
counted because it was run on two sides for real. Here it is the same with nodes.

---

## What this is NOT

**There is no transport.** There are no sockets, no peer discovery, no gossip: blocks are passed as
objects between two nodes in the same process. What is proved is **the separation between producing
and validating**, which is the protocol property; transport is engineering and does not move any
invariant.

Nor is there a network adversary —partitions, out-of-order messages, eclipse— nor any answer to why a
node would spend on verifying instead of trusting, which is a question for §6.

## Status

**268 criteria in Python, 20 in Rust, 34 mutations, all caught.**

```
cd geminis
python verificar.py red_sync    # the criteria of red/
python verificar.py             # all 268
python herramientas/mutar.py    # 34 mutations
```
