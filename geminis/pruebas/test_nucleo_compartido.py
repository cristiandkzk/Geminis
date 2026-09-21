"""El linaje y la firma no pueden compartir núcleo criptográfico (§10.1).

La escalera de canarios de §6.6 gradúa la respuesta suponiendo que las primitivas ceden **de a una y
en orden**. Ese supuesto se rompe si la función que encadena el linaje (`H`, I4) y la primitiva de
firma en vigor comparten núcleo: una sola rotura se lleva las dos, y la migración tendría que correr
sobre una cadena cuya verificación de linaje ya no es confiable.

Hasta el 21/9/2026 esto no lo hacía cumplir nada: `H` era SHA-256 y la firma inicial, Ed25519, hashea
con SHA-512 por dentro —las dos, SHA-2—, y el sucesor de la firma, ML-DSA-44, usa SHAKE (Keccak), de
modo que un `H` sucesor en Keccak la habría vuelto a acoplar. Ahora `H` es BLAKE2s (`HASH_GENESIS`).

**La tabla `NUCLEO` vive en `protocolo/nucleo.py`**, junto al chequeo que **reporta y no bloquea** el acople
del hash sucesor (SHA-3, Keccak) con ML-DSA-44: esa parte se prueba en `test_sucesion_independiente.py`. Lo que
estas pruebas sí hacen cumplir, **con filo**, es lo de la generación 0: `H` no comparte núcleo con la firma
inicial, y tampoco lo hace tras una sucesión de firma sola.

Y la segunda clase existe por una razón concreta: **ninguna otra prueba fija un hash literal**. El 17/9
un find-and-replace movió `H0_GENESIS` sin que cayera nada, y el 21/9 el cambio deliberado de SHA-256 a
BLAKE2s dio 302 de 302 con la raíz ya movida. Estos valores son los de *después* de ese cambio: si se
mueven, se movió lo publicado.
"""

from __future__ import annotations

import hashlib
import pathlib
import re
import unittest

from estado import arbol, desalojo
from predicado.aceptacion import Predicado
from protocolo import genesis as g
from protocolo import nucleo
from protocolo.serializacion import HASH_GENESIS, codificar, corto, huella
from pruebas.comun import GASTAR_CANARIO, nodo_canario


class ElHashDeGenesisNoComparteNucleoConLaFirma(unittest.TestCase):
    def test_todo_formato_de_firma_conocido_declara_su_nucleo(self):
        """Falla cerrado: una firma nueva sin núcleo declarado no puede colarse sin decidir esto."""
        for formato in nucleo.firmas(g.FORMATOS_CONOCIDOS):
            self.assertIn(formato, nucleo.NUCLEO, f"{formato} no declara su núcleo")

    def test_el_hash_de_genesis_declara_su_nucleo(self):
        self.assertIn(HASH_GENESIS, nucleo.NUCLEO)

    def test_en_la_generacion_0_no_comparten(self):
        nucleos = {nucleo.NUCLEO[f] for f in nucleo.firmas(g.PARAMS_INICIALES.formatos)}
        self.assertNotIn(nucleo.NUCLEO[HASH_GENESIS], nucleos)

    def test_tras_el_canario_tampoco_comparte_con_ninguna_firma_en_vigor(self):
        """La firma sucesora se suma (I5) y ed25519 no se retira: hay que mirar las dos."""
        nodo = nodo_canario()
        nodo.producir(2)
        nodo.producir_bloque([GASTAR_CANARIO])
        nodo.producir(45)
        self.assertEqual(nodo.generacion, 1)
        firmas = nucleo.firmas(nodo.ruleset.formatos)
        self.assertEqual(firmas, {"firma/ed25519", "firma/ml-dsa-44"})
        self.assertNotIn(nucleo.NUCLEO[HASH_GENESIS], {nucleo.NUCLEO[f] for f in firmas})

    def test_huella_es_de_verdad_el_hash_declarado(self):
        """El nombre no alcanza: lo que se calcula tiene que ser el algoritmo de esa familia."""
        base = b"genesis/" + b"prueba" + b"\x00" + codificar(b"x")
        self.assertEqual(huella(b"x", "prueba"), hashlib.blake2s(base).digest())
        self.assertNotEqual(huella(b"x", "prueba"), hashlib.sha256(base).digest())
        self.assertNotEqual(huella(b"x", "prueba"), hashlib.sha3_256(base).digest())


