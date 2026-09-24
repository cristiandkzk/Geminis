# Test 7 · El presupuesto de una firma compuesta

[English](RESULTS.md) · **Español**

> Estado: **parcial. Escritorio (x86-64) y teléfono (ARM64) corridos en los tres
> motores, veredicto preliminar.** Falta la Parte A (umbral de velocidad sobre
> valor dormiente) y el costo de tamaño — ver README.es.md, "Lo que falta". Esto es
> una señal de orden de magnitud, no un resultado citable como cerrado.

## 1. Qué se midió

`decode+verify` de ML-DSA-44 (la primitiva ya elegida, Test 2) y SLH-DSA-128s
(candidata a segunda familia para una firma compuesta — hash-based, sin
núcleo compartido con el reticulado de ML-DSA, condición de §10.1), en el
mismo módulo wasm, bajo tres motores: nativo, `wasmi` (intérprete puro — el
perfil "VM de cadena") y `wasmtime`/Cranelift (JIT — el motor que de hecho
entró en el presupuesto de Test 2). Metodología idéntica a Test 2: función
`measure` que escala iteraciones hasta 1,2 s de corrida y toma la mediana de
5 repeticiones.

Máquina: escritorio x86-64 (Windows), sin vectorización explícita (mismo
criterio que Test 2: "la columna native es Rust portable, no AVX2" — la
penalidad real contra el mejor nativo posible es mayor que la de esta tabla).

## 2. Resultados

**`decode+verify`** (µs por firma · firmas/s · penalidad vs. nativo)

| | native | cranelift (JIT) | wasmi (int.) |
|---|---|---|---|
| **ML-DSA-44** | 124,0 µs · 8 065/s | 471,3 µs · 2 122/s · **3,8×** | 3,51 ms · 285/s · **28,3×** |
| **SLH-DSA-128s** | 1 265,4 µs · 790/s · **10,2× ML-DSA-44** | 1 158,1 µs · 863/s · **2,5× ML-DSA-44 · 0,9× su propio nativo** | 10,18 ms · 98/s · **2,9× ML-DSA-44 · 8,0× su propio nativo** |

Firma: ML-DSA-44 = 2 420 B; SLH-DSA-128s = 7 856 B (3,2× más pesada).

*Corregido el 24/9/2026, después de cerrarlo:* la celda de SLH-DSA-128s bajo Cranelift decía **9,3×**, y
ese número comparaba SLH-DSA bajo Cranelift (1 158,1 µs) contra ML-DSA-44 **nativo** (124,0 µs), o sea
dos motores distintos. En el mismo motor, 1 158,1 / 471,3 = **2,5×**. Corregido también en la sección 3.

*Varianza:* tres corridas completas. `wasmi` y `cranelift` se mantuvieron
dentro del ~3% entre corridas para las dos primitivas — las cifras de la
tabla son representativas. `native` fue más ruidoso, sobre todo ML-DSA-44
(124–160 µs entre corridas, ~25%): es una medición de una sola pasada sin el
escalado de `measure`, y a esa escala de tiempo (decenas de microsegundos) el
scheduler de Windows y el ruido de caché pesan más. No cambia ninguna
conclusión de este test, que se apoyan en `wasmi`/`cranelift`, no en `native`.

**Costo de instalar el bytecode** (una vez, no por verificación): wasmi
0,8–1,2 ms; cranelift ~146 ms para un módulo de 142 KB (el módulo de este test
lleva las dos primitivas, más pesado que el de Test 2). Es ruido frente al
costo de verificar; no entra en el presupuesto por transacción.

## 3. El hallazgo que importa

**El orden entre motores se invierte entre primitivas.** ML-DSA-44 sufre una
penalidad de intérprete mucho mayor que de JIT (28,3× contra 3,8×) — es el
mismo patrón que ya midió Test 2. SLH-DSA-128s casi no paga penalidad de JIT
(0,9×, prácticamente empatado con su propio nativo) y paga una penalidad de
intérprete bastante menor que ML-DSA (8,0× contra 28,3×). Es consistente con
que SLH-DSA es una cascada de compresiones SHA-2 — un patrón de cómputo que
un JIT optimiza casi tan bien como el compilador nativo, y que un intérprete
castiga menos que la aritmética modular con acceso disperso a memoria de un
reticulado.

