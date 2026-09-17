//! Mismo `decode+verify`, como codigo nativo — la fila `native` de la tabla.

use std::time::Instant;

use ml_dsa::{B32, EncodedSignature, EncodedVerifyingKey, ExpandedSigningKey, MlDsa44};
use signature::{Keypair, Signer, Verifier};
use slh_dsa::{Sha2_128s, Signature as SlhSignature, SigningKey as SlhSigningKey};

const ITERS: u32 = 300;
const MSG32: [u8; 32] = [0x5a; 32];
const CTX: &[u8] = b"";

fn bench_ml_dsa44() -> f64 {
    let seed: B32 = [0x11u8; 32].into();
    let sk = ExpandedSigningKey::<MlDsa44>::from_seed(&seed);
    let vk_bytes = sk.verifying_key().encode().to_vec();
    let sig_bytes = sk.sign_deterministic(&MSG32, CTX).expect("sign").encode().to_vec();

    let run = || -> bool {
        let enc_vk = EncodedVerifyingKey::<MlDsa44>::try_from(vk_bytes.as_slice()).unwrap();
        let enc_sig = EncodedSignature::<MlDsa44>::try_from(sig_bytes.as_slice()).unwrap();
        let vk = ml_dsa::VerifyingKey::<MlDsa44>::decode(&enc_vk);
        match ml_dsa::Signature::<MlDsa44>::decode(&enc_sig) {
            Some(sig) => vk.verify_with_context(&MSG32, CTX, &sig),
            None => false,
        }
    };
    for _ in 0..10 {
        run();
    }
    let start = Instant::now();
    for _ in 0..ITERS {
        assert!(run());
    }
    start.elapsed().as_secs_f64() / ITERS as f64 * 1e6
}

fn bench_slh_dsa_128s() -> f64 {
    let mut rng = rand::thread_rng();
    let sk = SlhSigningKey::<Sha2_128s>::new(&mut rng);
    let vk_bytes = sk.verifying_key().to_bytes();
    let sig = sk.sign(&MSG32);
    let sig_bytes = signature::SignatureEncoding::to_bytes(&sig);

    let run = || -> bool {
        let vk = slh_dsa::VerifyingKey::<Sha2_128s>::try_from(vk_bytes.as_slice()).unwrap();
        let sig = SlhSignature::<Sha2_128s>::try_from(sig_bytes.as_slice()).unwrap();
        vk.verify(&MSG32, &sig).is_ok()
    };
    for _ in 0..10 {
        run();
    }
    let start = Instant::now();
    for _ in 0..ITERS {
        assert!(run());
    }
    start.elapsed().as_secs_f64() / ITERS as f64 * 1e6
}

fn main() {
    let ml = bench_ml_dsa44();
    println!("ML-DSA-44    native decode+verify: {ml:.1} us/op ({:.0} ops/s)", 1e6 / ml);
    let slh = bench_slh_dsa_128s();
    println!(
        "SLH-DSA-128s native decode+verify: {slh:.1} us/op ({:.0} ops/s)  [{:.1}x ML-DSA-44]",
        1e6 / slh,
        slh / ml
    );
}
