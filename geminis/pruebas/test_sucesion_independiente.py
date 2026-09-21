"""Las dos sucesiones —la del hash y la de la firma— avanzan de forma independiente.

    hash:   BLAKE2s  →  SHA-3 (Keccak)  →  …
    firma:  Ed25519  →  ML-DSA-44       →  …

**Qué se demuestra.** Cada sucesión tiene su canario, su regla y su formato, y avanza sin que la otra se
entere y en cualquier orden. La cadena cruza las dos transiciones sin reiniciarse, el linaje verifica de
punta a punta, `H0_GENESIS` no se mueve y cada checkpoint se calcula con el hash de su ancestro.

**Qué NO es independiente, y se declara.** La independencia es de *mecanismo*, no de *seguridad*: Ed25519
hashea con SHA-2 y ML-DSA con Keccak, así que apenas las dos transiciones ocurren, `H` (SHA-3, Keccak)
comparte núcleo con la firma sucesora. El chequeo (`protocolo/nucleo.py`) **reporta ese acople en el
escalón donde aparece y no lo bloquea**: bloquearlo dejaría la cadena de hash sin sucesor, porque la
biblioteca estándar solo garantiza tres familias y las firmas ya usan dos.

**Los "…" son abiertos, y es un límite.** §6.6 dice que no hay lista de reemplazos: el sucesor lo entrega un
pedido de trabajo como bytecode y lo acepta el guante. Ese camino no está construido; los dos escalones de
cada cadena son formatos que Génesis ya conoce. Y ML-DSA-87 **no** es un escalón: no está en el paper.

**Límites de esta prueba.** El canario de firma de `Geminis` sigue siendo un contador (`("gastar_canario",)`,
sin verificar), a diferencia del de hash, que exige trabajo; el estado sintético no tiene cuentas; y el
árbol de estado, el de desalojo y los predicados no siguen la sucesión del hash (re-hashear un árbol
Merkle no está construido).
"""

from __future__ import annotations

import unittest
from functools import cache

from nodo.pod import NodoPoD
from protocolo import genesis as g
from protocolo import nucleo
from protocolo.linaje import verificar_linaje
from protocolo.serializacion import HASH_BLAKE2S, HASH_SHA3, corto
from sucesion.regla import ReglaCanarioCriptografico, ReglaCanarioHash

ED25519 = "firma/ed25519"
ML_DSA_44 = "firma/ml-dsa-44"

GASTO_FIRMA = ("gastar_canario",)


@cache
def _solucion() -> bytes:
    for i in range(1 << 22):  # ~2^16 esperados; acotado
        candidata = i.to_bytes(8, "big")
        if g.resuelve_canario_hash(candidata):
            return candidata
    raise AssertionError("ninguna solución gasta el canario de hash")


GASTO_HASH = ("gastar_canario_hash", _solucion())

ACOPLE_FINAL = [(ML_DSA_44, "keccak")]  # SHA-3 (Keccak) contra ML-DSA-44 (SHAKE, Keccak)


def _hasta_generacion(nodo: NodoPoD, generacion: int) -> None:
    while nodo.generacion < generacion and nodo.altura < 400:
        nodo.producir(1)
    assert nodo.generacion == generacion, f"no llegó a la generación {generacion}"


def _foto(nodo: NodoPoD) -> dict:
    return {
        "generacion": nodo.generacion,
        "hash_id": nodo.estado.hash_id,
        "formatos": frozenset(nodo.ruleset.formatos),
        "acoples": nodo.acoples(),
        "acoples_de_la_activacion": nodo.conmutaciones[-1].acoples if nodo.conmutaciones else (),
    }


