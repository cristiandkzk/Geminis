"""La ventana de finalidad adaptativa — C23.

`VENTANA_FINALIDAD` no cerraba contra su propia cola: medido en C23 contra el
simulador de `liquidacion/impugnacion.py`, con `N=11` (el mínimo que el
proyecto reclama viable) el 6,2% de las impugnaciones legítimas, bajo el
ataque de censura de §6.3, no se verifican dentro de los 12 bloques
declarados. El tope duro por clase (`TOPE_DEMORA_LOCKIN`, C7.4) ya existía en
`cronograma.altura_de_lockin` para esto exacto, pero estaba inerte: nada hacía
crecer la ventana que `pod.py` le pasaba a `promover()`.

Estas pruebas fijan la activación de ese tope:

1. sin nadie reportando backlog, el comportamiento es idéntico a antes de C23
   —es la condición para no romper ninguna prueba ya escrita—;
2. backlog sostenido por encima de `backlog_seguro` estira el lock-in hasta el
   tope de la clase del disparo, no más allá;
3. backlog que se resuelve antes del tope deja madurar en cuanto la cola
   estuvo calma `ventana_finalidad` bloques seguidos — ni antes, ni con la
   altura vieja de antes del ataque;
4. la promesa de `Δ` se sostiene siempre: la activación queda **después** de
   la altura real en la que el lock-in se anuncia, nunca detrás. Ésa fue la
   forma exacta del bug que apareció escribiendo estas pruebas: grabar la
   altura teórica de la fórmula en vez de la altura real del bloque que
   proceso el lock-in dejaba `altura_activacion` ya pasada.
"""

from __future__ import annotations

import unittest

from protocolo import geminis as g
from pruebas.comun import GASTAR_CANARIO, alturas_de, nodo_canario, nodo_emision


class SinBacklogNoCambiaNada(unittest.TestCase):
    """Regresión: nadie reporta backlog todavía (Fase 3 no está conectada)."""

    def test_lockin_en_la_ventana_base_como_antes_de_c23(self):
        nodo = nodo_emision()
        while not nodo.cronograma.checkpoints and nodo.altura < 400:
            nodo.producir_bloque()

        disparo, lockin, activacion = alturas_de(nodo)[0]
        self.assertEqual(lockin, disparo + g.VENTANA_FINALIDAD)
        self.assertEqual(nodo.backlog_impugnaciones, 0)


class BacklogSostenidoEstiraHastaElTopeDeLaClase(unittest.TestCase):
    """La ventana crece, pero nunca más allá de `TOPE_DEMORA_LOCKIN` (C7.4)."""

    def test_circulacion_madura_en_su_tope(self):
        nodo = nodo_emision()
        while nodo.altura < 99:
            nodo.producir_bloque()
        while not nodo.cronograma.checkpoints and nodo.altura < 500:
            nodo.producir_bloque(backlog_impugnaciones=1_000)

        disparo, lockin, _ = alturas_de(nodo)[0]
        tope = g.VENTANA_FINALIDAD + g.tope_demora(g.CIRCULACION)
        self.assertEqual(lockin, disparo + tope)

    def test_criptografica_tiene_su_propio_tope_mas_corto(self):
        """Δ corto, tope corto: la migración de urgencia no espera lo mismo."""
        nodo = nodo_canario()
        nodo.producir(2)
        nodo.producir_bloque([GASTAR_CANARIO])
        while not nodo.cronograma.checkpoints and nodo.altura < 500:
            nodo.producir_bloque(backlog_impugnaciones=1_000)

        disparo, lockin, _ = alturas_de(nodo)[0]
        tope = g.VENTANA_FINALIDAD + g.tope_demora(g.CRIPTOGRAFICA)
        self.assertEqual(lockin, disparo + tope)
        self.assertLess(
            g.tope_demora(g.CRIPTOGRAFICA), g.tope_demora(g.CIRCULACION)
        )


class LaCalmaSostenidaDestrabaElLockin(unittest.TestCase):
    """Un ataque que para no deja el disparo esperando hasta el tope."""

    def setUp(self):
        self.nodo = nodo_emision()
        while self.nodo.altura < 99:
            self.nodo.producir_bloque()
        # dispara en la altura 100; ataque sostenido 30 bloques.
        for _ in range(30):
            self.nodo.producir_bloque(backlog_impugnaciones=1_000)

    def test_no_madura_mientras_dura_el_ataque(self):
        self.assertEqual(self.nodo.cronograma.checkpoints, [])

    def test_madura_exactamente_cuando_la_racha_de_calma_completa_la_ventana(self):
        while not self.nodo.cronograma.checkpoints and self.nodo.altura < 500:
            self.nodo.producir_bloque(backlog_impugnaciones=0)

        disparo, lockin, _ = alturas_de(self.nodo)[0]
        # ataque en 100..129 (30 bloques); calma desde 130; la racha de
        # VENTANA_FINALIDAD bloques calmos completa en 130 + 12 - 1 = 141.
        self.assertEqual(lockin, 141)
        # y NO en la altura que la formula vieja habria dado (100+12=112):
        # ese es justo el bug que estas pruebas existen para no dejar volver.
        self.assertNotEqual(lockin, disparo + g.VENTANA_FINALIDAD)


class LaPromesaDeDeltaSeSostieneBajoAtaque(unittest.TestCase):
    """El bug que casi entra: grabar una altura de lock-in ya pasada.

    Si `altura_lockin` quedara detrás de la altura real del bloque que la
    procesa, `altura_activacion = altura_lockin + Δ` podría cerrar **antes**
    de que el nodo la calcule -- el integrador se queda sin aviso, que es
    exactamente lo que Δ existe para prometer que no pasa.
    """

    def test_activacion_siempre_queda_despues_de_la_altura_real_del_lockin(self):
        nodo = nodo_emision()
        while nodo.altura < 99:
            nodo.producir_bloque()
        for _ in range(50):  # ataque más largo que en el resto de la clase
            nodo.producir_bloque(backlog_impugnaciones=1_000)
        while not nodo.cronograma.checkpoints and nodo.altura < 500:
            nodo.producir_bloque(backlog_impugnaciones=0)

        checkpoint = nodo.cronograma.checkpoints[0]
        altura_real_del_lockin = nodo.altura
        self.assertEqual(checkpoint.altura_lockin, altura_real_del_lockin)
        self.assertGreater(checkpoint.altura_activacion, altura_real_del_lockin)
        self.assertEqual(
            checkpoint.altura_activacion - checkpoint.altura_lockin,
            g.delta(g.CIRCULACION),
        )


if __name__ == "__main__":
    unittest.main()
