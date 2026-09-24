//! Test 11 — el binario que la prueba Python invoca.
//!
//!     vm-umbral simple   <archivo> <mensaje-hex> <techo-pasos> <techo-paginas> [variante]
//!     vm-umbral multisig <n> <indices-csv> <mensaje-hex> <techo-pasos> <techo-paginas> [variante]
//!
//! `simple` lee del archivo cada linea con `clave=<hex> firma=<hex>` (las que escribe el firmante
//! en Go, umbral o de un solo firmante) y por cada una hace lo que hace un nodo: admite el guest,
//! lo arranca, escribe la carga en su buffer, **pone los dos techos que le pasan (los del ruleset
//! vigente)** y recien ahi llama. Acepta solo si el guest retorna 1 sin pasarse de pasos ni de
//! paginas. Ademas verifica en nativo (crate `ml-dsa`, otra implementacion que la del firmante).
//!
//! `variante` aplica UNA alteracion (control negativo): `ok` | `bit-firma` | `otro-mensaje` |
//! `otra-clave` (simple) y `ok` | `firma-mala` | `direccion-mala` | `indice-repetido` (multisig).

use blake2::{Blake2s256, Digest};
use ml_dsa::{
    B32, EncodedSignature, EncodedVerifyingKey, ExpandedSigningKey, MlDsa44, Signature, VerifyingKey,
};
use vm::maquina::Veredicto;

const GUEST_SIMPLE: &[u8] = include_bytes!("../../guest-mldsa44/guest.elf");
const GUEST_MULTISIG: &[u8] = include_bytes!("../../guest-multisig/guest.elf");
const CTX: &[u8] = b"";
const LARGO_CLAVE: usize = 1312;
const LARGO_FIRMA: usize = 2420;

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

fn nativo(pk: &[u8], sig: &[u8], msg: &[u8]) -> bool {
    let Ok(enc_vk) = EncodedVerifyingKey::<MlDsa44>::try_from(pk) else { return false };
    let Ok(enc_sig) = EncodedSignature::<MlDsa44>::try_from(sig) else { return false };
    let vk = VerifyingKey::<MlDsa44>::decode(&enc_vk);
    match Signature::<MlDsa44>::decode(&enc_sig) {
        Some(s) => vk.verify_with_context(msg, CTX, &s),
        None => false,
    }
}

struct Corrida {
    veredicto: Veredicto,
    pasos: u64,
    paginas: u32,
}

impl Corrida {
    fn acepta(&self) -> bool {
        matches!(self.veredicto, Veredicto::Retorno(1))
    }
}

/// Admite el guest, lo arranca, escribe `carga` en su buffer y llama a `verificar(args)` con los
/// dos techos puestos y contados desde cero. El arranque y el andamiaje no se le cobran.
fn en_la_maquina(elf: &[u8], carga: &[u8], args: &[u32], techo_pasos: u64, techo_paginas: u32) -> Corrida {
    let (mut m, syms) = vm::admitir(elf, u64::MAX).expect("admitir el guest");
    m.techo = u64::MAX;
    m.techo_paginas = u32::MAX;
    m.arrancar();
    let entrada = *syms.get("entrada").expect("simbolo entrada");
    let verificar = *syms.get("verificar").expect("simbolo verificar");
    let dir = match m.llamar(entrada, &[]) {
        Veredicto::Retorno(a) => a,
        otro => panic!("entrada() no retorno: {:?}", otro),
    };
    assert!(m.escribir(dir, carga), "no entro en el buffer del guest");

    let base = m.pasos;
    m.techo = base + techo_pasos;
    m.borrar_paginas();
    m.techo_paginas = techo_paginas;
    let v = m.llamar(verificar, args);
    Corrida { veredicto: v, pasos: m.pasos - base, paginas: m.paginas_usadas }
}

