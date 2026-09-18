# Test 1 · The concrete transition

> Status: **closed. It passes, with a correction to the scope.**
> There are real transitions that meet all three conditions. The main one is alive and documented by
> the EIPs of the chain that needs it. But none of the ones found needs the interpreter or the
> chainable generations. See §5.

What §12 asks for: *"name **one** real transition that meets all three conditions at once"*. The
conditions, verbatim:

1. that its **trigger be computed from the state** of the chain — and, by I2, that it be monotone in
   its approach and expose how many blocks are left at the current rate;
2. that it be expressible as a **selection within a parameter space definable today** — by I1, with
   no new node code;
3. that **some real chain has needed it and not been able to have it**.

No protocol has to be written: it is a search, like Test 3, and it was run with the same two-
vocabulary method.

> **Note of 19/8/2026 — I2 was reformulated after running this test, and condition 1 was left
> written in its old wording.** It is not rewritten: the criterion of a closed test gets annotated,
> not accommodated. **The result does not change**, and for a reason worth stating: the three
> customers found are recalibrations of aggregate parameters —blobs, gas limit, difficulty bomb— and
> all three fire by **observable approach**, which is the form of I2 condition 1 already demanded.
> The form that was added —*demonstrated capability*— enables triggers this test did not look for,
> so if it does anything, it widens the universe of possible customers, never invalidates the ones
> found.

---

## 1. Method

Two vocabularies, which is the precaution `patron-construir-antes-de-medir` left written down and
which in Test 3 was the difference between finding Drake and not finding him:

- **governance / hard fork** — who decides a rule change and what coordinating it costs;
- **parameter recalibration** — *protocol constants*, *parameter-only upgrade*, *scheduled parameter
  growth*, automatic adjustment without a fork.

The second vocabulary is the one that brought the three qualifying cases. The first only returned
what Test 3 had already closed. **Searching by "governance" systematically finds competitors;
searching by "parameters" is what finds customers.** Worth noting for next time.

Each candidate was evaluated against the three conditions separately, and the ones that fail were
written down too (§6), which is where half the value of the test is.

---

## 2. Primary case · Ethereum's data capacity (blobs)

**The only one of the three whose need is alive today.** That is why it is the primary one, even
though it is not the one that best fits I2.

### Condition 2 — the space: it does not have to be defined, it is already defined

EIP-7892 (*Blob Parameter Only Hardforks*) introduced a `blobSchedule` object with three integers:

| parameter | what it is |
|---|---|
| *blob target* | blobs expected per block |
| *blob limit* | maximum per block |
| *blob base fee update fraction* | the speed of the price adjustment |

That is, literally, *"a point of a space the node already knows how to execute"* (I1). There is no
need to argue that the space is definable: **Ethereum already wrote it, with a name, in a
configuration file, in production**. And they are internal parameters —capacity, not format— so they
do not touch I5.

### Condition 3 — it needed it, and the evidence is revealed preference

Ethereum did not only need these changes: **it built dedicated machinery to make them cheaper**.
EIP-7892's motivation, verbatim:

> *"Large, infrequent blob parameter changes create high costs and inefficiencies."*
>
> *"Full Ethereum hard forks require significant coordination, testing, and implementation changes
> beyond parameter adjustments."*

And even so the firing stayed human: BPOs are activated **by a timestamp hardcoded in the client's
configuration**. Two ran on mainnet, with the date chosen by people and shipped in releases:

| fork | date | target / max |
|---|---|---|
| Fusaka | 3/12/2025 | 6 / 9 |
| BPO1 | 9/12/2025 | 10 / 15 |
| BPO2 | 7/1/2026 | 14 / 21 |

**The same pattern repeated on another parameter four months later.** EIP-8261 (*Gas Limit
Schedule*, 11/5/2026) proposes a gas limit schedule per epoch, in a machine-readable file, because
the current defaults are —verbatim— *"release-scoped rather than epoch-based: a new default
activates whenever an operator happens to update their node, not at a network-coordinated epoch."*

And then it stops just short of the edge:

> *"Validators retain sovereignty; the schedule serves as a coordinated default and recommendation,
> **not a consensus rule**."*

**That is the sharpest finding of the test.** In May 2026, the largest contract chain writes a
parameter schedule and explicitly decides not to make it binding. The need is documented by its own
EIPs; what is missing is exactly the piece this design puts into Geminis.