@cache
def recorrido(orden: str) -> dict:
    """Corre la cadena por un orden y va sacando una foto de cada escalón."""
    h0_antes = g.H0_GENESIS
    nodo = NodoPoD(reglas=[ReglaCanarioCriptografico(), ReglaCanarioHash()])
    nodo.producir(2)
    escalones = [_foto(nodo)]

    if orden == "hash-primero":
        nodo.producir_bloque([GASTO_HASH]); _hasta_generacion(nodo, 1); escalones.append(_foto(nodo))
        nodo.producir_bloque([GASTO_FIRMA]); _hasta_generacion(nodo, 2); escalones.append(_foto(nodo))
    elif orden == "firma-primero":
        nodo.producir_bloque([GASTO_FIRMA]); _hasta_generacion(nodo, 1); escalones.append(_foto(nodo))
        nodo.producir_bloque([GASTO_HASH]); _hasta_generacion(nodo, 2); escalones.append(_foto(nodo))
    elif orden == "a-la-vez":
        nodo.producir_bloque([GASTO_FIRMA, GASTO_HASH])
        _hasta_generacion(nodo, 2)
        escalones.append(_foto(nodo))
    else:  # pragma: no cover
        raise ValueError(orden)

    nodo.producir(5)  # la cadena sigue produciendo bajo la última generación
    checkpoints = nodo.cronograma.checkpoints
    return {
        "escalones": escalones,
        "final": _foto(nodo),
        "checkpoints": checkpoints,
        "linaje_verifica": verificar_linaje(checkpoints, g.H0_GENESIS),
        "h0_antes": h0_antes,
        "h0_despues": g.H0_GENESIS,
        "cadena_intacta": all(b.padre == a.hash() for a, b in zip(nodo.cadena, nodo.cadena[1:])),
        "altura": nodo.altura,
    }


ORDENES = ("hash-primero", "firma-primero", "a-la-vez")


class CadaSucesionAvanzaSinLaOtra(unittest.TestCase):
    def test_el_hash_avanza_y_la_firma_no_se_entera(self):
        gen1 = recorrido("hash-primero")["escalones"][1]
        self.assertEqual(gen1["hash_id"], HASH_SHA3)
        self.assertEqual(
            {f for f in gen1["formatos"] if f.startswith("firma/")}, {ED25519}
        )

    def test_la_firma_avanza_y_el_hash_no_se_entera(self):
        gen1 = recorrido("firma-primero")["escalones"][1]
        self.assertEqual(gen1["hash_id"], HASH_BLAKE2S)
        self.assertEqual(
            {f for f in gen1["formatos"] if f.startswith("firma/")}, {ED25519, ML_DSA_44}
        )
        self.assertFalse({f for f in gen1["formatos"] if f.startswith("hash/")})


class TodosLosOrdenesLlegan_AlMismoEstadoFinal(unittest.TestCase):
    def test_mismos_formatos_mismo_hash_misma_generacion(self):
        finales = [recorrido(o)["final"] for o in ORDENES]
        for f in finales:
            self.assertEqual(f["generacion"], 2)
            self.assertEqual(f["hash_id"], HASH_SHA3)
            self.assertEqual({x for x in f["formatos"] if x.startswith("firma/")}, {ED25519, ML_DSA_44})
        self.assertEqual(len({f["formatos"] for f in finales}), 1)

    def test_pero_no_es_la_misma_historia(self):
        """Que el orden importe para el linaje es lo que impide que esto sea vacuo."""
        a = [c.h0 for c in recorrido("hash-primero")["checkpoints"]]
        b = [c.h0 for c in recorrido("firma-primero")["checkpoints"]]
        self.assertNotEqual(a, b)


class LaCadenaConservaLoQueTieneQueConservar(unittest.TestCase):
    def test_h0_de_genesis_no_se_movio_en_ningun_orden(self):
        for o in ORDENES:
            r = recorrido(o)
            self.assertEqual(r["h0_antes"], r["h0_despues"], o)
            self.assertEqual(corto(r["h0_despues"]), "6175777756bd3f8c", o)

    def test_el_linaje_verifica_a_traves_de_las_dos_transiciones(self):
        for o in ORDENES:
            self.assertTrue(recorrido(o)["linaje_verifica"], o)
            self.assertEqual(len(recorrido(o)["checkpoints"]), 2, o)

    def test_la_cadena_de_bloques_cruza_todo_sin_cortarse(self):
        for o in ORDENES:
            r = recorrido(o)
            self.assertTrue(r["cadena_intacta"], o)
            self.assertGreater(r["altura"], 0)

    def test_cada_checkpoint_sale_del_hash_de_su_ancestro_en_cualquier_orden(self):
        """Hash primero: el 1º introduce SHA-3 y sale de BLAKE2s; el 2º (la firma) ya sale de SHA-3.
        Firma primero: el 1º introduce ML-DSA-44 y sale de BLAKE2s; el 2º introduce SHA-3 y también
        sale de BLAKE2s, porque el ancestro todavía no lo usa."""
        hp = recorrido("hash-primero")["checkpoints"]
        self.assertTrue(hp[0].es_valido(HASH_BLAKE2S) and not hp[0].es_valido(HASH_SHA3))
        self.assertTrue(hp[1].es_valido(HASH_SHA3) and not hp[1].es_valido(HASH_BLAKE2S))

        fp = recorrido("firma-primero")["checkpoints"]
        self.assertTrue(fp[0].es_valido(HASH_BLAKE2S) and not fp[0].es_valido(HASH_SHA3))
        self.assertTrue(fp[1].es_valido(HASH_BLAKE2S) and not fp[1].es_valido(HASH_SHA3))


