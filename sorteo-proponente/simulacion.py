# -*- coding: utf-8 -*-
"""El sorteo del proponente contra la ventana de finalidad (§10.2 del paper).

    python simulacion.py             # las tablas de RESULTS.es.md
    python simulacion.py verificar   # V1-V4 de CRITERIA.es.md

**Qué responde.** El proponente de cada bloque se sortea sin reposición por época entre los
asientos de un pool, y un nodo lento cede el turno. ¿Cuántos asientos puede tener un atacante
antes de poder enterrar una impugnación legítima más allá de la ventana?

**Cómo se mide.** El atacante conoce la permutación de la época y elige el momento: comete el
fraude al comienzo de su racha más larga, así que lo que importa no es la demora de una
impugnación cualquiera sino la existencia de una racha de **≥ W bloques seguidos** propuestos por
él. Con la permutación sin reposición, la cantidad esperada de esas rachas por época tiene forma
cerrada (`esperado`), y no hace falta simular para llegar a probabilidades de 1e-9.

Lo que la forma cerrada no puede decir por sí sola lo dicen V1-V4: que es exacta (V1), que el
proceso simulado con cesión coincide (V2), que la prueba tiene filo (V3) y que ignorar el borde
de la época casi no importa (V4).

Solo biblioteca estándar, como el resto del proyecto.
"""

from __future__ import annotations

import itertools
import math
import random
import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "geminis"))
from protocolo import genesis as g  # noqa: E402

#: La ventana base y el tiempo de bloque salen de Genesis, no de una copia: si se mueven, esta
#: medición se mueve con ellos.
VENTANA_BASE = g.VENTANA_FINALIDAD
TIEMPO_BLOQUE_S = g.RULESET_INICIAL.interno("tiempo_bloque_ms") / 1_000
BLOQUES_POR_ANIO = round(365 * 24 * 3_600 / TIEMPO_BLOQUE_S)
#: La cuota de riesgo de CRITERIA.es.md: 1 % en un año.
PRESUPUESTO_ANUAL = 0.01
UN_TERCIO = 1 / 3

SEMILLA = 20_260_925


# --------------------------------------------------------------------------- #
# La forma cerrada
# --------------------------------------------------------------------------- #


def _caida(x: int, w: int) -> int:
    """El factorial descendente `x·(x−1)·…·(x−w+1)`, exacto."""
    r = 1
    for j in range(w):
        r *= x - j
    return r


def esperado_exacto(n: int, a: int, w: int) -> Fraction:
    """Cantidad esperada de rachas máximas de ≥ `w` asientos del atacante en una permutación
    uniforme de `n` asientos con `a` del atacante. **En fracciones exactas** (V1).

    Se cuenta una vez cada racha, en su primer asiento: o es el asiento 1, o el anterior es
    honesto. Por linealidad de la esperanza no hace falta la distribución conjunta.
    """
    if w > a or w > n:
        return Fraction(0)
    h = n - a
    r = Fraction(_caida(a, w), _caida(n, w))  # la racha empieza en el asiento 1
    if n > w and h > 0:
        # empieza en i = 2..n−w+1: el i−1 es honesto y los `w` siguientes son del atacante
        r += (n - w) * Fraction(h, n) * Fraction(_caida(a, w), _caida(n - 1, w))
    return r


def _log_caida(x: int, w: int) -> float:
    return sum(math.log(x - j) for j in range(w))


def esperado(n: int, a: int, w: int) -> float:
    """Lo mismo que `esperado_exacto`, en flotante y sin desbordar para `n` grande."""
    if w > a or w > n:
        return 0.0
    h = n - a
    r = math.exp(_log_caida(a, w) - _log_caida(n, w))
    if n > w and h > 0:
        r += (n - w) * (h / n) * math.exp(_log_caida(a, w) - _log_caida(n - 1, w))
    return r


