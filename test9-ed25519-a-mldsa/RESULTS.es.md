# Test 9 — ed25519 → ML-DSA-44 en la misma cadena, con las firmas verificadas de verdad

**Pregunta.** La sucesión de formatos y el linaje estaban probados en Python con firmas que eran
etiquetas; la máquina de §6.6 estaba probada en Rust con cada primitiva suelta. ¿Componen? Es decir:
una cadena que cruza la transición del canario, ¿reconoce en cada generación las firmas que le tocan y
las verifica en la máquina real, dentro del presupuesto de *ese* ruleset?

## Qué se hizo

Un `NodoPoD` real con `ReglaCanarioCriptografico` cruza de la generación 0 (`firma/ed25519`) a la 1
(`firma/ed25519` + `firma/ml-dsa-44`). En cada generación una firma:

1. se **admite por formato** con `decodificar` (I5): falla cerrado si el ruleset no conoce el formato,
   antes de gastar un paso;
2. se **verifica en la máquina** (`geminis/predicado/vm`, sin tocarla) con los dos techos que dicta ese
   ruleset (`techo_vigente`, `paginas_vigentes`), en dos guests que reciben clave, firma y mensaje **por
   memoria** (`codigo/guest-ed25519`, `codigo/guest-mldsa44`; mismos crates que Test 8 y Test 2);
3. se **contrasta** contra la verificación nativa: todo veredicto de la máquina tiene que ser el nativo.

## Resultado — 16 pruebas, todas verdes

| caso | acepta | pasos | páginas |
|---|:-:|---:|---:|
| gen 0 · ed25519 válida | ✔ | 3.284.755 | 5 |
| gen 0 · ed25519, mensaje que no se firmó | ✘ | 3.277.090 | 5 |
| gen 0 · ed25519, `R` alterada | ✘ | 424.518 | 4 |
| gen 0 · **ml-dsa-44** | rechazada **por formato**, la máquina no se invocó | — | — |
| gen 1 · la firma ed25519 nacida en gen 0 | ✔ | 3.284.755 | 5 |
| gen 1 · ed25519, mensaje que no se firmó | ✘ | 3.277.090 | 5 |
| gen 1 · **ml-dsa-44 válida** | ✔ | 3.318.608 | 28 |
| gen 1 · ml-dsa-44, mensaje que no se firmó | ✘ | 3.318.387 | 28 |
| gen 1 · ml-dsa-44, firma alterada | ✘ | 3.318.422 | 28 |
| gen 1 · bytes de ed25519 bajo el formato ml-dsa-44 | ✘ | 40 | 1 |
| gen 1 · bytes de ml-dsa-44 bajo el formato ed25519 | ✘ | 5 | 0 |

Además, sobre la cadena:

- `H0_GENESIS` = `6175777756bd3f8c` **antes y después** (fijado en la prueba). Era `dd2ce1fe33cbcad0`
  hasta el 21/9/2026, cuando `H` pasó de SHA-256 a BLAKE2s a propósito.
- Activó en la altura 23; 1 checkpoint que cuelga de `H0_GENESIS`; `verificar_linaje` da verdadero.
- La cadena de bloques cruza la transición sin cortarse y sigue produciendo bajo la generación 1.
- La transición es **aditiva**: ed25519 sigue aceptado en la generación 1. Lo firmado en la generación 0
  sigue valiendo.

## Lo que se ve en los números

- **Rechazar cuesta lo que aceptar.** Una firma mala (mensaje distinto o firma alterada) gasta ~3,3 M
  pasos, igual que una buena: mandar basura no sale más barato para el verificador. La excepción es
  la `R` alterada de Ed25519, que la curva descarta al decodificar (424 K pasos).
- **Un formato equivocado es casi gratis de rechazar:** 40 y 5 pasos, por el largo.
- Las dos primitivas entran bajo el techo inicial (7.000.000 pasos, 96 páginas); ML-DSA-44 toca 28
  páginas y Ed25519 5.

## Filo de la prueba

Cuatro roturas deliberadas desde afuera, sin tocar el archivo; las cuatro hicieron caer pruebas:
no chequear el formato (cae 1), una máquina que acepta todo (cae 4), un techo de 1 M pasos (cae 5) y
verificar contra el ruleset viejo en la generación 1 (cae **todo**: rompe el escenario entero, así que
es una captura gruesa).

## Límites

- **El enrutado firma → máquina es de la prueba, no del protocolo.** El estado sintético no tiene
  cuentas ni transacciones firmadas (Fase 3, sin construir), y nada en `geminis/` manda una firma a la
  máquina. Lo que se prueba es que las piezas componen.
- **El canario de `Geminis` sigue siendo un contador** (`("gastar_canario",)` sin verificar). La versión
  con firma verificada solo existe en `Colosseum App`. Esta prueba no depende de cuán difícil sea
  gastarlo, pero el disparo no es el endurecido.
- **Una implementación por primitiva** (crates de referencia, sin ajustar) y **solo x86-64**.
- Los guests de esta prueba son binarios distintos de los publicados: ed25519 da 3.284.755 pasos
  (Test 8: 3.284.845) y ML-DSA-44 da 3.318.608 (Test 2, guest publicado: 3.339.364).
- Fuera de alcance: retirar ed25519 (transición posterior, no existe) y qué pasa con fondos bajo
  claves ed25519 después de una ruptura.

## Reproducir

```
cd test9-ed25519-a-mldsa/codigo/guest-ed25519 && cargo build --release
cp target/riscv32im-unknown-none-elf/release/guest-ed25519-io guest.elf
cd ../guest-mldsa44 && cargo build --release
cp target/riscv32im-unknown-none-elf/release/guest-mldsa44-io guest.elf
cd ../host && cargo build --release
cd ../.. && python prueba.py
```

Corrida cruda: `resultados/2026-09-21_x86_blake2s.txt`.
