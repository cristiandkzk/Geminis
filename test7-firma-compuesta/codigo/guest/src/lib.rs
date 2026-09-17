//! Test 7 — nucleo compartido, mismo patron que pqcore de Test 2.
//!
//! `decode + verify` de las dos primitivas de una firma compuesta, en el mismo
//! modulo wasm, para que host mida las dos bajo exactamente el mismo motor:
//!   - `run_ml_dsa44`   — la primitiva ya elegida en Test 2.
//!   - `run_slh_dsa128s` — candidata a segunda familia, hash-based, sin nucleo
//!     compartido con ML-DSA (§10.1, "el linaje y la firma no comparten nucleo").
//!
//! ML-DSA usa una semilla fija como pqcore::fixture (determinista, sin RNG en
//! el guest). SLH-DSA no tiene ese camino en esta version del crate, asi que
//! su clave/firma salen pre-generadas una vez y viajan como bytes fijos en
//! `fixture.rs` — el guest solo decodifica y verifica, igual que un nodo real.

use ml_dsa::{B32, EncodedSignature, EncodedVerifyingKey, ExpandedSigningKey, MlDsa44};
use signature::Verifier;
use slh_dsa::{Sha2_128s, Signature as SlhSignature, VerifyingKey as SlhVerifyingKey};

mod fixture;
use fixture::{SIG_BYTES as SLH_SIG_BYTES, VK_BYTES as SLH_VK_BYTES};

const MSG32: [u8; 32] = [0x5a; 32];
const CTX: &[u8] = b"";

#[no_mangle]
pub extern "C" fn run_ml_dsa44(iters: u32) -> u32 {
    let seed: B32 = [0x11u8; 32].into();
    let sk = ExpandedSigningKey::<MlDsa44>::from_seed(&seed);
    let vk_bytes = sk.verifying_key().encode().to_vec();
    let sig_bytes = sk
        .sign_deterministic(&MSG32, CTX)
        .expect("sign")
        .encode()
        .to_vec();

    let mut ok = 0u32;
    for _ in 0..iters {
        let enc_vk = match EncodedVerifyingKey::<MlDsa44>::try_from(vk_bytes.as_slice()) {
            Ok(v) => v,
            Err(_) => continue,
        };
        let enc_sig = match EncodedSignature::<MlDsa44>::try_from(sig_bytes.as_slice()) {
            Ok(s) => s,
            Err(_) => continue,
        };
        let vk = ml_dsa::VerifyingKey::<MlDsa44>::decode(&enc_vk);
        if let Some(sig) = ml_dsa::Signature::<MlDsa44>::decode(&enc_sig) {
            if vk.verify_with_context(&MSG32, CTX, &sig) {
                ok += 1;
            }
        }
    }
    ok
}

#[no_mangle]
pub extern "C" fn run_slh_dsa128s(iters: u32) -> u32 {
    let mut ok = 0u32;
    for _ in 0..iters {
        let vk = match SlhVerifyingKey::<Sha2_128s>::try_from(SLH_VK_BYTES) {
            Ok(v) => v,
            Err(_) => continue,
        };
        let sig = match SlhSignature::<Sha2_128s>::try_from(SLH_SIG_BYTES) {
            Ok(s) => s,
            Err(_) => continue,
        };
        if vk.verify(&MSG32, &sig).is_ok() {
            ok += 1;
        }
    }
    ok
}