fn cmd_simple(a: &[String]) {
    let archivo = &a[0];
    let msg = unhex(&a[1]);
    let techo: u64 = a[2].parse().expect("techo de pasos");
    let paginas: u32 = a[3].parse().expect("techo de paginas");
    let variante = a.get(4).map(String::as_str).unwrap_or("ok");

    let texto = std::fs::read_to_string(archivo).expect("leer el archivo del firmante");
    let mut i = 0;
    for linea in texto.lines().filter(|l| !l.starts_with('#') && l.contains("clave=")) {
        let campo = |nombre: &str| -> Vec<u8> {
            let pref = format!("{nombre}=");
            let t = linea.split_whitespace().find(|t| t.starts_with(&pref)).expect("campo");
            unhex(&t[pref.len()..])
        };
        let (mut pk, mut sig, mut m) = (campo("clave"), campo("firma"), msg.clone());
        match variante {
            "ok" => {}
            "bit-firma" => sig[0] ^= 1,
            "otro-mensaje" => m.push(0),
            "otra-clave" => pk[0] ^= 1,
            otra => panic!("variante desconocida: {otra}"),
        }
        assert_eq!((pk.len(), sig.len()), (LARGO_CLAVE, LARGO_FIRMA), "tamanos FIPS 204 de ML-DSA-44");
        let mut carga = pk.clone();
        carga.extend_from_slice(&sig);
        carga.extend_from_slice(&m);
        let c = en_la_maquina(
            GUEST_SIMPLE,
            &carga,
            &[pk.len() as u32, sig.len() as u32, m.len() as u32],
            techo,
            paginas,
        );
        println!(
            "i={} variante={} maquina_acepta={} veredicto={:?} pasos={} paginas={} nativo_acepta={}",
            i,
            variante,
            c.acepta() as u8,
            c.veredicto,
            c.pasos,
            c.paginas,
            nativo(&pk, &sig, &m) as u8
        );
        i += 1;
    }
}

/// Las `n` claves del multisig salen de semillas fijas: la prueba es reproducible byte a byte.
fn firmante(i: usize) -> ExpandedSigningKey<MlDsa44> {
    let seed: B32 = [0x40 + i as u8; 32].into();
    ExpandedSigningKey::<MlDsa44>::from_seed(&seed)
}

fn cmd_multisig(a: &[String]) {
    let n: usize = a[0].parse().expect("n");
    let idx: Vec<u8> = a[1].split(',').map(|s| s.parse().expect("indice")).collect();
    let msg = unhex(&a[2]);
    let techo: u64 = a[3].parse().expect("techo de pasos");
    let paginas: u32 = a[4].parse().expect("techo de paginas");
    let variante = a.get(5).map(String::as_str).unwrap_or("ok");
    let k = idx.len();

    let sks: Vec<_> = (0..n).map(firmante).collect();
    let pks: Vec<Vec<u8>> = sks.iter().map(|s| s.verifying_key().encode().to_vec()).collect();
    let claves: Vec<u8> = pks.concat();
    let mut dir = Blake2s256::digest(&claves).to_vec();
    let mut firmas: Vec<u8> = Vec::new();
    for &i in &idx {
        firmas.extend_from_slice(&sks[i as usize].sign_deterministic(&msg, CTX).expect("firmar").encode());
    }
    let mut idx_carga = idx.clone();
    match variante {
        "ok" => {}
        "firma-mala" => firmas[0] ^= 1,
        "direccion-mala" => dir[0] ^= 1,
        "indice-repetido" => {
            assert!(k >= 2, "indice-repetido pide k >= 2");
            idx_carga[1] = idx_carga[0];
        }
        otra => panic!("variante desconocida: {otra}"),
    }

    let mut carga = dir.clone();
    carga.extend_from_slice(&idx_carga);
    carga.extend_from_slice(&claves);
    carga.extend_from_slice(&firmas);
    carga.extend_from_slice(&msg);
    let bytes_firma_y_claves = claves.len() + firmas.len();
    let c = en_la_maquina(GUEST_MULTISIG, &carga, &[n as u32, k as u32, msg.len() as u32], techo, paginas);
    println!(
        "n={} k={} indices={} variante={} acepta={} veredicto={:?} pasos={} paginas={} bytes_claves_y_firmas={} bytes_carga={}",
        n,
        k,
        hex(&idx),
        variante,
        c.acepta() as u8,
        c.veredicto,
        c.pasos,
        c.paginas,
        bytes_firma_y_claves,
        carga.len()
    );
}

fn main() {
    let a: Vec<String> = std::env::args().collect();
    match a.get(1).map(String::as_str) {
        Some("simple") if a.len() >= 6 => cmd_simple(&a[2..]),
        Some("multisig") if a.len() >= 7 => cmd_multisig(&a[2..]),
        _ => {
            eprintln!("uso: vm-umbral simple <archivo> <msg-hex> <techo-pasos> <techo-paginas> [variante]");
            eprintln!("     vm-umbral multisig <n> <indices-csv> <msg-hex> <techo-pasos> <techo-paginas> [variante]");
            std::process::exit(2);
        }
    }
}
