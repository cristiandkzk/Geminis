//! Test 10 — el binario que la prueba Python invoca.
//!
//!     vm-firma10 firmar    <secp256k1|ml-dsa-44> <semilla-hex-32> <hash-o-mensaje-hex>
//!                              -> pk=.. sig=..            (secp256k1 agrega recid=..)
//!     vm-firma10 verificar <secp256k1|ml-dsa-44> <pk> <sig> <msg> <techo-pasos> <techo-paginas>   -> en la maquina
//!     vm-firma10 nativo    <secp256k1|ml-dsa-44> <pk> <sig> <msg>                                 -> en x86
//!     vm-firma10 recuperar <sig-hex> <hash-hex> <recid> <techo-pasos> <techo-paginas>             -> ecrecover en la maquina
//!     vm-firma10 direccion <pk-comprimida-hex>                                                    -> direccion de Ethereum (nativo)
//!     vm-firma10 alterar-s <sig-hex>                                                              -> la firma con `s` alto
//!
//! Igual que en Test 9, `verificar` hace lo que hace un nodo: admite el binario, lo arranca, escribe la carga en
//! el buffer del guest, **pone los dos techos que le pasan (los del ruleset vigente)** y recien ahi llama.

use k256::ecdsa::signature::hazmat::PrehashVerifier;
use k256::ecdsa::{Signature as KSig, SigningKey, VerifyingKey as KVk};
use ml_dsa::{
    B32, EncodedSignature, EncodedVerifyingKey, ExpandedSigningKey, MlDsa44, Signature, VerifyingKey,
};
use sha3::{Digest, Keccak256};
use vm::maquina::Veredicto;

const GUEST_SECP: &[u8] = include_bytes!("../../guest-secp256k1/guest.elf");
/// El mismo binario de ML-DSA-44 de Test 9: una sola fuente, no una copia.
const GUEST_ML: &[u8] = include_bytes!("../../../../test9-ed25519-a-mldsa/codigo/guest-mldsa44/guest.elf");
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

/// La direccion de Ethereum: los ultimos 20 bytes del keccak256 de la clave publica **sin el prefijo 0x04**.
fn direccion_de(sin_comprimir: &[u8]) -> String {
    assert_eq!(sin_comprimir.len(), 65, "clave SEC1 sin comprimir");
    let h = Keccak256::digest(&sin_comprimir[1..]);
    format!("0x{}", hex(&h[12..]))
}

fn firmar(formato: &str, semilla: &[u8], msg: &[u8]) {
    match formato {
        "secp256k1" => {
            let sk = SigningKey::from_slice(semilla).expect("clave privada valida");
            let (sig, recid) = sk.sign_prehash_recoverable(msg).expect("firmar");
            let pk = sk.verifying_key().to_encoded_point(true);
            println!("pk={}", hex(pk.as_bytes()));
            println!("sig={}", hex(&sig.to_bytes()));
            println!("recid={}", recid.to_byte());
        }
        "ml-dsa-44" => {
            let s: [u8; 32] = semilla.try_into().expect("semilla de 32 bytes");
            let seed: B32 = s.into();
            let sk = ExpandedSigningKey::<MlDsa44>::from_seed(&seed);
            let sig = sk.sign_deterministic(msg, CTX).expect("firmar");
            println!("pk={}", hex(&sk.verifying_key().encode()));
            println!("sig={}", hex(&sig.encode()));
        }
        otro => panic!("formato desconocido: {otro}"),
    }
}

