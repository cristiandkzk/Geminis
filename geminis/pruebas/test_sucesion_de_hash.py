"""La sucesión del hash DENTRO de la cadena: BLAKE2s en la generación 0, SHA-3 (Keccak) en la 1.

El disparo no es una adopción: es el canario de hash (`g.resuelve_canario_hash`), una prueba de trabajo
sobre una semilla pública. Ningún porcentaje del circulante decide nada, porque `progreso` sólo lee el
estado (I2). Y la misma cadena, sin reiniciarse, pasa de un hash al otro **en una altura fija que nadie
eligió** y todo lo anterior sigue verificando.

Hay una regla de diseño que estas pruebas fijan, y es la que no es obvia: **cada checkpoint del linaje
se calcula con el hash de su ancestro**, no con el que introduce. Verificar la transición A→B no puede
exigir confiar ya en la primitiva de B.

"SHA-3 (Keccak)" y no "Keccak-256": es `hashlib.sha3_256`, la misma permutación que el Keccak-256 de
Ethereum pero con otro relleno, así que no da los mismos digests.
"""

from __future__ import annotations

import dataclasses
import unittest
from functools import cache

from estado.sintetico import EstadoSintetico, OperacionInvalida
from nodo.pod import NodoPoD
from protocolo import genesis as g
from protocolo.linaje import calcular_h0, motivo_linaje_invalido, verificar_linaje
from protocolo.serializacion import HASH_BLAKE2S, HASH_SHA3, hash_vigente, huella
from pruebas.comun import GASTAR_CANARIO
from sucesion.regla import ReglaCanarioHash, ReglaEmisionAcumulada

BLOQUES = 60


@cache
def solucion() -> bytes:
    """Gasta el canario por fuerza bruta: 2^16 intentos, una fracción de segundo."""
    for i in range(1 << 22):  # ~2^16 esperados; acotado para que un canario imposible no cuelgue todo
        candidata = i.to_bytes(8, "big")
        if g.resuelve_canario_hash(candidata):
            return candidata
    raise AssertionError("ninguna solución gasta el canario de hash")


def gastar():
    return ("gastar_canario_hash", solucion())


def nodo_con_el_canario(paso_emision: int | None = None) -> NodoPoD:
    reglas = [ReglaCanarioHash()]
    if paso_emision is not None:
        reglas.append(ReglaEmisionAcumulada(paso=paso_emision))
    return NodoPoD(reglas=reglas)


def correr(nodo: NodoPoD, hasta: int) -> NodoPoD:
    """Dos bloques, el gasto del canario en el tercero, y vacíos hasta `hasta`."""
    nodo.producir(2)
    nodo.producir_bloque([gastar()])
    nodo.producir(hasta - nodo.altura)
    return nodo


@cache
def altura_de_activacion() -> int:
    """Dónde cambia el hash. Se mide, no se supone: depende de finalidad y de `Δ`."""
    return correr(nodo_con_el_canario(), BLOQUES).conmutaciones[0].altura


def nodo_de_dos_generaciones() -> NodoPoD:
    """Hash canario → SHA-3; después la regla de emisión, ya con SHA-3 vigente."""
    h = altura_de_activacion()
    paso = 1_000 * (h + 10)  # la emisión es 1.000 por bloque: dispara en h + 10
    # Se corta justo después de su lock-in (h + 22), antes de que otra pase a armarse.
    return correr(nodo_con_el_canario(paso), h + 25)


class ElCanarioDeHashSeVerifica(unittest.TestCase):
    def test_una_solucion_falsa_no_lo_gasta(self):
        falsa = next(
            (
                i.to_bytes(8, "big")
                for i in range(100_000)
                if not g.resuelve_canario_hash(i.to_bytes(8, "big"))
            ),
            None,
        )
        self.assertIsNotNone(falsa, "toda solución gasta el canario: no verifica nada")
        estado = EstadoSintetico()
        with self.assertRaises(OperacionInvalida):
            estado.aplicar(("gastar_canario_hash", falsa), g.RULESET_INICIAL)
        self.assertEqual(estado.canarios_hash_gastados, 0)

    def test_una_solucion_real_lo_gasta_una_sola_vez(self):
        estado = EstadoSintetico()
        estado.aplicar(gastar(), g.RULESET_INICIAL)
        self.assertEqual(estado.canarios_hash_gastados, 1)
        with self.assertRaises(OperacionInvalida):
            estado.aplicar(gastar(), g.RULESET_INICIAL)

    def test_una_solucion_del_canario_de_firma_no_sirve_de_hash(self):
        """Son dos alarmas distintas: gastar una no dispara la otra."""
        nodo = NodoPoD(reglas=[ReglaCanarioHash()])
        nodo.producir_bloque([GASTAR_CANARIO])
        nodo.producir(40)
        self.assertEqual(nodo.generacion, 0)