class ElAcopleSeReportaEnElEscalonDondeApareceYNoSeBloquea(unittest.TestCase):
    def test_al_arrancar_no_hay_acople(self):
        for o in ORDENES:
            self.assertEqual(recorrido(o)["escalones"][0]["acoples"], [], o)

    def test_hash_primero_el_primer_escalon_no_acopla_y_el_segundo_si(self):
        e = recorrido("hash-primero")["escalones"]
        self.assertEqual(e[1]["acoples"], [])  # SHA-3 (Keccak) contra Ed25519 (SHA-2): libre
        self.assertEqual(e[2]["acoples"], ACOPLE_FINAL)  # ...y entra ML-DSA-44 (Keccak)
        self.assertEqual(e[2]["acoples_de_la_activacion"], tuple(ACOPLE_FINAL))

    def test_firma_primero_el_primer_escalon_no_acopla_y_el_segundo_si(self):
        e = recorrido("firma-primero")["escalones"]
        self.assertEqual(e[1]["acoples"], [])  # BLAKE2s contra Ed25519 y ML-DSA-44: libre
        self.assertEqual(e[2]["acoples"], ACOPLE_FINAL)  # ...y entra SHA-3 (Keccak)
        self.assertEqual(e[2]["acoples_de_la_activacion"], tuple(ACOPLE_FINAL))

    def test_a_la_vez_el_acople_aparece_en_el_unico_escalon(self):
        e = recorrido("a-la-vez")["escalones"]
        self.assertEqual(e[1]["generacion"], 2)
        self.assertEqual(e[1]["acoples"], ACOPLE_FINAL)

    def test_reportar_no_es_bloquear_la_transicion_que_acopla_se_activa(self):
        """Si el chequeo bloqueara, la cadena no llegaría a la generación 2."""
        for o in ORDENES:
            self.assertEqual(recorrido(o)["final"]["generacion"], 2, o)
            self.assertEqual(recorrido(o)["final"]["acoples"], ACOPLE_FINAL, o)

    def test_la_funcion_reporta_sin_levantar(self):
        formatos = {ED25519, ML_DSA_44}
        self.assertEqual(nucleo.acoples(HASH_SHA3, formatos), ACOPLE_FINAL)
        self.assertEqual(nucleo.acoples(HASH_BLAKE2S, formatos), [])
        self.assertEqual(nucleo.acoples(HASH_SHA3, {ED25519}), [])


class LoQueLaDemostracionNoEs(unittest.TestCase):
    """Los límites declarados, fijados para que no se pierdan en una edición."""

    def test_ml_dsa_87_no_es_un_escalon(self):
        """Es un nivel de costo medido en Test 2, no una sucesora: no está en el paper ni en Génesis."""
        self.assertNotIn("firma/ml-dsa-87", g.FORMATOS_CONOCIDOS)

    def test_las_cadenas_son_de_dos_escalones_conocidos_por_genesis(self):
        self.assertEqual({HASH_SHA3, ML_DSA_44} <= g.FORMATOS_CONOCIDOS, True)
        self.assertEqual(
            {f for f in g.FORMATOS_CONOCIDOS if f.startswith(("hash/", "firma/"))},
            {ED25519, ML_DSA_44, HASH_SHA3},
        )


if __name__ == "__main__":
    unittest.main()
