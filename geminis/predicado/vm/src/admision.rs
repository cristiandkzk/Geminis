//! Admision: **lo que se decide antes de gastar el primer paso.**
//!
//! El cargador del arnes de Test 2 indexa el ELF sin chequear —`elf[o + 1]`,
//! `mem[dst..dst + filesz]`— porque ahi el ELF lo producia el mismo repo. Acá lo
//! produce la contraparte de una impugnacion, y entonces cada indexado sin chequeo
//! es un `panic` a pedido: **una transaccion malformada cuesta una transaccion y
//! tira un nodo** (C4). Todas las lecturas de este archivo pasan por `u8`, `u16`,
//! `u32`, que devuelven `Option`, y no hay un solo `[..]` directo sobre `elf`.
//!
//! Y acá vive C2. El punto flotante no se rechaza cuando el programa llega a la
//! instruccion: se rechaza **antes de empezar**, recorriendo una sola vez las
//! paginas ejecutables. Un rechazo en ejecucion seria un veredicto tardio — ya se
//! gasto presupuesto de bloque para descubrir algo que estaba escrito en el
//! binario desde el principio.
//!
//! ## El medidor (`../../CRITERIA-CARGADOR.es.md`)
//!
//! **Que no haga `panic` no es que sea barato.** Test 5 cerro dos amplificaciones
//! —64 MiB reservados antes de validar, 128 MiB de predecodificado por una
//! cabecera alterada— y una segunda ronda encontro cinco mas, todas bien formadas:
//! el trabajo dependia de lo que el ELF **declara** (`memsz`, una direccion alta,
//! segmentos que se pisan, una tabla de simbolos) y no de sus bytes. La admision
//! corre antes del primer paso, asi que ni el techo de pasos ni el de paginas la
//! cubrian.
//!
//! La regla es una sola: **la admision es trabajo, y todo trabajo va bajo el
//! medidor.** El costo se calcula **solo desde las cabeceras y antes de reservar
//! nada** (`analizar`), en palabras de cuatro bytes con **una palabra = un paso**, y
//! se paga del mismo techo que la ejecucion: la maquina recibe `techo − costo`. Una
//! palabra tarda mucho menos que un paso, asi que esto sobrecobra, que es el lado
//! correcto del error. **Los conteos de pasos de la ejecucion no se mueven.**
//!
//! Y lo que es comodidad del arnes no esta en el camino de consenso: los simbolos
//! (`leer_simbolos`) los lee `admitir`, no `admitir_para_consenso`.

use crate::maquina::{decodificar, Insn, Maquina, ILEGAL, MEM, TEXT_BASE};
use std::collections::BTreeMap;

/// Palabras que se cobran por cada cabecera de programa o de seccion que hay que
/// recorrer, ordenar y buscar. **Constante declarada**, del formato del predicado:
/// cambia con Genesis, no por generacion.
///
/// **No es la que se escribio primero.** Los criterios declararon 4, y L3 la cazo
/// subcobrando: 120 000 cabeceras (familia E) tardaban 13 ms de reloj y estaban
/// cobradas por 7,7. Medido, una cabecera cuesta ~108 ns, unas 7,6 palabras a
/// `R_declarado`. Se declara **16**, el doble redondeado a potencia de dos, por lo
/// mismo que `R_declarado` se declara por debajo del hardware real: un teléfono
/// tarda mas que el escritorio donde se midio.
pub const PALABRAS_POR_CABECERA: u64 = 16;

/// Largo maximo, en bytes, de un nombre de simbolo que lee el arnes. Un nombre que
/// no termina antes se ignora. Sin este tope, cada simbolo recorre el archivo hasta
/// el final buscando su terminador, y la lectura es cuadratica.
const NOMBRE_MAX: usize = 256;

