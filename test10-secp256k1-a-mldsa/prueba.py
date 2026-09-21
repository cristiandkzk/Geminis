"""Test 10 — secp256k1 → ML-DSA-44: el cambio de firma que Ethereum haría con un fork, hecho por sucesión.

Ethereum firma hoy las cuentas con ECDSA sobre secp256k1. Si tuviera que cambiar de firma, lo haría con un
fork (o, para las cuentas, con account abstraction). Esto prueba que el mecanismo de sucesión expresa ese
mismo cambio: una cadena cuya generación 0 acepta **solo** secp256k1 cruza la transición del canario y en la
generación 1 acepta además ML-DSA-44, con las firmas **verificadas de verdad** en la máquina de §6.6 bajo los
techos del ruleset de cada generación, y cada veredicto contrastado contra la verificación nativa.

**No hace falta que sea el Génesis de Geminis, y no lo es.** Se arma un Génesis alternativo, solo para esta
prueba, con `firma/secp256k1` en la generación 0. `H0_GENESIS` de Geminis no se toca (se comprueba). El
linaje se verifica contra la raíz de ese Génesis alternativo.

**Dos anclas externas**, para que no sea la implementación coincidiendo consigo misma: con la clave privada 1,
la dirección de Ethereum que sale de la clave pública es la conocida `0x7E5F…5Bdf`, y `ecrecover` corrido en la
máquina recupera esa misma dirección.

**Lo que es andamiaje y lo que es protocolo.** Igual que en Test 9: el estado sintético no tiene cuentas ni
transacciones firmadas, y nada en `geminis/` manda una firma a la máquina. El enrutado es
`VerificadorPorGeneracion`, de esta prueba. Y **no** se afirma que Ethereum deba elegir ML-DSA-44: el equipo
post-cuántico de Ethereum evalúa Falcon, Dilithium (ML-DSA) y SPHINCS+ para las cuentas.

    cd test10-secp256k1-a-mldsa/codigo/host && cargo build --release      # una vez
    python test10-secp256k1-a-mldsa/prueba.py
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
from protocolo import invariantes  # noqa: E402
from protocolo.generacion import FormatoDesconocido, Objeto, Params, Ruleset, decodificar  # noqa: E402
from protocolo.linaje import verificar_linaje  # noqa: E402
from protocolo.serializacion import corto, huella  # noqa: E402
from sucesion.regla import ReglaCanarioCriptografico  # noqa: E402

_EXE = RAIZ / "codigo" / "host" / "target" / "release" / (
    "vm-firma10.exe" if sys.platform == "win32" else "vm-firma10"
)

SECP = "secp256k1"
ML = "ml-dsa-44"
FORMATO = {SECP: "firma/secp256k1", ML: "firma/ml-dsa-44"}

#: La clave privada 1, y la dirección de Ethereum que todo el mundo conoce para ella.
CLAVE_PRIVADA_1 = "00" * 31 + "01"
DIRECCION_DE_LA_CLAVE_1 = "0x7e5f4552091a69125d5dfcb7b8c2659029395bdf"

SEMILLA_ML = "11" * 32
HASH = "5a" * 32        # el hash de 32 bytes que se firma (en Ethereum, keccak256 de la transacción)
HASH_OTRO = "5b" * 32   # el que NO se firmó


def _correr(*args: str) -> str:
    return subprocess.run([str(_EXE), *args], check=True, capture_output=True, text=True).stdout


def _campos(salida: str) -> dict[str, str]:
    return dict(par.split("=", 1) for par in salida.split())


def _firmar(formato: str) -> dict[str, str]:
    semilla = CLAVE_PRIVADA_1 if formato == SECP else SEMILLA_ML
    return _campos(_correr("firmar", formato, semilla, HASH))


def _alterar(hex_: str, byte: int) -> str:
    b = bytearray.fromhex(hex_)
    b[byte] ^= 1
    return b.hex()


def genesis_alternativo() -> Ruleset:
    """Un Génesis con `firma/secp256k1` en la generación 0. Es de esta prueba: el de Geminis no se toca."""
    formatos = frozenset({"direccion/gen0", "firma/secp256k1", "recibo/gen0"})
    params = Params(0, dict(g.PARAMS_INICIALES.internos), formatos)
    raiz = huella(
        {"interprete": g.HUELLA_INTERPRETE, "params": params.canonico()}, dominio="linaje/raiz"
    )
    return Ruleset(params=params, h0=raiz)


class VerificadorPorGeneracion:
    """**Andamiaje de esta prueba, no protocolo.** Admite por formato y verifica en la máquina."""

    def __init__(self, nodo: NodoPoD) -> None:
        self.nodo = nodo
        self.llamadas_a_la_maquina = 0

    def verificar(self, formato: str, pk: str, sig: str, msg: str, generacion_del_objeto: int) -> dict:
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
    h0_geminis = g.H0_GENESIS
    conocidos_antes = g.FORMATOS_CONOCIDOS
    i4_antes = invariantes.i4_linaje
    # Génesis alternativo: `firma/secp256k1` tiene que ser un formato que ese Génesis conozca (I1).
    g.FORMATOS_CONOCIDOS = conocidos_antes | {"firma/secp256k1"}
    try:
        ruleset0 = genesis_alternativo()
        # **Limitación del nodo, encontrada por esta prueba:** I4 se revisa en cada bloque contra
        # `g.H0_GENESIS` de Geminis (es el `h0_raiz` por defecto), así que el nodo hoy no soporta otro
        # Génesis. Sin apagar las invariantes, se le pasa la raíz del alternativo solo durante el escenario.
        invariantes.i4_linaje = lambda checkpoints, h0_raiz=ruleset0.h0: i4_antes(checkpoints, h0_raiz)
        nodo = NodoPoD(reglas=[ReglaCanarioCriptografico()], ruleset=ruleset0)
        nodo.producir(2)
        v = VerificadorPorGeneracion(nodo)
        secp, ml = _firmar(SECP), _firmar(ML)
        obs: dict = {"h0_geminis": h0_geminis, "h0_alternativo": ruleset0.h0}

        # ---------------------------------------------------------------- generación 0
        obs["gen0"] = nodo.generacion
        obs["formatos0"] = frozenset(nodo.ruleset.formatos)
        obs["secp_gen0"] = v.verificar(SECP, secp["pk"], secp["sig"], HASH, 0)
        obs["secp_hash_otro_gen0"] = v.verificar(SECP, secp["pk"], secp["sig"], HASH_OTRO, 0)
        alta = _campos(_correr("alterar-s", secp["sig"]))["sig"]
        obs["secp_s_alto_gen0"] = v.verificar(SECP, secp["pk"], alta, HASH, 0)

        llamadas = v.llamadas_a_la_maquina
        try:
            v.verificar(ML, ml["pk"], ml["sig"], HASH, 0)
            obs["ml_en_gen0"] = "admitida"
        except FormatoDesconocido as e:
            obs["ml_en_gen0"] = "rechazada por formato"
            obs["ml_en_gen0_mensaje"] = str(e)
        obs["ml_gen0_no_toco_la_maquina"] = v.llamadas_a_la_maquina == llamadas

        # ---------------------------------------------------------------- la transición
        nodo.producir_bloque([("gastar_canario",)])
        while nodo.generacion == 0 and nodo.altura < 300:
            nodo.producir(1)
        obs["altura_activacion"] = nodo.conmutaciones[0].altura
        nodo.producir(5)
        obs["gen1"] = nodo.generacion
        obs["formatos1"] = frozenset(nodo.ruleset.formatos)

        # ---------------------------------------------------------------- generación 1
        obs["secp_de_gen0_en_gen1"] = v.verificar(SECP, secp["pk"], secp["sig"], HASH, 0)
        obs["secp_s_alto_gen1"] = v.verificar(SECP, secp["pk"], alta, HASH, 1)
        obs["ml_gen1"] = v.verificar(ML, ml["pk"], ml["sig"], HASH, 1)
        obs["ml_hash_otro_gen1"] = v.verificar(ML, ml["pk"], ml["sig"], HASH_OTRO, 1)
        obs["ml_firma_alterada_gen1"] = v.verificar(ML, ml["pk"], _alterar(ml["sig"], 10), HASH, 1)
        obs["secp_bytes_como_ml"] = v.verificar(ML, secp["pk"], secp["sig"], HASH, 1)
        obs["ml_bytes_como_secp"] = v.verificar(SECP, ml["pk"], ml["sig"], HASH, 1)

        # ---------------------------------------------------------------- anclas externas
        obs["direccion_nativa"] = _campos(_correr("direccion", secp["pk"]))["direccion"]
        techo0 = g.techo_vigente(ruleset0)
        pag0 = g.paginas_vigentes(ruleset0)
        # ecrecover bajo el techo de la generación 0: es el hallazgo, no se le sube el techo.
        obs["ecrecover_bajo_el_techo"] = _campos(
            _correr("recuperar", secp["sig"], HASH, secp["recid"], str(techo0), str(pag0))
        )
        # y con un techo que alcance, para tener el número y comprobar la dirección que recupera.
        obs["ecrecover_sin_techo"] = _campos(
            _correr("recuperar", secp["sig"], HASH, secp["recid"], "1000000000", str(pag0))
        )

        # ---------------------------------------------------------------- lo que tiene que conservarse
        cps = nodo.cronograma.checkpoints
        obs["checkpoints"] = len(cps)
        obs["ancestro_del_primero"] = cps[0].h0_ancestro if cps else None
        obs["linaje_verifica"] = verificar_linaje(cps, ruleset0.h0)
        obs["cadena_intacta"] = all(b.padre == a.hash() for a, b in zip(nodo.cadena, nodo.cadena[1:]))
        obs["altura_final"] = nodo.altura
        obs["techo_gen0"] = techo0
    finally:
        g.FORMATOS_CONOCIDOS = conocidos_antes
        invariantes.i4_linaje = i4_antes
    obs["h0_geminis_despues"] = g.H0_GENESIS
    return obs


def _todas(obs: dict) -> dict[str, dict]:
    return {k: v for k, v in obs.items() if isinstance(v, dict) and "acepta" in v and "nativo" in v}


class Gen0ReconoceSoloSecp256k1(unittest.TestCase):
    def test_la_generacion_0_declara_solo_secp256k1(self):
        o = escenario()
        self.assertEqual(o["gen0"], 0)
        self.assertIn("firma/secp256k1", o["formatos0"])
        self.assertNotIn("firma/ml-dsa-44", o["formatos0"])

    def test_una_firma_secp256k1_valida_la_acepta_la_maquina(self):
        self.assertTrue(escenario()["secp_gen0"]["acepta"])

    def test_la_misma_firma_sobre_otro_hash_la_rechaza_la_maquina(self):
        self.assertFalse(escenario()["secp_hash_otro_gen0"]["acepta"])

    def test_una_firma_con_s_alto_se_rechaza_como_en_eip_2(self):
        """La maleabilidad (`s' = n - s`) que Ethereum no acepta: la máquina y el nativo la rechazan."""
        o = escenario()
        self.assertFalse(o["secp_s_alto_gen0"]["acepta"])
        self.assertFalse(o["secp_s_alto_gen1"]["acepta"])

    def test_una_firma_ml_dsa_44_no_pasa_ni_por_la_maquina(self):
        o = escenario()
        self.assertEqual(o["ml_en_gen0"], "rechazada por formato")
        self.assertTrue(o["ml_gen0_no_toco_la_maquina"])
        self.assertIn("generación 0", o["ml_en_gen0_mensaje"])


class LaTransicionNoRompeLaRaiz(unittest.TestCase):
    def test_el_genesis_de_geminis_no_se_toco(self):
        o = escenario()
        self.assertEqual(o["h0_geminis"], o["h0_geminis_despues"])
        self.assertEqual(corto(o["h0_geminis_despues"]), "6175777756bd3f8c")

    def test_el_genesis_alternativo_es_otra_raiz(self):
        o = escenario()
        self.assertNotEqual(o["h0_alternativo"], o["h0_geminis"])

    def test_la_cadena_cruzo_a_la_generacion_1_sin_cortarse(self):
        o = escenario()
        self.assertEqual(o["gen1"], 1)
        self.assertTrue(o["cadena_intacta"])
        self.assertGreater(o["altura_final"], o["altura_activacion"])

    def test_el_linaje_verifica_contra_la_raiz_del_genesis_alternativo(self):
        o = escenario()
        self.assertEqual(o["checkpoints"], 1)
        self.assertEqual(o["ancestro_del_primero"], o["h0_alternativo"])
        self.assertTrue(o["linaje_verifica"])


class Gen1ReconoceLosDosEstados(unittest.TestCase):
    def test_la_transicion_es_aditiva_y_no_retira_secp256k1(self):
        o = escenario()
        self.assertEqual(o["formatos1"], o["formatos0"] | {"firma/ml-dsa-44"})

    def test_lo_firmado_en_la_generacion_0_sigue_valiendo_en_la_1(self):
        self.assertTrue(escenario()["secp_de_gen0_en_gen1"]["acepta"])

    def test_ml_dsa_44_ahora_se_acepta(self):
        self.assertTrue(escenario()["ml_gen1"]["acepta"])

    def test_cada_primitiva_rechaza_lo_que_no_firmo(self):
        o = escenario()
        for k in ("ml_hash_otro_gen1", "ml_firma_alterada_gen1"):
            self.assertFalse(o[k]["acepta"], k)

    def test_los_bytes_de_un_formato_no_pasan_por_el_otro(self):
        o = escenario()
        self.assertFalse(o["secp_bytes_como_ml"]["acepta"])
        self.assertFalse(o["ml_bytes_como_secp"]["acepta"])


class AnclasExternas(unittest.TestCase):
    """Que no sea la implementación coincidiendo consigo misma."""

    def test_la_clave_privada_1_da_la_direccion_de_ethereum_conocida(self):
        self.assertEqual(escenario()["direccion_nativa"], DIRECCION_DE_LA_CLAVE_1)

    def test_ecrecover_en_la_maquina_recupera_esa_misma_direccion(self):
        r = escenario()["ecrecover_sin_techo"]
        self.assertEqual(r["acepta"], "1")
        self.assertEqual(r["direccion"], DIRECCION_DE_LA_CLAVE_1)


class LaMaquinaYElNativoCoinciden(unittest.TestCase):
    def test_todo_veredicto_de_la_maquina_es_el_de_la_verificacion_nativa(self):
        todas = _todas(escenario())
        # Exacto a propósito: agregar o sacar un caso al escenario tiene que ser una decisión.
        self.assertEqual(len(todas), 10)
        for nombre, r in todas.items():
            self.assertEqual(r["acepta"], r["nativo"], nombre)


class NadaSeSaleDelPresupuestoSalvoEcrecover(unittest.TestCase):
    def test_lo_que_se_acepta_entra_bajo_los_dos_techos_del_ruleset(self):
        for nombre, r in _todas(escenario()).items():
            if r["acepta"]:
                self.assertLess(r["pasos"], r["techo"], nombre)
                self.assertLessEqual(r["paginas"], r["techo_paginas"], nombre)

    def test_ecrecover_no_cabe_bajo_el_techo_inicial(self):
        """**El hallazgo.** Lo que hace Ethereum de verdad (recuperar la clave) cuesta más que el techo de un
        ruleset como el de Geminis: entraría bajando `tx_por_bloque`, que es exactamente el precio que §6.6
        le pone a una primitiva cara. Verificar con la clave conocida sí cabe."""
        o = escenario()
        self.assertEqual(o["ecrecover_bajo_el_techo"]["acepta"], "0")
        self.assertIn("TechoExcedido", o["ecrecover_bajo_el_techo"]["veredicto"])
        self.assertGreater(int(o["ecrecover_sin_techo"]["pasos"]), o["techo_gen0"])

    def test_verificar_secp256k1_cuesta_mas_que_ml_dsa_44_en_esta_maquina(self):
        """Dato incómodo y honesto: con estos dos crates de referencia, la firma de Ethereum es la más cara."""
        o = escenario()
        self.assertGreater(o["secp_gen0"]["pasos"], o["ml_gen1"]["pasos"])

    def test_un_rechazo_por_hash_o_firma_alterada_no_es_gratis(self):
        o = escenario()
        for nombre in ("secp_hash_otro_gen0", "ml_hash_otro_gen1", "ml_firma_alterada_gen1"):
            self.assertGreater(o[nombre]["pasos"], 3_000_000, nombre)


def resumen() -> None:
    o = escenario()
    print()
    print(f"# Génesis alternativo {corto(o['h0_alternativo'])} · Geminis {corto(o['h0_geminis_despues'])} sin tocar · "
          f"activó en la altura {o['altura_activacion']} · {o['checkpoints']} checkpoint, linaje verifica: {o['linaje_verifica']}")
    print(f"{'caso':28s} {'acepta':>6s} {'nativo':>6s} {'pasos':>10s} {'pág':>4s}")
    for nombre, r in _todas(o).items():
        print(f"{nombre:28s} {int(r['acepta']):>6d} {int(r['nativo']):>6d} {r['pasos']:>10,d} {r['paginas']:>4d}")
    e = o["ecrecover_sin_techo"]
    print(f"{'ecrecover (sin techo)':28s} {int(e['acepta']):>6d} {'':>6s} {int(e['pasos']):>10,d} {int(e['paginas']):>4d}  -> {e['direccion']}")
    print(f"ecrecover bajo el techo de {o['techo_gen0']:,}: {o['ecrecover_bajo_el_techo']['veredicto']}")
    print(f"ml_en_gen0: {o['ml_en_gen0']} (no invocó la máquina: {o['ml_gen0_no_toco_la_maquina']})")


if __name__ == "__main__":
    if not _EXE.exists():
        sys.exit(f"falta {_EXE}: cd codigo/host && cargo build --release")
    ok = unittest.main(exit=False, verbosity=1).result.wasSuccessful()
    resumen()
    sys.exit(0 if ok else 1)
