//! **Cuantos pasos cuesta un BLAKE2s en la maquina de §6.6.**
//!
//! El sucesor de `hash.rs`: el hash de Genesis paso de SHA-256 a BLAKE2s el 21/9/2026, y el
//! costo del arbol de estado —que son hashes— cuelga de este numero.
//!
//! Se mide igual que `hash.rs` y que `steps_per_verify` en Test 2 —diferencia entre dos
//! tandas— y el resultado es **exacto e independiente de la arquitectura**. Pero antes de
//! contar nada **se valida que el guest calcule BLAKE2s de verdad**: el digest de `"abc"` tiene
//! que ser el del Apendice B de la RFC 7693. Un numero de pasos de un algoritmo que calcula otra
//! cosa no vale.
//!
//!     cargo run --release --bin hash_blake2s

use vm::maquina::Veredicto;

/// BLAKE2s-256("abc"), RFC 7693 Apendice B.
const ABC: [u8; 32] = [
    0x50, 0x8c, 0x5e, 0x8c, 0x32, 0x7c, 0x14, 0xe2, 0xe1, 0xa7, 0x2b, 0xa3, 0x4e, 0xeb, 0x45,
    0x2f, 0x37, 0x45, 0x8b, 0x20, 0x9e, 0xd6, 0x3a, 0x29, 0x4d, 0x99, 0x9b, 0x4c, 0x86, 0x67,
    0x59, 0x82,
];

fn main() {
    let (mut m, syms) = vm::admitir(vm::GUEST_BLAKE2S, u64::MAX).expect("admitir el guest de BLAKE2s");
    println!("# guest-blake2s admitido: {} bytes, {} simbolos", vm::GUEST_BLAKE2S.len(), syms.len());
    m.arrancar();
    let comprimir = *syms.get("comprimir").expect("simbolo comprimir");
    let palabra = *syms.get("digest_palabra").expect("simbolo digest_palabra");

    // Validacion: el digest de "abc", palabra por palabra, contra la RFC.
    let mut digest = [0u8; 32];
    for i in 0..8u32 {
        match m.llamar(palabra, &[i]) {
            Veredicto::Retorno(w) => digest[i as usize * 4..i as usize * 4 + 4].copy_from_slice(&w.to_le_bytes()),
            otro => panic!("digest_palabra({}) no retorno: {:?}", i, otro),
        }
    }
    assert_eq!(digest, ABC, "el guest no calcula BLAKE2s-256: el digest de \"abc\" no es el de la RFC 7693");
    println!("# digest de \"abc\": correcto (RFC 7693 Apendice B)");

    // Dos tandas y una resta: el marco de la llamada se cancela.
    let base = m.pasos;
    let r1 = m.llamar(comprimir, &[100]);
    let p100 = m.pasos - base;
    let base = m.pasos;
    let r2 = m.llamar(comprimir, &[200]);
    let p200 = m.pasos - base;

    assert!(matches!(r1, Veredicto::Retorno(_)), "{:?}", r1);
    assert!(matches!(r2, Veredicto::Retorno(_)), "{:?}", r2);

    let por_compresion = (p200 - p100) / 100;
    println!("pasos_100,{}", p100);
    println!("pasos_200,{}", p200);
    println!();
    println!("pasos_por_compresion,{}", por_compresion);

    // Y la consecuencia, que es para lo que se midio.
    let hashes_por_actualizacion = 26u64;
    let ciclo = 2 * hashes_por_actualizacion * por_compresion;
    println!("hashes_por_actualizacion,{}", hashes_por_actualizacion);
    println!("pasos_del_ciclo_crear_desalojar,{}", ciclo);
    println!();
    println!("# con SHA-256 eran 4898 pasos por compresion y 254696 el ciclo");
    println!("# BLAKE2s: {:.2}x los pasos de SHA-256", por_compresion as f64 / 4898.0);
}