fn nativo(formato: &str, pk: &[u8], sig: &[u8], msg: &[u8]) -> bool {
    match formato {
        "secp256k1" => {
            let Ok(vk) = KVk::from_sec1_bytes(pk) else { return false };
            let Ok(s) = KSig::from_slice(sig) else { return false };
            if s.normalize_s().is_some() {
                return false; // EIP-2: `s` alto no se acepta
            }
            vk.verify_prehash(msg, &s).is_ok()
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

/// Arranca el guest como lo hace un nodo y le escribe la carga. Devuelve la maquina lista para llamar.
fn preparar(elf: &[u8], carga: &[u8]) -> (vm::maquina::Maquina, std::collections::BTreeMap<String, u32>, u32) {
    let (mut m, syms) = vm::admitir(elf, u64::MAX).expect("admitir el guest");
    m.techo = u64::MAX;
    m.techo_paginas = u32::MAX;
    m.arrancar();
    let entrada = *syms.get("entrada").expect("simbolo entrada");
    let dir = match m.llamar(entrada, &[]) {
        Veredicto::Retorno(a) => a,
        otro => panic!("entrada() no retorno: {:?}", otro),
    };
    assert!(m.escribir(dir, carga), "no entro en el buffer del guest");
    (m, syms.into_iter().collect(), dir)
}

fn poner_techos(m: &mut vm::maquina::Maquina, techo_pasos: u64, techo_paginas: u32) -> u64 {
    let base = m.pasos;
    m.techo = base + techo_pasos;
    m.borrar_paginas();
    m.techo_paginas = techo_paginas;
    base
}

fn en_la_maquina(formato: &str, pk: &[u8], sig: &[u8], msg: &[u8], techo_pasos: u64, techo_paginas: u32) {
    let elf = match formato {
        "secp256k1" => GUEST_SECP,
        "ml-dsa-44" => GUEST_ML,
        otro => panic!("formato desconocido: {otro}"),
    };
    let mut carga = pk.to_vec();
    carga.extend_from_slice(sig);
    carga.extend_from_slice(msg);
    let (mut m, syms, _) = preparar(elf, &carga);
    let verificar = *syms.get("verificar").expect("simbolo verificar");
    let base = poner_techos(&mut m, techo_pasos, techo_paginas);
    let v = m.llamar(verificar, &[pk.len() as u32, sig.len() as u32, msg.len() as u32]);
    let acepta = matches!(v, Veredicto::Retorno(1));
    println!("veredicto={:?} acepta={} pasos={} paginas={}", v, acepta as u8, m.pasos - base, m.paginas_usadas);
}

fn recuperar(sig: &[u8], hash: &[u8], recid: u32, techo_pasos: u64, techo_paginas: u32) {
    let mut carga = sig.to_vec();
    carga.extend_from_slice(hash);
    let (mut m, syms, dir) = preparar(GUEST_SECP, &carga);
    let recuperar = *syms.get("recuperar").expect("simbolo recuperar");
    let base = poner_techos(&mut m, techo_pasos, techo_paginas);
    let v = m.llamar(recuperar, &[recid]);
    let pasos = m.pasos - base;
    let paginas = m.paginas_usadas;
    match v {
        Veredicto::Retorno(65) => {
            // El guest dejo la clave sin comprimir (65 bytes) al principio del buffer: se lee de su memoria.
            let mut clave = Vec::with_capacity(68);
            for i in 0..17u32 {
                let w = m.leer32(dir + 4 * i).expect("leer la salida del guest");
                clave.extend_from_slice(&w.to_le_bytes());
            }
            clave.truncate(65);
            println!(
                "veredicto={:?} acepta=1 pasos={} paginas={} clave={} direccion={}",
                v, pasos, paginas, hex(&clave), direccion_de(&clave)
            );
        }
        otro => println!("veredicto={:?} acepta=0 pasos={} paginas={}", otro, pasos, paginas),
    }
}

fn main() {
    let a: Vec<String> = std::env::args().collect();
    match (a.get(1).map(String::as_str), a.len()) {
        (Some("firmar"), 5) => firmar(&a[2], &unhex(&a[3]), &unhex(&a[4])),
        (Some("verificar"), 8) => en_la_maquina(
            &a[2], &unhex(&a[3]), &unhex(&a[4]), &unhex(&a[5]),
            a[6].parse().expect("techo de pasos"), a[7].parse().expect("techo de paginas"),
        ),
        (Some("nativo"), 6) => {
            println!("acepta={}", nativo(&a[2], &unhex(&a[3]), &unhex(&a[4]), &unhex(&a[5])) as u8)
        }
        (Some("recuperar"), 7) => recuperar(
            &unhex(&a[2]), &unhex(&a[3]), a[4].parse().expect("recid"),
            a[5].parse().expect("techo de pasos"), a[6].parse().expect("techo de paginas"),
        ),
        (Some("direccion"), 3) => {
            let vk = KVk::from_sec1_bytes(&unhex(&a[2])).expect("clave SEC1");
            println!("direccion={}", direccion_de(vk.to_encoded_point(false).as_bytes()));
        }
        (Some("alterar-s"), 3) => {
            let s = KSig::from_slice(&unhex(&a[2])).expect("firma de 64 bytes");
            let alta = KSig::from_scalars(*s.r(), -*s.s()).expect("firma con s alto");
            println!("sig={}", hex(&alta.to_bytes()));
        }
        _ => {
            eprintln!("uso: vm-firma10 firmar|verificar|nativo|recuperar|direccion|alterar-s ...");
            std::process::exit(2);
        }
    }
}
