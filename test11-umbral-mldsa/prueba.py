"""Test 11 — firma umbral ML-DSA-44: ¿la cadena ve algo distinto de una firma común?

C25.12 razonó que un umbral entre dispositivos propios produce **una firma común bajo la clave
de la cuenta**, así que la máquina de §6.6 no ve nada nuevo. Eso era un argumento. Acá se mide:

  A. Un esquema de umbral real (el prototipo de Mithril, USENIX Security '26, sin modificar) firma
     2-de-3 con cada uno de los tres pares posibles; esas firmas entran a la máquina de §6.6
     (`geminis/predicado/vm`, sin tocarla) con los dos techos del ruleset inicial.
  B. El competidor sin criptografía de umbral: un multisig k-de-n on-chain con firmas sueltas,
     medido en pasos reales con el mismo crate y el mismo perfil.
  C. Lo que cada una cuesta en transacciones por bloque, con la fórmula de Genesis.

Requiere Go solo para A (el firmante). Sin Go, B y C corren y A se salta diciendo por qué.

    cd test11-umbral-mldsa/codigo/host && cargo build --release        # una vez
    cd ../firmante-go && go build -o target/firmante .                  # una vez (necesita ../mithril)
    python test11-umbral-mldsa/prueba.py
"""

from __future__ import annotations

import hashlib
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import unittest
from functools import cache
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ.parent / "geminis"))

from protocolo import genesis as g  # noqa: E402

_SUFIJO = ".exe" if sys.platform == "win32" else ""
_HOST = RAIZ / "codigo" / "host" / "target" / "release" / f"vm-umbral{_SUFIJO}"
_GO_DIR = RAIZ / "codigo" / "firmante-go"
_MITHRIL = RAIZ / "codigo" / "mithril" / "implementation"

MSG = "5a" * 32  # el hash de una transaccion, 32 bytes (el mismo tamano que Test 8 y 9)
SEMILLA = "0b" * 32
TECHO = g.techo_vigente(g.RULESET_INICIAL)
PAGINAS = g.paginas_vigentes(g.RULESET_INICIAL)
REPS_POR_PAR = 30
PARES = ((0, 1), (0, 2), (1, 2))
FORMAS_MULTISIG = ((1, (0,)), (2, (0, 1)), (3, (0, 2)), (3, (0, 1, 2)))  # (n, firmantes)


# ----------------------------------------------------------------------------------- #
# Herramientas
# ----------------------------------------------------------------------------------- #
def _firmante() -> Path | None:
    """El ejecutable del firmante en Go, o None si no se puede conseguir (y por que)."""
    previo = os.environ.get("FIRMANTE")
    if previo and Path(previo).exists():
        return Path(previo)
    exe = _GO_DIR / "target" / f"firmante{_SUFIJO}"
    if exe.exists():
        return exe
    if not _MITHRIL.exists() or shutil.which("go") is None:
        return None
    exe.parent.mkdir(exist_ok=True)
    subprocess.run(["go", "build", "-o", str(exe), "."], cwd=_GO_DIR, check=True)
    return exe


def _porque_no_hay_go() -> str:
    if not _MITHRIL.exists():
        return "falta codigo/mithril (ver RESULTS.md, 'Reproducir')"
    return "no hay `go` en el PATH ni la variable FIRMANTE"


def _correr(exe: Path, *args: str) -> str:
    return subprocess.run([str(exe), *args], check=True, capture_output=True, text=True).stdout


def _lineas(salida: str) -> list[dict[str, str]]:
    """Cada linea `clave=.. firma=.. intentos=..` (o `i=.. maquina_acepta=..`) como dict."""
    filas = []
    for linea in salida.splitlines():
        if linea.startswith("#") or "=" not in linea:
            continue
        filas.append(dict(p.split("=", 1) for p in linea.split() if "=" in p))
    return filas