### Condition 1 — the trigger, which is what has to be built

The inputs are already state: `excess_blob_gas` travels **in the block header** and the blob base
fee is derived from it. What does not meet I2 is the fee, which is not monotone.

The form that does meet I2 needs to invent nothing: **a counter of blocks at or above target since
the last transition**. It is monotone by construction, and the queryable distance —*how many blocks
are left at the current rate*— comes out of the recent fill rate.

A property that appears on its own and is worth noting: **advancing that counter costs money.**
Being above target raises the blob base fee exponentially, so forcing the trigger with induced
demand is paid for at the price the mechanism itself imposes. It is the pattern of §6.4 —the
watchman funded by the loot, seen from the other side— and here it comes for free, with nothing
designed. *To bound the claim:* it is a **cost bound**, not a proof of resistance. Nobody ran the
number.

---

## 3. Corroborating case · The difficulty bomb (Ethereum, six times)

**The best fit to I2 of everything found, and the most expensive record of what it costs for the
other half to be missing.**

### The three conditions

1. **Trigger:** perfect. The bomb is a pure function of the height
   —`2^((block−offset)/100000)`— so the distance to any block-time threshold is exactly computable
   and monotone. The chain could publish *"N blocks left until 20 s blocks"* precisely. In fact
   **EIP-2384 itself does that sum by hand**, in prose.
2. **Space:** one integer. Literally one:
   `fake_block_number = max(0, block.number − 9_000_000)`.
3. **Needed and not available:** six times in five years.

| EIP | fork | date | delay |
|---|---|---|---|
| 649 | Byzantium | 2017 | ~3 M blocks |
| 1234 | Constantinople | 2019 | ~5 M blocks |
| 2384 | Muir Glacier | Jan 2020 | ~9 M blocks (4 M more) |
| 3554 | London | 2021 | to Dec 2021 |
| 4345 | Arrow Glacier | Dec 2021 | to Jun 2022 |
| 5133 | Gray Glacier | Jun 2022 | 700 k blocks |

### Muir Glacier is the sharpest case of the test

The bomb came earlier than estimated. Block times went from ~13.1 s to ~14.3 s, and the EIP
projected 20 s for the end of December and 30 s+ from February. It was announced on **23 December
2019** as an emergency precaution; the developers had **less than three weeks**, over the holidays,
to coordinate a mainnet hard fork whose content was **one number**. It activated at block 9,200,000.

Tim Beiko's quote is the whole test in one line:

> *"We thought we had months until it kicked in, but those numbers were wrong."*

What is valuable is not that time was short. It is that **the human in the loop contributed no
judgement and did contribute error**: the badly estimated number was a quantity the chain measures
exactly. A `TRANSITION_RULE` written over the same formula could not be wrong, because the formula
*is* the source of the number.

### The objection that has to be written down

The need was **self-inflicted**. The bomb existed to force a transition, and what was recalibrated
six times was the bomb itself. A reader can rightly say that this is not a transition the chain
needed, but a patch to a device installed on purpose.

The answer does not weaken the case: it sharpens it. **The bomb is row 3 of the table of §1** —
*forced obsolescence*— and it is the closest ancestor in production of `TRANSITION_RULE`. Its
failure mode, repeated six times, is exactly the one this design attacks: *deterministic firing,
human successor*. The test did not find a hypothetical customer; it found **half the mechanism
already deployed**, and the bill for what it cost to be missing the other half.

Second objection, and it is the reason this case is not the primary one: post-Merge the bomb is
irrelevant. **That customer is historical.**

---

## 4. Corroborating case · Terminal issuance (the cleanest A/B)

Two chains, the same transition, opposite results depending on whether it was written in advance or
not.

**Monero wrote it in advance and got it for free.** The floor —`FINAL_SUBSIDY_PER_MINUTE`, 0.6 XMR
per block— was in the code years earlier. The issuance curve came down until it touched it in 2022
and terminal issuance became active **with no fork and with nobody deciding anything at that
moment**. It is condition 1 in its degenerate form —trigger = the height, which is state— and
condition 2 in its own: a space of one point.

*(Sources disagree on the exact block —2,628,888, end of May, against 2,641,623, 9 June— and the
discrepancy does not affect anything claimed here.)*