**Consecuencia práctica:** medido en nativo, SLH-DSA-128s parece ~10× más caro
que ML-DSA-44. Bajo Cranelift —el motor que de hecho decide el presupuesto,
porque fue el que se usó en el teléfono para la cifra de Test 2— la brecha
baja a **2,5×**, y el costo compuesto (las dos firmas verificadas juntas) da
**471 + 1 158 ≈ 1 630 µs**. Es **~3,5×** una verificación ML-DSA-44 sola en este
mismo módulo y motor (471 µs) — no ~10× ni ~30×, que es lo que una extrapolación
ingenua desde el número nativo habría sugerido. *(Contra los 391 µs de Test 2 daría
~4,2×, pero ese número salió de otro módulo, ~20% más rápido para ML-DSA-44; ver
sección 5. Corregido el 24/9/2026: esta sección usaba el 4,2× como si fuera la razón
de este módulo.)*

A ~1 630 µs por verificación compuesta, un cuarto de núcleo sostiene del orden de
~150 tx/s (0,25 / 1 630 µs) — muy por encima de lo que exige el caso de uso, que es
**solo** las transacciones que superen el umbral de velocidad sobre valor dormiente
(propuesto, todavía no existe ni en el paper ni en el código: es la Parte A), no el
tráfico general de la cadena.

## 4. Lo que este número NO dice todavía

- **El teléfono se corrió (sección 5), pero es un solo aparato** (Motorola Edge 40
  Neo, MT6879). El compuesto salió 3,9× bajo Cranelift, cerca del ~3,5× del
  escritorio (mismo módulo); pero el intérprete cuesta ~2× más que en x86, y un solo SoC no dice
  si eso se sostiene en otros teléfonos de gama media.
- **No incluye el costo de tamaño.** 7 856 B adicionales por transacción
  afectada es un costo de tamaño de bloque y de presupuesto de estado
  (§10.1) que este test no cuantifica — solo mide tiempo de verificación.
- **No dice si el mecanismo completo vale la pena.** Eso depende enteramente
  de la Parte A —qué techo de velocidad sobre valor dormiente no roza
  actividad legítima—, que sigue sin medir.

## 5. En el teléfono real (ARM64)

Motorola Edge 40 Neo (MediaTek MT6879), Termux, aarch64. Tres corridas completas el
2026-09-20, cada una un proceso nuevo, sin cargador enchufado y sin pausas (la
receta de Test 2, §6.1). Los binarios se cruzaron desde la PC con
`--target aarch64-linux-android`, porque Cranelift no compila dentro de Termux
(ver README.es.md, "En el teléfono"). Salidas crudas en `resultados-telefono/`.

**`decode+verify`**, mediana de las tres corridas (µs por firma · firmas/s ·
penalidad vs. su propio nativo)

| | native | cranelift (JIT) | wasmi (int.) |
|---|---|---|---|
| **ML-DSA-44** | 113,4 µs · 8 818/s | 469,8 µs · 2 129/s · **4,1×** | 7,35 ms · 136/s · **64,8×** |
| **SLH-DSA-128s** | 1 004,0 µs · 996/s | 1 363,3 µs · 734/s · **1,4×** | 20,21 ms · 49/s · **20,1×** |

**SLH-DSA-128s contra ML-DSA-44 en el mismo motor:** native 8,9× · cranelift
**2,9×** · wasmi 2,8×.

**Costo compuesto** (las dos firmas verificadas juntas):

| motor | ML-DSA-44 + SLH-DSA-128s | vs. ML-DSA-44 sola (mismo motor) | por núcleo · por cuarto de núcleo |
|---|---|---|---|
| cranelift | 469,8 + 1 363,3 = **1 833 µs** | **3,9×** | ~545/s · ~136/s |
| wasmi | 7,35 + 20,21 = **27,6 ms** | 3,75× | ~36/s · ~9/s |

