# Test 11 — threshold ML-DSA-44: does the chain see anything other than an ordinary signature?

**Question.** §10.2 says that splitting a wallet's key across several of the owner's own devices
with a threshold (two of three, say) is the way out that holds on any hardware, and that on the
network side "nothing new is seen": the threshold produces **one ordinary signature** under the
account's key. That was an argument. Measured: what does the §6.6 machine spend on a signature
produced by a real ML-DSA threshold scheme, against an ordinary one, and against the alternative
that needs no threshold cryptography (a k-of-n multisig on-chain, with loose signatures)?

## Method

- **Threshold scheme:** the public prototype of **Mithril** (Celi, del Pino, Espitau, Niot, Prest;
  USENIX Security '26), Go, commit `66e269e`, **unmodified**. Only its `thmldsa44` package is called;
  `firmante-go/` (a Go program of this test) signs 2-of-3 with each of the three possible pairs
  and prints key and signature in hex. Signature and key are the FIPS 204 ones (2,420 and 1,312
  bytes).
- **Machine:** an RV32IM guest on `geminis/predicado/vm`, **untouched**, with its admission in front
  and the two ceilings of the initial ruleset (7,000,000 steps, 96 pages), exactly like Test 9. The
  guest is the ML-DSA-44 one of Test 9 **byte for byte** (same `sha256`), and every machine verdict is
  cross-checked against native verification with the `ml-dsa` crate — a different implementation
  from the signer's.
- **The competitor:** `guest-multisig/`. The account is `BLAKE2s(key_1 || … || key_n)`; the
  transaction carries the `n` keys, `k` signatures and the signers' indices; the guest checks the
  address, that the indices do not repeat, and the `k` signatures. Same crate, same profile, **same
  `Cargo.lock`** as the simple guest (see "A trap" below).
- Message: 32 bytes (a transaction hash), empty context. 30 signatures per pair (90) and 30
  ordinary ones from as many keys.

## Result — 17 tests, all green

### A · the threshold signature, on the machine

| case | accepts | steps (min / median / max) | pages |
|---|:-:|---:|---:|
| **threshold 2-of-3, three pairs** | **90 / 90** | 3,318,613 / **3,318,732** / 3,318,814 | 28 |
| ordinary signature, one signer (same fork) | 30 / 30 | 3,318,542 / **3,318,658** / 3,318,863 | 28 |
| threshold + one bit of the signature altered | 0 / 90 | 3,318,369 / 3,318,512 / 3,318,599 | |
| threshold + message that was not signed | 0 / 90 | 3,318,399 / 3,318,518 / 3,318,600 | |
| threshold + key altered | 0 / 90 | 3,318,406 / 3,318,525 / 3,318,607 | |

- The three pairs {0,1}, {0,2}, {1,2} sign under **the same** public key: who signs does not show.
- The medians differ by **74 steps out of 3.3 M (0.002 %)**, and the ranges overlap. The threshold has
  **no cost on the chain**. Test 9's published figure for the same guest, signed by a Rust
  implementation, is 3,318,608.
- Rejecting costs what accepting costs (~3.3 M), as in Test 9.
- Below the threshold, nothing comes out: with **one** active party and `t = 2`, 50 of 50 attempts
  end in **a `panic` of the prototype** (index out of range in `recoverShare`), not in an error and not
  in a signature; with two parties signing but `Combine` given **one** response, 0 of 50 signatures.
  This is observable from the API; it is not a security proof (that is in the paper).

### B · the competitor: a k-of-n multisig on-chain, loose signatures

| shape | steps | pages | under the initial ceiling | tx/block at 96 pages | bytes of keys + signatures |
|---|---:|---:|---|---:|---:|
| 1-of-1 (baseline, with the hash) | 3,370,359 | 29 | accepts | 15 | 3,732 |
| 2-of-2 | 6,737,639 | 30 | accepts | 7 | 7,464 |
| **2-of-3** | **6,782,939** | 30 | accepts, **3.1 % of the ceiling left** | **7** | 8,776 |
| 3-of-3 | 10,107,025 | 31 | **`TechoExcedido`** | 5 | 11,196 |

`tx/block` is `g.capacidad_para(96, steps)`, Genesis's formula (2× margin), the same one as Test 8.

- The cost is linear in the signatures verified: 2.00× and 3.00× the baseline. What matters is `k`, not `n`.
- A 2-of-3 multisig fits under the ceiling **without margin**, spends **2×** the steps, **halves**
  the capacity (15 → 7 tx/block) and weighs **2.35×** in bytes (8,776 vs 3,732). A 3-of-3 **does not
  enter** a single transaction: the ceiling rejects it.
- Bad signature: it is rejected after the first verification (3.46 M). Bad address or repeated
  index: it is rejected **before spending a verification** (~135 k steps).

### C · what the threshold moves to the wallet's side

Local Go signing on this PC, in-process, **without a network**, 300 signatures per shape:

| t-of-n | mean attempts (max) | mean ms (p95) | bytes per party per attempt |
|---|---:|---:|---:|
| 2-of-2 | 1.75 (8) | 2.35 (5.51) | 10,528 |
| **2-of-3** | **1.70 (7)** | **3.43 (8.19)** | **15,776** |
| 3-of-5 | 2.00 (15) | 30.48 (75.37) | 73,504 |

An attempt is three rounds and each party sends the sum of the three messages; the attempts are ML-DSA's
rejection sampling, spread across the parties. A 2-of-3 wallet exchanges ~27 KB per party per
signature (15,776 × 1.70). The *time* is in the network, not in the arithmetic (see Limits).

## What the numbers show

- **The claim of §10.2, measured:** for this prototype the chain sees an ordinary FIPS 204 signature
  and spends the same steps on it. Nothing new is verified, so there is no composite verification to
  count in RV32IM steps for the wallet's second factor; what remains unmeasured in steps is Test 7's
  composite signature, which is another mitigation (dormant value above a threshold).
- **Why the threshold matters here, and not as a matter of taste:** without it, the same protection
  costs 2× the steps and half the capacity at 2-of-3, and does not enter at 3-of-3. The 7 M ceiling
  is what makes a per-account policy unaffordable on-chain.
- **What it costs, and where:** on the wallet, not on the chain — attempts, ~27 KB of exchange and
  three rounds per attempt.

## A trap (a number that measures something else without saying so)

The first build of `guest-multisig` gave **4,924,461 steps for a single verification**, against
3,370,359 when it was corrected. Nothing in the code differed: its `Cargo.lock` had been resolved from
scratch and pulled `keccak 0.2.2` instead of `0.2.1`. **Changing only that crate** —forcing it in an
otherwise identical lock— reproduces the 4,924,461 exactly: **+46 % for one verification, by a patch
bump of a transitive dependency.** The `Cargo.lock` of the simple guest was copied on purpose, and the
header of the results file records the versions. Consequence for any cost figure in this repository: it
belongs to a **binary**, not to a crate name; and a number carried from one build to another without
checking the lock can be off by half.

## Whether the test bites

Exercised: a 1 M-step ceiling makes the machine reject all 90 (the test that accepts would fail); the
three alterations of the threshold signature and the three of the multisig are rejected by the machine
and, in the first case, by the native verification too; the guest is checked byte for byte against
Test 9's. **Not done:** a deliberately broken machine (one that accepts everything) as in Test 9.

## Limits

- **Signing is in-process on one machine.** No network, no separate devices, no phone. The 3.4 ms is
  arithmetic; a real 2-of-3 pays three round trips per attempt (~1.7 attempts on average here). The
  authors report 751 ms for a 4-of-6 across four AWS regions in their preview writeup; **not measured
  here.**
- **The keys are dealt from a seed by one process (a dealer).** The public `thmldsa44` package at this
  commit exposes `GenerateThresholdKey` and `NewThresholdKeysFromSeed`; **no DKG and no sharing of an
  already existing key** appear in its API, although the authors' preview lists them. For a wallet, the
  device that deals is a point of trust for as long as it holds the seed.
- **Academic prototype, per its own README:** "have not received careful code review, and are not ready
  for production use". Per the preview, its hyperball sampling uses floating point (a C reference with fixed point is
  announced); it does not touch the chain's determinism —only the machine's verifier does— but it is
  not constant time either. **Not audited here.**
