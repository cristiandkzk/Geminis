//! Test 9 — el binario que la prueba Python invoca.
//!
//!     vm-firma firmar    <ed25519|ml-dsa-44> <semilla-hex-32> <mensaje-hex>   -> pk=..  sig=..
//!     vm-firma verificar <ed25519|ml-dsa-44> <pk-hex> <sig-hex> <mensaje-hex> <techo-pasos> <techo-paginas>
//!                                                                              -> en la maquina
//!     vm-firma nativo    <ed25519|ml-dsa-44> <pk-hex> <sig-hex> <mensaje-hex> -> en x86
//!
//! `verificar` hace lo que hace un nodo: admite el binario, lo arranca, escribe la carga en
//! el buffer del guest, **pone los dos techos que le pasan (los del ruleset vigente)** y recien ahi llama. El
//! veredicto es "acepta" solo si el guest retorna 1 sin pasarse de pasos ni de paginas.

use ed25519_dalek::{Signer, SigningKey, VerifyingKey as EdVk};
use ml_dsa::{
    B32, EncodedSignature, EncodedVerifyingKey, ExpandedSigningKey, MlDsa44, Signature, VerifyingKey,
};
use vm::maquina::Veredicto;

const GUEST_ED: &[u8] = include_bytes!("../../guest-ed25519/guest.elf");
const GUEST_ML: &[u8] = include_bytes!("../../guest-mldsa44/guest.elf");
const CTX: &[u8] = b"";

fn hex(b: &[u8]) -> String {
    b.iter().map(|x| format!("{:02x}", x)).collect()
}

fn unhex(s: &str) -> Vec<u8> {
    assert!(s.len() % 2 == 0, "hex de largo impar");
    (0..s.len())
        .step_by(2)
        .map(|i| u8::from_str_radix(&s[i..i + 2], 16).expect("hex invalido"))
        .collect()
}

fn firmar(formato: &str, semilla: &[u8], msg: &[u8]) -> (Vec<u8>, Vec<u8>) {
    match formato {
        "ed25519" => {
            let sk = SigningKey::from_bytes(semilla.try_into().expect("semilla de 32 bytes"));
            (sk.verifying_key().to_bytes().to_vec(), sk.sign(msg).to_bytes().to_vec())
        }
        "ml-dsa-44" => {
            let s: [u8; 32] = semilla.try_into().expect("semilla de 32 bytes");
            let seed: B32 = s.into();
            let sk = ExpandedSigningKey::<MlDsa44>::from_seed(&seed);
            let sig = sk.sign_deterministic(msg, CTX).expect("firmar");
            (sk.verifying_key().encode().to_vec(), sig.encode().to_vec())
        }
        otro => panic!("formato desconocido: {otro}"),
    }
}

fn nativo(formato: &str, pk: &[u8], sig: &[u8], msg: &[u8]) -> bool {
    match formato {
        "ed25519" => {
            let (Ok(pk), Ok(sig)) = (<[u8; 32]>::try_from(pk), <[u8; 64]>::try_from(sig)) else {
                return false;
            };
            let Ok(vk) = EdVk::from_bytes(&pk) else { return false };
            vk.verify_strict(msg, &ed25519_dalek::Signature::from_bytes(&sig)).is_ok()
        }
        "ml-dsa-44" => {
            let Ok(enc_vk) = EncodedVerifyingKey::<MlDsa44>::try_from(pk) else { return false };
            let Ok(enc_sig) = EncodedSignature::<MlDsa44>::try_from(sig) else { return false };
            let vk = VerifyingKey::<MlDsa44>::decode(&enc_vk);
            match Signature::<MlDsa44>::decode(&enc_sig) {
                Some(s) => vk.verify_with_context(msg, CTX, &s),
                None => false,
            }
        }
        otro => panic!("formato desconocido: {otro}"),
    }
}

fn en_la_maquina(
    formato: &str,
    pk: &[u8],
    sig: &[u8],
    msg: &[u8],
    techo_pasos: u64,
    techo_paginas: u32,
) {
    let elf = match formato {
        "ed25519" => GUEST_ED,
        "ml-dsa-44" => GUEST_ML,
        otro => panic!("formato desconocido: {otro}"),
    };
    let (mut m, syms) = vm::admitir(elf, u64::MAX).expect("admitir el guest");

    // Arranque y andamiaje: sin techo, y no se le cobra a la verificacion.
    m.techo = u64::MAX;
    m.techo_paginas = u32::MAX;
    m.arrancar();
    let entrada = *syms.get("entrada").expect("simbolo entrada");
    let verificar = *syms.get("verificar").expect("simbolo verificar");
    let dir = match m.llamar(entrada, &[]) {
        Veredicto::Retorno(a) => a,
        otro => panic!("entrada() no retorno: {:?}", otro),
    };
    let mut carga = pk.to_vec();
    carga.extend_from_slice(sig);
    carga.extend_from_slice(msg);
    assert!(m.escribir(dir, &carga), "no entro en el buffer del guest");

    // Los dos techos como los pone un nodo, contados desde cero para esta verificacion. Los
    // dicta el ruleset vigente (los pasa quien invoca), no una constante de este binario.
    let base = m.pasos;
    m.techo = base + techo_pasos;
    m.borrar_paginas();
    m.techo_paginas = techo_paginas;
    let v = m.llamar(verificar, &[pk.len() as u32, sig.len() as u32, msg.len() as u32]);
    let acepta = matches!(v, Veredicto::Retorno(1));
    println!(
        "veredicto={:?} acepta={} pasos={} paginas={}",
        v,
        acepta as u8,
        m.pasos - base,
        m.paginas_usadas
    );
}

fn main() {
    let a: Vec<String> = std::env::args().collect();
    match (a.get(1).map(String::as_str), a.len()) {
        (Some("firmar"), 5) => {
            let (pk, sig) = firmar(&a[2], &unhex(&a[3]), &unhex(&a[4]));
            println!("pk={}", hex(&pk));
            println!("sig={}", hex(&sig));
        }
        (Some("verificar"), 8) => en_la_maquina(
            &a[2],
            &unhex(&a[3]),
            &unhex(&a[4]),
            &unhex(&a[5]),
            a[6].parse().expect("techo de pasos"),
            a[7].parse().expect("techo de paginas"),
        ),
        (Some("nativo"), 6) => {
            println!("acepta={}", nativo(&a[2], &unhex(&a[3]), &unhex(&a[4]), &unhex(&a[5])) as u8)
        }
        _ => {
            eprintln!("uso: vm-firma firmar|verificar|nativo <ed25519|ml-dsa-44> ...");
            std::process::exit(2);
        }
    }
}