/// Por que no entra. Cada variante es una decision de admision, no un error de
/// ejecucion: **el programa nunca corrio.**
#[derive(Clone, PartialEq, Eq, Debug)]
pub enum Rechazo {
    /// Menos bytes que la cabecera, o firma equivocada.
    NoEsElf32,
    /// `e_machine` no es RISC-V.
    NoEsRiscV(u16),
    /// Una cabecera de programa o de seccion apunta fuera del archivo.
    CabeceraFueraDelArchivo,
    /// Un `PT_LOAD` no entra en la memoria declarada.
    SegmentoFueraDeMemoria,
    /// No hay ni una pagina ejecutable, o el binario no declara sus secciones de
    /// codigo. **Un ELF sin tabla de secciones no es un predicado admisible**, y
    /// eso es una condicion del formato, no una limitacion de la maquina.
    SinTexto,
    /// Una seccion de codigo declara estar donde no hay segmento ejecutable
    /// cargado. Es la cabecera mintiendo sobre cuanto codigo hay.
    SeccionFueraDeSegmento { addr: u32, size: u32 },
    /// **Regla de formato F1.** Una seccion de codigo cae dentro de la memoria de un
    /// segmento ejecutable pero **no dentro de los bytes que el archivo trae**: el
    /// resto de `memsz` es relleno de ceros. Codigo declarado donde no hay bytes es
    /// la forma barata de pedirle a un nodo que barra y predecodifique 64 MiB.
    SeccionSinBytesEnElArchivo { addr: u32, size: u32 },
    /// Una palabra de una pagina ejecutable usa un opcode **reservado**: todo el
    /// punto flotante, y los atomicos. **Es el rechazo de C2.**
    OpcodeReservado { pc: u32, palabra: u32, opcode: u8 },
    /// **El medidor.** Admitir este ELF cuesta mas que el techo entero, y se sabe
    /// leyendo las cabeceras: no se reservo memoria ni se barrio nada.
    AdmisionExcedeElTecho { costo: u64, techo: u64 },
}

// --------------------------------------------------------------------------- #
// Lectores totales. Ninguno puede hacer panic; el precio es un `?` por campo.
// --------------------------------------------------------------------------- #

fn u8a(b: &[u8], o: usize) -> Option<u8> {
    b.get(o).copied()
}

fn u16a(b: &[u8], o: usize) -> Option<u16> {
    Some(u16::from_le_bytes([*b.get(o)?, *b.get(o + 1)?]))
}

fn u32a(b: &[u8], o: usize) -> Option<u32> {
    Some(u32::from_le_bytes([
        *b.get(o)?,
        *b.get(o + 1)?,
        *b.get(o + 2)?,
        *b.get(o + 3)?,
    ]))
}

/// **El espacio de opcodes que Genesis declara cerrado para siempre (I1).**
///
/// No es *"lo que esta maquina no implementa"* —eso cambia con cada bug— sino los
/// opcodes mayores que RISC-V ya le asigno a extensiones que esta maquina no puede
/// tener nunca:
///
/// | opcode | extension | por que no puede entrar |
/// |---|---|---|
/// | `0x07` | `LOAD-FP` (`flw`, `fld`) | punto flotante |
/// | `0x27` | `STORE-FP` (`fsw`, `fsd`) | punto flotante |
/// | `0x2F` | `AMO` (extension A) | atomicos: orden no determinista |
/// | `0x43` | `MADD` | multiply-add flotante |
/// | `0x47` | `MSUB` | multiply-add flotante |
/// | `0x4B` | `NMSUB` | multiply-add flotante |
/// | `0x4F` | `NMADD` | multiply-add flotante |
/// | `0x53` | `OP-FP` (el resto de F, D, Q) | punto flotante |
///
/// El flotante no esta prohibido porque sea caro: esta prohibido porque el
/// redondeo es la unica operacion de un ISA donde dos implementaciones correctas
/// pueden diferir, y una diferencia de un ulp entre dos nodos es una bifurcacion.
/// Cerrar el espacio de opcodes es mas fuerte que no implementarlo: **el dia que
/// alguien quiera agregar F, tiene que romper una constante de Genesis.**
const RESERVADOS: [u8; 8] = [0x07, 0x27, 0x2F, 0x43, 0x47, 0x4B, 0x4F, 0x53];

