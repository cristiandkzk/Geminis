//! Test 11 — guest RV32IM: **multisig k-de-n on-chain** con firmas ML-DSA-44 sueltas.
//!
//! Es lo que costaria proteger una cuenta con varios dispositivos SIN firma umbral: la cadena
//! verifica `k` firmas y reconstruye la direccion desde las `n` claves. Se mide contra la
//! verificacion simple (`guest-mldsa44`) para saber que compra el umbral criptografico.
//!
//! ABI (igual que los otros guests: la carga entra por memoria):
//!   `entrada()` da la direccion del buffer; el host escribe
//!     direccion(32) || indices(k) || claves(n * 1312) || firmas(k * 2420) || mensaje
//!   y llama `verificar(n, k, largo_msg)`. Devuelve 1 si y solo si
//!     - la direccion es BLAKE2s-256 de las `n` claves concatenadas,
//!     - los `k` indices son estrictamente crecientes y menores que `n` (sin repetir firmante),
//!     - las `k` firmas verifican, cada una bajo la clave que indica su indice.

#![no_std]
#![no_main]

extern crate alloc;

mod alloc_ff;

use blake2::{Blake2s256, Digest};
use core::cell::UnsafeCell;
use core::panic::PanicInfo;
use ml_dsa::{EncodedSignature, EncodedVerifyingKey, MlDsa44, Signature, VerifyingKey};

/// Debe coincidir con MEM_SIZE / STACK de la maquina (igual que `guest-mldsa44`).
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

/// 8 claves + 8 firmas + direccion + indices + mensaje caben de sobra.
const CAP: usize = 32 * 1024;
const LARGO_CLAVE: usize = 1312;
const LARGO_FIRMA: usize = 2420;
const MAX_N: usize = 8;

struct Buf(UnsafeCell<[u8; CAP]>);
unsafe impl Sync for Buf {}
static ENTRADA: Buf = Buf(UnsafeCell::new([0; CAP]));

#[no_mangle]
pub extern "C" fn entrada() -> u32 {
    ENTRADA.0.get() as u32
}

const CTX: &[u8] = b"";

#[no_mangle]
pub extern "C" fn verificar(n: u32, k: u32, largo_msg: u32) -> u32 {
    let (n, k, lm) = (n as usize, k as usize, largo_msg as usize);
    if n == 0 || n > MAX_N || k == 0 || k > n {
        return 0;
    }
    let total = 32 + k + n * LARGO_CLAVE + k * LARGO_FIRMA + lm;
    if total > CAP {
        return 0;
    }
    let buf = unsafe { &*ENTRADA.0.get() };
    let dir = &buf[..32];
    let idx = &buf[32..32 + k];
    let claves = &buf[32 + k..32 + k + n * LARGO_CLAVE];
    let firmas = &buf[32 + k + n * LARGO_CLAVE..32 + k + n * LARGO_CLAVE + k * LARGO_FIRMA];
    let msg = &buf[32 + k + n * LARGO_CLAVE + k * LARGO_FIRMA..total];

    // La direccion ata las n claves: sin esto cualquiera presentaria claves propias.
    let mut h = Blake2s256::new();
    h.update(claves);
    if h.finalize().as_slice() != dir {
        return 0;
    }

    // Firmantes distintos: indices estrictamente crecientes y dentro de rango.
    let mut previo: isize = -1;
    for j in 0..k {
        let i = idx[j] as usize;
        if i >= n || (i as isize) <= previo {
            return 0;
        }
        previo = i as isize;
    }

    for j in 0..k {
        let i = idx[j] as usize;
        let clave = &claves[i * LARGO_CLAVE..(i + 1) * LARGO_CLAVE];
        let firma = &firmas[j * LARGO_FIRMA..(j + 1) * LARGO_FIRMA];
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
            Some(sig) => {
                if !vk.verify_with_context(msg, CTX, &sig) {
                    return 0;
                }
            }
            None => return 0,
        }
    }
    1
}

#[panic_handler]
fn panicked(_: &PanicInfo) -> ! {
    unsafe {
        core::arch::asm!("li a0, 0xdead", "ecall", "1: j 1b", options(noreturn));
    }
}
