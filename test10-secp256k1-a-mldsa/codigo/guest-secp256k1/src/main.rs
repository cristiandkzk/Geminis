//! Test 10 — guest RV32IM: verifica una firma ECDSA secp256k1 **que le entra por memoria**.
//!
//! Misma ABI que `test9-…/guest-ed25519` y `guest-mldsa44`: el host pregunta donde esta el buffer con
//! `entrada()`, escribe ahi la carga y llama. Dos funciones:
//!
//!   `verificar(largo_clave, largo_firma, largo_msg)`   carga: `clave(33) || firma(64) || hash(32)`
//!       Devuelve 1 si acepta. La clave es SEC1 comprimida, la firma es `r || s` y el mensaje es el
//!       **hash de 32 bytes** (en Ethereum, keccak256 de la transaccion: se firma el hash, no el
//!       mensaje). **Rechaza `s` alto**: es la regla de EIP-2 (una firma con `s` alto es una
//!       maleabilidad y Ethereum no la acepta).
//!
//!   `recuperar(recid)`   carga: `firma(64) || hash(32)`
//!       Es `ecrecover`, lo que de verdad hace Ethereum: no recibe la clave, la **recupera** de la
//!       firma. Escribe la clave publica SEC1 sin comprimir (65 bytes) al principio del buffer y
//!       devuelve 65, o 0 si no recupera nada.

#![no_std]
#![no_main]

use core::cell::UnsafeCell;
use core::panic::PanicInfo;
use k256::ecdsa::signature::hazmat::PrehashVerifier;
use k256::ecdsa::{RecoveryId, Signature, VerifyingKey};

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
    // Un largo que no es el de secp256k1 no es una firma secp256k1: rechaza sin tocar la curva.
    if largo_clave != 33 || largo_firma != 64 || largo_msg != 32 {
        return 0;
    }
    let buf = unsafe { &*ENTRADA.0.get() };
    let vk = match VerifyingKey::from_sec1_bytes(&buf[..33]) {
        Ok(vk) => vk,
        Err(_) => return 0,
    };
    let sig = match Signature::from_slice(&buf[33..97]) {
        Ok(s) => s,
        Err(_) => return 0,
    };
    // EIP-2: `s` alto no se acepta. `normalize_s` devuelve `Some` cuando la firma NO estaba normalizada.
    if sig.normalize_s().is_some() {
        return 0;
    }
    vk.verify_prehash(&buf[97..129], &sig).is_ok() as u32
}

#[no_mangle]
pub extern "C" fn recuperar(recid: u32) -> u32 {
    let buf = unsafe { &mut *ENTRADA.0.get() };
    let sig = match Signature::from_slice(&buf[..64]) {
        Ok(s) => s,
        Err(_) => return 0,
    };
    let id = match RecoveryId::from_byte(recid as u8) {
        Some(id) => id,
        None => return 0,
    };
    let vk = match VerifyingKey::recover_from_prehash(&buf[64..96], &sig, id) {
        Ok(vk) => vk,
        Err(_) => return 0,
    };
    let punto = vk.to_encoded_point(false);
    let bytes = punto.as_bytes();
    if bytes.len() != 65 {
        return 0;
    }
    buf[..65].copy_from_slice(bytes);
    65
}

#[panic_handler]
fn panicked(_: &PanicInfo) -> ! {
    unsafe {
        core::arch::asm!("li a0, 0xdead", "ecall", "1: j 1b", options(noreturn));
    }
}
