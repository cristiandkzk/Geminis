//! Los ELF hostiles de `../../CRITERIA-CARGADOR.es.md`, **construidos**.
//!
//! Compartidos por `tests/cargador.rs` (las propiedades) y `src/bin/cargador.rs` (el reloj).
//! Ninguno es un ELF legitimo con bytes alterados: son ELF **bien formados** que declaran
//! mas de lo que traen, que es justo lo que un barrido por mutacion no encuentra.

#![allow(dead_code)]

use vm::maquina::{MEM, TEXT_BASE};

/// `jal x0, 0`: un salto a si mismo. Una palabra que no es un opcode reservado.
pub const JAL_CERO: u32 = 0x0000_006f;

/// `addi x0, x0, 0`: el `nop`.
pub const NOP: u32 = 0x0000_0013;

pub struct Ph {
    pub off: u32,
    pub vaddr: u32,
    pub filesz: u32,
    pub memsz: u32,
    pub flags: u32,
}

pub struct Sh {
    pub tipo: u32,
    pub flags: u32,
    pub addr: u32,
    pub off: u32,
    pub size: u32,
    pub link: u32,
}

/// Cabecera de programa ejecutable (`R + X`).
fn rx(off: u32, vaddr: u32, filesz: u32, memsz: u32) -> Ph {
    Ph { off, vaddr, filesz, memsz, flags: 5 }
}

/// Seccion `PROGBITS` con `ALLOC | EXECINSTR`: codigo que se carga.
fn codigo(addr: u32, off: u32, size: u32) -> Sh {
    Sh { tipo: 1, flags: 6, addr, off, size, link: 0 }
}

fn p16(e: &mut Vec<u8>, x: u16) {
    e.extend_from_slice(&x.to_le_bytes());
}

fn p32(e: &mut Vec<u8>, x: u32) {
    e.extend_from_slice(&x.to_le_bytes());
}

/// Donde empieza `datos` en un ELF con `nph` cabeceras de programa: tras la cabecera
/// ELF (52 bytes) y las de programa (32 cada una).
pub fn base_datos(nph: usize) -> u32 {
    52 + 32 * nph as u32
}

/// Un ELF32 RV32: cabecera, `phs`, `datos` crudos, y las secciones `shs` (la nula se agrega
/// sola). El `off` de cada cabecera lo pone quien llama, con `base_datos`.
pub fn elf(entrada: u32, phs: &[Ph], datos: &[u8], shs: &[Sh]) -> Vec<u8> {
    let phoff = 52u32;
    let shoff = base_datos(phs.len()) + datos.len() as u32;
    let mut e = Vec::new();
    e.extend_from_slice(&[0x7f, b'E', b'L', b'F', 1, 1, 1, 0]);
    e.extend_from_slice(&[0u8; 8]);
    p16(&mut e, 2); // e_type
    p16(&mut e, 0xf3); // e_machine: RISC-V
    p32(&mut e, 1); // e_version
    p32(&mut e, entrada);
    p32(&mut e, phoff);
    p32(&mut e, shoff);
    p32(&mut e, 0); // e_flags
    p16(&mut e, 52); // e_ehsize
    p16(&mut e, 32); // e_phentsize
    p16(&mut e, phs.len() as u16);
    p16(&mut e, 40); // e_shentsize
    p16(&mut e, (shs.len() + 1) as u16);
    p16(&mut e, 0); // e_shstrndx
    assert_eq!(e.len(), 52);
    for p in phs {
        p32(&mut e, 1); // PT_LOAD
        p32(&mut e, p.off);
        p32(&mut e, p.vaddr);
        p32(&mut e, p.vaddr);
        p32(&mut e, p.filesz);
        p32(&mut e, p.memsz);
        p32(&mut e, p.flags);
        p32(&mut e, 0x1000);
    }
    e.extend_from_slice(datos);
    e.extend_from_slice(&[0u8; 40]); // la seccion nula
    for s in shs {
        p32(&mut e, 0); // sh_name
        p32(&mut e, s.tipo);
        p32(&mut e, s.flags);
        p32(&mut e, s.addr);
        p32(&mut e, s.off);
        p32(&mut e, s.size);
        p32(&mut e, s.link);
        p32(&mut e, 0);
        p32(&mut e, 4);
        p32(&mut e, 0);
    }
    e
}

/// Un ELF minimo y legitimo: cuatro bytes de codigo en `TEXT_BASE`. Es el `T₀` de L3.
pub fn minimo() -> Vec<u8> {
    let d = base_datos(1);
    elf(TEXT_BASE, &[rx(d, TEXT_BASE, 4, 4)], &JAL_CERO.to_le_bytes(), &[codigo(TEXT_BASE, d, 4)])
}

