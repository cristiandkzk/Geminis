//! Los criterios L1, L4, L5 y L6 de `../CRITERIA-CARGADOR.es.md`, como pruebas.
//!
//! L2 y L3 son mediciones con reloj y viven en `src/bin/cargador.rs`: no se afirman, se corren.
//! L7 es que `criterios.rs` no cambie una linea. Los dientes (M1-M6) se aplican a una copia del
//! crate y estan en `../RESULTS-CARGADOR.es.md`.
//!
//!     cargo test --release

mod comun;

use comun::*;
use std::time::{Duration, Instant};
use vm::admision::PALABRAS_POR_CABECERA;
use vm::{admitir, admitir_para_consenso, costo_de_admision, Rechazo, GUEST_BLAKE2S, GUEST_RV, GUEST_SHA, TECHO_INICIAL};

// =========================================================================== //
// L1 — cada una de las cinco familias queda bajo el medidor
// =========================================================================== //

/// **A.** Codigo declarado donde el archivo no trae bytes. Se rechaza por F1, con la variante
/// propia, y no por el medidor: es una regla de formato. Se prueba con una y con dieciseis
/// secciones porque las repetidas fueron lo que multiplico el costo.
#[test]
fn l1_a_el_codigo_declarado_sin_bytes_se_rechaza_por_f1() {
    for k in [1u16, 16] {
        let e = familia_a(k);
        match admitir_para_consenso(&e, TECHO_INICIAL) {
            Err(Rechazo::SeccionSinBytesEnElArchivo { .. }) => {}
            otro => panic!("k = {k}: se esperaba F1, salio {:?}", otro.map(|_| ())),
        }
        // Y el arnes, que comparte el camino, tambien.
        assert!(matches!(
            admitir(&e, TECHO_INICIAL),
            Err(Rechazo::SeccionSinBytesEnElArchivo { .. })
        ));
    }
}

/// **B.** Cuatro bytes de codigo en la ultima direccion: el predecodificado abarca toda la
/// distancia. F1 no lo ve —hay bytes en el archivo—; lo frena el medidor, y **sin reservar**.
#[test]
fn l1_b_el_codigo_en_direccion_alta_se_rechaza_por_el_medidor() {
    let e = familia_b();
    let costo = costo_de_admision(&e).expect("el analisis no reserva y esta bien formado");
    assert!(costo > TECHO_INICIAL, "el costo tiene que reflejar el arreglo denso: {costo}");
    match admitir_para_consenso(&e, TECHO_INICIAL) {
        Err(Rechazo::AdmisionExcedeElTecho { costo: c, techo }) => {
            assert_eq!(c, costo);
            assert_eq!(techo, TECHO_INICIAL);
        }
        otro => panic!("se esperaba el medidor, salio {:?}", otro.map(|_| ())),
    }
}

/// **C.** Segmentos superpuestos, cada uno copia el mismo trozo: cuadratico en la entrada.
/// Con 1 024 se rechaza por el medidor; con 16 **entra pagando** —el medidor no rechaza lo
/// que cabe—, y lo pagado sale del techo.
#[test]
fn l1_c_los_segmentos_superpuestos_se_pagan_o_se_rechazan() {
    let e = familia_c(1024, 1_000_000);
    let costo = costo_de_admision(&e).unwrap();
    assert!(costo > 1024 * 250_000, "cada segmento cobra su copia: {costo}");
    assert!(matches!(
        admitir_para_consenso(&e, TECHO_INICIAL),
        Err(Rechazo::AdmisionExcedeElTecho { .. })
    ));

    let e = familia_c(16, 1_000_000);
    let costo = costo_de_admision(&e).unwrap();
    assert!(costo < TECHO_INICIAL, "dieciseis caben: {costo}");
    let m = admitir_para_consenso(&e, TECHO_INICIAL).expect("cabe en el techo");
    assert_eq!(m.techo, TECHO_INICIAL - costo, "lo pagado sale del techo de la maquina");
}

/// **D.** Una tabla de simbolos con nombres sin NUL. El camino de consenso no la recorre: el
/// costo es lineal en el archivo y admite. Se cuenta ≤ 4 palabras por palabra de archivo, mas
/// una constante — la copia, el barrido y el predecodificado son constantes de un ELF asi.
#[test]
fn l1_d_los_simbolos_no_entran_al_camino_de_consenso() {
    let e = familia_d(30_000, 400_000);
    let costo = costo_de_admision(&e).unwrap();
    let palabras_de_archivo = (e.len() as u64 + 3) / 4;
    assert!(costo <= 4 * palabras_de_archivo + 1_000, "costo {costo}, archivo {palabras_de_archivo} palabras");
    admitir_para_consenso(&e, TECHO_INICIAL).expect("es un ELF valido: los simbolos no cuentan");
}

/// **E.** N segmentos por N secciones. Es la unica familia cuya falla no cambia ningun valor
/// devuelto sino el tiempo, asi que lleva un chequeo grueso: con 60 000 la version cuadratica
/// tarda del orden de tres segundos y la de union y busqueda binaria, milisegundos.
#[test]
fn l1_e_secciones_por_segmentos_no_es_cuadratico() {
    let e = familia_e(60_000);
    let t = Instant::now();
    let costo = costo_de_admision(&e).expect("bien formado");
    let dt = t.elapsed();
    assert!(dt < Duration::from_secs(1), "analizar 60 000 x 60 000 tardo {dt:?}: es cuadratico");
    assert!(costo < TECHO_INICIAL, "es un ELF chico: {costo}");
}

