"""El chequeo del núcleo compartido (§10.1): **reporta, no bloquea.**

La escalera de canarios de §6.6 gradúa la respuesta suponiendo que las primitivas ceden **de a una y en
orden**. Ese supuesto se rompe si la función que encadena el linaje (`H`, I4) y una primitiva de firma
en vigor comparten núcleo: una sola rotura se lleva las dos, y la migración tendría que correr sobre una
cadena cuya verificación de linaje ya no es confiable.

**Por qué reporta y no bloquea** (decisión del 21/9/2026). Con las firmas aditivas (I5: Ed25519 no se
retira) y una biblioteca estándar que solo garantiza tres familias de hash —SHA-2, Keccak y BLAKE—, las
sucesiones independientes de hash y de firma **no pueden evitar acoplarse en algún escalón**: Ed25519
usa SHA-2 y ML-DSA usa Keccak, así que la única familia libre para `H` es BLAKE. Bloquear el escalón
dejaría la cadena de hash sin sucesor. Se declara el acople como un límite, en el escalón donde aparece,
y no se lo esconde.

**La tabla `NUCLEO` es de este módulo y no de Genesis (I1):** decide un chequeo, no una regla que el nodo
aplique. Si algún día tiene que ser condición de Genesis, es otra decisión.
"""

from __future__ import annotations

from collections.abc import Iterable

#: Familia de cada primitiva, por cómo está construida por dentro. Cada entrada lleva de dónde sale.
NUCLEO = {
    "hash/blake2s": "blake2",
    # SHA-3 (`hashlib.sha3_256`): la permutación Keccak. No es el Keccak-256 de Ethereum (otro relleno).
    "hash/sha3-256": "keccak",
    # RFC 8032: Ed25519 hashea con SHA-512. Verificado en ed25519-dalek 2.2.0 (`verifying.rs`, `signing.rs`).
    "firma/ed25519": "sha2",
    # FIPS 204: ML-DSA usa SHAKE. Verificado: el guest de Test 2 depende de `shake` y `keccak`, y el 59%
    # de una verificación se va expandiendo la matriz con SHAKE128 (test2-interprete/RESULTS).
    "firma/ml-dsa-44": "keccak",
}


def firmas(formatos: Iterable[str]) -> set[str]:
    """Los formatos de firma de un conjunto de formatos."""
    return {f for f in formatos if f.startswith("firma/")}


def sin_nucleo_declarado(formatos: Iterable[str]) -> list[str]:
    """Los formatos de firma que no declaran su núcleo. **Falla cerrado**: una firma nueva sin núcleo
    declarado no puede colarse sin decidir esto."""
    return sorted(f for f in firmas(formatos) if f not in NUCLEO)


def acoples(hash_id: str, formatos: Iterable[str]) -> list[tuple[str, str]]:
    """Las firmas en vigor que comparten núcleo con el hash `hash_id`: `[(formato, núcleo), ...]`.

    Vacío es que no hay acople. **No levanta ni bloquea nada**: es un reporte. Un formato de firma sin
    núcleo declarado se ignora acá y lo caza `sin_nucleo_declarado`.
    """
    nucleo_del_hash = NUCLEO[hash_id]
    return sorted(
        (f, NUCLEO[f]) for f in firmas(formatos) if NUCLEO.get(f) == nucleo_del_hash
    )