def _en_la_maquina(archivo: Path, variante: str = "ok", techo: int = TECHO) -> list[dict[str, str]]:
    salida = _correr(_HOST, "simple", str(archivo), MSG, str(techo), str(PAGINAS), variante)
    return _lineas(salida)


def _multisig(n: int, firmantes: tuple[int, ...], variante: str = "ok",
              techo: int = TECHO, paginas: int = PAGINAS) -> dict[str, str]:
    idx = ",".join(map(str, firmantes))
    return _lineas(_correr(_HOST, "multisig", str(n), idx, MSG, str(techo), str(paginas), variante))[0]


def _sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ----------------------------------------------------------------------------------- #
# El escenario, una vez
# ----------------------------------------------------------------------------------- #
@cache
def escenario_go() -> dict | None:
    """Todo lo que necesita el firmante en Go. None si no esta disponible."""
    exe = _firmante()
    if exe is None:
        return None
    tmp = Path(tempfile.mkdtemp(prefix="test11-"))
    o: dict = {"exe": exe}

    # A1 · umbral 2-de-3, cada par, REPS_POR_PAR firmas cada uno.
    o["umbral"] = {}
    for par in PARES:
        salida = _correr(exe, "umbral", "2", "3", ",".join(map(str, par)), SEMILLA, MSG, str(REPS_POR_PAR))
        archivo = tmp / f"umbral_{par[0]}{par[1]}.txt"
        archivo.write_text(salida)
        o["umbral"][par] = {"archivo": archivo, "go": _lineas(salida)}
    todas = "".join(o["umbral"][p]["archivo"].read_text() for p in PARES)
    o["archivo_umbral"] = tmp / "umbral_todas.txt"
    o["archivo_umbral"].write_text(todas)

    # A2 · firma comun de UN firmante, con el mismo codigo del mismo fork: 30 claves distintas.
    simples = ""
    for i in range(REPS_POR_PAR):
        semilla = f"{i + 1:02x}" * 32
        simples += _correr(exe, "simple", semilla, MSG)
    o["archivo_simple"] = tmp / "simple.txt"
    o["archivo_simple"].write_text(simples)
    o["simple_go"] = _lineas(simples)

    # La maquina, con el ok y con los tres controles negativos.
    o["maq"] = {v: _en_la_maquina(o["archivo_umbral"], v) for v in ("ok", "bit-firma", "otro-mensaje", "otra-clave")}
    o["maq_simple"] = _en_la_maquina(o["archivo_simple"])
    o["maq_techo_1M"] = _en_la_maquina(o["archivo_umbral"], "ok", techo=1_000_000)

    # Una sola parte con umbral 2.
    o["insuficiente"] = _lineas(_correr(exe, "insuficiente", "2", "3", SEMILLA, MSG))[0]

    # Lado de la wallet: intentos y tiempo, en esta maquina, en proceso (sin red).
    o["wallet"] = {}
    for t, n, act in ((2, 2, "0,1"), (2, 3, "0,2"), (3, 5, "0,1,2")):
        filas = _lineas(_correr(exe, "umbral", str(t), str(n), act, SEMILLA, MSG, "300"))
        o["wallet"][(t, n)] = {
            "intentos": [int(f["intentos"]) for f in filas],
            "ms": [float(f["ms"]) for f in filas],
            "bytes_parte": int(filas[0]["bytes_parte"]),
            "todas_verifican": all(f["go_verifica"] == "1" for f in filas),
        }
    return o


@cache
def escenario_multisig() -> dict:
    o: dict = {"bajo_techo": {}, "sin_techo": {}}
    for n, firmantes in FORMAS_MULTISIG:
        o["bajo_techo"][(n, len(firmantes))] = _multisig(n, firmantes)
        o["sin_techo"][(n, len(firmantes))] = _multisig(n, firmantes, techo=100_000_000, paginas=4096)
    o["negativos"] = {v: _multisig(3, (0, 2), v) for v in ("firma-mala", "direccion-mala", "indice-repetido")}
    return o


