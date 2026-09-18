# State expiration — measurement

**Run on 17/8/2026.** Reproduce with `python medicion.py`. No external data.

**The question:** state eviction promises that what is evicted *"is not destroyed, it can be revived
with a proof"*. Is that real, or is it a promise nobody can keep? And before that: is expiring
needed at all, or is the problem theoretical?

**The short answer: the problem is large, and it is not where it looked like it was.**

---

## Assumptions, all declared

| assumption | value | why |
|---|---|---|
| state entry | 64 / 128 / 256 B | key, id, pointer to metadata, prepaid balance, counters. It is swept so that nothing depends on the number chosen |
| disk budget of a node | 2 / 4 / 8 GB | it is what sustains the cheap-entry argument of §6.1 (*"the price of a phone"*) |
| state commitment | binary Merkle, 32 B hash | |
| replication | 3,000 nodes | the figure the paper itself uses when discussing concentration |
| horizon | 10 years | |

---

## A · Is expiring needed? Yes, and the threshold is extremely low

The question was asked the other way round from the intuitive one: instead of guessing how many
assets there will be, what was calculated is **how many are enough to fill the budget**.

| budget | entry | entry cap | creations/day that exhaust it in 10 years |
|---|---|---|---|
| 2 GB | 128 B | 16,777,216 | **4,596** |
| 4 GB | 128 B | 33,554,432 | **9,193** |
| 8 GB | 128 B | 67,108,864 | **18,386** |

**~9,200 creations a day fill a phone in ten years. That is 0.1 per second.** Any real adoption
crosses that threshold effortlessly, so expiration is not an optimization: it is what keeps the
argument of §6.1 standing, and with it the non-saturation of the queue of §6.3.

## B · The proof does not weigh anything. Keeping it up to date does

A proof is the path of siblings from the leaf to the root. The sibling at each level covers a
subtree, and **the union of all the siblings along the path is the whole tree minus the leaf
itself**. So the proof survives a block only if that block did not touch any other leaf.

With 4 GB and 128 B entries: 33,554,432 leaves, depth 25, **800-byte proof**.

```
P(the proof survives a block that changes one leaf) = 1/33,554,432 = 0.00000003
```

> **The proof does not degrade over the years: it expires at the next block.**

Storing it is free —less than one kilobyte—. What is expensive is **keeping it up to date**, and
that means following every block without ever breaking off.

## C · The result that was not expected

To rebuild an old proof you need the current values of the siblings, and that can only be provided
by whoever has the tree of the **evicted state** — which is, by construction, what no node is
obliged to store.

| evicted state | if all 3,000 store it | if one archive stores it | factor |
|---|---|---|---|
| 2 GB | 6 TB | 2 GB | 3,000× |
| 4 GB | 12 TB | 4 GB | 3,000× |
| 8 GB | 23 TB | 8 GB | 3,000× |

> **Expiration does not eliminate the cost of storing: it dereplicates it.** It goes from 3,000
> mandatory copies to a few voluntary ones.

It is still a gain of three orders of magnitude and it **justifies the mechanism**. But the data has
to exist somewhere for reactivation to be real, and **nobody is obliged to have it.**

---

## Verdict

1. **Expiration is needed.** The threshold that fills a phone is thousands of creations per day, not
   millions.
2. **"Let the owner keep the proof" is not enough as an answer.** The proof expires at the next
   block, so *keeping it* actually means **following the chain without ever breaking off**. It works
   for a permanently online agent —which is the declared audience of this design— and it does not
   work for a person.
3. **The problem is large, but it is not the one it looked like.** It is not that the proof is
   heavy: it weighs less than a kilobyte. It is that **reactivation depends on someone storing the
   evicted state**, and that is a dependency the paper today declares nowhere.
4. **The honest way to write it is as a boundary of §10.1, not as a solved mechanism.** And it has an
   exact precedent in that same section — *"the rule does not summon hardware: the protocol can
   determine the next generation down to the last byte, but it cannot force nodes to exist running
   it"*:

> **The protocol can guarantee that an evicted asset *can* be revived. It cannot guarantee that
> anyone will have what it takes.**
