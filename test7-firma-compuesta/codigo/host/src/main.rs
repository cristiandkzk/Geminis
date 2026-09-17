//! Test 7 — arnes de medicion.
//!
//! Mide `decode+verify` de ML-DSA-44 y SLH-DSA-128s bajo dos motores —wasmi
//! (interprete puro, "VM de cadena") y wasmtime/Cranelift (JIT, el motor que
//! de hecho entro en el presupuesto de Test 2)— sobre el mismo modulo wasm,
//! con la misma funcion `measure` que us el host de Test 2.
//!
//! No corre en el telefono: falta esa pata (§10.3 de este test). Ver LEEME.md.

use std::time::{Duration, Instant};

const WASM: &[u8] = include_bytes!("../../guest/guest.wasm");

const TARGET: Duration = Duration::from_millis(1200);
const REPS: usize = 5;

fn measure(mut f: impl FnMut(u32)) -> f64 {
    let mut iters: u32 = 1;
    loop {
        let t = Instant::now();
        f(iters);
        let e = t.elapsed();
        if e >= TARGET || iters >= 1 << 24 {
            break;
        }
        let grow = (TARGET.as_secs_f64() / e.as_secs_f64().max(1e-9)).min(8.0);
        iters = ((iters as f64 * grow).ceil() as u32).max(iters + 1);
    }
    let mut samples = Vec::with_capacity(REPS);
    for _ in 0..REPS {
        let t = Instant::now();
        f(iters);
        samples.push(t.elapsed().as_secs_f64() / iters as f64 * 1e9);
    }
    samples.sort_by(|a, b| a.partial_cmp(b).unwrap());
    samples[REPS / 2]
}

fn bench_wasmi(export: &str) -> (f64, f64) {
    let engine = wasmi::Engine::default();
    let t = Instant::now();
    let module = wasmi::Module::new(&engine, WASM).expect("module");
    let compile_ms = t.elapsed().as_secs_f64() * 1e3;

    let mut store = wasmi::Store::new(&engine, ());
    let linker = wasmi::Linker::<()>::new(&engine);
    let inst = linker
        .instantiate_and_start(&mut store, &module)
        .expect("instantiate");
    let run = inst
        .get_typed_func::<u32, u32>(&store, export)
        .expect("export");

    let ns = measure(|n| {
        let ok = run.call(&mut store, n).expect("run call");
        assert_eq!(ok, n, "verificacion fallida");
    });
    (ns, compile_ms)
}

fn bench_cranelift(export: &str) -> (f64, f64) {
    let mut cfg = wasmtime::Config::new();
    cfg.cranelift_opt_level(wasmtime::OptLevel::Speed);
    let engine = wasmtime::Engine::new(&cfg).expect("engine");

    let t = Instant::now();
    let module = wasmtime::Module::new(&engine, WASM).expect("module");
    let compile_ms = t.elapsed().as_secs_f64() * 1e3;

    let mut store = wasmtime::Store::new(&engine, ());
    let inst = wasmtime::Instance::new(&mut store, &module, &[]).expect("instance");
    let run = inst
        .get_typed_func::<u32, u32>(&mut store, export)
        .expect("export");

    let ns = measure(|n| {
        let ok = run.call(&mut store, n).expect("run call");
        assert_eq!(ok, n, "verificacion fallida");
    });
    (ns, compile_ms)
}

fn fila(nombre: &str, export: &str) {
    let (ns_i, c_i) = bench_wasmi(export);
    let (ns_c, c_c) = bench_cranelift(export);
    println!(
        "{nombre:<14} wasmi: {:>7.1} us/op ({:>6.0} ops/s, compilar {c_i:.1} ms)   \
cranelift: {:>7.1} us/op ({:>6.0} ops/s, compilar {c_c:.1} ms)",
        ns_i / 1e3,
        1e9 / ns_i,
        ns_c / 1e3,
        1e9 / ns_c,
    );
}

fn main() {
    println!("modulo: {} bytes\n", WASM.len());
    fila("ML-DSA-44", "run_ml_dsa44");
    fila("SLH-DSA-128s", "run_slh_dsa128s");
}