**Bitcoin did not write it and today cannot have it.** The security budget is the most discussed
unsolved need in the industry, and Peter Todd's terminal issuance proposal ran into the fact that 21
million is the one rule no developer can revisit; Adam Back called it a trap disguised as technical
logic. Todd himself admits that the window is *"in 10-20 years"*.

That is **the strongest "could not have it" that appeared**, and not for the expected reason: it is
not engineering that is missing —the engineering is a constant in a reward function, and Monero has
it running— and even so the transition is impossible. What is missing is **legitimacy**, and
legitimacy is bought at block 0 or it is not bought.

It is exactly what §5 sustains, and it is the design's commercial argument in one sentence: the
window for writing the succession rule is Geminis.

**Honest weakness:** Monero's terminal issuance is a **constant**, not a selection as a function of
the state. It exercises the firing, not the successor.

---

## 5. Verdict, and the correction to the scope

**Test 1 passes.** Real transitions exist that meet all three conditions at once, and the main one
is alive, in production, and documented by the EIPs of the chain that needs it. The mechanism has a
customer: the dominant risk of §12 did not materialize.

But —just as in Test 3— **the customer is smaller than the shop window**. Against the pieces of the
design:

| piece | do the customers found ask for it? |
|---|---|
| §3 trigger/lock-in/activation with `Δ` | **yes**, all three |
| I2 trigger from the state, monotone, with notice | **yes**, all three |
| I5 additivity in the interface | does not apply — all three are internal parameters |
| selection of the successor as a function of the state | **A and B yes**; C is a constant |
| interpreter (strong I1, infinite space) | **none** |
| chainable generations | **none** |
| §6.6 cryptographic evolution | **none** |

Four consequences, in order of how much they hurt:

1. **§6.6 still has no demonstrated customer.** The three cases are internal parameters —capacity,
   issuance, timings—; none is cryptographic. And §6.6 was already the weakest application because
   of the tension in CONTEXTO §3.2. **The paper's order of exposition is inverted with respect to
   where the demand is:** the shop-window section is the only one with no customer, and the boring
   sections are the ones with three.
2. **None needs the interpreter.** The three spaces are integers: target, max, update fraction,
   offset, issuance rate. They are covered by a finite list —weak I1—, which is the one that does
   **not** pay the price declared in §10.1 (*"the set of possible futures stops being auditable"*)
   nor that of *"a single point of failure that can never be patched"*. The interpreter is necessary
   for §6.6 and, by what this test shows, only for §6.6.
3. **None needs chainable generations** — they are repeated recalibrations within the same space,
   not a succession of spaces. And chainable is precisely the differentiator declared against Drake
   in §6.6. That is: **the differentiator against the competitor is the part the customer found does
   not ask for.**
4. **Selection with real content appears in only one case.** In B the successor was an integer a
   human computed wrong; in C it is a constant. Only in A does the selection have substance —how
   much to raise the target depends on measured propagation health— and that is why Ethereum did not
   solve it with a fixed schedule in the style of BIP-101.

**The minimal mechanism that covers all three customers is §3 + I2 with a finite space.** No
interpreter, no chaining, no §6.6. It is a much smaller version of the design, much cheaper to
defend —it pays none of the expensive boundaries of §10.1— and it is the one with demand written by
third parties. The large version remains speculative; this does not refute it, but it stops being
sustained by the same argument.

---

## 6. Reviewed and discarded (so that nobody repeats the work)

| candidate | fails | why |
|---|---|---|
| **Ethereum's gas limit** (±1/1024 per block) | 1 | It moves without a fork, but by **proposer signalling**: it is a vote, forbidden by I2. A useful counterexample — the only parameter Ethereum made adjustable without a fork, it made adjustable by vote. |
| **Monero's dynamic block size** | 3 | It meets 1 and 2 (median of the last 100 blocks + a penalty to the miner) but **it had it**: it did not lack it. It is closed-loop control *within* a ruleset, not ruleset commutation. An existence proof that the space works; not a customer. |
| **Bitcoin's halving** | 3 | Automatic since block 0. Same case. |
| **Zcash's development fund** | 2 | The firing is state (the halving), but the successor is *who collects*. That is not a point of a parameter space: it is a political decision. |
| **Cardano's `k` parameter** | 3 | Recalibration from on-chain metrics, but Cardano **can** change it by governance. It fails the "could not have it" in the strong sense. |
| **Bitcoin's block size** | 3 (disputed) | The most famous need, but **contested**: the conservative faction holds that the change was not necessary. A case whose condition 3 is the object of the conflict itself is no good as evidence. What it does contribute is in §7. |

