# Test 8 — Ed25519 en la máquina de §6.6

**Pregunta.** ¿Cuánto cuesta verificar una firma Ed25519 en la máquina que I1 congela, comparado con
ML-DSA-44? La tabla de `geminis/herramientas/techo.py` solo tiene ML-DSA; "Ed25519 es más eficiente"
era una intuición, no una medición.

## Método

Igual que `steps_per_verify` (Test 2) y `hash.rs` (Fase 5): un guest RV32IM corre en
`geminis/predicado/vm` **sin tocarla**, con su admisión delante, y se cuentan pasos por diferencia
entre una tanda de 1 verificación y una de 11 (el marco de la llamada se cancela).

- Guest: `codigo/guest/` — ed25519-dalek 2.2.0, curve25519-dalek 4.1.3 (backend de 32 bits: lo elige
  el target, `riscv32` tiene puntero de 32), sha2 0.10.9. `opt-level 3`, LTO: el mismo perfil que el
  guest de ML-DSA.
- Mensaje de 32 bytes (un hash de transacción), el mismo tamaño que firma el guest de ML-DSA.
- Corrida cruda: `resultados/2026-09-20_x86_dalek-2.2.0.txt`.

## Resultado

| primitiva y modo | pasos por verificación | páginas |
|---|---:|---:|
| ML-DSA-44 `decode+verify` (Test 2) | 3.339.364 | 26 |
| Ed25519 `from_bytes` + `verify` | 3.013.696 | 6 |
| Ed25519 `from_bytes` + `verify_strict` | 3.284.845 | 6 |
| Ed25519 `verify`, clave ya decodificada | 2.801.768 | 6 |

Ed25519 cuesta **1,11× menos pasos** que ML-DSA-44 con `verify`, y **1,02× menos** con `verify_strict`,
que es la variante que usaría una cadena (rechaza claves y `R` de orden chico). En páginas la diferencia
es mayor: 6 contra 26.

### Lo que eso compra en `tx_por_bloque`

Con `g.capacidad_para` (margen 2×) y **cada primitiva en el menor punto medido de la curva que cubre
sus páginas** (`R_DECLARADO_POR_PAGINAS`):

| | páginas declaradas | tx por bloque |
|---|---:|---:|
| ML-DSA-44 | 96 (Génesis hoy) | 15 |
| ML-DSA-44 | 32 | 19 |
| Ed25519 `verify_strict` | 16 | 24 |
| Ed25519 `verify` | 16 | 26 |

La ventaja de Ed25519 en la máquina es de **~1,3× en capacidad**, no un orden de magnitud. Donde sí
gana por mucho es en bytes por transacción, que este test **no mide**.

## Controles

- **Ancla externa:** el vector 1 de RFC 8032 §7.1 verifica en el guest (11 de 11). No es solo
  autoconsistencia del crate.
- **Control negativo:** una firma con un bit alterado da 0 de 11.
- **Admisión y techos:** el guest pasa la admisión y una verificación entra bajo el techo inicial
  (7.000.000 pasos, 96 páginas): 3.285.175 pasos con `verify_strict`.

## Límites

- **Una implementación por primitiva.** Ed25519 y ML-DSA-44 se midieron con su crate de referencia,
  sin ajustar. Una implementación a mano podría bajar cualquiera de los dos números, y el cociente
  entre ambos con ellos.
- **Solo x86-64.** El conteo de pasos es determinístico por diseño y Test 2 lo midió idéntico en ARM;
  acá no se repitió en ARM.
- **El punto de 16 páginas no es el que usa Génesis** (96). La segunda tabla responde "qué compraría
  cada primitiva con su propio presupuesto de páginas", no "qué hace hoy la cadena".
- No se midió tamaño en bytes ni tiempo de reloj.

## Reproducir

```
cd test8-ed25519/codigo/guest && cargo build --release
cp target/riscv32im-unknown-none-elf/release/guest-ed25519 guest.elf
cd ../host && cargo run --release
```
