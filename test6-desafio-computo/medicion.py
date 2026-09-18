#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cuánto tarda un nodo de cómputo en producir un intento válido del desafío de §6.7,
y qué tan sensible es esa latencia al dominio del filtro estructural.

    python medicion.py --endpoint http://localhost:11434/v1/chat/completions \
                        --model <modelo> --intentos 30

Existe para derivar X, el piso de la ventana de ronda T de §6.7.1 (problema
abierto en §10.3). No corre en teléfono a propósito: el desafío lo compiten nodos
de cómputo (GPU y RAM, §6.1), no nodos PoD — medir sobre la clase de hardware
equivocada mide la pregunta equivocada. Ver README.es.md.

El filtro estructural de este script es un placeholder de referencia (JSON válido
+ nonce repetido + longitud mínima + proporción de palabras alfabéticas + sin
repetición degenerada) — la versión de producción usa un diccionario on-chain
(§6.7) y no es la que corre acá. Alcanza para no confundir la latencia de generar
ruido con la de generar una respuesta de verdad.

Sin dependencias externas: sólo la librería estándar, vía urllib, para no atarse a
qué cliente HTTP tenga instalado cada máquina.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import secrets
import statistics
import time
import urllib.request
from dataclasses import dataclass

TIEMPO_DE_BLOQUE_S = 6.0  # fijado en §10.3

# ------------------------------------------------------------- A: los dominios


@dataclass
class Dominio:
    nombre: str
    idioma: str
    tema: str
    min_palabras: int
    piso_alfabeticas: float = 0.85


DOMINIOS = [
    Dominio("es-cocina", "español", "una receta de cocina", 40),
    Dominio("en-historia", "inglés", "a historical event", 40),
    Dominio("pt-tecnologia", "portugués", "una novedad tecnológica", 40),
    Dominio("es-producto", "español", "la descripción de un producto", 60),
]

# --------------------------------------------------------- B: filtro estructural

PATRON_PALABRA = re.compile(r"[^\W\d_]+", re.UNICODE)


def tasa_alfabetica(texto: str) -> float:
    tokens = texto.split()
    if not tokens:
        return 0.0
    alfabeticos = sum(
        1 for t in tokens if PATRON_PALABRA.fullmatch(t.strip(".,;:!?\"'()"))
    )
    return alfabeticos / len(tokens)


def es_degenerado(texto: str) -> bool:
    palabras = [p.lower() for p in texto.split() if p]
    if len(palabras) < 6:
        return True
    mas_comun = max(set(palabras), key=palabras.count)
    return palabras.count(mas_comun) / len(palabras) > 0.4


def filtro_estructural(salida_cruda: str, nonce: str, dominio: Dominio) -> tuple[bool, str]:
    """Verdadero si pasa; si no, el motivo, para poder diagnosticar sin adivinar."""
    try:
        obj = json.loads(salida_cruda)
    except json.JSONDecodeError:
        return False, "no es JSON válido"

    if not isinstance(obj, dict) or "nonce" not in obj or "continuacion" not in obj:
        return False, "faltan campos"

    if obj["nonce"] != nonce:
        return False, "nonce no coincide"

    continuacion = obj["continuacion"]
    if not isinstance(continuacion, str):
        return False, "continuacion no es texto"

    if len(continuacion.split()) < dominio.min_palabras:
        return False, "por debajo del mínimo de palabras"

    if tasa_alfabetica(continuacion) < dominio.piso_alfabeticas:
        return False, "por debajo del piso de palabras alfabéticas"

    if es_degenerado(continuacion):
        return False, "repetición degenerada"

    return True, "ok"


# ------------------------------------------------------------------- C: el prompt


def armar_prompt(dominio: Dominio, nonce: str) -> str:
    ejemplo = json.dumps(
        {
            "nonce": nonce,
            "continuacion": (
                f"<al menos {dominio.min_palabras} palabras en {dominio.idioma}, "
                f"sobre {dominio.tema}>"
            ),
        },
        ensure_ascii=False,
    )
    return (
        f"Dominio: {dominio.idioma}. Tema: {dominio.tema}.\n"
        f"Devolvé ÚNICAMENTE un objeto JSON con esta forma exacta, sin texto extra "
        f"antes ni después:\n{ejemplo}\n\nnonce: {nonce}"
    )


# --------------------------------------------------------------- D: la llamada HTTP


def llamar_modelo(
    endpoint: str, modelo: str, prompt: str, api_key: str | None, timeout_s: float
) -> tuple[str, float]:
    cuerpo = json.dumps(
        {
            "model": modelo,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
        }
    ).encode("utf-8")

    encabezados = {"Content-Type": "application/json"}
    if api_key:
        encabezados["Authorization"] = f"Bearer {api_key}"

    peticion = urllib.request.Request(endpoint, data=cuerpo, headers=encabezados, method="POST")

    inicio = time.perf_counter()
    with urllib.request.urlopen(peticion, timeout=timeout_s) as resp:
        crudo = resp.read().decode("utf-8")
    latencia_s = time.perf_counter() - inicio

    respuesta = json.loads(crudo)
    contenido = respuesta["choices"][0]["message"]["content"]
    return contenido, latencia_s