/// **Familia A.** Un segmento ejecutable de casi 64 MiB con cuatro bytes de archivo, y `k`
/// secciones de codigo que declaran todas el rango entero.
pub fn familia_a(k: u16) -> Vec<u8> {
    let d = base_datos(1);
    let memsz = MEM - TEXT_BASE;
    let shs: Vec<Sh> = (0..k).map(|_| codigo(TEXT_BASE, d, memsz)).collect();
    elf(TEXT_BASE, &[rx(d, TEXT_BASE, 4, memsz)], &JAL_CERO.to_le_bytes(), &shs)
}

/// **Familia B.** Cuatro bytes de codigo en la ultima direccion posible: el arreglo
/// predecodificado tiene que llegar hasta ahi.
pub fn familia_b() -> Vec<u8> {
    let d = base_datos(1);
    let vaddr = MEM - TEXT_BASE;
    elf(vaddr, &[rx(d, vaddr, 4, 4)], &JAL_CERO.to_le_bytes(), &[codigo(vaddr, d, 4)])
}

/// **Familia C.** `k` segmentos `PT_LOAD` superpuestos, cada uno con `filesz` bytes del mismo
/// trozo del archivo.
pub fn familia_c(k: u32, filesz: u32) -> Vec<u8> {
    let d = base_datos(k as usize);
    let phs: Vec<Ph> = (0..k).map(|_| rx(d, TEXT_BASE, filesz, filesz)).collect();
    elf(TEXT_BASE, &phs, &vec![0u8; filesz as usize], &[codigo(TEXT_BASE, d, 4)])
}

/// **Familia D.** Una tabla de simbolos de `nsyms` simbolos cuyos nombres apuntan a `cola`
/// bytes sin ningun NUL: cada uno recorre hasta el final del archivo.
pub fn familia_d(nsyms: u32, cola: u32) -> Vec<u8> {
    let d = base_datos(1);
    let symoff = d + 4;
    let symsz = 16 * nsyms;
    let stroff = symoff + symsz;
    let mut datos = JAL_CERO.to_le_bytes().to_vec();
    for _ in 0..nsyms {
        datos.extend_from_slice(&1u32.to_le_bytes()); // st_name: un byte adentro de la cola
        datos.extend_from_slice(&TEXT_BASE.to_le_bytes());
        datos.extend_from_slice(&0u32.to_le_bytes());
        datos.extend_from_slice(&0u32.to_le_bytes());
    }
    datos.extend_from_slice(&vec![0x41u8; cola as usize]);
    let shs = [
        codigo(TEXT_BASE, d, 4),
        Sh { tipo: 2, flags: 0, addr: 0, off: symoff, size: symsz, link: 3 }, // SYMTAB -> STRTAB
        Sh { tipo: 3, flags: 0, addr: 0, off: stroff, size: cola, link: 0 },
    ];
    elf(TEXT_BASE, &[rx(d, TEXT_BASE, 4, 4)], &datos, &shs)
}

/// **Familia E.** `n` segmentos y `n` secciones de codigo. Solo el ultimo segmento contiene el
/// codigo, asi que cada seccion, buscando su segmento, los recorre a todos.
pub fn familia_e(n: u32) -> Vec<u8> {
    let d = base_datos(n as usize);
    let mut phs: Vec<Ph> = (0..n - 1).map(|i| rx(d, 0x0010_0000 + i * 0x10, 4, 4)).collect();
    phs.push(rx(d, TEXT_BASE, 4, 4));
    let shs: Vec<Sh> = (0..n).map(|_| codigo(TEXT_BASE, d, 4)).collect();
    elf(TEXT_BASE, &phs, &JAL_CERO.to_le_bytes(), &shs)
}

/// Un ELF legitimo con `sec_bytes` bytes de codigo real y **`k` secciones que declaran el mismo
/// rango**. Con la union, repetir secciones solo cuesta las cabeceras.
pub fn con_secciones_repetidas(sec_bytes: u32, k: u16) -> Vec<u8> {
    let d = base_datos(1);
    let datos: Vec<u8> = (0..sec_bytes / 4).flat_map(|_| NOP.to_le_bytes()).collect();
    let shs: Vec<Sh> = (0..k).map(|_| codigo(TEXT_BASE, d, sec_bytes)).collect();
    elf(TEXT_BASE, &[rx(d, TEXT_BASE, sec_bytes, sec_bytes)], &datos, &shs)
}
