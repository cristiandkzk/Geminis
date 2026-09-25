//! L2 y L3 de `../../CRITERIA-CARGADOR.es.md`: el corpus completo, **con reloj**.
//!
//!     cargo run --release --bin cargador
//!
//! **Las cifras son del equipo donde corre.** Este binario existe para que la corrida en el
//! telefono sea un solo comando, como `vectores`; los milisegundos de un escritorio no se citan
//! como si fueran de ahi.
//!
//! - **L2**: ninguna admision ni rechazo del corpus pasa de 25 ms.
//! - **L3**: el medidor no subcobra. Para toda entrada admitida,
//!   `tiempo − T₀ ≤ costo / R_declarado + 0,05 ms`, con `T₀` el tiempo de admitir un ELF minimo
//!   (la reserva fija de 64 MiB, que no se cobra) y 0,05 ms la banda de ruido del reloj.
//! - **L6**: el arnes tambien tarda menos de 25 ms con la familia D.
//!
//! Sale con codigo 1 si algun criterio reprueba.

#[path = "../../tests/comun/mod.rs"]
mod comun;

use comun::*;
use std::time::Instant;
use vm::{
    admitir, admitir_para_consenso, costo_de_admision, GUEST_BLAKE2S, GUEST_RV, GUEST_SHA,
    TECHO_INICIAL,
};

const LIMITE_MS: f64 = 25.0;
/// La banda de ruido de L3 (`CRITERIA-CARGADOR.es.md`, segunda correccion): por debajo de esto el
/// reloj no distingue una entrada de `T₀`.
const RUIDO_MS: f64 = 0.05;
/// `R_declarado` del ruleset inicial, en pasos por segundo (`protocolo/genesis.py`).
const R_DECLARADO: f64 = 70_000_000.0;
const REPETICIONES: usize = 7;

/// La mediana de `REPETICIONES` corridas, en milisegundos. La mediana y no el minimo: el minimo
/// es el numero que nadie vuelve a ver.
fn ms(mut f: impl FnMut()) -> f64 {
    f();
    let mut v: Vec<f64> = (0..REPETICIONES)
        .map(|_| {
            let t = Instant::now();
            f();
            t.elapsed().as_secs_f64() * 1000.0
        })
        .collect();
    v.sort_by(|a, b| a.partial_cmp(b).unwrap());
    v[REPETICIONES / 2]
}

fn main() {
    let t0 = ms(|| {
        let _ = admitir_para_consenso(&minimo(), TECHO_INICIAL);
    });
    println!("T0 (ELF minimo, la reserva fija) = {t0:.2} ms · R_declarado = 70 M pasos/s = 14.3 ns por palabra\n");

    let corpus: Vec<(&str, Vec<u8>)> = vec![
        ("real · guest de Test 2 (ML-DSA-44)", GUEST_RV.to_vec()),
        ("real · guest de SHA-256", GUEST_SHA.to_vec()),
        ("real · guest de BLAKE2s", GUEST_BLAKE2S.to_vec()),
        ("A · 64 MiB declarados, 1 seccion", familia_a(1)),
        ("A · 64 MiB declarados, 16 secciones", familia_a(16)),
        ("B · codigo en la ultima direccion", familia_b()),
        ("C · 16 segmentos de 1 MB superpuestos", familia_c(16, 1_000_000)),
        ("C · 1024 segmentos de 1 MB superpuestos", familia_c(1024, 1_000_000)),
        ("D · 30 000 simbolos sin NUL (consenso)", familia_d(30_000, 400_000)),
        ("E · 60 000 segmentos x 60 000 secciones", familia_e(60_000)),
        ("legitimo · 100 KB de codigo, 64 secciones", con_secciones_repetidas(100_000, 64)),
        ("PEOR CASO ADMITIDO · costo justo bajo el techo", con_secciones_repetidas(6_900_000, 1)),
    ];

    let mut fallos = 0;
    println!(
        "{:<52} {:>10} {:>12} {:>9} {:>9}  resultado",
        "entrada", "bytes", "costo", "ms", "ns/palabra"
    );
    for (nombre, e) in &corpus {
        let costo = costo_de_admision(e).ok();
        let mut admitida = false;
        let dt = ms(|| {
            admitida = admitir_para_consenso(e, TECHO_INICIAL).is_ok();
        });

        let mut nota = String::new();
        // L2
        if dt > LIMITE_MS {
            fallos += 1;
            nota.push_str(" L2 REPRUEBA");
        }
        // L3, solo si entro: si se rechazo, el medidor no dejo pasar nada que subcobrar.
        let ns_palabra = match (admitida, costo) {
            (true, Some(c)) if c > 0 => {
                let permitido = c as f64 / R_DECLARADO * 1000.0 + RUIDO_MS; // ms
                if dt - t0 > permitido {
                    fallos += 1;
                    nota.push_str(&format!(" L3 REPRUEBA (permitido {permitido:.2} ms)"));
                }
                format!("{:.1}", (dt - t0).max(0.0) * 1_000_000.0 / c as f64)
            }
            _ => "-".to_string(),
        };
        println!(
            "{:<52} {:>10} {:>12} {:>9.2} {:>9}  {}{}",
            nombre,
            e.len(),
            costo.map_or("-".to_string(), |c| c.to_string()),
            dt,
            ns_palabra,
            if admitida { "admitida" } else { "rechazada antes de trabajar" },
            nota
        );
    }

    // L6: el arnes, que si lee simbolos, con la familia D.
    let d = familia_d(30_000, 400_000);
    let dt = ms(|| {
        let _ = admitir(&d, TECHO_INICIAL);
    });
    let ok = dt <= LIMITE_MS;
    println!("\nL6 · el arnes con la familia D: {dt:.2} ms (limite {LIMITE_MS} ms) {}", if ok { "OK" } else { "REPRUEBA" });
    if !ok {
        fallos += 1;
    }

    println!();
    if fallos == 0 {
        println!("L2, L3 y L6: todo en verde");
    } else {
        println!("{fallos} criterio(s) reprobado(s)");
        std::process::exit(1);
    }
}
