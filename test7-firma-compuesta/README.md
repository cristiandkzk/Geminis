# Test 7 · The budget of a composite signature

**English** · [Español](README.es.md)

> Status: **partial.** Desktop (x86-64) run on all three engines. The phone leg
> (ARM64) is missing — no device at hand for this run — and the whole of Part A
> of the problem that motivates this test is missing. See RESULTS.md.

## Where this comes from

No numbered section of the paper asks for it yet. It comes out of a discussion
about §10.2 (the canary pays for telling, and whoever can break the primitive
gains more by keeping quiet): an attacker who breaks **one** primitive can empty
any account with that single break. The mitigation that was evaluated —a velocity
ceiling on dormant value (§8.5, `permanencia.py`/`desalojo.py`) that requires a
**second signature, from an independent cryptographic family**, for any
transaction that trips that ceiling— only makes sense if that second verification
is cheap in the rare case that pays for it. This test measures that.

**Why SLH-DSA and not something else.** It has to be a family with no core shared
with ML-DSA (the same condition §10.1 already imposes for the lineage hash:
"lineage and signature cannot share a cryptographic core"). SLH-DSA (FIPS-205 /
SPHINCS+) is hash-based — pure SHA-2 in the `Sha2_128s` variant — whereas ML-DSA
is lattice-based (Module-LWE). They share no base primitive, so breaking one says
nothing about the other.

## What exactly it measures

The same pattern as `pqcore` from Test 2: a single wasm module with `decode+verify`
of both primitives (`run_ml_dsa44`, `run_slh_dsa128s`), measured with the same
`measure` function (scales iterations up to 1.2 s, median of 5 runs) under two
engines — `wasmi` (pure interpreter, the "chain VM" profile) and
`wasmtime`/Cranelift (JIT, the engine that actually fit into the budget of Test 2,
with "391 µs · ~640 tx/s" on the real phone). Plus a native binary
(`host/src/bin/nativo.rs`) to have the reference `native` row.

ML-DSA-44 uses a fixed seed (same as `pqcore::fixture`, deterministic, no RNG
inside the guest). SLH-DSA-128s does not have that path in this version of the
crate (`slh-dsa` 0.1.0), so its key and signature were generated once outside the
guest and travel as fixed bytes in `codigo/guest/src/fixture.rs` — the guest only
decodes and verifies, which is exactly what a real node does with a signature that
arrives in a transaction.

## How to run it

`codigo/guest/guest.wasm` is already versioned — the same decision as Test 2 for
its guests: the compiled binary is ignored (`target/` is in `.gitignore`), but
**this** wasm is the input of the benchmark, not a throwaway build artifact, so it
goes into the repo. The guest does not have to be recompiled to run the
measurements:

```
cd codigo/host
cargo run --release --bin nativo    # the `native` row
cargo run --release                 # the wasmi + cranelift rows
```

To regenerate `guest.wasm` after touching `codigo/guest/src/`:

```
cd codigo/guest
cargo build --release --target wasm32-unknown-unknown
cp target/wasm32-unknown-unknown/release/guest.wasm guest.wasm
```

No dependencies outside `crates.io`: `ml-dsa` and `slh-dsa` are the same RustCrypto
crates `pqcore` (Test 2) already uses, plus `wasmi` and `wasmtime` at the same
versions `test2-interprete/telefono/host/Cargo.toml` already pins. `signature` is
pinned to `=2.3.0-pre.4` on purpose: it is the exact version `slh-dsa` 0.1.0 is
compiled against — a newer one (`2.3.0-pre.7`, the one that resolves by default)
breaks the crate's compilation because of an API change between pre-releases. If
`slh-dsa` moves version, this has to be revisited.

## What is missing before the number means anything for the paper

1. **The real phone.** Just as in Test 2 and Test 5, the reference hardware of the
   PoD nodes is a mid-range phone, not an x86 desktop. Everything in this test ran
   on a desktop machine — the native/wasmi ratio might not carry over the same way
   to ARM (§10.3 already measured that ARM and x86 break at different places for
   ML-DSA).
2. **Part A of the problem that motivates this:** the velocity threshold on dormant
   value itself — which ceiling does not brush against legitimate activity — is not
   measured. `herramientas/traer_datos.py` only brings block-level series (blobs,
   gas, difficulty); a per-address data source is needed that does not exist in the
   repo today. Without that, knowing that the second signature is cheap is not
   enough to decide whether the complete mechanism makes sense.
3. **Size cost, not just time cost.** SLH-DSA-128s weighs ~7.9 KB per signature
   against ML-DSA-44's 2.4 KB — a real bandwidth/storage cost this test does not
   quantify in those terms (bytes per block, the state budget of §10.1).

Without all three, this is an order-of-magnitude signal — useful for deciding
whether it is worth continuing down this branch — not a result that can be cited as
closed in the paper.