/// Declarar el mismo rango mil veces cuesta las cabeceras y nada mas. **Es lo que hace la
/// union**: sin ella, cada seccion repetida se barre de nuevo y esta diferencia seria enorme.
#[test]
fn l1_las_secciones_repetidas_solo_cuestan_sus_cabeceras() {
    let una = costo_de_admision(&con_secciones_repetidas(100_000, 1)).unwrap();
    let muchas = costo_de_admision(&con_secciones_repetidas(100_000, 64)).unwrap();
    assert_eq!(muchas - una, PALABRAS_POR_CABECERA * 63);
}

// =========================================================================== //
// L3 — el medidor no subcobra (la medicion vive en `src/bin/cargador.rs`)
// =========================================================================== //

/// L3 es una medicion con reloj y no se puede afirmar en una prueba; lo que **si** se puede fijar es
/// el resultado de su calibracion. Con 4 palabras por cabecera, 120 000 cabeceras tardaban 13 ms y
/// estaban cobradas por 7,7: el binario reprobo. Medido, una cabecera cuesta ~7,6 palabras a
/// `R_declarado`, asi que **por debajo de 8 el medidor vuelve a subcobrar**. Se declara 16.
#[test]
fn l3_el_cobro_por_cabecera_no_baja_de_lo_medido() {
    assert!(
        PALABRAS_POR_CABECERA >= 8,
        "{PALABRAS_POR_CABECERA} palabras por cabecera subcobra: L3 midio ~7,6 (ver `src/bin/cargador.rs`)"
    );
}

// =========================================================================== //
// L4 — lo legitimo entra y no se mueve un paso
// =========================================================================== //

/// Los tres guests reales entran bajo el techo inicial y pagan poco. Que **el conteo de pasos
/// no se mueve** lo sostiene `la_semantica_reproduce_test2_paso_a_paso`, que no se toco.
#[test]
fn l4_los_guests_reales_entran_y_cuestan_poco() {
    for (nombre, guest) in [("RV", GUEST_RV), ("SHA", GUEST_SHA), ("BLAKE2s", GUEST_BLAKE2S)] {
        let costo = costo_de_admision(guest).expect(nombre);
        assert!(costo * 20 <= TECHO_INICIAL, "{nombre}: {costo} pasa del 5 % del techo");
        let m = admitir_para_consenso(guest, TECHO_INICIAL).expect(nombre);
        assert_eq!(m.pasos, 0, "{nombre}: admitir no ejecuta");
        assert_eq!(m.techo, TECHO_INICIAL - costo, "{nombre}");
    }
}

// =========================================================================== //
// L5 — el techo cubre la evaluacion entera, en los bordes exactos
// =========================================================================== //

#[test]
fn l5_el_techo_cubre_la_evaluacion_en_los_bordes_exactos() {
    let e = GUEST_SHA;
    let c = costo_de_admision(e).unwrap();
    for _ in 0..3 {
        assert_eq!(costo_de_admision(e).unwrap(), c, "el costo es determinista");
    }

    match admitir_para_consenso(e, c - 1) {
        Err(Rechazo::AdmisionExcedeElTecho { costo, techo }) => {
            assert_eq!((costo, techo), (c, c - 1));
        }
        otro => panic!("con techo = costo − 1 se esperaba el medidor: {:?}", otro.map(|_| ())),
    }

    let m = admitir_para_consenso(e, c).expect("techo = costo entra");
    assert_eq!((m.techo, m.pasos), (0, 0), "no queda nada para ejecutar");

    let m = admitir_para_consenso(e, c + 1_000).unwrap();
    assert_eq!(m.techo, 1_000);
}

// =========================================================================== //
// L6 — los simbolos no estan en el camino de consenso
// =========================================================================== //

/// El arnes acota los nombres: la familia D, que tardaba 9,7 segundos, ya no. El limite de la
/// prueba es grueso a proposito; el de L6 (25 ms) lo mide el binario.
#[test]
fn l6_el_arnes_acota_los_nombres() {
    let e = familia_d(30_000, 400_000);
    let t = Instant::now();
    let (_, simbolos) = admitir(&e, TECHO_INICIAL).expect("valido");
    let dt = t.elapsed();
    assert!(dt < Duration::from_millis(500), "el arnes tardo {dt:?} con nombres sin NUL");
    assert!(simbolos.is_empty(), "un nombre sin terminador en la ventana se ignora");
}

/// **El camino de consenso no recorre la tabla.** Como los nombres ya estan acotados, leerla ahi no
/// cambiaria ningun valor devuelto —solo el tiempo—, asi que se compara contra el arnes, que si la
/// lee: mediana de cinco, y el consenso tiene que ser al menos diez veces mas rapido. Medido, ~150.
#[test]
fn l6_el_camino_de_consenso_no_recorre_los_simbolos() {
    fn mediana(mut f: impl FnMut()) -> Duration {
        let mut v: Vec<Duration> = (0..5)
            .map(|_| {
                let t = Instant::now();
                f();
                t.elapsed()
            })
            .collect();
        v.sort();
        v[2]
    }
    let e = familia_d(60_000, 400_000);
    let consenso = mediana(|| {
        let _ = admitir_para_consenso(&e, TECHO_INICIAL);
    });
    let arnes = mediana(|| {
        let _ = admitir(&e, TECHO_INICIAL);
    });
    assert!(consenso * 10 < arnes, "consenso {consenso:?} contra arnes {arnes:?}: el consenso lee simbolos");
}

/// Y acotar los nombres no le saca los simbolos al guest real: `prepare` y `run` siguen ahi.
#[test]
fn l6_el_guest_real_conserva_sus_simbolos() {
    let (_, simbolos) = admitir(GUEST_RV, u64::MAX).unwrap();
    assert!(simbolos.contains_key("prepare"));
    assert!(simbolos.contains_key("run"));
}
