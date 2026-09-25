# -*- coding: utf-8 -*-
"""El costo del asiento contra el botín (`CRITERIA.es.md`, Parte 2; §10.2 del paper).

    python costo.py              # las tablas y el veredicto de C1
    python costo.py verificar    # V5: el costo reproduce las cuentas ya hechas de la tasa inicial

`simulacion.py` dijo cuántos asientos necesita un atacante para tener una racha de ≥ W bloques.
Esto pone precio a esos asientos con la renta de permanencia de §8.5 y §8.6 y lo compara con el
botín. **Es un cálculo con supuestos declarados, no una medición**: ningún número de acá sale de
correr el sistema, y `r0` posterior a Geminis lo fija una subasta que hoy no existe.

**El botín no tiene unidad interna.** El protocolo no lee precios (I2, §7.6), así que `X` se
expresa como fracción del supply, que es lo único que la cadena puede contar.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import simulacion as sim  # noqa: E402
from estado import permanencia as perm  # noqa: E402
from protocolo import genesis as g  # noqa: E402

# --------------------------------------------------------------------------- #
# Los supuestos, con su origen
# --------------------------------------------------------------------------- #

#: Divisibilidad y supply: los de `parametros-mint/`. **Supuestos, no decisiones.**
DIVISIBILIDAD = 10**8
SUPPLY = 10**6  # tokens

#: `r0(0)`: §10.3, "mil veces el piso de representabilidad", en unidades mínimas por época y por entrada.
R0_UNIDADES_POR_EPOCA = 1_000
#: `F(0)`: `parametros-mint/RESULTS.es.md`, "15,8 h de guardado".
F_HORAS = 15.8

EPOCA_S = perm.EPOCA_BLOQUES * sim.TIEMPO_BLOQUE_S  # 86 400 s: un día
R0_TOKEN_POR_EPOCA = R0_UNIDADES_POR_EPOCA / DIVISIBILIDAD
F_TOKEN = R0_TOKEN_POR_EPOCA * (F_HORAS * 3_600) / EPOCA_S

#: Las cuentas ya hechas de la tasa inicial (notas de trabajo, fuera del repo), para V5.
D25_PUBLICADO = 0.000257
LLENAR_ESTADO_PUBLICADO = 9_110  # tokens, 35,5 M de objetos, 25 épocas

DIA_S = 86_400.0


def costo_de_un_asiento(dias: float) -> float:
    """Tokens quemados por tener un asiento `dias` días: el piso al crearlo más la renta."""
    return F_TOKEN + R0_TOKEN_POR_EPOCA * dias * DIA_S / EPOCA_S


def llenar_estado(epocas: int) -> float:
    """Tokens que cuesta ocupar **todo** el presupuesto de estado `epocas` épocas (§10.3: del orden del 1 % del supply)."""
    return perm.entradas_que_entran() * costo_de_un_asiento(epocas * EPOCA_S / DIA_S)


def monto_maximo_sin_quema() -> int:
    """La transferencia más grande, en unidades mínimas, que el fee no quema **nada**.

    `EstadoSintetico._transferir` calcula `quema = monto * ppm // 1_000_000`: con división entera,
    todo lo que quede por debajo de `1e6 / ppm` se transfiere gratis. La actividad que hace falta
    para ser un asiento no suma costo, y esto lo verifica en vez de suponerlo.
    """
    ppm = g.RULESET_INICIAL.interno("fee_quema_ppm")
    return (1_000_000 - 1) // ppm


def ataque_con(n_honestos: int, a: int, w: int) -> dict:
    """El atacante se suma con `a` asientos a `n_honestos` y espera la primera racha de ≥ `w`."""
    n = n_honestos + a
    riesgo = sim.riesgo_por_bloque(n, a, w)
    if riesgo <= 0.0:
        # Con muy pocos asientos la probabilidad se pierde en el flotante (`(a/n)^W` con W grande):
        # la espera es efectivamente infinita, no un error.
        return {"a": a, "n": n, "s": a / n, "espera_dias": math.inf, "costo": math.inf,
                "x_equilibrio": math.inf}
    espera_dias = (1 / riesgo) * sim.TIEMPO_BLOQUE_S / DIA_S
    costo = a * costo_de_un_asiento(espera_dias)
    return {"a": a, "n": n, "s": a / n, "espera_dias": espera_dias, "costo": costo,
            "x_equilibrio": costo / SUPPLY}


def ataque(n_honestos: int, s: float, w: int) -> dict:
    """El atacante se suma a `n_honestos` asientos hasta tener la fracción `s` del total."""
    return ataque_con(n_honestos, math.ceil(n_honestos * s / (1 - s)), w)


def capacidad_de_asientos() -> int:
    """Cuántas entradas caben en el objetivo de ocupación `θ*` (§10.1): el techo del total de asientos."""
    return perm.entradas_que_entran() * g.THETA_ESTRELLA_PPM // 1_000_000


def ataque_mas_barato(n_honestos: int, w: int) -> dict:
    """**El `s` que minimiza el costo esperado por ataque exitoso.** No estaba en CRITERIA.

    C1 fija `s = 1/3`, pero el atacante elige. Con asientos casi gratis le conviene tener **muchos**
    más: la espera esperada baja como `s^W` mientras que los asientos suben como `s/(1−s)`, y la
    renta se paga por espera. El barrido llega hasta el 99 % de los asientos o hasta la capacidad
    del estado, lo que ocurra primero.
    """
    a_max = min(capacidad_de_asientos() - n_honestos, 99 * n_honestos)
    mejor = None
    a = max(w, 1)
    while a <= a_max:
        r = ataque_con(n_honestos, a, w)
        if mejor is None or r["costo"] < mejor["costo"]:
            mejor = r
        a = max(a + 1, int(a * 1.05))
    return mejor


# --------------------------------------------------------------------------- #
# V5
# --------------------------------------------------------------------------- #


def verificar() -> int:
    fallos = 0

    d25 = costo_de_un_asiento(g.L_MAX_EPOCAS * EPOCA_S / DIA_S)
    ok_d25 = abs(d25 - D25_PUBLICADO) / D25_PUBLICADO < 0.01
    fallos += 0 if ok_d25 else 1
    print(f"{'✅' if ok_d25 else '❌'} V5a · D_25(0) = {d25:.6f} token por asiento (las cuentas previas dan {D25_PUBLICADO})")

    entradas = perm.entradas_que_entran()
    llenar = entradas * d25
    ok_llenar = abs(llenar - LLENAR_ESTADO_PUBLICADO) / LLENAR_ESTADO_PUBLICADO < 0.01
    fallos += 0 if ok_llenar else 1
    print(f"{'✅' if ok_llenar else '❌'} V5b · llenar el estado 25 épocas = {llenar:,.0f} tokens con "
          f"{entradas:,} entradas de {perm.ENTRADA_BYTES} B (las cuentas previas dan ~{LLENAR_ESTADO_PUBLICADO:,} con 35,5 M)")

    sin_quema = monto_maximo_sin_quema()
    gratis = g.RULESET_INICIAL.interno("fee_quema_ppm")
    ok_gratis = sin_quema * gratis // 1_000_000 == 0 and (sin_quema + 1) * gratis // 1_000_000 >= 1
    fallos += 0 if ok_gratis else 1
    print(f"{'✅' if ok_gratis else '❌'} extra · una transferencia de hasta {sin_quema} unidades mínimas "
          f"({sin_quema / DIVISIBILIDAD:.0e} token) no quema nada; con {sin_quema + 1} ya quema 1")

    print()
    print("todo en verde" if not fallos else f"{fallos} criterio(s) reprobado(s)")
    return 1 if fallos else 0


# --------------------------------------------------------------------------- #
# Las tablas
# --------------------------------------------------------------------------- #


def _duracion(dias: float) -> str:
    if dias < 2:
        return f"{dias * 24:.1f} h"
    if dias < 730:
        return f"{dias:.0f} días"
    return f"{dias / 365:.3g} años"


def _tokens(x: float) -> str:
    return f"{x:.3g}" if x < 1_000 else f"{x:,.0f}"


def tablas() -> None:
    print(f"r0(0) = {R0_TOKEN_POR_EPOCA:.0e} token por día y por asiento · F(0) = {F_TOKEN:.2e} token · "
          f"supply {SUPPLY:,} tokens · un asiento no paga fee de actividad "
          f"(hasta {monto_maximo_sin_quema()} unidades mínimas)\n")

    escenarios = (
        ("un cuarto, W = 12", 12, 0.25),
        ("un tercio, W = 12", 12, 1 / 3),
        ("la mitad, W = 12", 12, 0.5),
        ("65 %, W = 44", 44, 0.656),
        ("88 %, W = 130", 130, 0.879),
    )
    poblaciones = (100, 1_000, 10_000, 1_000_000)

    print("A · el costo esperado de un ataque exitoso, X*  (tokens; entre paréntesis, fracción del supply)")
    print(f"{'atacante':<20} | " + " | ".join(f"n_h = {n:>9,}" for n in poblaciones))
    for nombre, w, s in escenarios:
        celdas = []
        for n_h in poblaciones:
            r = ataque(n_h, s, w)
            celdas.append(f"{_tokens(r['costo'])} ({r['x_equilibrio']:.0e})")
        print(f"{nombre:<20} | " + " | ".join(f"{c:>16}" for c in celdas))

    print("\nB · el detalle del escenario de C1: un tercio, W = 12, n_h = 1 000")
    r = ataque(1_000, 1 / 3, 12)
    print(f"  asientos del atacante {r['a']:,} · espera esperada {_duracion(r['espera_dias'])} · "
          f"costo {r['costo']:.3g} token · X* = {r['x_equilibrio']:.1e} del supply")

    print("\nC · el retorno de un ataque en ese escenario, según el botín (fracción del supply)")
    for x in (1e-6, 1e-4, 1e-2):
        print(f"  botín {x:.0e} del supply ({x * SUPPLY:,.0f} tokens): rinde {x * SUPPLY / r['costo']:,.0f} veces lo que costó")

    print("\nD · cuánto cuesta tener la mitad de los asientos, según cuántos honestos haya (W = 12, un día)")
    for n_h in poblaciones:
        a = n_h
        dia = a * costo_de_un_asiento(1)
        print(f"  n_h = {n_h:>9,}: {a:>9,} asientos → {dia:.3g} token el primer día ({dia / SUPPLY:.1e} del supply)")

    cupo = g.PRESUPUESTO_ESTADO_BYTES * g.THETA_ESTRELLA_PPM // 1_000_000 // (g.L_MAX_EPOCAS * perm.ENTRADA_BYTES)
    print(f"\nE · el cupo de admisión por época (§8.6) es de ~{cupo:,} entradas: es el techo de cuántos asientos "
          f"nuevos puede sumar un atacante por época, y es más grande que cualquier población honesta que la "
          f"tabla D considera")

    print("\nF · C1")
    x = ataque(1_000, 1 / 3, 12)["x_equilibrio"]
    umbral = 1e-4
    print(f"  X* = {x:.1e} del supply contra la vara de {umbral:.0e}: "
          + ("APRUEBA" if x >= umbral else f"REPRUEBA (por un factor de ~{umbral / x:,.0f})"))

    print("\nG · EXTRA, no estaba en CRITERIA: el ataque MÁS BARATO (el atacante elige `s`), X* en tokens")
    print(f"  (techo de asientos: {capacidad_de_asientos():,}, la ocupación objetivo θ*)")
    print(f"{'ventana':<10} | " + " | ".join(f"n_h = {n:>9,}" for n in poblaciones))
    for w in (12, 44, 130):
        celdas = []
        for n_h in poblaciones:
            r = ataque_mas_barato(n_h, w)
            celdas.append(f"{_tokens(r['costo'])} @{r['s']:.0%}")
        print(f"{'W = ' + str(w):<10} | " + " | ".join(f"{c:>16}" for c in celdas))
    barato = ataque_mas_barato(1_000, 12)
    print(f"  con W = 12 y n_h = 1 000: {barato['a']:,} asientos ({barato['s']:.0%}), espera "
          f"{_duracion(barato['espera_dias'])}, costo {barato['costo']:.3g} token = {barato['x_equilibrio']:.1e} del supply "
          f"(C1 reprobaría por ~{umbral / barato['x_equilibrio']:,.0f}×)")

    print("\nH · ¿se arregla subiendo r0? el multiplicador que C1 pediría, y lo que le hace al resto")
    factor = umbral / x
    print(f"  C1 (un tercio, n_h = 1 000) pide r0 × {factor:,.0f}. Con eso llenar el estado 25 épocas costaría "
          f"{llenar_estado(25) * factor:,.0f} tokens = {llenar_estado(25) * factor / SUPPLY:.1f} veces el supply, "
          f"y un usuario con 1 000 entradas pagaría {1_000 * costo_de_un_asiento(25) * factor:,.0f} tokens por ciclo "
          f"(hoy {1_000 * costo_de_un_asiento(25):.2f})")


def main(argv: list[str]) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    if argv[1:] == ["verificar"]:
        return verificar()
    tablas()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
