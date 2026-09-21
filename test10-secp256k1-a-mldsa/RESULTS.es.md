# Test 10 — secp256k1 → ML-DSA-44: el cambio de firma que Ethereum haría con un fork, hecho por sucesión

**Pregunta.** Ethereum firma hoy las cuentas con ECDSA sobre secp256k1. Si tuviera que cambiar de firma, lo
haría con un fork o, para las cuentas, con account abstraction. ¿El mecanismo de sucesión expresa ese mismo
cambio, con las firmas verificadas de verdad?

**Qué NO se afirma.** Que Ethereum deba elegir ML-DSA-44. Según [ethereum.org](https://ethereum.org/roadmap/security/quantum-resistance/)
y [pq.ethereum.org](https://pq.ethereum.org/), el equipo evalúa Falcon, Dilithium (ML-DSA) y SPHINCS+ para las
cuentas (vía EIP-8141, en consideración para Hegotá) y leanXMSS, basada en hashes, para los validadores. ML-DSA-44
es la candidata que elige el paper de Geminis (§10.1: la primitiva PQ más escrutinada), no una decisión de Ethereum.

## Qué se hizo

Un Génesis alternativo, solo de esta prueba, con `firma/secp256k1` en la generación 0 (el de Geminis, con
`H0_GENESIS` `6175777756bd3f8c`, no se toca y se comprueba). Un `NodoPoD` real con `ReglaCanarioCriptografico` cruza a
la generación 1 (`firma/secp256k1` + `firma/ml-dsa-44`). En cada generación una firma:

1. se **admite por formato** con `decodificar` (I5), antes de gastar un paso;
2. se **verifica en la máquina** (`geminis/predicado/vm`, sin tocarla) con los dos techos de *ese* ruleset. El
   guest de secp256k1 (`k256` 0.13.4) verifica ECDSA sobre el **hash de 32 bytes** con clave SEC1 comprimida y
   **rechaza `s` alto** (EIP-2); el de ML-DSA-44 es el mismo binario de Test 9;
3. se **contrasta** contra la verificación nativa.

## Resultado — 21 pruebas, todas verdes

| caso | acepta | pasos | páginas |
|---|:-:|---:|---:|
| gen 0 · secp256k1 válida | ✔ | 5.673.513 | 5 |
| gen 0 · secp256k1, hash que no se firmó | ✘ | 5.673.513 | 5 |
| gen 0 · secp256k1, `s` alto (maleable, EIP-2) | ✘ | 254.962 | 2 |
| gen 0 · **ml-dsa-44** | rechazada **por formato**, la máquina no se invocó | — | — |
| gen 1 · la firma secp256k1 nacida en gen 0 | ✔ | 5.673.513 | 5 |
| gen 1 · secp256k1, `s` alto | ✘ | 254.962 | 2 |
| gen 1 · **ml-dsa-44 válida** | ✔ | 3.318.608 | 28 |
| gen 1 · ml-dsa-44, hash que no se firmó | ✘ | 3.318.387 | 28 |
| gen 1 · ml-dsa-44, firma alterada | ✘ | 3.318.422 | 28 |
| gen 1 · bytes de secp256k1 bajo el formato ml-dsa-44 | ✘ | 40 | 1 |
| gen 1 · bytes de ml-dsa-44 bajo el formato secp256k1 | ✘ | 33 | 1 |

Sobre la cadena: activó en la altura 23, 1 checkpoint que cuelga de la raíz del Génesis alternativo
(`adf7399e299686d8`), el linaje verifica, la cadena de bloques cruza sin cortarse, la transición es **aditiva**
(secp256k1 sigue aceptado) y lo firmado en la generación 0 sigue valiendo.

## Dos anclas externas

Para que no sea la implementación coincidiendo consigo misma:

- Con la **clave privada 1**, la dirección de Ethereum derivada de la clave pública es
  `0x7e5f4552091a69125d5dfcb7b8c2659029395bdf`, la conocida para esa clave.
- **`ecrecover` corrido en la máquina** recupera esa misma dirección desde la firma.

## Lo que muestran los números

| | pasos | páginas | tx/bloque a 96 pág. | bytes clave + firma |
|---|---:|---:|---:|---:|
| Ed25519 (Test 9) | 3.284.755 | 5 | 15 | 96 |
| ML-DSA-44 (Test 9) | 3.318.608 | 28 | 15 | 3.732 |
| **secp256k1, verificar** | **5.673.513** | 5 | **9** | 97 |
| **secp256k1, `ecrecover`** | **11.331.894** | 7 | **4** | — |

- **La firma de Ethereum es la más cara de las tres en pasos**: verificar secp256k1 cuesta 1,71× lo que ML-DSA-44.
  Migrar de secp256k1 a ML-DSA-44 devolvería capacidad en esta máquina (de 9 a 15 tx/bloque a 96 páginas), al
  revés de lo que se suele esperar de una primitiva post-cuántica. **Lo que sí crece es el tamaño**: ~38× en bytes
  por firma más clave.
- **`ecrecover` no cabe bajo el techo inicial** (11,3 M pasos contra 7 M): la máquina lo corta con `TechoExcedido`.
  Entraría bajando `tx_por_bloque`, que es el precio que §6.6 le pone a una primitiva cara. Verificar con la clave
  conocida sí cabe (5,67 M < 7 M).
- Rechazar una firma mala cuesta lo mismo que aceptar una buena (~5,67 M pasos); solo el `s` alto y los bytes de
  otro formato se descartan barato.

## Un hallazgo sobre el nodo

**El nodo hoy no soporta un Génesis distinto del de Geminis.** La invariante I4 se revisa en cada bloque contra
`g.H0_GENESIS` (es el `h0_raiz` por defecto de `i4_linaje`), así que un `NodoPoD` con otro Génesis falla en el primer
checkpoint. La prueba le pasa la raíz alternativa a I4 solo durante el escenario, sin apagar ninguna invariante.
Hacerlo bien es pasar la raíz del ruleset inicial; no se tocó el protocolo.

## Filo de la prueba

Siete roturas deliberadas desde afuera, sin tocar archivos; las siete hicieron caer pruebas: no chequear el formato
(cae 1), una máquina que acepta todo (5), un techo de 1 M pasos (6), una máquina que rechaza todo (4), la dirección
conocida que no coincide (1), `ecrecover` que recupera otra dirección (1) y verificar contra el ruleset viejo en la
generación 1 (cae **todo**: rompe el escenario entero, así que es una captura gruesa).

## Límites

- **Una implementación por primitiva.** `k256` y `ml-dsa` son crates de referencia de propósito general, sin
  ajustar. Una implementación de secp256k1 pensada solo para verificar (datos públicos) podría costar bastante
  menos: no se midió, y el 1,71× es de estos dos crates.
- **El enrutado firma → máquina es de la prueba, no del protocolo.** El estado sintético no tiene cuentas ni
  transacciones firmadas (Fase 3, sin construir). El Génesis alternativo se arma en la prueba, con
  `FORMATOS_CONOCIDOS` ampliado solo durante el escenario.
- **El canario de `Geminis` sigue siendo un contador** (`("gastar_canario",)`, sin verificar).
- **Verifica con la clave conocida**, no con `ecrecover`: eso último solo se mide y se ancla, no se enruta.
- **Solo x86-64.** El conteo de pasos es determinístico por diseño (Test 2 lo midió idéntico en ARM), no repetido acá.
- Fuera de alcance: retirar secp256k1 y qué pasa con los fondos bajo claves ECDSA tras una ruptura cuántica.

## Reproducir

```
cd test10-secp256k1-a-mldsa/codigo/guest-secp256k1 && cargo build --release
cp target/riscv32im-unknown-none-elf/release/guest-secp256k1-io guest.elf
cd ../host && cargo build --release          # usa el guest de ML-DSA-44 de test9-ed25519-a-mldsa/
cd ../.. && python prueba.py
```

Corrida cruda: `resultados/2026-09-21_x86.txt`.
