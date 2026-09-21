# Sucesiones independientes de hash y de firma

**Qué se demuestra.** La cadena puede cambiar su función de hash y su primitiva de firma **de forma
independiente**, en cualquier orden, sin reiniciarse y sin mover su raíz:

```
hash:   BLAKE2s  →  SHA-3 (Keccak)  →  …
firma:  Ed25519  →  ML-DSA-44       →  …
```

Cada sucesión tiene su propio canario, su propia regla (`ReglaCanarioHash`, `ReglaCanarioCriptografico`) y su
propio formato. Se corre con `python herramientas/independencia.py`; lo fijan 31 pruebas
(`pruebas/test_sucesion_de_hash.py` y `pruebas/test_sucesion_independiente.py`).

## Resultado

Cadena real (`NodoPoD`), `H0_GENESIS` `6175777756bd3f8c`:

| orden | escalón | gen | hash vigente | firmas en vigor | acople de núcleo |
|---|---:|---:|---|---|---|
| hash primero | 0 | 0 | BLAKE2s | Ed25519 | — |
| | 1 | 1 | **SHA-3 (Keccak)** | Ed25519 | — |
| | 2 | 2 | SHA-3 (Keccak) | Ed25519 + **ML-DSA-44** | **H con ML-DSA-44 (Keccak)** |
| firma primero | 0 | 0 | BLAKE2s | Ed25519 | — |
| | 1 | 1 | BLAKE2s | Ed25519 + **ML-DSA-44** | — |
| | 2 | 2 | **SHA-3 (Keccak)** | Ed25519 + ML-DSA-44 | **H con ML-DSA-44 (Keccak)** |
| a la vez | 0 | 0 | BLAKE2s | Ed25519 | — |
| | 1 | 2 | **SHA-3 (Keccak)** | Ed25519 + **ML-DSA-44** | **H con ML-DSA-44 (Keccak)** |

En los tres órdenes: el linaje verifica de punta a punta (2 checkpoints), `H0_GENESIS` no se mueve, la cadena de
bloques cruza todo sin cortarse y el estado final es el mismo. **La historia no es la misma**: los checkpoints
difieren según el orden, y eso es lo que impide que la prueba sea vacua.

**Cada checkpoint se calcula con el hash de su ancestro, no con el que introduce.** Con el hash primero, el
checkpoint que introduce SHA-3 sale de BLAKE2s y el siguiente ya sale de SHA-3; con la firma primero, los dos
salen de BLAKE2s porque el ancestro todavía no usa SHA-3. Verificar A→B no exige confiar en la primitiva de B.

## Lo que NO es independiente: el acople se reporta, no se bloquea

La independencia es de **mecanismo**, no de **seguridad**. Ed25519 hashea con SHA-2 (SHA-512) y ML-DSA con
Keccak (SHAKE), así que apenas ocurren las dos transiciones `H` (SHA-3) comparte núcleo con la firma sucesora,
que es lo que §10.1 quiere evitar. El chequeo (`protocolo/nucleo.py`) **lo reporta en el escalón donde aparece
(columna de la derecha) y no lo bloquea**, por una razón estructural:

- las firmas son aditivas (I5: Ed25519 no se retira), así que tras el primer salto de firma están vigentes SHA-2
  y Keccak a la vez;
- la biblioteca estándar solo garantiza tres familias de hash (SHA-2, Keccak, BLAKE), y las firmas ya usan dos;
- bloquear dejaría la cadena de hash sin sucesor. Se declara el límite en lugar de esconderlo.

La generación 0 sí se hace cumplir con filo: `H` (BLAKE2s) no comparte núcleo con Ed25519, ni tras una sucesión
de firma sola (`pruebas/test_nucleo_compartido.py`).

## Límites, todos declarados

- **Los "…" son abiertos y no están construidos.** §6.6 dice que no hay lista de reemplazos: el sucesor lo entrega
  un pedido de trabajo como bytecode y lo acepta el guante. Acá cada cadena tiene dos escalones y son formatos que
  Génesis ya conoce.
- **ML-DSA-87 no es un escalón**: no está en el paper ni en Génesis. Es un nivel de costo medido en Test 2.
- **"SHA-3 (Keccak)" y no "Keccak-256":** es `hashlib.sha3_256`, la misma permutación que el Keccak-256 de Ethereum
  con otro relleno; no da los mismos digests.
- **El canario de firma de `Geminis` sigue siendo un contador** (`("gastar_canario",)`, sin verificar); el de hash
  exige trabajo (`CANARIO_HASH_BITS = 16`, valor de demostración sin calibrar). La versión verificada del de firma
  solo existe en `Colosseum App`.
- **El árbol de estado, el de desalojo y los predicados no siguen la sucesión del hash:** hashean siempre con el de
  Génesis, porque migrar un árbol Merkle a un hash nuevo es re-hashearlo entero y eso no está construido.
- El estado sintético no tiene cuentas ni valor: se conserva el estado del protocolo, no fondos bajo claves.
