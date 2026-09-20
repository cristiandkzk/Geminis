# Test 7 · El presupuesto de una firma compuesta

[English](README.md) · **Español**

> Estado: **parcial.** Escritorio (x86-64) y teléfono (ARM64) corridos en los
> tres motores. Falta toda la Parte A del problema que motiva este test y el
> costo de tamaño. Ver RESULTS.es.md.

## De dónde sale esto

No lo pide ninguna sección numerada del paper todavía. Sale de una discusión
sobre §10.2 (el canario paga por delatar, y quien puede romper la primitiva
gana más callándose): un atacante que rompe **una** primitiva puede vaciar
cualquier cuenta con esa sola ruptura. La mitigación que se evaluó —un techo
de velocidad sobre valor dormiente (§8.5, `permanencia.py`/`desalojo.py`) que
exige una **segunda firma, de una familia criptográfica independiente**, para
cualquier transacción que dispare ese techo— solo tiene sentido si esa segunda
verificación es barata en el caso raro que la paga. Este test mide eso.

**Por qué SLH-DSA y no otra cosa.** Tiene que ser una familia sin núcleo
compartido con ML-DSA (la misma condición que ya impone §10.1 para el hash de
linaje: "el linaje y la firma no pueden compartir núcleo criptográfico"). SLH-DSA
(FIPS-205 / SPHINCS+) es hash-based — SHA-2 puro en la variante `Sha2_128s` —
mientras que ML-DSA es reticulado (Module-LWE). No comparten primitiva de base,
así que romper una no dice nada sobre la otra.

## Qué mide exactamente

El mismo patrón que `pqcore` de Test 2: un módulo wasm único con `decode+verify`
de las dos primitivas (`run_ml_dsa44`, `run_slh_dsa128s`), medido con la misma
función `measure` (escala iteraciones hasta 1,2 s, mediana de 5 corridas) bajo
dos motores — `wasmi` (intérprete puro, el perfil "VM de cadena") y
`wasmtime`/Cranelift (JIT, el motor que de hecho entró en el presupuesto de
Test 2, con "391 µs · ~640 tx/s" en el teléfono real). Más un binario nativo
(`host/src/bin/nativo.rs`) para tener la fila `native` de referencia.

ML-DSA-44 usa una semilla fija (igual que `pqcore::fixture`, determinista, sin
RNG dentro del guest). SLH-DSA-128s no tiene ese camino en esta versión del
crate (`slh-dsa` 0.1.0), así que su clave y firma se generaron una vez fuera
del guest y viajan como bytes fijos en `codigo/guest/src/fixture.rs` — el guest
solo decodifica y verifica, que es exactamente lo que hace un nodo real con
una firma que le llega en una transacción.

## Cómo correrlo

`codigo/guest/guest.wasm` ya está versionado — la misma decisión que Test 2
para sus guests: el binario compilado se ignora (`target/` está en
`.gitignore`), pero **este** wasm es la entrada del benchmark, no un
artefacto de build descartable, así que va al repo. No hace falta recompilar
el guest para correr las mediciones:

```
cd codigo/host
cargo run --release --bin nativo    # fila `native`
cargo run --release                 # filas wasmi + cranelift
```

Para regenerar `guest.wasm` después de tocar `codigo/guest/src/`:

```
cd codigo/guest
cargo build --release --target wasm32-unknown-unknown
cp target/wasm32-unknown-unknown/release/guest.wasm guest.wasm
```

Sin dependencias fuera de `crates.io`: `ml-dsa` y `slh-dsa` son las mismas
crates de RustCrypto que ya usa `pqcore` (Test 2), más `wasmi` y `wasmtime` en
las mismas versiones que ya fija `test2-interprete/telefono/host/Cargo.toml`.
`signature` queda pineado a `=2.3.0-pre.4` a propósito: es la versión exacta
contra la que está compilado `slh-dsa` 0.1.0 — una versión más nueva
(`2.3.0-pre.7`, la que resuelve por defecto) rompe la compilación del crate
por un cambio de API entre pre-releases. Si `slh-dsa` sube de versión, esto
hay que revisarlo.

## En el teléfono (Termux, aarch64)

Cranelift no compila dentro de Termux: `cranelift-codegen` hace desbordar la pila
de rustc parseando el código que genera ISLE para ARM64 (ver
`test2-interprete/RESULTS.es.md`), y el host de este test lleva `wasmtime` siempre.
Hay que cruzar desde la PC:

```
rustup target add aarch64-linux-android
cd codigo/host
cargo build --release --locked --target aarch64-linux-android
```

`codigo/host/.cargo/config.toml` apunta al NDK de esta PC (rutas absolutas de
Windows: hay que ajustarlas). Salen `target/aarch64-linux-android/release/host` y
`.../nativo`; se copian al teléfono y en Termux se les hace `chmod +x` **dentro de
`~`**, porque el almacenamiento compartido está montado `noexec`. Cada corrida es un
proceso nuevo, sin cargador enchufado y sin pausas (Test 2, §6.1). `--locked`
conserva el pin de `signature`.

## Lo que falta antes de que el número signifique algo para el paper

1. **Más de un teléfono.** La pata de ARM64 está corrida (RESULTS.es.md, sección
   5), pero es un solo aparato y un solo SoC (Motorola Edge 40 Neo, MT6879). La
   penalidad de intérprete (~2× más que en x86) y la brecha de SLH-DSA-128s bajo
   JIT podrían moverse en otro teléfono de gama media.
2. **La Parte A del problema que motiva esto:** el umbral de velocidad sobre
   valor dormiente en sí — qué techo no roza actividad legítima — no está
   medido. `herramientas/traer_datos.py` solo trae series a nivel de bloque
   (blobs, gas, dificultad); hace falta una fuente de datos por dirección que
   hoy no existe en el repo. Sin eso, saber que la segunda firma es barata no
   alcanza para decidir si el mecanismo completo tiene sentido.
3. **Costo de tamaño, no solo de tiempo.** SLH-DSA-128s pesa ~7,9 KB por firma
   contra los 2,4 KB de ML-DSA-44 — un costo de ancho de banda/almacenamiento
   real que este test no cuantifica en esos términos (bytes por bloque,
   presupuesto de estado de §10.1).

Sin las tres, esto es una señal de orden de magnitud — útil para decidir si
vale la pena seguir por esta rama — no un resultado que se pueda citar como
cerrado en el paper.
