"""`python herramientas/independencia.py` — las sucesiones de hash y de firma, independientes.

    hash:   BLAKE2s  ->  SHA-3 (Keccak)  ->  ...
    firma:  Ed25519  ->  ML-DSA-44       ->  ...

Corre la cadena real (`NodoPoD`) por los tres órdenes posibles —hash primero, firma primero y las dos a la
vez— y muestra qué hay en vigor después de cada transición. Es la misma corrida que fijan
`pruebas/test_sucesion_independiente.py` y `sucesion/RESULTS-HASH-Y-FIRMA.es.md`.

Lo que se ve, y es lo que hay que mirar:

- cada sucesión avanza sin la otra, y todos los órdenes llegan al mismo estado final;
- el linaje verifica de punta a punta y `H0_GENESIS` no se mueve;
- **el acople de núcleo aparece en el escalón donde las dos ya ocurrieron, y no se bloquea**: es un
  límite declarado (`protocolo/nucleo.py`).

Los "..." son abiertos y no están construidos: §6.6 dice que no hay lista de reemplazos, el sucesor lo
entrega un pedido de trabajo como bytecode. ML-DSA-87 no es un escalón: no está en el paper.
"""

from __future__ import annotations

import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from protocolo.serializacion import corto  # noqa: E402
from pruebas.test_sucesion_independiente import ORDENES, recorrido  # noqa: E402

NOMBRES = {
    "hash/blake2s": "BLAKE2s",
    "hash/sha3-256": "SHA-3 (Keccak)",
}


def _firmas(formatos) -> str:
    return " + ".join(
        f.split("/")[1] for f in sorted(formatos) if f.startswith("firma/")
    )


def main() -> int:
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:  # pragma: no cover
            pass

    print("Sucesiones independientes de hash y de firma (cadena real, H0_GENESIS "
          f"{corto(recorrido(ORDENES[0])['h0_despues'])})")
    for orden in ORDENES:
        r = recorrido(orden)
        print(f"\n== {orden}")
        print(f"   {'escalon':7s} {'gen':>3s}  {'hash vigente':16s} {'firmas en vigor':22s} acople de nucleo")
        for i, e in enumerate(r["escalones"]):
            acople = ", ".join(f"H con {f.split('/')[1]} ({n})" for f, n in e["acoples"]) or "-"
            print(
                f"   {i:<7d} {e['generacion']:>3d}  {NOMBRES[e['hash_id']]:16s} "
                f"{_firmas(e['formatos']):22s} {acople}"
            )
        estado = "verifica" if r["linaje_verifica"] else "NO VERIFICA"
        igual = "no se movio" if r["h0_antes"] == r["h0_despues"] else "SE MOVIO"
        print(
            f"   linaje {estado} ({len(r['checkpoints'])} checkpoints) - H0_GENESIS {igual} - "
            f"cadena {'intacta' if r['cadena_intacta'] else 'CORTADA'} hasta la altura {r['altura']}"
        )
    print("\nEl acople se REPORTA en el escalon donde aparece y no se bloquea (protocolo/nucleo.py).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