/// Un `PT_LOAD` ya validado, todavia sin copiar.
struct Segmento {
    off: usize,
    filesz: usize,
    vaddr: u32,
    memsz: u32,
    ejecutable: bool,
}

// --------------------------------------------------------------------------- #
// Rangos: la union y la pertenencia, en `O(n log n)` y `O(log n)`.
// --------------------------------------------------------------------------- #

/// Los rangos `[inicio, fin)` de `v`, unidos: ordenados y disjuntos.
///
/// **Es lo que impide que declarar mil veces el mismo rango cueste mil veces.** Sin
/// unir, cada seccion repetida se barria de nuevo (+26 ms por cada una de 40 bytes,
/// medido) y cada seccion buscaba su segmento recorriendolos a todos: secciones por
/// segmentos, cuadratico. Los rangos que se tocan se funden, asi que una seccion que
/// cruza dos segmentos ejecutables contiguos, los dos respaldados por el archivo,
/// tambien entra: sigue siendo codigo que el archivo trae.
fn unir(mut v: Vec<(u64, u64)>) -> Vec<(u64, u64)> {
    v.sort_unstable();
    let mut unido: Vec<(u64, u64)> = Vec::new();
    for (a, b) in v {
        if a >= b {
            continue;
        }
        match unido.last_mut() {
            Some(ultimo) if a <= ultimo.1 => {
                if b > ultimo.1 {
                    ultimo.1 = b;
                }
            }
            _ => unido.push((a, b)),
        }
    }
    unido
}

/// ¿Cae `[a, b)` entero dentro de un rango de la union? Busqueda binaria.
fn cubre(unido: &[(u64, u64)], a: u64, b: u64) -> bool {
    let i = unido.partition_point(|r| r.0 <= a);
    i > 0 && b <= unido[i - 1].1
}

// --------------------------------------------------------------------------- #
// El analisis: valida y **mide**, y no reserva ni barre nada.
// --------------------------------------------------------------------------- #

/// Todo lo que se sabe de un ELF leyendo solo sus cabeceras.
struct Analisis {
    segmentos: Vec<Segmento>,
    /// La union de las secciones de codigo `[inicio, fin)`: lo que se barre, una vez.
    codigo: Vec<(u64, u64)>,
    /// La union de lo ejecutable **que el archivo respalda**: lo que se predecodifica.
    ejecutable: Vec<(u64, u64)>,
    /// Palabras del arreglo predecodificado: de `TEXT_BASE` al fin del ultimo codigo.
    palabras: usize,
    entrada: u32,
    /// **Lo que cuesta admitir este ELF**, en palabras, y que se descuenta del techo.
    costo: u64,
}