def _esperado_roto(n: int, a: int, w: int) -> Fraction:
    """**La fórmula rota a propósito para V3**: cuenta ventanas de `w` seguidos, no rachas
    máximas (le falta la condición *"el asiento anterior es honesto"*). Una racha de 13 cuenta
    como dos ventanas de 12."""
    if w > a or w > n:
        return Fraction(0)
    return (n - w + 1) * Fraction(_caida(a, w), _caida(n, w))


def con_cesion(n_honestos: int, a: int, w: int, q: float) -> tuple[float, float]:
    """`(rachas esperadas por época, bloques esperados por época)` cuando cada asiento honesto
    cede con probabilidad `q`.

    Quien produce entre los honestos es binomial `(n_honestos, 1−q)`. Dado cuántos producen, los
    asientos que producen son una permutación uniforme, así que la forma cerrada vale y se promedia.
    """
    if q == 0 or n_honestos == 0:
        n = n_honestos + a
        return esperado(n, a, w), float(n)
    p = 1.0 - q
    media = n_honestos * p
    desvio = math.sqrt(n_honestos * p * q)
    lo = max(0, int(media - 9 * desvio) - 1)
    hi = min(n_honestos, int(media + 9 * desvio) + 1)
    total = 0.0
    lgn = math.lgamma(n_honestos + 1)
    for m in range(lo, hi + 1):
        lp = (
            lgn
            - math.lgamma(m + 1)
            - math.lgamma(n_honestos - m + 1)
            + m * math.log(p)
            + (n_honestos - m) * math.log(q)
        )
        total += math.exp(lp) * esperado(a + m, a, w)
    return total, a + media


def riesgo_por_bloque(n: int, a: int, w: int, q: float = 0.0) -> float:
    eventos, bloques = con_cesion(n - a, a, w, q)
    return eventos / bloques


def riesgo_anual(n: int, a: int, w: int, q: float = 0.0) -> float:
    """Probabilidad de al menos una racha de ≥ `w` en un año de bloques."""
    return -math.expm1(-riesgo_por_bloque(n, a, w, q) * BLOQUES_POR_ANIO)


def asientos_tolerados(n: int, w: int, q: float = 0.0, presupuesto: float = PRESUPUESTO_ANUAL) -> int:
    """La mayor cantidad de asientos del atacante con `riesgo_anual ≤ presupuesto`.

    Es creciente en `a`, así que se busca por bisección.
    """
    lo, hi = 0, n  # invariante: `lo` cumple, `hi + 1` no
    if riesgo_anual(n, n, w, q) <= presupuesto:
        return n
    hi = n - 1
    while lo < hi:
        medio = (lo + hi + 1) // 2
        if riesgo_anual(n, medio, w, q) <= presupuesto:
            lo = medio
        else:
            hi = medio - 1
    return lo


def s_estrella(n: int, w: int, q: float = 0.0) -> float:
    return asientos_tolerados(n, w, q) / n


# --------------------------------------------------------------------------- #
# El proceso simulado (V2, V4)
# --------------------------------------------------------------------------- #


def _rachas(secuencia: list[bool], w: int) -> int:
    """Rachas máximas de ≥ `w` valores `True` seguidos."""
    cuenta = largo = 0
    for x in secuencia:
        if x:
            largo += 1
            if largo == w:
                cuenta += 1
        else:
            largo = 0
    return cuenta


def racha_maxima(secuencia: list[bool]) -> int:
    mejor = largo = 0
    for x in secuencia:
        largo = largo + 1 if x else 0
        mejor = max(mejor, largo)
    return mejor


def _epoca(rng: random.Random, n_honestos: int, a: int, q: float) -> list[bool]:
    """Una época: los honestos que no ceden y los del atacante, en orden uniforme."""
    m = sum(1 for _ in range(n_honestos) if rng.random() >= q)
    secuencia = [True] * a + [False] * m
    rng.shuffle(secuencia)
    return secuencia


