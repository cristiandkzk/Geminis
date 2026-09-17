# Test 7 · El presupuesto de una firma compuesta

> Estado: **parcial. Escritorio (x86-64) corrido en los tres motores, veredicto
> preliminar.** Falta el teléfono (ARM64) y falta la Parte A (umbral de
> velocidad sobre valor dormiente) — ver LEEME.md, "Lo que falta". Esto es una
> señal de orden de magnitud, no un resultado citable como cerrado.

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
| **SLH-DSA-128s** | 1 265,4 µs · 790/s · **10,2× ML-DSA-44** | 1 158,1 µs · 863/s · **9,3× ML-DSA-44 · 0,9× su propio nativo** | 10,18 ms · 98/s · **2,9× ML-DSA-44 · 8,0× su propio nativo** |

Firma: ML-DSA-44 = 2 420 B; SLH-DSA-128s = 7 856 B (3,2× más pesada).

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
baja a **9,3×**, y el costo compuesto (las dos firmas verificadas juntas) da
**471 + 1 158 ≈ 1 630 µs**, contra los 391 µs que costó una sola verificación
ML-DSA-44 en el teléfono real (Test 2). Es **~4,2×** el costo de una
verificación simple — no ~10× ni ~30×, que es lo que una extrapolación
ingenua desde el número nativo habría sugerido.

Con la cifra de Test 2 de ~640 tx/s por cuarto de núcleo para una verificación
ML-DSA-44 sola, una verificación compuesta a ~4,2× ese costo sostendría del
orden de ~150 tx/s — muy por encima de lo que exige el caso de uso, que es
**solo** las transacciones que disparan el circuit breaker de velocidad
(§8.5), no el tráfico general de la cadena.

## 4. Lo que este número NO dice todavía

- **No está corrido en el teléfono.** El ratio nativo/JIT/intérprete de Test 2
  no fue idéntico entre x86 y ARM (§10.3 ya lo midió para ML-DSA); no hay
  garantía de que el ~4,2× compuesto se sostenga igual en el hardware de
  referencia real.
- **No incluye el costo de tamaño.** 7 856 B adicionales por transacción
  afectada es un costo de tamaño de bloque y de presupuesto de estado
  (§10.1) que este test no cuantifica — solo mide tiempo de verificación.
- **No dice si el mecanismo completo vale la pena.** Eso depende enteramente
  de la Parte A —qué techo de velocidad sobre valor dormiente no roza
  actividad legítima—, que sigue sin medir.

## 5. Reproducibilidad

Código en `codigo/`. Dos crates: `guest/` (compila a `wasm32-unknown-unknown`,
expone `run_ml_dsa44` y `run_slh_dsa128s`) y `host/` (mide con `wasmi` y
`wasmtime`, más el binario `nativo` para la fila de referencia). Instrucciones
completas en `LEEME.md`. Sin dependencias fuera de `crates.io`; las mismas
crates de RustCrypto que ya usa `pqcore` de Test 2, más `slh-dsa` 0.1.0.

*Nota de método:* `slh-dsa` 0.1.0 exige pinear `signature = "=2.3.0-pre.4"` a
mano — la resolución por defecto (`2.3.0-pre.7`) rompe la compilación del
crate por un cambio de API entre dos pre-releases de la misma versión mayor.
Es una fragilidad real de depender de un crate pre-1.0 en un pre-release
ajeno; documentado en el `LEEME.md` para que no se pierda si `slh-dsa` sube de
versión.