fn analizar(elf: &[u8]) -> Result<Analisis, Rechazo> {
    if elf.len() < 52 || elf.get(0..4) != Some(b"\x7fELF") {
        return Err(Rechazo::NoEsElf32);
    }
    // clase 32 bits, little-endian.
    if u8a(elf, 4) != Some(1) || u8a(elf, 5) != Some(1) {
        return Err(Rechazo::NoEsElf32);
    }
    let maq = u16a(elf, 18).ok_or(Rechazo::NoEsElf32)?;
    if maq != 0xf3 {
        return Err(Rechazo::NoEsRiscV(maq));
    }

    let phoff = u32a(elf, 28).ok_or(Rechazo::NoEsElf32)? as usize;
    let phentsize = u16a(elf, 42).ok_or(Rechazo::NoEsElf32)? as usize;
    let phnum = u16a(elf, 44).ok_or(Rechazo::NoEsElf32)? as usize;
    if phentsize < 32 {
        return Err(Rechazo::CabeceraFueraDelArchivo);
    }

    // **Primero se validan todas las cabeceras y despues se reserva la memoria.**
    // Al reves —que es como estaba— un ELF de trescientos bytes con la firma bien
    // y el resto basura costaba 64 MiB de reserva antes de que nadie mirara si era
    // valido. Eso es amplificacion: la entrada es barata y el trabajo que provoca
    // no. Lo destapo el barrido de C4, que tardaba minutos por esto y no por el
    // trabajo real.
    let mut segmentos: Vec<Segmento> = Vec::new();
    let mut tope = TEXT_BASE;

    for i in 0..phnum {
        let p = phoff
            .checked_add(i.checked_mul(phentsize).ok_or(Rechazo::CabeceraFueraDelArchivo)?)
            .ok_or(Rechazo::CabeceraFueraDelArchivo)?;
        // Una cabecera que no entra en el archivo es rechazo, no salteo: el ELF
        // esta mintiendo sobre su propia forma.
        if u32a(elf, p + 28).is_none() {
            return Err(Rechazo::CabeceraFueraDelArchivo);
        }
        if u32a(elf, p) != Some(1) {
            continue; // solo PT_LOAD
        }
        let off = u32a(elf, p + 4).ok_or(Rechazo::CabeceraFueraDelArchivo)? as usize;
        let vaddr = u32a(elf, p + 8).ok_or(Rechazo::CabeceraFueraDelArchivo)?;
        let filesz = u32a(elf, p + 16).ok_or(Rechazo::CabeceraFueraDelArchivo)? as usize;
        let memsz = u32a(elf, p + 20).ok_or(Rechazo::CabeceraFueraDelArchivo)?;
        let flags = u32a(elf, p + 24).ok_or(Rechazo::CabeceraFueraDelArchivo)?;

        let fin_mem = (vaddr as u64) + (memsz as u64);
        if vaddr < TEXT_BASE || fin_mem > MEM as u64 || (filesz as u64) > (memsz as u64) {
            return Err(Rechazo::SegmentoFueraDeMemoria);
        }
        let fin_arch = off.checked_add(filesz).ok_or(Rechazo::CabeceraFueraDelArchivo)?;
        if elf.get(off..fin_arch).is_none() {
            return Err(Rechazo::CabeceraFueraDelArchivo);
        }

        tope = tope.max(fin_mem as u32);
        segmentos.push(Segmento {
            off,
            filesz,
            vaddr,
            memsz,
            ejecutable: flags & 1 != 0,
        });
    }

    if !segmentos.iter().any(|s| s.ejecutable) {
        return Err(Rechazo::SinTexto);
    }

    let entrada = u32a(elf, 24).ok_or(Rechazo::NoEsElf32)?;
    if entrada < TEXT_BASE || entrada >= tope || (entrada & 3) != 0 {
        return Err(Rechazo::SinTexto);
    }

    // Las secciones de codigo se leen y se validan **antes** de reservar nada, por
    // lo mismo de arriba: son las que fijan cuanto texto hay que predecodificar, y
    // predecodificar es la parte cara. Cada una tiene que caer entera dentro de un
    // segmento ejecutable cargado — si no, una cabecera de seccion alterada podria
    // declarar 64 MiB de codigo que no existe y costar 128 MiB de predecodificado
    // por una transaccion de trescientos bytes.
    let (secciones, shnum) = secciones_de_codigo(elf).ok_or(Rechazo::SinTexto)?;
    if secciones.is_empty() {
        return Err(Rechazo::SinTexto);
    }

    // **Y tiene que caer dentro de lo que el archivo trae**, no solo de `memsz`. Con
    // el chequeo de arriba a secas un segmento ejecutable de 64 MiB con cuatro bytes
    // de archivo dejaba declarar una seccion de 64 MiB, y 168 bytes costaban 197 ms.
    let ejecutable_en_memoria = unir(
        segmentos
            .iter()
            .filter(|s| s.ejecutable)
            .map(|s| (s.vaddr as u64, s.vaddr as u64 + s.memsz as u64))
            .collect(),
    );
    let ejecutable = unir(
        segmentos
            .iter()
            .filter(|s| s.ejecutable)
            .map(|s| (s.vaddr as u64, s.vaddr as u64 + s.filesz as u64))
            .collect(),
    );

    let mut tope_codigo = TEXT_BASE;
    let mut rangos = Vec::with_capacity(secciones.len());
    for (inicio, largo) in &secciones {
        let (a, b) = (*inicio as u64, *inicio as u64 + *largo as u64);
        if !cubre(&ejecutable_en_memoria, a, b) {
            return Err(Rechazo::SeccionFueraDeSegmento { addr: *inicio, size: *largo });
        }
        if !cubre(&ejecutable, a, b) {
            return Err(Rechazo::SeccionSinBytesEnElArchivo { addr: *inicio, size: *largo });
        }
        tope_codigo = tope_codigo.max(b as u32);
        rangos.push((a, b));
    }
    let codigo = unir(rangos);

    // El arreglo predecodificado va de `TEXT_BASE` al fin del ultimo codigo, **huecos
    // incluidos**: es un arreglo denso indexado por pc. Poner codigo en una direccion
    // alta cuesta entonces toda la distancia, y por eso se cobra el rango y no las
    // secciones (familia B: 168 bytes, 23 ms).
    let palabras = ((tope_codigo.saturating_sub(TEXT_BASE) as usize) + 4) / 4;

    let copia: u64 = segmentos.iter().map(|s| (s.filesz as u64 + 3) / 4).sum();
    let barrido: u64 = codigo.iter().map(|r| (r.1 - r.0 + 3) / 4).sum();
    let costo = copia
        + barrido
        + 2 * palabras as u64
        + PALABRAS_POR_CABECERA * (phnum as u64 + shnum as u64);

    Ok(Analisis { segmentos, codigo, ejecutable, palabras, entrada, costo })
}

