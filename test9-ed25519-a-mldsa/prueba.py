"""Test 9 — ed25519 → ML-DSA-44 en la misma cadena, con las firmas verificadas de verdad.

Lo que estaba probado por separado:
  - la sucesión de formatos y el linaje (Python, `geminis/`), pero las firmas eran *etiquetas*;
  - que la máquina de §6.6 ejecuta cada primitiva dentro del presupuesto (Rust, Test 2 y Test 8),
    pero fuera de cualquier cadena.

Acá se juntan. Un nodo real (`NodoPoD`) cruza la transición del canario y, en **cada generación**,
una firma se admite por el **formato que ese ruleset conoce** (`decodificar`, I5) y recién entonces
se verifica en la máquina real con los **techos de ese ruleset** (`techo_vigente`,
`paginas_vigentes`). Cada veredicto de la máquina se contrasta contra la verificación nativa.

**Qué es andamiaje y qué es protocolo.** El estado sintético no tiene cuentas ni transacciones
firmadas (Fase 3, sin construir): nada en `geminis/` enruta una firma a la máquina. Ese enrutado es
`VerificadorPorGeneracion`, de esta prueba. Lo que se prueba es que las piezas del protocolo
componen; no que exista ya un camino transacción → máquina dentro del nodo.

    cd test9-ed25519-a-mldsa/codigo/host && cargo build --release      # una vez
    python test9-ed25519-a-mldsa/prueba.py
"""

from __future__ import annotations

import subprocess
import sys
import unittest
from functools import cache
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ.parent / "geminis"))

from nodo.pod import NodoPoD  # noqa: E402
from protocolo import genesis as g  # noqa: E402
from protocolo.generacion import FormatoDesconocido, Objeto, decodificar  # noqa: E402
from protocolo.linaje import verificar_linaje  # noqa: E402
from protocolo.serializacion import corto  # noqa: E402
from sucesion.regla import ReglaCanarioCriptografico  # noqa: E402

_EXE = RAIZ / "codigo" / "host" / "target" / "release" / (
    "vm-firma.exe" if sys.platform == "win32" else "vm-firma"
)

ED = "ed25519"
ML = "ml-dsa-44"
FORMATO = {ED: "firma/ed25519", ML: "firma/ml-dsa-44"}

SEMILLA = "11" * 32
MSG = "5a" * 32
MSG_OTRO = "5b" * 32  # el mensaje que NO se firmó


def _correr(*args: str) -> str:
    return subprocess.run(
        [str(_EXE), *args], check=True, capture_output=True, text=True
    ).stdout


def _campos(salida: str) -> dict[str, str]:
    return dict(par.split("=", 1) for par in salida.split())


def _firmar(formato: str) -> tuple[str, str]:
    campos = dict(
        linea.split("=", 1) for linea in _correr("firmar", formato, SEMILLA, MSG).split()
    )
    return campos["pk"], campos["sig"]


def _alterar(hex_: str, byte: int) -> str:
    """Da vuelta un bit del byte `byte`."""
    b = bytearray.fromhex(hex_)
    b[byte] ^= 1
    return b.hex()


class VerificadorPorGeneracion:
    """**Andamiaje de esta prueba, no protocolo.** Admite por formato y verifica en la máquina."""

    def __init__(self, nodo: NodoPoD) -> None:
        self.nodo = nodo
        self.llamadas_a_la_maquina = 0

    def verificar(
        self, formato: str, pk: str, sig: str, msg: str, generacion_del_objeto: int
    ) -> dict:
        objeto = Objeto(generacion_del_objeto, FORMATO[formato])
        decodificar(objeto, self.nodo.ruleset)  # FormatoDesconocido si el ruleset no lo conoce
        self.llamadas_a_la_maquina += 1
        techo = g.techo_vigente(self.nodo.ruleset)
        paginas = g.paginas_vigentes(self.nodo.ruleset)
        maquina = _campos(_correr("verificar", formato, pk, sig, msg, str(techo), str(paginas)))
        nativo = _campos(_correr("nativo", formato, pk, sig, msg))
        return {
            "acepta": maquina["acepta"] == "1",
            "nativo": nativo["acepta"] == "1",
            "veredicto": maquina["veredicto"],
            "pasos": int(maquina["pasos"]),
            "paginas": int(maquina["paginas"]),
            "techo": techo,
            "techo_paginas": paginas,
        }