def _pasos(filas: list[dict[str, str]]) -> list[int]:
    return [int(f["pasos"]) for f in filas]


def _aceptadas(filas: list[dict[str, str]]) -> int:
    return sum(f["maquina_acepta"] == "1" for f in filas)


# ----------------------------------------------------------------------------------- #
# A · la firma umbral, en la maquina
# ----------------------------------------------------------------------------------- #
class TestUmbralEnLaMaquina(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.o = escenario_go()
        if cls.o is None:
            raise unittest.SkipTest(_porque_no_hay_go())

    def test_el_verificador_del_propio_firmante_acepta_las_90(self):
        for par, d in self.o["umbral"].items():
            self.assertEqual(len(d["go"]), REPS_POR_PAR, par)
            self.assertTrue(all(f["go_verifica"] == "1" for f in d["go"]), par)

    def test_la_clave_de_la_cuenta_no_depende_de_quien_firma(self):
        claves = {f["clave"] for d in self.o["umbral"].values() for f in d["go"]}
        self.assertEqual(len(claves), 1)

    def test_la_maquina_acepta_las_90_y_coincide_con_el_nativo(self):
        filas = self.o["maq"]["ok"]
        self.assertEqual(len(filas), len(PARES) * REPS_POR_PAR)
        self.assertEqual(_aceptadas(filas), len(filas))
        self.assertTrue(all(f["nativo_acepta"] == "1" for f in filas))
        self.assertTrue(all(f["veredicto"] == "Retorno(1)" for f in filas))

    def test_entra_bajo_los_dos_techos_del_ruleset_inicial(self):
        filas = self.o["maq"]["ok"]
        self.assertLess(max(_pasos(filas)), TECHO)
        self.assertLessEqual(max(int(f["paginas"]) for f in filas), PAGINAS)

    def test_cuesta_lo_mismo_que_una_firma_comun(self):
        """La afirmacion de C25.12, medida: no hay un costo del umbral en la cadena."""
        um = _pasos(self.o["maq"]["ok"])
        si = _pasos(self.o["maq_simple"])
        self.assertEqual(_aceptadas(self.o["maq_simple"]), len(si))
        dif = abs(statistics.median(um) - statistics.median(si)) / statistics.median(si)
        self.assertLess(dif, 0.001)  # < 0,1 %; lo medido es ~0,004 %
        self.assertEqual({f["paginas"] for f in self.o["maq"]["ok"]}, {f["paginas"] for f in self.o["maq_simple"]})

    def test_alterar_la_firma_el_mensaje_o_la_clave_la_rechaza(self):
        for variante in ("bit-firma", "otro-mensaje", "otra-clave"):
            filas = self.o["maq"][variante]
            self.assertEqual(_aceptadas(filas), 0, variante)
            self.assertTrue(all(f["nativo_acepta"] == "0" for f in filas), variante)
            self.assertGreater(min(_pasos(filas)), 3_000_000, variante)  # rechazar cuesta lo que aceptar

    def test_por_debajo_del_umbral_no_sale_ninguna_firma(self):
        """Dos formas: una sola parte activa con t=2 (el prototipo hace panic, se cuenta aparte) y
        dos partes que firman pero `Combine` recibe una sola respuesta. Observable desde la API,
        no una prueba de seguridad."""
        f = self.o["insuficiente"]
        self.assertEqual(f["una_parte_activa_firmas"], "0")
        self.assertEqual(f["una_respuesta_firmas"], "0")
        self.assertEqual(f["firmas_aceptadas"], "0")

    def test_el_guest_simple_es_byte_a_byte_el_de_test9(self):
        t9 = RAIZ.parent / "test9-ed25519-a-mldsa" / "codigo" / "guest-mldsa44" / "guest.elf"
        if not t9.exists():
            self.skipTest("falta el guest de Test 9")
        self.assertEqual(_sha256(RAIZ / "codigo" / "guest-mldsa44" / "guest.elf"), _sha256(t9))

    def test_el_test_muerde_con_un_techo_de_1M_no_acepta_nada(self):
        filas = self.o["maq_techo_1M"]
        self.assertEqual(_aceptadas(filas), 0)
        self.assertTrue(all(f["veredicto"] == "TechoExcedido" for f in filas))

    def test_la_wallet_produce_firmas_validas_en_todas_las_formas(self):
        for forma, w in self.o["wallet"].items():
            self.assertTrue(w["todas_verifican"], forma)
            self.assertGreaterEqual(min(w["intentos"]), 1, forma)
            self.assertLess(max(w["intentos"]), 1000, forma)


# ----------------------------------------------------------------------------------- #
# B · el multisig on-chain, sin criptografia de umbral
# ----------------------------------------------------------------------------------- #
class TestMultisigOnChain(unittest.TestCase):
    def setUp(self):
        self.o = escenario_multisig()

    def test_el_costo_es_lineal_en_las_firmas_verificadas(self):
        base = int(self.o["sin_techo"][(1, 1)]["pasos"])
        for k, (lo, hi) in ((2, (1.98, 2.02)), (3, (2.97, 3.03))):
            pasos = int(self.o["sin_techo"][(3 if k == 3 else 2, k)]["pasos"])
            self.assertTrue(lo < pasos / base < hi, (k, pasos / base))

    def test_bajo_el_techo_inicial_entran_1_2_y_2_de_3_pero_no_3_de_3(self):
        bt = self.o["bajo_techo"]
        for forma in ((1, 1), (2, 2), (3, 2)):
            self.assertEqual(bt[forma]["acepta"], "1", forma)
        self.assertEqual(bt[(3, 3)]["acepta"], "0")
        self.assertEqual(bt[(3, 3)]["veredicto"], "TechoExcedido")

    def test_el_2_de_3_entra_pero_sin_margen(self):
        pasos = int(self.o["bajo_techo"][(3, 2)]["pasos"])
        self.assertLess((TECHO - pasos) / TECHO, 0.05)  # menos del 5 % del techo libre

    def test_controles_negativos_del_multisig(self):
        for variante, r in self.o["negativos"].items():
            self.assertEqual(r["acepta"], "0", variante)
            self.assertEqual(r["veredicto"], "Retorno(0)", variante)

    def test_direccion_o_indices_malos_se_rechazan_casi_gratis(self):
        # Se rechazan antes de gastar una verificacion: ~135 k pasos, no ~3,3 M.
        for variante in ("direccion-mala", "indice-repetido"):
            self.assertLess(int(self.o["negativos"][variante]["pasos"]), 200_000, variante)

    def test_bytes_del_multisig_2_de_3_contra_los_de_una_firma_comun(self):
        simple = 1312 + 2420
        self.assertEqual(int(self.o["sin_techo"][(1, 1)]["bytes_claves_y_firmas"]), simple)
        self.assertEqual(int(self.o["sin_techo"][(3, 2)]["bytes_claves_y_firmas"]), 3 * 1312 + 2 * 2420)


# ----------------------------------------------------------------------------------- #
# C · capacidad, con la formula de Genesis
# ----------------------------------------------------------------------------------- #
class TestCapacidad(unittest.TestCase):
    def test_transacciones_por_bloque(self):
        o = escenario_multisig()
        simple = g.capacidad_para(PAGINAS, 3_318_750)
        self.assertEqual(simple, 15)  # la cifra de Test 8 y Test 9 para ML-DSA-44 a 96 paginas
        dos_de_tres = g.capacidad_para(PAGINAS, int(o["sin_techo"][(3, 2)]["pasos"]))
        self.assertLessEqual(dos_de_tres, simple // 2)


def resumen() -> None:
    m = escenario_multisig()
    print()
    print(f"# techos del ruleset inicial: {TECHO:,} pasos, {PAGINAS} paginas")
    print("## B · multisig k-de-n on-chain (firmas ML-DSA-44 sueltas + BLAKE2s de las n claves)")
    print(f"{'forma':>8s} {'pasos':>11s} {'pag':>4s} {'bajo el techo':>16s} {'tx/bloque':>9s} {'bytes claves+firmas':>20s}")
    for (n, k), r in m["sin_techo"].items():
        bt = m["bajo_techo"][(n, k)]
        estado = "acepta" if bt["acepta"] == "1" else bt["veredicto"]
        print(f"{f'{k}-de-{n}':>8s} {int(r['pasos']):>11,d} {int(r['paginas']):>4d} {estado:>16s} "
              f"{g.capacidad_para(PAGINAS, int(r['pasos'])):>9d} {int(r['bytes_claves_y_firmas']):>20,d}")
    for v, r in m["negativos"].items():
        print(f"  control {v:16s}: acepta={r['acepta']} {r['veredicto']} pasos={int(r['pasos']):,}")

    o = escenario_go()
    if o is None:
        print(f"\n## A · saltado: {_porque_no_hay_go()}")
        return
    um, si = _pasos(o["maq"]["ok"]), _pasos(o["maq_simple"])
    print(f"\n## A · firma umbral 2-de-3 (prototipo de Mithril) en la maquina de §6.6")
    print(f"{'caso':30s} {'acepta':>7s} {'pasos min':>11s} {'mediana':>11s} {'max':>11s} {'pag':>4s}")
    print(f"{'umbral 2-de-3 (90 firmas)':30s} {_aceptadas(o['maq']['ok']):>3d}/{len(um):<3d} "
          f"{min(um):>11,d} {int(statistics.median(um)):>11,d} {max(um):>11,d} {o['maq']['ok'][0]['paginas']:>4s}")
    print(f"{'firma comun, 1 firmante (30)':30s} {_aceptadas(o['maq_simple']):>3d}/{len(si):<3d} "
          f"{min(si):>11,d} {int(statistics.median(si)):>11,d} {max(si):>11,d} {o['maq_simple'][0]['paginas']:>4s}")
    for v in ("bit-firma", "otro-mensaje", "otra-clave"):
        p = _pasos(o["maq"][v])
        print(f"{'umbral + ' + v:30s} {_aceptadas(o['maq'][v]):>3d}/{len(p):<3d} "
              f"{min(p):>11,d} {int(statistics.median(p)):>11,d} {max(p):>11,d}")
    i = o["insuficiente"]
    print(f"por debajo del umbral (t=2, n=3, {i['intentos']} intentos de cada forma): "
          f"una parte activa -> {i['una_parte_activa_firmas']} firmas y {i['una_parte_activa_panicos']} panics del prototipo; "
          f"dos firman y Combine recibe una respuesta -> {i['una_respuesta_firmas']} firmas")
    print("\n## lado de la wallet (esta maquina, en proceso, SIN red; Go)")
    print(f"{'t-de-n':>7s} {'intentos medio':>15s} {'max':>4s} {'ms medio':>9s} {'ms p95':>8s} {'bytes/parte/intento':>20s}")
    for (t, n), w in o["wallet"].items():
        ms = sorted(w["ms"])
        print(f"{f'{t}-de-{n}':>7s} {statistics.mean(w['intentos']):>15.2f} {max(w['intentos']):>4d} "
              f"{statistics.mean(w['ms']):>9.2f} {ms[int(len(ms) * 0.95)]:>8.2f} {w['bytes_parte']:>20,d}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # el resumen lleva acentos y §; en Windows redirigido seria cp1252
    if not _HOST.exists():
        sys.exit(f"falta {_HOST}: cd codigo/host && cargo build --release")
    ok = unittest.main(exit=False, verbosity=1).result.wasSuccessful()
    resumen()
    sys.exit(0 if ok else 1)