class ElHashCambiaEnLaActivacionYNoAntes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nodo = correr(nodo_con_el_canario(), BLOQUES)
        cls.h = cls.nodo.conmutaciones[0].altura

    def test_la_generacion_uno_declara_el_hash_nuevo(self):
        self.assertEqual(self.nodo.generacion, 1)
        self.assertIn(HASH_SHA3, self.nodo.ruleset.formatos)
        self.assertEqual(hash_vigente(g.RULESET_INICIAL.formatos), HASH_BLAKE2S)
        self.assertEqual(self.nodo.estado.hash_id, HASH_SHA3)

    def test_cada_bloque_se_identifica_con_el_hash_de_su_altura(self):
        for bloque in self.nodo.cadena:
            esperado = HASH_SHA3 if bloque.altura >= self.h else HASH_BLAKE2S
            self.assertEqual(bloque.hash_id, esperado, f"altura {bloque.altura}")
            self.assertEqual(
                bloque.hash(), huella(bloque.canonico(), "bloque", esperado)
            )

    def test_el_hash_nuevo_da_otra_imagen_del_mismo_bloque(self):
        bloque = self.nodo.cadena[self.h]
        otro = HASH_BLAKE2S if bloque.hash_id == HASH_SHA3 else HASH_SHA3
        self.assertNotEqual(bloque.hash(), huella(bloque.canonico(), "bloque", otro))

    def test_la_cadena_de_bloques_cruza_el_cambio_sin_cortarse(self):
        cadena = self.nodo.cadena
        for anterior, siguiente in zip(cadena, cadena[1:]):
            self.assertEqual(siguiente.padre, anterior.hash())
        # El primer bloque de SHA-3 apunta a un padre que se hasheó con BLAKE2s.
        self.assertEqual(cadena[self.h].hash_id, HASH_SHA3)
        self.assertEqual(cadena[self.h - 1].hash_id, HASH_BLAKE2S)

    def test_la_huella_del_estado_usa_el_hash_vigente(self):
        estado = self.nodo.estado
        self.assertEqual(
            estado.huella(),
            huella(estado.canonico(), "estado/sintetico", HASH_SHA3),
        )
        self.assertEqual(self.nodo.cadena[-1].raiz_estado, estado.huella())


class ElLinajeAtraviesaElCambio(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nodo = nodo_de_dos_generaciones()
        cls.checkpoints = cls.nodo.cronograma.checkpoints

    def test_hay_dos_generaciones_y_verify_da_true(self):
        self.assertEqual(len(self.checkpoints), 2)
        self.assertTrue(verificar_linaje(self.checkpoints, g.H0_GENESIS))

    def test_el_checkpoint_que_introduce_sha3_sale_de_blake2s(self):
        """Verificar A→B no puede exigir confiar ya en la primitiva de B."""
        primero = self.checkpoints[0]
        self.assertIn(HASH_SHA3, primero.params.formatos)
        self.assertTrue(primero.es_valido(HASH_BLAKE2S))
        self.assertFalse(primero.es_valido(HASH_SHA3))

    def test_el_siguiente_ya_sale_de_sha3(self):
        segundo = self.checkpoints[1]
        self.assertTrue(segundo.es_valido(HASH_SHA3))
        self.assertFalse(segundo.es_valido(HASH_BLAKE2S))

    def test_un_nodo_que_siguio_con_blake2s_no_tiene_checkpoint_valido(self):
        segundo = self.checkpoints[1]
        con_el_hash_viejo = dataclasses.replace(
            segundo,
            h0=calcular_h0(
                segundo.h0_ancestro, segundo.state_trigger, segundo.params, HASH_BLAKE2S
            ),
        )
        motivo = motivo_linaje_invalido(
            [self.checkpoints[0], con_el_hash_viejo], g.H0_GENESIS
        )
        self.assertIsNotNone(motivo)
        self.assertIn(HASH_SHA3, motivo)

    def test_alterar_el_primer_eslabon_rompe_todo_lo_que_cuelga(self):
        roto = dataclasses.replace(self.checkpoints[0], state_trigger=b"\x00" * 32)
        self.assertFalse(verificar_linaje([roto, self.checkpoints[1]], g.H0_GENESIS))


class NodosQueNoSeHablanConvergen(unittest.TestCase):
    def test_cuatro_nodos_llegan_a_lo_mismo_y_el_desviado_no(self):
        honestos = [correr(nodo_con_el_canario(), BLOQUES) for _ in range(4)]
        referencia = honestos[0]
        for nodo in honestos[1:]:
            self.assertEqual(
                [b.hash() for b in nodo.cadena], [b.hash() for b in referencia.cadena]
            )
            self.assertEqual(
                [c.h0 for c in nodo.cronograma.checkpoints],
                [c.h0 for c in referencia.cronograma.checkpoints],
            )
            self.assertEqual(nodo.estado.hash_id, HASH_SHA3)

        desviado = NodoPoD(reglas=[])
        desviado.producir(BLOQUES)
        self.assertEqual(desviado.estado.hash_id, HASH_BLAKE2S)
        self.assertEqual(desviado.cronograma.checkpoints, [])
        self.assertNotEqual(desviado.cadena[-1].hash(), referencia.cadena[-1].hash())


class UnaReorganizacionNoDejaElHashColgado(unittest.TestCase):
    def test_deshacer_la_activacion_vuelve_a_blake2s_y_reaplicar_a_sha3(self):
        h = altura_de_activacion()
        recto = correr(nodo_con_el_canario(), h + 1)
        nodo = correr(nodo_con_el_canario(), h + 1)
        self.assertEqual(nodo.estado.hash_id, HASH_SHA3)

        nodo.reorganizar(h)  # deshace la activación; el lock-in sigue en pie
        self.assertEqual(nodo.generacion, 0)
        self.assertEqual(nodo.estado.hash_id, HASH_BLAKE2S)

        nodo.producir_bloque()  # el bloque h se vuelve a producir y reactiva la generación 1
        self.assertEqual(nodo.generacion, 1)
        self.assertEqual(nodo.estado.hash_id, HASH_SHA3)
        nodo.producir_bloque()  # y el h + 1, para igualar la altura de `recto`
        self.assertEqual(
            [b.hash() for b in nodo.cadena], [b.hash() for b in recto.cadena]
        )


if __name__ == "__main__":
    unittest.main()
