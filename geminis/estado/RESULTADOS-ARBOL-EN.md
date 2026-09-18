# `estado/arbol.py` — results

**Run on 22/8/2026.** Criteria in `CRITERIOS-ARBOL-EN.md`, written beforehand.

| criterion | verdict |
|---|---|
| **T1** the tree works | **passed** |
| **T2** proving is cheap and updating is what bites | **measured** |
| **T3** the already measured table reproduces | **passed**, exactly |
| **T4** which `d` the 26 of Phase 5 corresponds to | **FAILED** |

---

## T4 · The 26 was the tree the design discarded

Phase 5 derived the floor of §8.5 with `hashes_por_actualizacion = 26`, taken from a sum —the height
of the tree over the disk budget— **without the tree existing**.

Built, updating costs `2^d − 1 + (H − d)`: recomputing the subtree that is not stored, plus climbing
the levels that are. And with `d = 1` that gives exactly `H`.

> **So 26 is the cost of storing all the internal nodes** — the row that costs 32 B per entry, the
> one `presupuesto-nodo/` discarded on 18/8. With the cut the design did choose it is **83**, a factor
> of 3.2.

| `d` | B/entry | hashes per update | floor (epochs) | % of `L_max` |
|---:|---:|---:|---:|---:|
| 1 | 32.0 | 26 | 6.03 | 24% |
| 4 | 4.0 | 37 | 8.58 | 34% |
| **6** | **1.0** | **83** | **19.25** | **77%** |
| 7 | 0.5 | 146 | 33.86 | **135%** |
| 9 | 0.125 | 528 | 122.44 | 490% |

**The floor went from 6.03 to 19.25 epochs.**

### And there §8.5 is in doubt again

The section discards the charge on creation with an argument that **does not depend on the
magnitude**: *a charge on creation does not reduce creation, it reduces the registration of
creation.* With the floor at 19.25 epochs:

- whoever buys the maximum deposit pays 43% at creation — still less than half;
- **whoever only wants the entry for one epoch pays 95% at creation.**

For short lives, the floor *is* the cost. It is exactly the form the section rejects, and saying that
the floor is small is no longer enough.

> The Phase 5 criterion that required the floor to be below 35% of `L_max` **fell and was rewritten
> to say what is now true**, the threshold was not loosened.

---

## The biggest thing: the cut is not an implementation decision

`presupuesto-nodo/RESULTADOS-EN.md` closes its table with this sentence:

> *"It is an implementation decision that has to be taken, not a cost that is suffered."*

**It cannot be.** The floor is derived from the cost of updating the tree, and the floor **is burned**
— that is, it enters the state. Two nodes with different `d` would not agree on how much was burned
when creating an entry, which is a consensus divergence over a parameter nobody declared.

**Either `d` is a constant of Geminis, or the floor stops being derived** — and the second would lose
what Phase 5 gained. It was left as `CORTE_ARBOL` in `protocolo/genesis.py`.

It is the same form that has already appeared twice: **something that looked free turns out to be
tied, because some other sum uses it.** The page ceiling looked like a constant and was a price; the
tree's cut looked like implementation and is consensus.

---

## T3 · The byte table reproduced exactly

32.0 / 1.0 / 0.125 / 0.016 B per entry for `d` = 1 / 6 / 9 / 12, and the closed formula is `64 / 2^d`.
The 18/8 measurement was right; what does not hold is its last sentence.

**It was annotated beside it, not rewritten** — it is a closed measurement.

## T2 · Proving and updating cost the same per operation

And there is the nuance of the roadmap's sentence: **the unit cost is identical**; what separates the
two operations is the frequency. Updating happens on every transaction and proving only when someone
revives an evicted entry. That is why the decision about `d` is taken looking at updating.

---

## What remains open

**Which `d` to choose**, now that it is known that there are three currencies and not two: disk, hash
budget and the floor of §8.5. It was left at 6 because that is what the design chose when only two
were visible — but **at 7 the floor already exceeds the maximum deposit**, so the margin is fine and
choosing again is a decision with new information.

## Status

**282 criteria in Python, 20 in Rust, 36 mutations, all caught.**