/// Lo que cuesta admitir `elf`, en palabras, **sin reservar ni barrer nada**.
///
/// Es una funcion de las cabeceras y es lo que `admitir_para_consenso` descuenta del
/// techo. Determinista: dos nodos que lean el mismo ELF leen el mismo numero.
pub fn costo_de_admision(elf: &[u8]) -> Result<u64, Rechazo> {
    analizar(elf).map(|a| a.costo)
}

// --------------------------------------------------------------------------- #
// La admision de consenso.
// --------------------------------------------------------------------------- #

/// Carga y valida un ELF32 RISC-V estatico **para el consenso**. Si devuelve `Ok`, el
/// programa es admisible y **todavia no ejecuto nada**: `pasos == 0`.
///
/// El costo de admitir sale del techo: la maquina que devuelve tiene `techo − costo`.
/// **No lee simbolos**: un predicado real entra por el punto de entrada fijo de la
/// ABI, y una tabla de simbolos es un campo de tamano libre que el que manda el ELF
/// elige.
pub fn admitir_para_consenso(elf: &[u8], techo: u64) -> Result<Maquina, Rechazo> {
    let a = analizar(elf)?;
    if a.costo > techo {
        return Err(Rechazo::AdmisionExcedeElTecho { costo: a.costo, techo });
    }

    // Recien acá se reserva. Todo lo de arriba se decidio leyendo cabeceras.
    let mut mem = vec![0u8; MEM as usize].into_boxed_slice();
    for s in &a.segmentos {
        let d = s.vaddr as usize;
        mem[d..d + s.filesz].copy_from_slice(&elf[s.off..s.off + s.filesz]);
        // El resto de memsz —el .bss— ya esta en cero, y tiene que estarlo:
        // memoria sin inicializar seria estado que no viene del bloque.
    }

    // ------------------------------------------------------------------ #
    // C2 — el barrido de admision.
    //
    // Solo sobre paginas ejecutables, y no sobre todo lo cargado: `.rodata` son
    // bytes que se parecen a lo que sea, y rechazar un programa porque una
    // constante coincide con un `fadd.s` seria absurdo.
    //
    // **Y el barrido rechaza por espacio de opcode, no por "no decodifico".**
    // La primera version rechazaba toda palabra ilegal y con eso rebotaba el guest
    // real de Test 2 en el primer intento: el relleno de alineacion de `.text` son
    // ceros, y `0x00000000` no decodifica. El relleno es legitimo. Lo que no puede
    // aparecer nunca es un opcode de una extension que esta maquina no tiene y no
    // va a tener — ahi es donde una implementacion futura agregaria F y rompria el
    // consenso por redondeo, y por eso ese espacio se declara cerrado en Genesis.
    // Una palabra ilegal por cualquier otra razon no se rechaza: si el pc llega,
    // es `Trampa`, que es un veredicto determinista y ya esta pago en pasos.
    // El barrido va sobre las **secciones** de codigo, no sobre los segmentos.
    // Las banderas de segmento son demasiado gruesas: el enlazador junta `.text`
    // y `.rodata` en un mismo PT_LOAD de solo-lectura-ejecutable, asi que barrer
    // el segmento rechaza el binario por una constante que se parece a un `fsw`.
    // Eso paso con el guest real en el segundo intento, y es la razon por la que
    // **el formato de predicado exige que el binario declare donde esta su
    // codigo**: un ELF sin tabla de secciones no entra.
    //
    // Se barre la **union** de las secciones, una sola vez.
    // ------------------------------------------------------------------ #
    for &(inicio, fin) in &a.codigo {
        let mut dir = (inicio as u32) & !3;
        let fin = fin as u32;
        while dir + 4 <= fin && (dir as usize) + 4 <= mem.len() {
            let i = dir as usize;
            let w = u32::from_le_bytes([mem[i], mem[i + 1], mem[i + 2], mem[i + 3]]);
            let opc = (w & 0x7f) as u8;
            if RESERVADOS.contains(&opc) {
                return Err(Rechazo::OpcodeReservado { pc: dir, palabra: w, opcode: opc });
            }
            dir += 4;
        }
    }

    // Predecodificado, una sola vez, igual que `wasmi` traduce el modulo al
    // instanciarlo. Cubre desde TEXT_BASE hasta el fin del ultimo codigo; lo que cae
    // fuera de una pagina ejecutable queda como ILEGAL y no se puede ejecutar: si el
    // pc llega ahi, es `Trampa`, que es el comportamiento correcto.
    //
    // Se recorre la union de lo ejecutable **que el archivo respalda**, acotada al
    // arreglo. Antes se recorria `memsz` entero y se descartaba lo que no entraba: un
    // segmento de 64 MiB costaba 16,7 M de decodificaciones tiradas. El resultado es
    // el mismo —el resto de `memsz` son ceros y `0x00000000` decodifica a `ILEGAL`—.
    let mut codigo: Vec<Insn> = vec![ILEGAL; a.palabras];
    for &(inicio, fin) in &a.ejecutable {
        let mut dir = (inicio as u32) & !3;
        let fin = fin as u32;
        while dir + 4 <= fin {
            let k = ((dir - TEXT_BASE) >> 2) as usize;
            if k >= codigo.len() {
                break;
            }
            let i = dir as usize;
            let w = u32::from_le_bytes([mem[i], mem[i + 1], mem[i + 2], mem[i + 3]]);
            codigo[k] = decodificar(w);
            dir += 4;
        }
    }

    Ok(Maquina::nueva(mem, codigo.into_boxed_slice(), techo - a.costo, a.entrada))
}

