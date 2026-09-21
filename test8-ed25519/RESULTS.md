# Test 8 — Ed25519 on the §6.6 machine

**Question.** How many steps does verifying an Ed25519 signature cost on the machine I1 freezes,
against ML-DSA-44? The table in `geminis/herramientas/techo.py` only has ML-DSA; "Ed25519 is more
efficient" was an intuition, not a measurement.

## Method

Same as `steps_per_verify` (Test 2) and `hash.rs` (Phase 5): an RV32IM guest runs on
`geminis/predicado/vm` **untouched**, with its admission in front, and steps are counted as the
difference between a batch of 1 verification and a batch of 11 (the call frame cancels out).

- Guest: `codigo/guest/` — ed25519-dalek 2.2.0, curve25519-dalek 4.1.3 (32-bit backend: picked by the
  target, `riscv32` has a 32-bit pointer), sha2 0.10.9. `opt-level 3`, LTO: the same profile as the
  ML-DSA guest.
- 32-byte message (a transaction hash), the same size the ML-DSA guest signs.
- Raw run: `resultados/2026-09-20_x86_dalek-2.2.0.txt`.

## Result

| primitive and mode | steps per verification | pages |
|---|---:|---:|
| ML-DSA-44 `decode+verify` (Test 2) | 3,339,364 | 26 |
| Ed25519 `from_bytes` + `verify` | 3,013,696 | 6 |
| Ed25519 `from_bytes` + `verify_strict` | 3,284,845 | 6 |
| Ed25519 `verify`, key already decoded | 2,801,768 | 6 |

Ed25519 costs **1.11× fewer steps** than ML-DSA-44 with `verify`, and **1.02× fewer** with
`verify_strict`, the variant a chain would use (it rejects small-order keys and `R`). In pages the gap
is larger: 6 against 26.

### What that buys in `tx_por_bloque`

With `g.capacidad_para` (2× margin) and **each primitive at the smallest measured point of the curve
that covers its pages** (`R_DECLARADO_POR_PAGINAS`):

| | declared pages | tx per block |
|---|---:|---:|
| ML-DSA-44 | 96 (Genesis today) | 15 |
| ML-DSA-44 | 32 | 19 |
| Ed25519 `verify_strict` | 16 | 24 |
| Ed25519 `verify` | 16 | 26 |

Ed25519's advantage on the machine is **~1.3× in capacity**, not an order of magnitude. Where it does
win by a wide margin is bytes per transaction, which this test **does not measure**.

## Controls

- **External anchor:** RFC 8032 §7.1 test vector 1 verifies in the guest (11 of 11). It is not only
  the crate agreeing with itself.
- **Negative control:** a signature with one bit flipped gives 0 of 11.
- **Admission and ceilings:** the guest passes admission and one verification fits under the initial
  ceiling (7,000,000 steps, 96 pages): 3,285,175 steps with `verify_strict`.

## Limits

- **One implementation per primitive.** Ed25519 and ML-DSA-44 were measured with their reference
  crate, untuned. A hand-written implementation could lower either number, and the ratio between them.
- **x86-64 only.** The step count is deterministic by design and Test 2 measured it identical on ARM;
  it was not repeated on ARM here.
- **The 16-page point is not the one Genesis uses** (96). The second table answers "what would each
  primitive buy with its own page budget", not "what the chain does today".
- Byte size and wall-clock time were not measured.

## Reproduce

```
cd test8-ed25519/codigo/guest && cargo build --release
cp target/riscv32im-unknown-none-elf/release/guest-ed25519 guest.elf
cd ../host && cargo run --release
```
