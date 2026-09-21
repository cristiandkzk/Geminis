//! Test 9 — guest RV32IM: verifica una firma Ed25519 **que le entra por memoria**.
//!
//! A diferencia del de Test 8 (que fabrica su propio material), este recibe lo que
//! recibiria un predicado real: el host pregunta donde esta el buffer con `entrada()`, escribe
//! ahi `clave || firma || mensaje` y llama `verificar(largo_clave, largo_firma, largo_msg)`.
//! Devuelve 1 si acepta y 0 si no. Usa `verify_strict`, la variante que usaria una cadena.

#![no_std]
#![no_main]

use core::cell::UnsafeCell;
use core::panic::PanicInfo;
use ed25519_dalek::{Signature, VerifyingKey};

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

const CAP: usize = 4096;

struct Buf(UnsafeCell<[u8; CAP]>);
unsafe impl Sync for Buf {}
static ENTRADA: Buf = Buf(UnsafeCell::new([0; CAP]));

/// La direccion del buffer de entrada, para que el host escriba ahi.
#[no_mangle]
pub extern "C" fn entrada() -> u32 {
    ENTRADA.0.get() as u32
}

#[no_mangle]
pub extern "C" fn verificar(largo_clave: u32, largo_firma: u32, largo_msg: u32) -> u32 {
    let (lc, lf, lm) = (largo_clave as usize, largo_firma as usize, largo_msg as usize);
    // Un largo que no es el de Ed25519 no es una firma Ed25519: rechaza sin tocar la curva.
    if lc != 32 || lf != 64 || lm > CAP - 96 {
        return 0;
    }
    let buf = unsafe { &*ENTRADA.0.get() };
    let mut clave = [0u8; 32];
    clave.copy_from_slice(&buf[..32]);
    let mut firma = [0u8; 64];
    firma.copy_from_slice(&buf[32..96]);
    let msg = &buf[96..96 + lm];

    let vk = match VerifyingKey::from_bytes(&clave) {
        Ok(vk) => vk,
        Err(_) => return 0,
    };
    let sig = Signature::from_bytes(&firma);
    vk.verify_strict(msg, &sig).is_ok() as u32
}

#[panic_handler]
fn panicked(_: &PanicInfo) -> ! {
    unsafe {
        core::arch::asm!("li a0, 0xdead", "ecall", "1: j 1b", options(noreturn));
    }
}