def mc_por_epoca(n_honestos: int, a: int, w: int, q: float, epocas: int, rng: random.Random):
    """`(media, error estándar)` de las rachas por época, simulando el proceso."""
    cuentas = [_rachas(_epoca(rng, n_honestos, a, q), w) for _ in range(epocas)]
    media = sum(cuentas) / epocas
    var = sum((c - media) ** 2 for c in cuentas) / (epocas - 1)
    return media, math.sqrt(var / epocas)


def mc_flujo(n_honestos: int, a: int, w: int, epocas: int, rng: random.Random) -> float:
    """Riesgo por bloque en un flujo **continuo** de épocas: las rachas cruzan el borde."""
    flujo: list[bool] = []
    for _ in range(epocas):
        flujo.extend(_epoca(rng, n_honestos, a, 0.0))
    return _rachas(flujo, w) / len(flujo)


# --------------------------------------------------------------------------- #
# V1-V4
# --------------------------------------------------------------------------- #


def _enumerado(n: int, a: int, w: int) -> Fraction:
    total = 0
    for ubicacion in itertools.combinations(range(n), a):
        secuencia = [False] * n
        for i in ubicacion:
            secuencia[i] = True
        total += _rachas(secuencia, w)
    return Fraction(total, math.comb(n, a))


def v1(formula=esperado_exacto) -> list[tuple[int, int, int]]:
    """Los `(n, a, w)` donde `formula` difiere de la enumeración. Vacío es que coincide."""
    diferencias = []
    for n in range(1, 11):
        for a in range(0, n + 1):
            for w in range(1, n + 1):
                if formula(n, a, w) != _enumerado(n, a, w):
                    diferencias.append((n, a, w))
    return diferencias


def verificar() -> int:
    fallos = 0

    def informar(nombre: str, ok: bool, detalle: str) -> None:
        nonlocal fallos
        fallos += 0 if ok else 1
        print(f"{'✅' if ok else '❌'} {nombre} · {detalle}")

    # V1
    dif = v1()
    informar("V1 la forma cerrada es exacta", not dif,
             "coincide con la enumeración en todos los (n ≤ 10, a, W)" if not dif else f"difiere en {dif[:5]}")

    # V2
    rng = random.Random(SEMILLA)
    n_h, a, w, q = 20, 20, 7, 0.2
    cerrada, _ = con_cesion(n_h, a, w, q)
    media, se = mc_por_epoca(n_h, a, w, q, 100_000, rng)
    distancia = abs(media - cerrada) / se
    rango_ok = 0.05 <= cerrada <= 0.5
    informar("V2 el proceso simulado coincide con la forma cerrada, con cesión",
             rango_ok and distancia < 3,
             f"cerrada {cerrada:.4f}, simulada {media:.4f} ± {se:.4f} ({distancia:.1f} σ)"
             + ("" if rango_ok else " — los parámetros no caen en el rango 0,05–0,5 de CRITERIA"))

    # V3
    roto_cazado = bool(v1(_esperado_roto))
    informar("V3 la prueba tiene filo", roto_cazado,
             "V1 caza la fórmula que cuenta ventanas en vez de rachas" if roto_cazado
             else "V1 PASA con la fórmula rota: es un V1 vacío")

    # V4
    rng = random.Random(SEMILLA + 1)
    n, a, w = 60, 30, 6
    flujo = mc_flujo(n - a, a, w, 20_000, rng)
    cerrada = riesgo_por_bloque(n, a, w)
    razon = flujo / cerrada
    informar("V4 el borde de época importa poco", 0.75 <= razon <= 1.25,
             f"riesgo por bloque en flujo continuo {flujo:.5f} contra cerrada {cerrada:.5f} (razón {razon:.3f})")

    print()
    print("todo en verde" if not fallos else f"{fallos} criterio(s) reprobado(s)")

    # Extra, NO estaba en CRITERIA.es.md: el sorteo sin reposición tiene una cota determinística.
    # Cada época contiene todos los asientos honestos, así que una racha del atacante no puede
    # abarcar una época entera: cruza a lo sumo un borde y vale `cola + cabeza ≤ a + a = 2a`.
    rng = random.Random(SEMILLA + 2)
    peor = {}
    for n, a in ((30, 5), (30, 10), (60, 6)):
        flujo: list[bool] = []
        for _ in range(60_000):
            flujo.extend(_epoca(rng, n - a, a, 0.0))
        peor[(n, a)] = racha_maxima(flujo)
    cota_ok = all(m <= 2 * a for (n, a), m in peor.items())
    detalle = ", ".join(f"n={n} a={a}: máx {m} (cota {2 * a})" for (n, a), m in peor.items())
    print(f"{'✅' if cota_ok else '❌'} extra · ninguna racha supera 2a · {detalle}")
    return 1 if (fallos or not cota_ok) else 0