/// **El arnes**: la admision de consenso mas la tabla de simbolos, para llamar a
/// `prepare` y `run` del guest de Test 2 por nombre. Es lo que usan las mediciones y
/// las pruebas; **el nodo usa `admitir_para_consenso`**.
pub fn admitir(
    elf: &[u8],
    techo: u64,
) -> Result<(Maquina, BTreeMap<String, u32>), Rechazo> {
    let maquina = admitir_para_consenso(elf, techo)?;
    let simbolos = leer_simbolos(elf).unwrap_or_default();
    Ok((maquina, simbolos))
}

/// Los rangos `(vaddr, tamano)` de las secciones con `SHF_EXECINSTR`, y cuantas
/// secciones declara el archivo.
///
/// Devuelve `None` si el binario no tiene tabla de secciones. **Eso es un rechazo
/// y no un caso benigno**: sin secciones no hay forma de distinguir codigo de
/// constantes, y sin esa distincion el barrido de C2 o rechaza binarios legitimos
/// o deja pasar lo que tiene que frenar.
fn secciones_de_codigo(elf: &[u8]) -> Option<(Vec<(u32, u32)>, usize)> {
    let shoff = u32a(elf, 32)? as usize;
    let shentsize = u16a(elf, 46)? as usize;
    let shnum = u16a(elf, 48)? as usize;
    if shoff == 0 || shnum == 0 || shentsize < 40 {
        return None;
    }
    let mut v = Vec::new();
    for k in 0..shnum {
        let s = shoff.checked_add(k.checked_mul(shentsize)?)?;
        let tipo = u32a(elf, s + 4)?;
        let flags = u32a(elf, s + 8)?;
        let addr = u32a(elf, s + 12)?;
        let size = u32a(elf, s + 20)?;
        // SHT_PROGBITS con SHF_EXECINSTR y SHF_ALLOC: codigo que se carga.
        if tipo == 1 && flags & 0x4 != 0 && flags & 0x2 != 0 && size > 0 {
            v.push((addr, size));
        }
    }
    Some((v, shnum))
}