**Contra el escritorio** (teléfono / PC, mediana de tres corridas cada uno)

| | native | cranelift | wasmi |
|---|---|---|---|
| ML-DSA-44 | 0,91× | 1,00× | 2,09× |
| SLH-DSA-128s | 0,79× | 1,18× | 1,99× |

*Varianza y validez.* Entre corridas (máximo menos mínimo, sobre la mediana):
cranelift 0,1 % en ML-DSA-44 y 0,02 % en SLH-DSA-128s; wasmi 0,7 % y 1,8 %; native
8 % y 5 % (el más ruidoso, por la misma razón que en el escritorio). El
`compile_ms` de cranelift dio 184,0–186,7 ms en las seis medidas; una corrida
contaminada por migración al cluster chico daría ~4× (Test 2, §6), y no hay
rastro. Contra Test 2: el módulo de este test da ML-DSA-44/cranelift ~20 % más
lento que el de Test 2 *en las dos máquinas* (PC: 471,3 vs. 392,5 µs; teléfono:
469,8 vs. 390,6 µs), con cociente teléfono/PC de 1,00 en ambos. Es una diferencia
del módulo y no del teléfono; la causa no se investigó. Por eso el compuesto se
compara contra ML-DSA-44 dentro de este mismo módulo (3,9×) y no contra los
391 µs de Test 2 (que daría 4,7×).

**Lo que se ve:**

- **El intérprete cuesta ~2× más en ARM** (2,09× en ML-DSA-44, 1,99× en
  SLH-DSA-128s), el mismo patrón que Test 2 (5,96 vs. 3,11 ms en ML-DSA-44, 1,9×).
  Contra el nativo, eso lleva la penalidad de wasmi en ML-DSA-44 de 28,3× a
  64,8×. El JIT, en cambio, rinde igual en las dos arquitecturas para ML-DSA-44.
- **SLH-DSA-128s ya no empata con su nativo bajo JIT:** 0,9× en el escritorio,
  1,4× en el teléfono. Quien se mueve es el nativo (0,79× del de la PC), no el JIT
  (1,18×). Una causa posible, sin verificar: el nativo de ARM usa instrucciones
  SHA-2 por hardware y el guest wasm no puede; el i5-9400 no tiene SHA-NI, así que
  en x86 esa ventaja no existía.
- **El orden de magnitud del escritorio se sostiene bajo Cranelift** (compuesto
  3,9×, ~136 tx/s por cuarto de núcleo, contra ~3,5× y ~150 tx/s). **Lo que cambia
  es el intérprete:** ~27,6 ms por verificación compuesta, ~9 tx/s por cuarto de
  núcleo, unas 15× menos que Cranelift. Cuál de los dos números vale para el
  presupuesto depende de qué motor use la VM real, y eso este test no lo decide.

## 6. Reproducibilidad

Código en `codigo/`. Dos crates: `guest/` (compila a `wasm32-unknown-unknown`,
expone `run_ml_dsa44` y `run_slh_dsa128s`) y `host/` (mide con `wasmi` y
`wasmtime`, más el binario `nativo` para la fila de referencia). Instrucciones
completas en `README.es.md`, incluida la ruta para el teléfono (binarios cruzados
desde la PC). Sin dependencias fuera de `crates.io`; las mismas
crates de RustCrypto que ya usa `pqcore` de Test 2, más `slh-dsa` 0.1.0.

*Nota de método:* `slh-dsa` 0.1.0 exige pinear `signature = "=2.3.0-pre.4"` a
mano — la resolución por defecto (`2.3.0-pre.7`) rompe la compilación del
crate por un cambio de API entre dos pre-releases de la misma versión mayor.
Es una fragilidad real de depender de un crate pre-1.0 en un pre-release
ajeno; documentado en el `README.es.md` para que no se pierda si `slh-dsa` sube de
versión.