RAIZ = pathlib.Path(__file__).resolve().parent.parent

#: Los únicos módulos del protocolo que pueden importar `hashlib`. `serializacion` es el punto
#: único de entrada al hash de Genesis. `doble_firma` es una excepción **declarada**: es un
#: Schnorr de juguete de 127 bits (Fase 3) donde SHA-256 es parte interna *de esa primitiva*, no
#: el hash de consenso de la cadena; migrarlo sería reescribir el modelo de otra firma.
PUEDEN_IMPORTAR_HASHLIB = {"protocolo/serializacion.py", "liquidacion/doble_firma.py"}


class ElHashDeConsensoSaleDeUnSoloLugar(unittest.TestCase):
    def test_ningun_otro_modulo_del_protocolo_importa_hashlib(self):
        """Si otro módulo hasheara por su cuenta, cambiar `H` dejaría una parte del consenso en la
        familia vieja sin que nada lo notara: eso fue lo que pasó con el árbol el 21/9."""
        sospechosos = []
        for archivo in RAIZ.rglob("*.py"):
            rel = archivo.relative_to(RAIZ).as_posix()
            if rel.startswith(("pruebas/", "herramientas/")) or "__pycache__" in rel:
                continue
            if re.search(r"^\s*(import hashlib|from hashlib)", archivo.read_text(encoding="utf-8"), re.M):
                sospechosos.append(rel)
        self.assertEqual(set(sospechosos), PUEDEN_IMPORTAR_HASHLIB)

    def test_el_arbol_el_desalojo_y_los_predicados_hashean_con_el_hash_de_genesis(self):
        """No alcanza con que no importen `hashlib`: tienen que dar lo que da BLAKE2s."""
        self.assertEqual(
            arbol.hoja(b"x"), hashlib.blake2s(b"genesis/arbol/hoja" + b"x").digest()
        )
        self.assertEqual(
            desalojo.hoja(b"x"), hashlib.blake2s(b"genesis/desalojo/hoja" + b"x").digest()
        )
        pred = Predicado(programa=b"\x11" * 32, vectores=((b"a", b"ok"),))
        esperado = hashlib.blake2s(
            b"\x11" * 32
            + (1).to_bytes(4, "little") + b"a"
            + (2).to_bytes(4, "little") + b"ok"
        ).digest()
        self.assertEqual(pred.huella(), esperado)


class LoPublicadoSeMovioAPropositoYNoSeMueveSolo(unittest.TestCase):
    def test_h0_de_genesis(self):
        self.assertEqual(corto(g.H0_GENESIS), "6175777756bd3f8c")
        # El valor de antes del cambio de SHA-256 a BLAKE2s: que no vuelva sin que nadie lo decida.
        self.assertNotEqual(corto(g.H0_GENESIS), "dd2ce1fe33cbcad0")

    def test_una_cadena_de_dos_generaciones(self):
        nodo = nodo_canario()
        nodo.producir(2)
        nodo.producir_bloque([GASTAR_CANARIO])
        nodo.producir(20)
        nodo.producir_bloque([GASTAR_CANARIO])
        nodo.producir(20)
        self.assertEqual(nodo.generacion, 2)
        self.assertEqual(
            [corto(c.h0) for c in nodo.cronograma.checkpoints],
            ["364ef77e52352d12", "f837f159c58a8de6"],
        )
        self.assertEqual(corto(nodo.estado.huella()), "3887ccbf014685a6")
        self.assertEqual(corto(nodo.cadena[-1].hash()), "a2906696782ebe23")


if __name__ == "__main__":
    unittest.main()
