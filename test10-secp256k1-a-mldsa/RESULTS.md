# Test 10 — secp256k1 → ML-DSA-44: the signature change Ethereum would make with a fork, done by succession

**Question.** Ethereum signs accounts today with ECDSA over secp256k1. If it had to change signature it would do
so with a fork or, for accounts, with account abstraction. Does the succession mechanism express that same
change, with the signatures actually verified?

**What is NOT claimed.** That Ethereum should choose ML-DSA-44. According to [ethereum.org](https://ethereum.org/roadmap/security/quantum-resistance/)
and [pq.ethereum.org](https://pq.ethereum.org/), the team is evaluating Falcon, Dilithium (ML-DSA) and SPHINCS+ for
accounts (via EIP-8141, under consideration for Hegotá) and leanXMSS, hash-based, for validators. ML-DSA-44 is the
candidate the Geminis paper picks (§10.1: the most scrutinized PQ primitive), not an Ethereum decision.

## What was done

An alternative Genesis, for this test only, with `firma/secp256k1` in generation 0 (Geminis' own, with
`H0_GENESIS` `6175777756bd3f8c`, is not touched and this is checked). A real `NodoPoD` with
`ReglaCanarioCriptografico` crosses to generation 1 (`firma/secp256k1` + `firma/ml-dsa-44`). In each generation a
signature is:

1. **admitted by format** with `decodificar` (I5), before a single step is spent;
2. **verified on the machine** (`geminis/predicado/vm`, untouched) under the two ceilings of *that* ruleset. The
   secp256k1 guest (`k256` 0.13.4) verifies ECDSA over the **32-byte hash** with a compressed SEC1 key and
   **rejects a high `s`** (EIP-2); the ML-DSA-44 guest is the same binary as Test 9;
3. **cross-checked** against native verification.

## Result — 21 tests, all green

| case | accepts | steps | pages |
|---|:-:|---:|---:|
| gen 0 · valid secp256k1 | ✔ | 5,673,513 | 5 |
| gen 0 · secp256k1, hash that was not signed | ✘ | 5,673,513 | 5 |
| gen 0 · secp256k1, high `s` (malleable, EIP-2) | ✘ | 254,962 | 2 |
| gen 0 · **ml-dsa-44** | rejected **by format**, the machine was not invoked | — | — |
| gen 1 · the secp256k1 signature born in gen 0 | ✔ | 5,673,513 | 5 |
| gen 1 · secp256k1, high `s` | ✘ | 254,962 | 2 |
| gen 1 · **valid ml-dsa-44** | ✔ | 3,318,608 | 28 |
| gen 1 · ml-dsa-44, hash that was not signed | ✘ | 3,318,387 | 28 |
| gen 1 · ml-dsa-44, altered signature | ✘ | 3,318,422 | 28 |
| gen 1 · secp256k1 bytes under the ml-dsa-44 format | ✘ | 40 | 1 |
| gen 1 · ml-dsa-44 bytes under the secp256k1 format | ✘ | 33 | 1 |

On the chain: activated at height 23, 1 checkpoint hanging from the alternative Genesis' root
(`adf7399e299686d8`), the lineage verifies, the block chain crosses without breaking, the transition is
**additive** (secp256k1 is still accepted) and what was signed in generation 0 stays valid.

## Two external anchors

So that it is not the implementation agreeing with itself:

- With **private key 1**, the Ethereum address derived from the public key is
  `0x7e5f4552091a69125d5dfcb7b8c2659029395bdf`, the well-known one for that key.
- **`ecrecover` run on the machine** recovers that same address from the signature.

## What the numbers show

| | steps | pages | tx/block at 96 pages | key + signature bytes |
|---|---:|---:|---:|---:|
| Ed25519 (Test 9) | 3,284,755 | 5 | 15 | 96 |
| ML-DSA-44 (Test 9) | 3,318,608 | 28 | 15 | 3,732 |
| **secp256k1, verify** | **5,673,513** | 5 | **9** | 97 |
| **secp256k1, `ecrecover`** | **11,331,894** | 7 | **4** | — |

- **Ethereum's signature is the most expensive of the three in steps**: verifying secp256k1 costs 1.71× what
  ML-DSA-44 does. Migrating from secp256k1 to ML-DSA-44 would give capacity back on this machine (from 9 to 15
  tx/block at 96 pages), the opposite of what one would usually expect from a post-quantum primitive. **What does grow is
  size**: ~38× in bytes per signature plus key.
- **`ecrecover` does not fit under the initial ceiling** (11.3 M steps against 7 M): the machine cuts it off with
  `TechoExcedido`. It would get in by lowering `tx_por_bloque`, which is the price §6.6 puts on an expensive
  primitive. Verifying with the known key does fit (5.67 M < 7 M).
- Rejecting a bad signature costs what accepting a good one costs (~5.67 M steps); only a high `s` and bytes of
  another format are discarded cheaply.

## A finding about the node

**The node today does not support a Genesis other than Geminis'.** Invariant I4 is checked on every block against
`g.H0_GENESIS` (it is `i4_linaje`'s default `h0_raiz`), so a `NodoPoD` with another Genesis fails at the first
checkpoint. The test passes I4 the alternative root only during the scenario, without turning any invariant off.
Doing it properly means passing the initial ruleset's root; the protocol was not touched.

## Whether the test bites

Seven deliberate breakages applied from outside, without touching files; all seven made tests fail: skipping the
format check (1 fails), a machine that accepts everything (5), a 1 M-step ceiling (6), a machine that rejects
everything (4), the well-known address not matching (1), `ecrecover` recovering another address (1) and
verifying against the old ruleset in generation 1 (**all** fail: it breaks the whole scenario, so it is a coarse
catch).

## Limits

- **One implementation per primitive.** `k256` and `ml-dsa` are general-purpose reference crates, untuned. A
  secp256k1 implementation built only for verification (public data) could cost noticeably less: it was not
  measured, and the 1.71× is for these two crates.
- **The signature → machine routing belongs to the test, not to the protocol.** The synthetic state has no
  accounts or signed transactions (Phase 3, unbuilt). The alternative Genesis is assembled in the test, with
  `FORMATOS_CONOCIDOS` extended only during the scenario.
- **`Geminis`' canary is still a counter** (`("gastar_canario",)`, unverified).
- **It verifies with the known key**, not with `ecrecover`: the latter is only measured and anchored, not routed.
- **x86-64 only.** The step count is deterministic by design (Test 2 measured it identical on ARM); not repeated here.
- Out of scope: retiring secp256k1 and what happens to funds under ECDSA keys after a quantum break.

## Reproduce

```
cd test10-secp256k1-a-mldsa/codigo/guest-secp256k1 && cargo build --release
cp target/riscv32im-unknown-none-elf/release/guest-secp256k1-io guest.elf
cd ../host && cargo build --release          # uses the ML-DSA-44 guest from test9-ed25519-a-mldsa/
cd ../.. && python prueba.py
```

Raw run: `resultados/2026-09-21_x86.txt`.