@cache
def escenario() -> dict:
    """La cadena cruza la transición; se registra qué pasa en cada lado."""
    h0_antes = g.H0_GENESIS
    nodo = NodoPoD(reglas=[ReglaCanarioCriptografico()])
    nodo.producir(2)
    v = VerificadorPorGeneracion(nodo)
    pk = {f: _firmar(f)[0] for f in (ED, ML)}
    sig = {f: _firmar(f)[1] for f in (ED, ML)}

    obs: dict = {"h0_antes": h0_antes}

    # ------------------------------------------------------------------ generación 0
    obs["gen0"] = nodo.generacion
    obs["formatos0"] = frozenset(nodo.ruleset.formatos)
    obs["ed_gen0"] = v.verificar(ED, pk[ED], sig[ED], MSG, 0)
    obs["ed_msg_otro_gen0"] = v.verificar(ED, pk[ED], sig[ED], MSG_OTRO, 0)
    obs["ed_R_alterado_gen0"] = v.verificar(ED, pk[ED], _alterar(sig[ED], 10), MSG, 0)

    llamadas = v.llamadas_a_la_maquina
    try:
        v.verificar(ML, pk[ML], sig[ML], MSG, 0)
        obs["ml_en_gen0"] = "admitida"
    except FormatoDesconocido as e:
        obs["ml_en_gen0"] = "rechazada por formato"
        obs["ml_en_gen0_mensaje"] = str(e)
    obs["ml_gen0_no_toco_la_maquina"] = v.llamadas_a_la_maquina == llamadas

    # ------------------------------------------------------------------ la transición
    nodo.producir_bloque([("gastar_canario",)])
    while nodo.generacion == 0 and nodo.altura < 300:
        nodo.producir(1)
    obs["altura_activacion"] = nodo.conmutaciones[0].altura
    nodo.producir(5)  # la cadena sigue produciendo bajo la generación 1
    obs["gen1"] = nodo.generacion
    obs["formatos1"] = frozenset(nodo.ruleset.formatos)

    # ------------------------------------------------------------------ generación 1
    # Un objeto nacido en la generación 0 sigue valiendo en la 1 (I5).
    obs["ed_de_gen0_en_gen1"] = v.verificar(ED, pk[ED], sig[ED], MSG, 0)
    obs["ed_msg_otro_gen1"] = v.verificar(ED, pk[ED], sig[ED], MSG_OTRO, 1)
    obs["ml_gen1"] = v.verificar(ML, pk[ML], sig[ML], MSG, 1)
    obs["ml_msg_otro_gen1"] = v.verificar(ML, pk[ML], sig[ML], MSG_OTRO, 1)
    obs["ml_firma_alterada_gen1"] = v.verificar(ML, pk[ML], _alterar(sig[ML], 10), MSG, 1)
    # Bytes de un formato presentados bajo el otro: la máquina tiene que rechazarlos.
    obs["ed_bytes_como_ml"] = v.verificar(ML, pk[ED], sig[ED], MSG, 1)
    obs["ml_bytes_como_ed"] = v.verificar(ED, pk[ML], sig[ML], MSG, 1)

    # ------------------------------------------------------------------ lo que tiene que conservarse
    cps = nodo.cronograma.checkpoints
    obs["checkpoints"] = len(cps)
    obs["ancestro_del_primero"] = cps[0].h0_ancestro if cps else None
    obs["linaje_verifica"] = verificar_linaje(cps, g.H0_GENESIS)
    obs["h0_despues"] = g.H0_GENESIS
    obs["cadena_intacta"] = all(
        b.padre == a.hash() for a, b in zip(nodo.cadena, nodo.cadena[1:])
    )
    obs["altura_final"] = nodo.altura
    return obs


def _todas(obs: dict) -> dict[str, dict]:
    return {k: v for k, v in obs.items() if isinstance(v, dict) and "acepta" in v}


class Gen0ReconoceSoloEd25519(unittest.TestCase):
    def test_la_generacion_0_declara_solo_ed25519(self):
        o = escenario()
        self.assertEqual(o["gen0"], 0)
        self.assertIn("firma/ed25519", o["formatos0"])
        self.assertNotIn("firma/ml-dsa-44", o["formatos0"])

    def test_una_firma_ed25519_valida_la_acepta_la_maquina(self):
        self.assertTrue(escenario()["ed_gen0"]["acepta"])

    def test_la_misma_firma_sobre_otro_mensaje_la_rechaza_la_maquina(self):
        self.assertFalse(escenario()["ed_msg_otro_gen0"]["acepta"])

    def test_una_firma_ml_dsa_44_no_pasa_ni_por_la_maquina(self):
        """El formato no está en `formatos`: falla cerrado antes de gastar un solo paso."""
        o = escenario()
        self.assertEqual(o["ml_en_gen0"], "rechazada por formato")
        self.assertTrue(o["ml_gen0_no_toco_la_maquina"])
        self.assertIn("generación 0", o["ml_en_gen0_mensaje"])