- **Round state is single-use:** reusing the state of round 1 across two challenges reveals the
  signer's secret share (`z − z' = (c − c')·s`). It can only be enforced in memory: a phone that
  persists and restores that state, or restarts mid-signature, is a risk. **No identifiable aborts**:
  a malicious device can make the signature fail without it being known which.
- **Patents:** PQShield states two pending applications over the blocks Mithril rests on
  (`PCT/GB2025/051022`, `2509575.3`) and promises a permissive license for the core implementation.
- **Security of the scheme is not tested here** —that is the paper and its review—, only what is observable:
  the output is a valid signature and the machine treats it as one. Quorus (JPMorgan, also USENIX
  Security '26) and TALUS (arXiv) were **not** run.
- **One implementation per primitive** (reference crates, untuned) and **x86-64 only**.
- The multisig reveals all `n` keys in every transaction; a Merkle root of keys would shrink the bytes
  for large `n` but **not the steps**, which are `k` verifications. Not measured.
- The 7 M ceiling is the initial ruleset's; §6.6 freezes the formula, not the point.

## Reproduce

```
cd test11-umbral-mldsa/codigo
git clone https://github.com/Threshold-ML-DSA/Threshold-ML-DSA mithril
git -C mithril checkout 66e269e75dd8f5d722675a3d276a1aedc58bc4ef
cd guest-mldsa44 && cargo build --release
cp target/riscv32im-unknown-none-elf/release/guest-mldsa44-io guest.elf
cd ../guest-multisig && cargo build --release        # keep its Cargo.lock: see "A trap"
cp target/riscv32im-unknown-none-elf/release/guest-multisig guest.elf
cd ../host && cargo build --release
cd ../firmante-go && go build -o target/firmante .   # Go 1.22 or later; go1.27.1 was used
cd ../.. && python prueba.py
```

Raw run: `resultados/2026-09-24_x86.txt`.
