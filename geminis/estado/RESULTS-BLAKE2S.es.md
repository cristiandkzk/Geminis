# El hash de consenso pasa a BLAKE2s — qué cambia en el piso de §8.5

**Qué cambió.** El 21/9/2026 el hash de Genesis (`H`, I4) pasó de SHA-256 a BLAKE2s. La firma inicial
es Ed25519, que hashea con SHA-512 por dentro, y un `H` de la familia SHA-2 comparte núcleo con ella;
§10.1 lo prohíbe (linaje y firma no pueden caer juntos). BLAKE2 no es SHA-2 ni Keccak (la familia de
SHAKE, que usa ML-DSA-44, la firma sucesora).

**Qué se migró.** `huella()` (linaje, raíz de estado, hash de bloque), el árbol de estado, el árbol de
desalojo y el digest de predicados: todos hashean por `protocolo.serializacion.hasher`, el único punto
de entrada, y una prueba verifica que ningún otro módulo importa `hashlib`. **Excepción declarada:**
`liquidacion/doble_firma.py`, un Schnorr de juguete de 127 bits donde SHA-256 es parte interna *de esa
primitiva* y no el hash de consenso.

## La medición

Igual que `steps_per_verify` (Test 2) y que la de SHA-256: un BLAKE2s escrito a mano (RFC 7693),
compilado a RV32IM (`predicado/vm/guest-blake2s/`), corrido en la máquina de §6.6 restando dos tandas
(`cargo run --release --bin hash_blake2s`). **Antes de contar pasos se valida que calcule BLAKE2s de
verdad:** el digest de `"abc"` es el del Apéndice B de la RFC.

| | pasos por compresión | ciclo crear + desalojar (26 hashes) |
|---|---:|---:|
| SHA-256 (`guest-sha`, 21/8/2026) | 4.898 | 254.696 |
| **BLAKE2s (`guest-blake2s`, 21/9/2026)** | **2.529** | **131.508** |

BLAKE2s cuesta **0,52×**. El conteo es exacto y no depende de la arquitectura. Ambos guests son
escritos a mano por el mismo método, así que la razón entre ellos es comparable.

## Lo que se mueve

El modelo reproduce la tabla publicada con SHA-256 (fila por fila, antes de tocar nada) y da esto con
BLAKE2s:

| corte `d` | hashes por actualización | piso con SHA-256 | piso con BLAKE2s |
|---:|---:|---:|---:|
| 1 | 26 | 6,03 (24% de `L_max`) | 3,11 (12%) |
| 4 | 37 | 8,58 (34%) | 4,43 (18%) |
| **6** | **83** | **19,25 (77%)** | **9,94 (40%)** |
| 7 | 146 | 33,86 (135%) | 17,48 (70%) |
| 9 | 528 | 122,44 (490%) | 63,22 (253%) |

Devnet B4 (qué se lleva el desalojo del bloque, `d = 6`): **9,62% con SHA-256, 4,97% con BLAKE2s**.
Ver `devnet/RESULTS.es.md`, donde además figura que el 3,01% publicado ya estaba desactualizado.

### Qué conclusiones se mueven y cuáles no

- **El criterio original de la Fase 5 sigue sin cumplirse:** exigía el piso por debajo del 35% de
  `L_max`; con BLAKE2s es 40%. Se mueve la distancia, no el veredicto.
- **Vida corta:** quien compra una época paga el 91% al crear (95% con SHA-256). El criterio que exige
  más del 90% pasa por **0,909**, con margen fino.
- **El corte `d = 6` no se re-decidió.** A `d = 7` el piso ya no supera `L_max` (70%, antes 135%), o
  sea que la decisión abierta de elegir el corte de nuevo tiene más espacio. Es una decisión de
  Genesis, no un efecto colateral de cambiar el hash.
- **Que el piso baje no es un mérito del árbol:** es el costo de otro hash.

## Límites

- **El modelo cuenta una compresión por hash, y un nodo interno son dos.** El mensaje que hashea el
  árbol es la etiqueta de dominio (18 B) más dos hijos de 32 B: 82 bytes, dos bloques de 64 en SHA-256
  y en BLAKE2s. `PASOS_POR_HASH` es por compresión y la cuenta multiplica por hashes, no por
  compresiones. Es una simplificación **previa** a este cambio, no documentada, y **no altera el
  cociente 0,52**, pero sí el nivel absoluto: si se corrigiera, los pisos de arriba se duplicarían
  para los dos algoritmos. (BLAKE2s admite separar dominios con su parámetro de personalización, que
  es gratis y dejaría cada nodo en una compresión; es una opción de diseño, no se hizo.)
- **Una implementación por algoritmo**, escritas a mano y por el mismo método; solo x86-64 (el
  conteo es determinístico por diseño y Test 2 lo midió idéntico en ARM, no repetido acá).
- **Los documentos anteriores conservan sus números**, calculados con SHA-256, como registro de lo que
  se midió entonces: `estado/RESULTS.es.md`, `estado/RESULTS-TREE.es.md`, `presupuesto-nodo/`.
