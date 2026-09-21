# Test 9 — ed25519 → ML-DSA-44 in the same chain, with signatures actually verified

**Question.** The format succession and the lineage were tested in Python with signatures that were
labels; the §6.6 machine was tested in Rust with each primitive on its own. Do they compose? That is:
a chain that crosses the canary transition, does it recognise in each generation the signatures that
belong to it and verify them on the real machine, inside the budget of *that* ruleset?

## What was done

A real `NodoPoD` with `ReglaCanarioCriptografico` crosses from generation 0 (`firma/ed25519`) to
generation 1 (`firma/ed25519` + `firma/ml-dsa-44`). In each generation a signature is:

1. **admitted by format** with `decodificar` (I5): it fails closed if the ruleset does not know the
   format, before a single step is spent;
2. **verified on the machine** (`geminis/predicado/vm`, untouched) under the two ceilings that ruleset
   dictates (`techo_vigente`, `paginas_vigentes`), in two guests that receive key, signature and
   message **through memory** (`codigo/guest-ed25519`, `codigo/guest-mldsa44`; same crates as Test 8
   and Test 2);
3. **cross-checked** against native verification: every machine verdict has to equal the native one.

## Result — 16 tests, all green

| case | accepts | steps | pages |
|---|:-:|---:|---:|
| gen 0 · valid ed25519 | ✔ | 3,284,755 | 5 |
| gen 0 · ed25519, message that was not signed | ✘ | 3,277,090 | 5 |
| gen 0 · ed25519, `R` altered | ✘ | 424,518 | 4 |
| gen 0 · **ml-dsa-44** | rejected **by format**, the machine was not invoked | — | — |
| gen 1 · the ed25519 signature born in gen 0 | ✔ | 3,284,755 | 5 |
| gen 1 · ed25519, message that was not signed | ✘ | 3,277,090 | 5 |
| gen 1 · **valid ml-dsa-44** | ✔ | 3,318,608 | 28 |
| gen 1 · ml-dsa-44, message that was not signed | ✘ | 3,318,387 | 28 |
| gen 1 · ml-dsa-44, altered signature | ✘ | 3,318,422 | 28 |
| gen 1 · ed25519 bytes under the ml-dsa-44 format | ✘ | 40 | 1 |
| gen 1 · ml-dsa-44 bytes under the ed25519 format | ✘ | 5 | 0 |

Also, on the chain:

- `H0_GENESIS` = `6175777756bd3f8c` **before and after** (pinned in the test). It was
  `dd2ce1fe33cbcad0` until 2026-09-21, when `H` moved from SHA-256 to BLAKE2s on purpose.
- Activated at height 23; 1 checkpoint hanging from `H0_GENESIS`; `verificar_linaje` is true.
- The block chain crosses the transition without breaking and keeps producing under generation 1.
- The transition is **additive**: ed25519 is still accepted in generation 1. What was signed in
  generation 0 stays valid.

## What the numbers show

- **Rejecting costs what accepting costs.** A bad signature (different message or altered signature)
  spends ~3.3 M steps, the same as a good one: sending garbage is no cheaper for the verifier. The
  exception is Ed25519's altered `R`, which the curve discards while decoding (424 K steps).
- **A wrong format is nearly free to reject:** 40 and 5 steps, by length.
- Both primitives fit under the initial ceiling (7,000,000 steps, 96 pages); ML-DSA-44 touches 28
  pages and Ed25519 5.

## Whether the test bites

Four deliberate breakages applied from outside, without touching the file; all four made tests fail:
skipping the format check (1 fails), a machine that accepts everything (4 fail), a 1 M-step ceiling
(5 fail) and verifying against the old ruleset in generation 1 (**all** fail: it breaks the whole
scenario, so it is a coarse catch).

## Limits

- **The signature → machine routing belongs to the test, not to the protocol.** The synthetic state has
  no accounts or signed transactions (Phase 3, unbuilt), and nothing in `geminis/` sends a signature to
  the machine. What is shown is that the pieces compose.
- **`Geminis`' canary is still a counter** (`("gastar_canario",)`, unverified). The version with a
  verified signature only exists in `Colosseum App`. This test does not depend on how hard the canary
  is to spend, but the trigger is not the hardened one.
- **One implementation per primitive** (reference crates, untuned) and **x86-64 only**.
- The guests here are different binaries from the published ones: ed25519 takes 3,284,755 steps
  (Test 8: 3,284,845) and ML-DSA-44 takes 3,318,608 (Test 2, published guest: 3,339,364).
- Out of scope: retiring ed25519 (a later transition, does not exist) and what happens to funds under
  ed25519 keys after a break.

## Reproduce

```
cd test9-ed25519-a-mldsa/codigo/guest-ed25519 && cargo build --release
cp target/riscv32im-unknown-none-elf/release/guest-ed25519-io guest.elf
cd ../guest-mldsa44 && cargo build --release
cp target/riscv32im-unknown-none-elf/release/guest-mldsa44-io guest.elf
cd ../host && cargo build --release
cd ../.. && python prueba.py
```

Raw run: `resultados/2026-09-21_x86_blake2s.txt`.
