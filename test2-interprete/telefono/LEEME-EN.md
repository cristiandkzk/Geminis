# Test 2 — how to run it on the phone

Same phone that closed the ARM axis in `Chain` (Motorola Edge 40 Neo, Termux, aarch64).

```
pkg install -y rust
cd telefono
bash correr.sh          # interpreters + native
bash correr.sh jit      # + Cranelift JIT and Pulley (compiles slowly)
```

What each engine measures:

| engine | what it represents |
|---|---|
| `native` | baseline: the primitive as node code, which is what §6.6 wants to avoid |
| `wasmtime-cranelift` | bytecode with JIT — equally deterministic, available on Android |
| `wasmi` | pure register interpreter — the "chain VM" profile |
| `wasmtime-pulley` | portable interpreter, pessimistic bound |
| `rv32im` | own RV32IM interpreter — the small machine at 32 bits |
| `rv64imac` | the same interpreter at 64 bits — the small machine at the right width |

`decode+verify` is the honest number: a node receives key and signature as bytes in every
transaction. `verify_only` is the case with the key already expanded in memory.

## The two guests

It is the **same `pqcore`** compiled to two different ISAs:

- `guest/guest.wasm` — target `wasm32-unknown-unknown`.
- `guest-rv/guest.elf` — target `riscv32im-unknown-none-elf`, plus the bare-metal
  scaffolding of `guest-rv/src/` (its own allocator: RV32IM does not have the A
  extension, so there is no CAS and no allocator with a spinlock compiles).

Both expose the same ABI (`prepare(level)`, `run(mode, iters)`), so the measured
code is identical and the only thing that changes is the engine.

Both are versioned: the phone needs neither of the two toolchains. To regenerate
them you need `rustup target add wasm32-unknown-unknown` /
`riscv32im-unknown-none-elf` and to run `construir-rv.sh` (RISC-V).

## The `steps_per_verify` column

Only `rv32im` reports it: it is the exact count of instructions retired per
verification. It is deterministic and independent of the hardware — the same figure
on x86 and on ARM — which is exactly what the step ceiling of RESULTADOS §4.1 asks
for. `wasmi` and `wasmtime` have *fuel* counting, but it is a feature of the engine
and not of the Wasm spec, so it is no good as a consensus primitive without also
pinning a version of the engine.

## Why both RISC-V interpreters are written by hand

So that the comparison measures the ISA and not the quality of a third-party
emulator, and because the point being evaluated is precisely that the set fits in
one file. Both use the same design —predecode once, dispatch by match— so the
RV32/RV64 pair isolates a single variable: the register width.

`rv64` has one extra turn that `rv32` does not need. With compressed instructions
an instruction can start at any even address, so the naive version indexes the
predecoded table every 2 bytes and ends up with twice the entries, half of them
junk. That cost ~1.5× per instruction and has nothing to do with the ISA. The
current version does a **linear sweep** of the text —it reads the real length and
advances by it— and leaves `code` with one entry per instruction and no gaps; the
fall-through successor is the next entry of the array. A separate table translates
address to index and is only consulted when control jumps. With that, RV64's cost
per instruction ended up at 1.04-1.18× that of RV32, which is what the size of the
decoded entry explains (12 vs 8 bytes), not the compressed ones.

The `steps_per_verify` counts did not change by a single unit with that fix: they
are the regression test that the semantics was left intact.
