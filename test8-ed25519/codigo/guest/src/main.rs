//! Test 8 — guest RV32IM de verificacion Ed25519.
//!
//! Misma ABI que el guest de ML-DSA de Test 2: `prepare()` fabrica el material una vez
//! (fuera de lo que se mide) y `run(modo, iters)` verifica `iters` veces. El host mide
//! pasos por diferencia entre dos tandas, asi el marco de la llamada se cancela.
//!
//! Modos:
//!   0  decodifica la clave desde bytes + `verify`        (par de `decode+verify` de ML-DSA)
//!   1  `verify` con la clave ya decodificada             (par de `verify_only`)
//!   2  decodifica + `verify_strict`                      (la variante que se usaria en cadena)
//!   3  control negativo: firma con un bit alterado       (tiene que dar 0 exitos)
//!   4  vector 1 de RFC 8032 §7.1                         (ancla externa: no es autoconsistencia)

#![no_std]
#![no_main]

use core::cell::UnsafeCell;
use core::hint::black_box;
use core::panic::PanicInfo;
use ed25519_dalek::{Signature, Signer, SigningKey, Verifier, VerifyingKey};

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

/// Semilla y mensaje fijos. El mensaje es de 32 bytes, el tamano de un hash de
/// transaccion: el mismo que usa el guest de ML-DSA, para que los dos numeros firmen
/// lo mismo. (Con 32 bytes el SHA-512 interno de Ed25519 hashea R||A||M = 96 bytes: un
/// solo bloque.)
const SEED: [u8; 32] = [0x11; 32];
const MSG: [u8; 32] = [0x5a; 32];

/// RFC 8032 §7.1, TEST 1 (mensaje vacio).
const RFC_PK: [u8; 32] = [
    0xd7, 0x5a, 0x98, 0x01, 0x82, 0xb1, 0x0a, 0xb7, 0xd5, 0x4b, 0xfe, 0xd3, 0xc9, 0x64, 0x07,
    0x3a, 0x0e, 0xe1, 0x72, 0xf3, 0xda, 0xa6, 0x23, 0x25, 0xaf, 0x02, 0x1a, 0x68, 0xf7, 0x07,
    0x51, 0x1a,
];
const RFC_SIG: [u8; 64] = [
    0xe5, 0x56, 0x43, 0x00, 0xc3, 0x60, 0xac, 0x72, 0x90, 0x86, 0xe2, 0xcc, 0x80, 0x6e, 0x82,
    0x8a, 0x84, 0x87, 0x7f, 0x1e, 0xb8, 0xe5, 0xd9, 0x74, 0xd8, 0x73, 0xe0, 0x65, 0x22, 0x49,
    0x01, 0x55, 0x5f, 0xb8, 0x82, 0x15, 0x90, 0xa3, 0x3b, 0xac, 0xc6, 0x1e, 0x39, 0x70, 0x1c,
    0xf9, 0xb4, 0x6b, 0xd2, 0x5b, 0xf5, 0xf0, 0x59, 0x5b, 0xbe, 0x24, 0x65, 0x51, 0x41, 0x43,
    0x8e, 0x7a, 0x10, 0x0b,
];

struct Slot<T>(UnsafeCell<T>);
unsafe impl<T> Sync for Slot<T> {}

static PK: Slot<[u8; 32]> = Slot(UnsafeCell::new([0; 32]));
static SIG: Slot<[u8; 64]> = Slot(UnsafeCell::new([0; 64]));
static BAD: Slot<[u8; 64]> = Slot(UnsafeCell::new([0; 64]));
static VK: Slot<Option<VerifyingKey>> = Slot(UnsafeCell::new(None));

#[no_mangle]
pub extern "C" fn prepare() -> u32 {
    let sk = SigningKey::from_bytes(&SEED);
    let vk = sk.verifying_key();
    let sig = sk.sign(&MSG).to_bytes();
    let mut bad = sig;
    bad[10] ^= 1;
    unsafe {
        *PK.0.get() = vk.to_bytes();
        *SIG.0.get() = sig;
        *BAD.0.get() = bad;
        *VK.0.get() = Some(vk);
    }
    1
}

#[no_mangle]
pub extern "C" fn run(modo: u32, iters: u32) -> u32 {
    let mut ok = 0u32;
    unsafe {
        let pk = *PK.0.get();
        let sig = Signature::from_bytes(&*SIG.0.get());
        let bad = Signature::from_bytes(&*BAD.0.get());
        let rfc_sig = Signature::from_bytes(&RFC_SIG);
        let pre = (*VK.0.get()).as_ref().unwrap();
        for _ in 0..iters {
            // `black_box` en las entradas: que el optimizador no saque la verificacion
            // del lazo por ser invariante. La cuenta de exitos es el otro seguro.
            let pk = black_box(&pk);
            let hecho = match modo {
                0 => VerifyingKey::from_bytes(pk)
                    .map(|vk| vk.verify(black_box(&MSG), &sig).is_ok())
                    .unwrap_or(false),
                1 => pre.verify(black_box(&MSG), &sig).is_ok(),
                2 => VerifyingKey::from_bytes(pk)
                    .map(|vk| vk.verify_strict(black_box(&MSG), &sig).is_ok())
                    .unwrap_or(false),
                3 => VerifyingKey::from_bytes(pk)
                    .map(|vk| vk.verify(black_box(&MSG), &bad).is_ok())
                    .unwrap_or(false),
                _ => VerifyingKey::from_bytes(black_box(&RFC_PK))
                    .map(|vk| vk.verify(black_box(&[]), &rfc_sig).is_ok())
                    .unwrap_or(false),
            };
            if hecho {
                ok += 1;
            }
        }
    }
    ok
}

/// Un panic sale por `ecall` con 0xDEAD en a0.
#[panic_handler]
fn panicked(_: &PanicInfo) -> ! {
    unsafe {
        core::arch::asm!("li a0, 0xdead", "ecall", "1: j 1b", options(noreturn));
    }
}