/// Tabla de simbolos. **Comodidad del arnes, no del protocolo**: un predicado real
/// entra por el punto de entrada fijo de la ABI, no por un nombre. Vive acá porque
/// la medicion necesita llamar a `prepare` y `run` del guest de Test 2 por nombre, y
/// **solo la llama `admitir`, no `admitir_para_consenso`**.
///
/// Que no encuentre nada no es un rechazo: un binario sin `.symtab` es perfectamente
/// valido, y de hecho es lo que produce un release con `strip`.
///
/// **Cada nombre se busca en una ventana de `NOMBRE_MAX` bytes.** Antes cada simbolo
/// recorria el archivo hasta el final buscando su terminador: con nombres sin NUL era
/// cuadratico, y 880 KB tardaban 9,7 segundos.
fn leer_simbolos(elf: &[u8]) -> Option<BTreeMap<String, u32>> {
    let shoff = u32a(elf, 32)? as usize;
    let shentsize = u16a(elf, 46)? as usize;
    let shnum = u16a(elf, 48)? as usize;
    if shentsize < 40 {
        return None;
    }
    let mut syms = BTreeMap::new();
    for i in 0..shnum {
        let s = shoff.checked_add(i.checked_mul(shentsize)?)?;
        if u32a(elf, s + 4)? != 2 {
            continue; // SHT_SYMTAB
        }
        let symoff = u32a(elf, s + 16)? as usize;
        let symsz = u32a(elf, s + 20)? as usize;
        let strsec = shoff.checked_add((u32a(elf, s + 24)? as usize).checked_mul(shentsize)?)?;
        let stroff = u32a(elf, strsec + 16)? as usize;
        for k in 0..(symsz / 16) {
            let e = symoff.checked_add(k.checked_mul(16)?)?;
            let name_off = stroff.checked_add(u32a(elf, e)? as usize)?;
            let value = u32a(elf, e + 4)?;
            let cola = elf.get(name_off..)?;
            let ventana = &cola[..cola.len().min(NOMBRE_MAX)];
            let fin = ventana.iter().position(|&c| c == 0).unwrap_or(0);
            if fin > 0 {
                syms.insert(String::from_utf8_lossy(&ventana[..fin]).into_owned(), value);
            }
        }
    }
    Some(syms)
}
