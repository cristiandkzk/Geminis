# The machine — §6.2, Phase 4

**English** · [Español](README.es.md)

**The language changes here and it is on purpose.** The rest of `geminis/` is in Python because
what it models is rules, and rules are meant to be read. This is not that: it is the piece I1
freezes forever and the only one that runs third-party code under a budget.

It was not written from scratch. It reuses the RV32IM interpreter from the harness of
`test2-interprete/telefono`, which already had the expensive parts measured: the complete set, the
predecoding, and the step count that reproduces byte for byte between x86 and ARM. **What changes
is who writes the program.** That one ran a guest of its own; this one runs the program of the
counterparty to a challenge, who wants the node to hang or fall over.

```
src/
├── lib.rs        # the Geminis constants and the harness assemblers
├── maquina.rs    # the interpreter: two ceilings, traps, canonical verdicts
├── admision.rs   # what is decided before spending the first step
└── bin/          # the measurements — see ../RESULTS.md
tests/criterios.rs  # C2, C4, C5, C6 and the regression against Test 2
```

## The four differences from the harness, and all of them are about consensus

- **the ceiling cuts.** The harness counts steps and never stops. Here `pasos` is a budget: on
  running out, the machine stops at the exact step and returns a verdict. It is what prevents a
  challenge from existing that is more expensive to verify than to create;
- **there is a second ceiling.** Distinct pages touched. **It is the finding of Phase 4:** `lw`
  costs the same as `addi` with the data in cache and twenty-three times more without it, and it
  is the same opcode, so no per-instruction weight separates them;
- **out of range is a trap, not a wrap.** The harness does `dir & MASK`: deterministic, but **it
  depends on the size of memory**, and with that the same program would give a different result in
  two generations. It breaks I1 exactly where it cannot be broken;
- **every ending is a verdict, not an `Err`.** Both parties to a challenge have to read the same
  thing. The ending enters the block hash, so it is encoded in five bytes with no text.

## Two things that are not here, and not by oversight

**There are no dependencies.** Every crate that came in would be code that gets updated one day,
and a change of semantics between two versions is a consensus fork nobody chose.

**There is not a single wall-clock number.** A consensus machine that knew how long it takes would
be an oracle (I2). The only resources it can count are those that reproduce identically on all
hardware: steps and pages. The milliseconds live in the measurement binaries, and there is a test
in `pruebas/test_fase4_vm.py` that verifies not one `f32`, nor one `f64`, nor one decimal literal
slips into the whole crate.

## Running it

```
cargo test --release              # the criteria that are properties
cargo run --release --bin mezclas    # C7 — the rate per instruction mix
cargo run --release --bin conjunto   # what it depends on: memory and text size
cargo run --release --bin bloque     # C1 — 26 verifications as one block
cargo run --release --bin vectores            # generates the C3 table
cargo run --release --bin vectores verificar  # compares it against vectores.csv
```

### On the phone (Termux, aarch64) — what is missing to close C3

**This crate is not self-contained:** `lib.rs` does an `include_bytes!` of the ELF of the Test 2
guest, which lives four levels further up. Copying only this folder to the phone does not compile.
The minimal package —with the relative paths intact, ~130 KB— is assembled by:

```
python geminis/herramientas/empaquetar_vm.py --probar
```

`--probar` extracts it into a clean directory and compiles it there, which is the only way of
knowing that nothing is missing: a package that compiles *because the rest of the repo was next to
it* is no good for what this was made for.

Then, on Termux:

```
pkg install -y rust tar
tar xzf vm-telefono.tar.gz
cd geminis/predicado/vm
cargo run --release --bin vectores verificar
```

It compiles in seconds: **the crate has no dependencies**, so there is no network, no registry, and
none of the twenty minutes the Test 2 harness took with `wasmtime`.

The seven vectors have to come out identical. **There is no tolerance**: if two nodes count
differently, the challenge has no result.

And while you are at it, it is worth running `bloque` there, because **the protocol's reference
hardware is the phone and not a desktop**: the C1 margin that has been measured is the x86-64 one.