# ------------------------------------------------------------------ E: la corrida


@dataclass
class Resultado:
    dominio: str
    latencia_s: float
    paso: bool
    motivo: str


def correr(
    endpoint: str,
    modelo: str,
    intentos: int,
    warmup: int,
    api_key: str | None,
    timeout_s: float,
) -> list[Resultado]:
    resultados: list[Resultado] = []
    total = intentos + warmup

    for i in range(total):
        dominio = DOMINIOS[i % len(DOMINIOS)]
        nonce = secrets.token_hex(8)
        prompt = armar_prompt(dominio, nonce)

        try:
            contenido, latencia_s = llamar_modelo(endpoint, modelo, prompt, api_key, timeout_s)
        except (OSError, KeyError, ValueError) as e:
            print(f"  [{i + 1}/{total}] {dominio.nombre}: fallo de transporte — {e}")
            continue

        if i < warmup:
            print(f"  [{i + 1}/{total}] {dominio.nombre}: {latencia_s:.2f}s (warmup, descartado)")
            continue

        paso, motivo = filtro_estructural(contenido, nonce, dominio)
        resultados.append(Resultado(dominio.nombre, latencia_s, paso, motivo))
        marca = "OK" if paso else f"RECHAZADO ({motivo})"
        print(f"  [{i + 1}/{total}] {dominio.nombre}: {latencia_s:.2f}s — {marca}")

    return resultados


# --------------------------------------------------------------------- F: el reporte


def percentil(datos: list[float], p: float) -> float:
    datos = sorted(datos)
    if not datos:
        return float("nan")
    k = (len(datos) - 1) * p
    f, c = math.floor(k), math.ceil(k)
    if f == c:
        return datos[int(k)]
    return datos[f] + (datos[c] - datos[f]) * (k - f)


def reportar(resultados: list[Resultado], tiempo_de_bloque_s: float) -> None:
    print()
    print("=" * 78)
    print("Resultado")
    print("=" * 78)

    if not resultados:
        print("Ningún intento completó — revisar endpoint/modelo antes de mirar números.")
        return

    validos = [r for r in resultados if r.paso]
    tasa = len(validos) / len(resultados)
    print(
        f"\nTasa de intentos que pasan el filtro estructural: {tasa:.0%} "
        f"({len(validos)}/{len(resultados)})"
    )

    if not validos:
        print("Ninguno pasó el filtro — no hay latencia que reportar todavía.")
        return

    latencias = [r.latencia_s for r in validos]
    p50 = percentil(latencias, 0.50)
    p90 = percentil(latencias, 0.90)
    p99 = percentil(latencias, 0.99)
    peor = max(latencias)

    print("\nLatencia de intentos válidos (segundos):")
    print(f"  p50 = {p50:.2f}   p90 = {p90:.2f}   p99 = {p99:.2f}   peor caso = {peor:.2f}")

    print("\nPor dominio:")
    por_dominio: dict[str, list[float]] = {}
    for r in validos:
        por_dominio.setdefault(r.dominio, []).append(r.latencia_s)
    for nombre, lats in por_dominio.items():
        print(f"  {nombre:<20} p50 = {statistics.median(lats):.2f}s  (n={len(lats)})")

    x_bloques = math.ceil(peor / tiempo_de_bloque_s)
    print(
        f"\nCon tiempo_de_bloque = {tiempo_de_bloque_s:.0f}s, el peor caso medido "
        f"da X ≈ {x_bloques} bloques."
    )
    print("Si los intentos son secuenciales (no en paralelo), el tiempo esperado hasta")
    print("el primero válido es aproximadamente p50 / tasa_de_éxito, no p50 solo.")
    print("Esto es un solo modelo en una sola corrida — no alcanza para fijar X (ver README.es.md).")


# -------------------------------------------------------------------------- main


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.strip().split("\n\n")[0])
    parser.add_argument(
        "--endpoint", required=True, help="URL compatible con OpenAI /v1/chat/completions"
    )
    parser.add_argument("--model", required=True, help="nombre del modelo en el servidor")
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--intentos", type=int, default=20)
    parser.add_argument(
        "--warmup",
        type=int,
        default=3,
        help="intentos iniciales descartados (carga en frío del modelo)",
    )
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--tiempo-de-bloque", type=float, default=TIEMPO_DE_BLOQUE_S)
    args = parser.parse_args()

    print(
        f"Corriendo {args.intentos} intentos (+{args.warmup} de warmup) contra "
        f"{args.model} en {args.endpoint}\n"
    )

    resultados = correr(
        args.endpoint, args.model, args.intentos, args.warmup, args.api_key, args.timeout
    )
    reportar(resultados, args.tiempo_de_bloque)


if __name__ == "__main__":
    main()
