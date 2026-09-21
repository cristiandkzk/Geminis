//! **Test 8 — cuantos pasos cuesta verificar una firma Ed25519 en la maquina de §6.6.**
//!
//! Es el numero que faltaba para decidir con que primitiva arranca Geminis: la tabla de
//! `herramientas/techo.py` tiene ML-DSA-44/65/87 y ninguna clasica, asi que "Ed25519 es
//! mas eficiente" era una intuicion. Se mide igual que `steps_per_verify` en Test 2 y que
//! `hash.rs` en la VM —diferencia entre dos tandas, para que el marco de la llamada no
//! entre— y el conteo es **exacto e independiente de la arquitectura**.
//!
//!     cargo run --release

use vm::maquina::Veredicto;

const GUEST: &[u8] = include_bytes!("../../guest/guest.elf");

/// `steps_per_verify` de ML-DSA-44 en Test 2 (`herramientas/techo.py`): `decode+verify` y
/// `verify_only`. Son los numeros contra los que se compara.
const MLDSA44_DECODE_VERIFY: u64 = 3_339_364;

/// `f* × tiempo_de_bloque × R_declarado` = 0,25 × 6000 ms × 70 M pasos/s.
const PASOS_POR_BLOQUE: u64 = 105_000_000;
const MARGEN: f64 = 2.0;

fn retorno(v: Veredicto) -> u32 {
    match v {
        Veredicto::Retorno(n) => n,
        otro => panic!("el guest no retorno limpio: {:?}", otro),
    }
}

fn main() {
    let (mut m, syms) = vm::admitir(GUEST, u64::MAX).expect("admitir guest-ed25519");
    println!("# guest-ed25519 admitido: {} bytes, {} simbolos", GUEST.len(), syms.len());
    m.techo_paginas = u32::MAX;
    m.arrancar();
    let prepare = *syms.get("prepare").expect("simbolo prepare");
    let run = *syms.get("run").expect("simbolo run");
    assert_eq!(retorno(m.llamar(prepare, &[])), 1);

    println!();
    println!("modo,descripcion,pasos_1,pasos_11,pasos_por_verificacion,exitos_en_11,paginas");
    let modos = [
        (0u32, "from_bytes + verify"),
        (1, "verify (clave ya decodificada)"),
        (2, "from_bytes + verify_strict"),
        (3, "control negativo (firma alterada)"),
        (4, "RFC 8032 vector 1"),
    ];
    let mut medidos = Vec::new();
    for (modo, nombre) in modos {
        let base = m.pasos;
        let e1 = retorno(m.llamar(run, &[modo, 1]));
        let p1 = m.pasos - base;

        let base = m.pasos;
        let e11 = retorno(m.llamar(run, &[modo, 11]));
        let p11 = m.pasos - base;

        // Paginas distintas que toca UNA verificacion, contadas desde cero.
        m.borrar_paginas();
        m.llamar(run, &[modo, 1]);
        let paginas = m.paginas_usadas;

        let por = (p11 - p1) / 10;
        println!("{},{},{},{},{},{},{}", modo, nombre, p1, p11, por, e11, paginas);

        // Lo que tiene que dar, o la medicion no vale.
        match modo {
            3 => assert_eq!((e1, e11), (0, 0), "el control negativo tiene que rechazar"),
            _ => assert_eq!((e1, e11), (1, 11), "modo {} tiene que verificar", modo),
        }
        medidos.push((modo, por, paginas));
    }

    // ---------------------------------------------------------------------------------- //
    // Con los dos techos puestos como los pone un nodo: cabe una verificacion?
    // ---------------------------------------------------------------------------------- //
    let base = m.pasos;
    m.techo = base + vm::TECHO_INICIAL;
    m.borrar_paginas();
    m.techo_paginas = vm::PAGINAS_INICIALES;
    let v = m.llamar(run, &[2, 1]);
    println!();
    println!(
        "# bajo el techo inicial ({} pasos, {} paginas): {:?}, uso {} pasos",
        vm::TECHO_INICIAL,
        vm::PAGINAS_INICIALES,
        v,
        m.pasos - base
    );

    // ---------------------------------------------------------------------------------- //
    // Contra ML-DSA-44 y la consecuencia para `tx_por_bloque` (cota inferior: mismas 96
    // paginas y 70 M pasos/s que ML-DSA-44, aunque Ed25519 toque muchas menos).
    // ---------------------------------------------------------------------------------- //
    println!();
    println!("# contra ML-DSA-44 decode+verify = {} pasos", MLDSA44_DECODE_VERIFY);
    for (modo, por, _) in &medidos {
        if *modo == 3 || *modo == 4 {
            continue;
        }
        let tx = (PASOS_POR_BLOQUE as f64 / (*por as f64 * MARGEN)) as u64;
        println!(
            "modo {}: {} pasos = {:.2}x menos que ML-DSA-44 -> tx_por_bloque con margen {:.0}x: {} (ML-DSA-44: 15)",
            modo,
            por,
            MLDSA44_DECODE_VERIFY as f64 / *por as f64,
            MARGEN,
            tx
        );
    }
}
