//! Test 9 — guest RV32IM: verifica una firma ML-DSA-44 **que le entra por memoria**.
//!
//! Misma ABI que `guest-ed25519`: `entrada()` da la direccion del buffer, el host escribe
//! `clave || firma || mensaje` y llama `verificar(largo_clave, largo_firma, largo_msg)`.
//! El andamiaje bare-metal (`_start`, allocator, heap) es el de `guest-rv` de Test 2.

#![no_std]
#![no_main]

extern crate alloc;

mod alloc_ff;

use core::cell::UnsafeCell;
use core::panic::PanicInfo;
use ml_dsa::{EncodedSignature, EncodedVerifyingKey, MlDsa44, Signature, VerifyingKey};

/// Debe coincidir con MEM_SIZE / STACK de la maquina (igual que `guest-rv`).
const MEM_SIZE: u32 = 64 * 1024 * 1024;
const STACK: u32 = 1024 * 1024;
const HEAP_END: u32 = MEM_SIZE - STACK;

#[global_allocator]
static ALLOC: alloc_ff::FirstFit = alloc_ff::FirstFit;

extern "C" {
    static __heap_start: u8;
}

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
    call guest_init
    ecall
    "#
);

#[no_mangle]
pub extern "C" fn guest_init() {
    unsafe {
        let start = core::ptr::addr_of!(__heap_start) as usize;
        alloc_ff::init(start, HEAP_END as usize);
    }
}

const CAP: usize = 4096;
const LARGO_CLAVE: usize = 1312;
const LARGO_FIRMA: usize = 2420;

struct Buf(UnsafeCell<[u8; CAP]>);
unsafe impl Sync for Buf {}
static ENTRADA: Buf = Buf(UnsafeCell::new([0; CAP]));

#[no_mangle]
pub extern "C" fn entrada() -> u32 {
    ENTRADA.0.get() as u32
}

const CTX: &[u8] = b"";

#[no_mangle]
pub extern "C" fn verificar(largo_clave: u32, largo_firma: u32, largo_msg: u32) -> u32 {
    let (lc, lf, lm) = (largo_clave as usize, largo_firma as usize, largo_msg as usize);
    if lc != LARGO_CLAVE || lf != LARGO_FIRMA || lm > CAP - LARGO_CLAVE - LARGO_FIRMA {
        return 0;
    }
    let buf = unsafe { &*ENTRADA.0.get() };
    let clave = &buf[..LARGO_CLAVE];
    let firma = &buf[LARGO_CLAVE..LARGO_CLAVE + LARGO_FIRMA];
    let msg = &buf[LARGO_CLAVE + LARGO_FIRMA..LARGO_CLAVE + LARGO_FIRMA + lm];

    let enc_vk = match EncodedVerifyingKey::<MlDsa44>::try_from(clave) {
        Ok(e) => e,
        Err(_) => return 0,
    };
    let enc_sig = match EncodedSignature::<MlDsa44>::try_from(firma) {
        Ok(e) => e,
        Err(_) => return 0,
    };
    let vk = VerifyingKey::<MlDsa44>::decode(&enc_vk);
    match Signature::<MlDsa44>::decode(&enc_sig) {
        Some(sig) => vk.verify_with_context(msg, CTX, &sig) as u32,
        None => 0,
    }
}

#[panic_handler]
fn panicked(_: &PanicInfo) -> ! {
    unsafe {
        core::arch::asm!("li a0, 0xdead", "ecall", "1: j 1b", options(noreturn));
    }
}
