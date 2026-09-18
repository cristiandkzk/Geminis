# `estado/arbol.py` — pass criteria

**English** · [Español](CRITERIA-TREE.es.md)

**Written on 22/8/2026, before the first line.** The roadmap lists `arbol.py` in its structure and no
phase built it: *"tree with cut `d`; the binding cap is updating, not proving"*.

## Why it matters now and not before

Phase 5 derived the floor of §8.5 using `hashes_por_actualizacion = 26`, and that 26 came out of a
sum —the height of the tree over the disk budget— **without the tree existing**.

And the tree's design was already decided and measured (`presupuesto-nodo/RESULTS.md`, 18/8/2026):
not all internal nodes are stored, the levels **above a cut `d`** are stored and the subtree of `2^d`
leaves is recomputed. With `d=6` the tree costs ~1 B per entry instead of 32, and the price is eight
points of the hash budget.

> **The suspicion to be verified: 26 is the height, that is, the cost of updating when everything is
> stored — `d=1`, the row the design discarded for costing 32 B per entry.** If so, the floor is
> computed with the tree that is not used.

---

## T1 · The tree works

**Passed if** inserting, updating and proving close: a leaf's proof verifies against the root, and
stops verifying if the leaf, the path or the root is altered.

## T2 · Proving is cheap and updating is what bites

It is the sentence the roadmap uses to justify the design, and it was never measured.

**Passed if the number gets written down**: hashes per proof and hashes per update, as a function of
`d`. No threshold — what fails is being unable to measure it.

## T3 · The already measured table reproduces

`presupuesto-nodo/RESULTS.md` claims **32 B per entry with `d=1`, 1.0 B with `d=6` and 0.125 B
with `d=9`**.

**Passed if** the built tree gives those bytes per entry. **Failed if** not —and then it has to be
seen which of the two is wrong, because the budget of §10.1 came out of that table.

> That measurement is **closed**: if it differs, it is annotated beside it, not rewritten.

## T4 · Which `d` the 26 of Phase 5 corresponds to *(the one that can fail)*

**Passed if** `hashes_por_actualizacion = 26` corresponds to the `d` the design chose.

**Failed if** it corresponds to another — and in that case the floor of §8.5 has to be redone with
the number of the tree that is really used, and it has to be seen whether it still stays below the
maximum deposit. With the signature inside the cycle the floor already went over `L_max` once, so
there is no margin for assuming that a factor of three changes nothing.

---

## What this does NOT answer

- **Which `d` to choose.** It is an implementation decision with a price measured in both currencies
  —disk and hashing—, and the roadmap leaves it as such.
- **Nothing about the tree under concurrent load.** There is no concurrency anywhere in the project.