# --------------------------------------------------------------------------- #
# Las tablas
# --------------------------------------------------------------------------- #


def _duracion(bloques: float) -> str:
    segundos = bloques * TIEMPO_BLOQUE_S
    if segundos < 3_600:
        return f"{segundos / 60:.0f} min"
    if segundos < 86_400 * 2:
        return f"{segundos / 3_600:.1f} h"
    if segundos < 86_400 * 730:
        return f"{segundos / 86_400:.0f} días"
    return f"{segundos / (86_400 * 365):.3g} años"


def tablas() -> None:
    print(f"ventana base {VENTANA_BASE} bloques · bloque {TIEMPO_BLOQUE_S:g} s · "
          f"{BLOQUES_POR_ANIO:,} bloques por año · cuota {PRESUPUESTO_ANUAL:.0%} en un año\n")

    ns = (100, 1_000, 10_000)
    ws = (VENTANA_BASE, VENTANA_BASE + g.TOPE_DEMORA_LOCKIN[g.CRIPTOGRAFICA], 130)

    print("A · s* — la mayor fracción de asientos del atacante con riesgo anual ≤ 1 %  (q = 0)")
    print(f"{'n':>7} | " + " | ".join(f"W = {w:>3}" for w in ws))
    for n in ns:
        celdas = []
        for w in ws:
            if w > n:
                # La ventana es más larga que la época: la forma cerrada por época no aplica
                # (dar 100 % sería un artefacto). Vale la cota determinística de `verificar`.
                celdas.append("— (W > n)")
                continue
            a = asientos_tolerados(n, w)
            celdas.append(f"{a / n:6.1%} ({a})")
        print(f"{n:>7} | " + " | ".join(f"{c:>15}" for c in celdas))

    print("\nB · el efecto de ceder — s*, n = 1000, W = base")
    base = s_estrella(1_000, VENTANA_BASE, 0.0)
    for q in (0.0, 0.2, 0.5):
        s = s_estrella(1_000, VENTANA_BASE, q)
        print(f"  q = {q:>3}: s* = {s:6.1%}   ({(s - base) / base:+.0%} relativo)")

    print("\nC · M2 — el menor W con s* ≥ 1/3  (q = 0)")
    for n in ns:
        w = 1
        while s_estrella(n, w) < UN_TERCIO:
            w += 1
        print(f"  n = {n:>6}: W = {w}")

    print("\nD · cuánto tarda el primer evento a un tercio de los asientos y a la mitad  (n = 1000, q = 0)")
    for s in (0.25, 1 / 3, 0.5):
        a = round(s * 1_000)
        lam = riesgo_por_bloque(1_000, a, VENTANA_BASE)
        print(f"  s = {s:5.1%}: riesgo por bloque {lam:.2e} → primer evento en ~{_duracion(1 / lam)}")

    print("\nE · M1 — ¿aguanta como está? (s* con W = base ≥ 1/3 para todo n)")
    valores = [s_estrella(n, VENTANA_BASE) for n in ns]
    print("  " + ", ".join(f"n={n}: {v:.1%}" for n, v in zip(ns, valores)))
    print("  " + ("APRUEBA" if all(v >= UN_TERCIO for v in valores) else "REPRUEBA"))


def main(argv: list[str]) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    if argv[1:] == ["verificar"]:
        return verificar()
    tablas()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
