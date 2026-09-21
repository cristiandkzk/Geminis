//! **Cuantos pasos cuesta un BLAKE2s en la maquina de §6.6** — el sucesor de `guest-sha`.
//!
//! El 21/9/2026 el hash de Genesis (`H`, I4) paso de SHA-256 a BLAKE2s: la firma inicial,
//! Ed25519, hashea con SHA-512 por dentro, y un `H` de la familia SHA-2 comparte nucleo con
//! ella (§10.1). El costo del arbol de estado —que es hashes— cuelga de este numero, asi
//! que hay que medirlo con el algoritmo nuevo. `guest-sha` queda como medicion historica y
//! como segunda carga independiente para la admision.
//!
//! ## Por que escrito a mano y sin dependencias
//!
//! Igual que `guest-sha`: una implementacion de terceros metaria sus propias decisiones en
//! el medio del numero. Esta es la version de la RFC 7693, sin desenrollar y sin tablas mas
//! alla de las constantes del estandar. Se valida contra el vector de la RFC (`abc`) desde el
//! host, asi que el numero no sale de un algoritmo que calcula otra cosa.

#![no_std]
#![no_main]

use core::panic::PanicInfo;

core::arch::global_asm!(
    r#"
    .section .text._start
    .globl _start
_start:
    .option push
    .option norelax
    la   gp, __global_pointer$
    .option pop
    li   sp, 0x04000000
    ecall
    "#
);

/// El vector de inicializacion: los mismos que SHA-256 (RFC 7693 §2.6).
const IV: [u32; 8] = [
    0x6A09E667, 0xBB67AE85, 0x3C6EF372, 0xA54FF53A, 0x510E527F, 0x9B05688C, 0x1F83D9AB,
    0x5BE0CD19,
];

/// La permutacion de palabras del mensaje por ronda (RFC 7693 §2.7). Diez rondas.
const SIGMA: [[u8; 16]; 10] = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
    [14, 10, 4, 8, 9, 15, 13, 6, 1, 12, 0, 2, 11, 7, 5, 3],
    [11, 8, 12, 0, 5, 2, 15, 13, 10, 14, 3, 6, 7, 1, 9, 4],
    [7, 9, 3, 1, 13, 12, 11, 14, 2, 6, 5, 10, 4, 0, 15, 8],
    [9, 0, 5, 7, 2, 4, 10, 15, 14, 1, 11, 12, 6, 8, 3, 13],
    [2, 12, 6, 10, 0, 11, 8, 3, 4, 13, 7, 5, 15, 14, 1, 9],
    [12, 5, 1, 15, 14, 13, 4, 10, 0, 7, 6, 3, 9, 2, 8, 11],
    [13, 11, 7, 14, 12, 1, 3, 9, 5, 0, 15, 4, 8, 6, 2, 10],
    [6, 15, 14, 9, 11, 3, 0, 8, 12, 2, 13, 7, 1, 4, 10, 5],
    [10, 2, 8, 4, 7, 6, 1, 5, 15, 11, 9, 14, 3, 12, 13, 0],
];

/// La funcion de mezcla `G` (RFC 7693 §3.1).
#[inline(always)]
fn g(v: &mut [u32; 16], a: usize, b: usize, c: usize, d: usize, x: u32, y: u32) {
    v[a] = v[a].wrapping_add(v[b]).wrapping_add(x);
    v[d] = (v[d] ^ v[a]).rotate_right(16);
    v[c] = v[c].wrapping_add(v[d]);
    v[b] = (v[b] ^ v[c]).rotate_right(12);
    v[a] = v[a].wrapping_add(v[b]).wrapping_add(y);
    v[d] = (v[d] ^ v[a]).rotate_right(8);
    v[c] = v[c].wrapping_add(v[d]);
    v[b] = (v[b] ^ v[c]).rotate_right(7);
}

/// Una compresion `F` (RFC 7693 §3.2): un bloque de 64 bytes.
///
/// **Es la unidad que el piso necesita**, igual que en `guest-sha`: una actualizacion del
/// arbol son ~26 hashes y el ciclo crear + desalojar son dos actualizaciones.
#[inline(never)]
fn comprimir_uno(h: &mut [u32; 8], m: &[u32; 16], t: u64, ultimo: bool) {
    let mut v = [0u32; 16];
    let mut i = 0;
    while i < 8 {
        v[i] = h[i];
        v[i + 8] = IV[i];
        i += 1;
    }
    v[12] ^= t as u32;
    v[13] ^= (t >> 32) as u32;
    if ultimo {
        v[14] = !v[14];
    }

    let mut r = 0;
    while r < 10 {
        let s = &SIGMA[r];
        g(&mut v, 0, 4, 8, 12, m[s[0] as usize], m[s[1] as usize]);
        g(&mut v, 1, 5, 9, 13, m[s[2] as usize], m[s[3] as usize]);
        g(&mut v, 2, 6, 10, 14, m[s[4] as usize], m[s[5] as usize]);
        g(&mut v, 3, 7, 11, 15, m[s[6] as usize], m[s[7] as usize]);
        g(&mut v, 0, 5, 10, 15, m[s[8] as usize], m[s[9] as usize]);
        g(&mut v, 1, 6, 11, 12, m[s[10] as usize], m[s[11] as usize]);
        g(&mut v, 2, 7, 8, 13, m[s[12] as usize], m[s[13] as usize]);
        g(&mut v, 3, 4, 9, 14, m[s[14] as usize], m[s[15] as usize]);
        r += 1;
    }

    i = 0;
    while i < 8 {
        h[i] ^= v[i] ^ v[i + 8];
        i += 1;
    }
}

/// El estado inicial de BLAKE2s-256 sin clave: `IV[0] ^ 0x01010000 ^ largo_de_salida`.
fn estado_inicial() -> [u32; 8] {
    let mut h = IV;
    h[0] ^= 0x0101_0020;
    h
}

/// Corre `n` compresiones encadenadas y devuelve una palabra del estado.
///
/// Se devuelve algo para que el optimizador no borre el trabajo, y se encadenan —cada bloque
/// depende del estado anterior— para que tampoco pueda sacarlas del bucle. Es la misma
/// construccion que `comprimir` de `guest-sha`.
#[no_mangle]
pub extern "C" fn comprimir(n: u32) -> u32 {
    let mut h = estado_inicial();
    let mut bloque = [0u32; 16];
    let mut k = 0;
    while k < n {
        bloque[0] = h[0] ^ k;
        bloque[15] = k;
        comprimir_uno(&mut h, &bloque, (k as u64 + 1) * 64, false);
        k += 1;
    }
    h[0]
}

/// La palabra `i` (0..8, little-endian) del BLAKE2s-256 de `"abc"`, calculado de verdad con
/// el estado inicial, el contador y la marca de ultimo bloque. **Es lo que valida el guest
/// contra el vector de la RFC 7693 Apendice B**: si esto no da, `comprimir` mide otra cosa.
#[no_mangle]
pub extern "C" fn digest_palabra(i: u32) -> u32 {
    let mut m = [0u32; 16];
    // "abc" en las tres primeras posiciones del bloque, little-endian.
    m[0] = u32::from_le_bytes([b'a', b'b', b'c', 0]);
    let mut h = estado_inicial();
    comprimir_uno(&mut h, &m, 3, true);
    h[(i & 7) as usize]
}

#[panic_handler]
fn panicked(_: &PanicInfo) -> ! {
    unsafe {
        core::arch::asm!("li a0, 0xdead", "ecall", "1: j 1b", options(noreturn));
    }
}