### The counter-case that has to be declared: Bitcoin Cash's EDA → DAA

BCH **did** carry an automatic difficulty adjustment rule written in advance —the *Emergency
Difficulty Adjustment*: −20% if more than 12 hours passed between block −6 and block −12— and **it
was wrong**. It oscillated, ran thousands of blocks ahead of Bitcoin and shifted the issuance
schedule. It was replaced by a **human hard fork** on 13 November 2017.

It is the exact instance of the first boundary of §10.1: *"adaptation is bounded to what Geminis
anticipated"*. Writing the rule in advance **does not eliminate the fork — it moves it to the case in
which the written rule is the wrong one**, and there there is no override by construction.

It is also evidence in favour of two demands of I2 that might look decorative: the EDA was not
monotone and gave no notice. The two things I2 asks for are the two it lacked.

---

## 7. Prior art that turned up along this route (for the Test 3 record)

**BIP-103** (Pieter Wuille, 2015). It replaces the block size limit with a deterministic function:
**+4.4% every ~97 days** (17.7% a year) until 2063, evaluated over the median of the timestamps of
the previous 11 blocks, **with no miners' vote**. It is parameter succession written in advance and
without voting, in Bitcoin, ten years earlier.

It does not close the declared gap: **the firing is time, not state**; the successor is a constant of
a fixed curve, with no selection; and there is no chaining. But it has to be cited for the same
reason as Drake, and it is the reason the author already fixed: **to demonstrate command of the
terrain, not to attribute inspiration.**

The full context matters and it is elegant: the block size war produced all three possible forms at
once —**BIP-100** (miners' vote), **BIP-101** (fixed schedule, double every two years), **BIP-103**
(slow deterministic schedule)— and none activated. Bitcoin ended in a split. The form that was never
tried is the fourth: **a schedule fired from the state**.

---

## 8. Limits of the search

One pass, in English, two vocabularies (governance/hard fork and parameter recalibration), over the
web and indexed literature.

- **Biased towards large and well-documented chains.** If the best customer is a small chain that
  suffered a recalibration with no coverage, I would not have seen it.
- **Core dev meeting minutes and non-indexed forums were not searched**, which is precisely where the
  real coordination cost of each of these changes lives. Everything claimed here about that cost
  comes from what the EIPs and the press said, not from the calls.
- **Nothing outside the blockchain world was searched.** An analogous customer could exist in network
  protocols with negotiated parameters; that was not looked at.
- The three qualifying cases come from **two chains** (Ethereum ×2, Monero/Bitcoin). That is little
  diversity for a market conclusion.

---

## 9. Sources

- EIP-7892, *Blob Parameter Only Hardforks* — https://eips.ethereum.org/EIPS/eip-7892
- EIP-8261, *Gas Limit Schedule* (11/5/2026) — https://eips.ethereum.org/EIPS/eip-8261
- EIP-2384, *Muir Glacier Difficulty Bomb Delay* — https://eips.ethereum.org/EIPS/eip-2384
- EIP-649 / EIP-1234 — https://eips.ethereum.org/EIPS/eip-649 · https://eips.ethereum.org/EIPS/eip-1234
- Fusaka mainnet announcement (BPO calendar) — https://blog.ethereum.org/2025/11/06/fusaka-mainnet-announcement
- Muir Glacier, context and the Beiko quote — https://decrypt.co/15813/ethereum-hard-fork-muir-glacier-goes-live · https://medium.com/ethereum-cat-herders/ethereum-muir-glacier-upgrade-89b8cea5a210
- BIP-103 — https://bips.dev/103/ · BIP-101 — https://github.com/bitcoin/bips/blob/master/bip-0101.mediawiki
- Monero's terminal issuance — https://www.getmonero.org/resources/moneropedia/tail-emission.html
- Bitcoin's terminal issuance, 2025-26 debate — https://news.bitcoin.com/featured/peter-todds-tail-emissions-pitch-sparks-bitcoin-inflation-debate/
- Bitcoin Cash's DAA — https://www.bitcoinabc.org/2017-11-01-DAA/
