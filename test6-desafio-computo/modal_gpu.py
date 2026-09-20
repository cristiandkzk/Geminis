#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test 6 sobre una GPU grande, en Modal (plan Starter: $30/mes de cómputo gratis).

    python -m modal run modal_gpu.py
    python -m modal run modal_gpu.py --modelos llama3.1:8b --intentos 30

Por cada modelo levanta un contenedor con una GPU, arranca Ollama adentro y corre
medicion.py contra localhost, para que la red no entre en la latencia. Los modelos se
bajan una sola vez a un volumen de Modal. La salida cruda queda en resultados-gpu/.

Lo que se fija para que la única variable sea el hardware y no el motor:
  - la misma versión de Ollama que en las medidas locales (OLLAMA_TAG)
  - contexto 4096, una petición a la vez, un solo modelo cargado
  - los mismos tags de modelo, o sea la misma cuantización de Ollama

Otra GPU: TEST6_GPU=H100 python -m modal run modal_gpu.py
"""

import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import date, datetime
from pathlib import Path

import modal

OLLAMA_TAG = "0.34.2"  # la versión con la que se corrieron las medidas locales
GPU = os.environ.get("TEST6_GPU", "A100-80GB")
MODELOS_POR_DEFECTO = "llama3.1:8b,mistral:7b,llama3.1:70b"  # de barato a caro
BASE = "http://127.0.0.1:11434"
AQUI = Path(__file__).resolve().parent

app = modal.App("test6-desafio-computo")
volumen = modal.Volume.from_name("test6-ollama-modelos", create_if_missing=True)

imagen = (
    modal.Image.from_registry(f"ollama/ollama:{OLLAMA_TAG}", add_python="3.12")
    .entrypoint([])
    .add_local_file(AQUI / "medicion.py", "/root/medicion.py")
)


@app.function(image=imagen, gpu=GPU, volumes={"/modelos": volumen}, timeout=2 * 3600)
def correr(modelo: str, intentos: int, warmup: int, timeout_s: float) -> str:
    entorno = {
        **os.environ,
        "OLLAMA_MODELS": "/modelos",
        "OLLAMA_HOST": "127.0.0.1:11434",
        "OLLAMA_KEEP_ALIVE": "1h",
        "OLLAMA_CONTEXT_LENGTH": "4096",
        "OLLAMA_NUM_PARALLEL": "1",
        "OLLAMA_MAX_LOADED_MODELS": "1",
        "PYTHONIOENCODING": "utf-8",
    }
    lineas: list[str] = []

    def decir(texto: str = "") -> None:
        print(texto, flush=True)
        lineas.append(texto)

    def sh(*cmd: str) -> tuple[int, str]:
        r = subprocess.run(cmd, env=entorno, capture_output=True, text=True)
        return r.returncode, (r.stdout + r.stderr).strip()

    log = open("/tmp/ollama.log", "w")
    servidor = subprocess.Popen(["ollama", "serve"], env=entorno, stdout=log, stderr=log)
    try:
        for _ in range(120):
            try:
                urllib.request.urlopen(f"{BASE}/api/version", timeout=2).read()
                break
            except OSError:
                time.sleep(1)
        else:
            raise RuntimeError("Ollama no arrancó en 2 minutos:\n" + open("/tmp/ollama.log").read())

        decir(f"# fecha:  {date.today().isoformat()}")
        decir(
            "# gpu:    "
            + sh("nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader")[1]
        )
        decir(f"# ollama: {sh('ollama', '--version')[1]}")
        decir(f"# modelo: {modelo}")
        decir()

        rc, salida = sh("ollama", "pull", modelo)
        if rc != 0:
            raise RuntimeError(f"ollama pull {modelo} falló:\n{salida}")
        volumen.commit()  # deja el modelo en el volumen para las próximas corridas

        # Carga el modelo antes de medir: la carga en frío de un 70B puede tardar minutos
        # y no es lo que se mide (el warmup de medicion.py descarta los primeros intentos).
        carga = urllib.request.Request(
            f"{BASE}/api/generate",
            data=json.dumps(
                {"model": modelo, "prompt": "hola", "stream": False, "options": {"num_predict": 1}}
            ).encode(),
            headers={"Content-Type": "application/json"},
        )
        t0 = time.perf_counter()
        urllib.request.urlopen(carga, timeout=1800).read()
        decir(f"# carga del modelo: {time.perf_counter() - t0:.1f}s (fuera de la medición)")
        decir()

        proceso = subprocess.Popen(
            [
                sys.executable, "-u", "/root/medicion.py",  # -u: cada intento sale en vivo
                "--endpoint", f"{BASE}/v1/chat/completions",
                "--model", modelo,
                "--intentos", str(intentos),
                "--warmup", str(warmup),
                "--timeout", str(timeout_s),
            ],
            env=entorno, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8",
        )
        for linea in proceso.stdout:
            decir(linea.rstrip("\n"))
        proceso.wait()

        estado = sh("ollama", "ps")[1]
        decir()
        decir(estado)
        if "100% GPU" not in estado:
            decir("!! ESTA FILA NO VALE: el modelo no está 100% en GPU (ver ollama ps).")
        if "4096" not in estado:
            decir("!! El contexto no es 4096: no es comparable con las medidas locales.")
    finally:
        servidor.terminate()
        try:
            servidor.wait(timeout=30)
        except subprocess.TimeoutExpired:
            servidor.kill()
        log.close()

    return "\n".join(lineas)


@app.local_entrypoint()
def main(
    modelos: str = MODELOS_POR_DEFECTO,
    intentos: int = 100,
    warmup: int = 3,
    timeout: float = 300.0,
):
    carpeta = AQUI / "resultados-gpu"
    carpeta.mkdir(exist_ok=True)
    for modelo in [m.strip() for m in modelos.split(",") if m.strip()]:
        texto = correr.remote(modelo, intentos, warmup, timeout)
        archivo = carpeta / f"{date.today().isoformat()}_{GPU}_{modelo.replace(':', '_')}.txt"
        if archivo.exists():  # nunca pisar una corrida ya guardada
            archivo = archivo.with_name(f"{archivo.stem}_{datetime.now():%H%M}.txt")
        archivo.write_text(texto + "\n", encoding="utf-8")
        print(f"\n>> guardado: {archivo}\n")