class LaTransicionNoRompeLaRaiz(unittest.TestCase):
    def test_h0_de_genesis_no_se_movio(self):
        o = escenario()
        self.assertEqual(o["h0_antes"], o["h0_despues"])
        # Movido a propósito el 21/9/2026 al pasar `H` de SHA-256 a BLAKE2s (antes: dd2ce1fe33cbcad0).
        self.assertEqual(corto(o["h0_despues"]), "6175777756bd3f8c")

    def test_la_cadena_cruzo_a_la_generacion_1_sin_cortarse(self):
        o = escenario()
        self.assertEqual(o["gen1"], 1)
        self.assertTrue(o["cadena_intacta"])
        self.assertGreater(o["altura_final"], o["altura_activacion"])

    def test_el_linaje_verifica_a_traves_del_cambio(self):
        o = escenario()
        self.assertEqual(o["checkpoints"], 1)
        self.assertEqual(o["ancestro_del_primero"], o["h0_antes"])
        self.assertTrue(o["linaje_verifica"])


class Gen1ReconoceLosDosEstados(unittest.TestCase):
    def test_la_transicion_es_aditiva_y_no_retira_ed25519(self):
        o = escenario()
        self.assertEqual(o["formatos1"], o["formatos0"] | {"firma/ml-dsa-44"})

    def test_lo_firmado_en_la_generacion_0_sigue_valiendo_en_la_1(self):
        """El estado que se conserva: la misma firma, el mismo objeto, otra generación."""
        self.assertTrue(escenario()["ed_de_gen0_en_gen1"]["acepta"])

    def test_ml_dsa_44_ahora_se_acepta(self):
        self.assertTrue(escenario()["ml_gen1"]["acepta"])

    def test_cada_primitiva_rechaza_lo_que_no_firmo(self):
        o = escenario()
        for k in ("ed_msg_otro_gen1", "ml_msg_otro_gen1", "ml_firma_alterada_gen1"):
            self.assertFalse(o[k]["acepta"], k)

    def test_los_bytes_de_un_formato_no_pasan_por_el_otro(self):
        o = escenario()
        self.assertFalse(o["ed_bytes_como_ml"]["acepta"])
        self.assertFalse(o["ml_bytes_como_ed"]["acepta"])


class LaMaquinaYElNativoCoinciden(unittest.TestCase):
    def test_todo_veredicto_de_la_maquina_es_el_de_la_verificacion_nativa(self):
        todas = _todas(escenario())
        # Exacto a propósito: agregar o sacar un caso al escenario tiene que ser una decisión.
        self.assertEqual(len(todas), 10)
        for nombre, r in todas.items():
            self.assertEqual(r["acepta"], r["nativo"], nombre)


class NadaSeSaleDelPresupuesto(unittest.TestCase):
    def test_lo_que_se_acepta_entra_bajo_los_dos_techos_del_ruleset(self):
        for nombre, r in _todas(escenario()).items():
            if r["acepta"]:
                self.assertLess(r["pasos"], r["techo"], nombre)
                self.assertLessEqual(r["paginas"], r["techo_paginas"], nombre)

    def test_un_rechazo_por_mensaje_o_firma_alterada_no_es_gratis(self):
        """Verificar una firma mala cuesta lo mismo que una buena: el techo de la cola
        (§6.3) no se puede saltear mandando basura. Salvo la R alterada de Ed25519, que la
        curva descarta al decodificar y es *más barata* de rechazar, no más cara."""
        o = escenario()
        for nombre in ("ed_msg_otro_gen0", "ml_msg_otro_gen1", "ml_firma_alterada_gen1"):
            self.assertGreater(o[nombre]["pasos"], 3_000_000, nombre)
        self.assertLess(o["ed_R_alterado_gen0"]["pasos"], o["ed_gen0"]["pasos"])

    def test_el_techo_que_uso_la_maquina_es_el_del_ruleset(self):
        o = escenario()
        self.assertEqual(o["ed_gen0"]["techo"], g.techo_vigente(g.RULESET_INICIAL))
        self.assertEqual(o["ml_gen1"]["techo"], g.techo_vigente(g.RULESET_INICIAL))


def resumen() -> None:
    o = escenario()
    print()
    print(f"# H0_GENESIS {corto(o['h0_despues'])} (igual antes y después) · activó en la altura "
          f"{o['altura_activacion']} · {o['checkpoints']} checkpoint, linaje verifica: {o['linaje_verifica']}")
    print(f"{'caso':28s} {'acepta':>6s} {'nativo':>6s} {'pasos':>10s} {'pág':>4s}")
    for nombre, r in _todas(o).items():
        print(f"{nombre:28s} {int(r['acepta']):>6d} {int(r['nativo']):>6d} {r['pasos']:>10,d} {r['paginas']:>4d}")
    print(f"ml_en_gen0: {o['ml_en_gen0']} (no invocó la máquina: {o['ml_gen0_no_toco_la_maquina']})")


if __name__ == "__main__":
    if not _EXE.exists():
        sys.exit(f"falta {_EXE}: cd codigo/host && cargo build --release")
    ok = unittest.main(exit=False, verbosity=1).result.wasSuccessful()
    resumen()
    sys.exit(0 if ok else 1)
