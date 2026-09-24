# Test 11 — ML-DSA-44 con umbral: ¿la cadena ve algo distinto de una firma común?

**Pregunta.** §10.2 dice que repartir la clave de una wallet entre varios dispositivos propios con un
umbral (dos de tres, por ejemplo) es la salida que vale en cualquier hardware, y que del lado de la
red "no se ve nada nuevo": el umbral produce **una firma común** bajo la clave de la cuenta. Eso era
un argumento. Medido: ¿cuánto gasta la máquina de §6.6 con una firma producida por un esquema real de
umbral para ML-DSA, contra una común, y contra la alternativa que no necesita criptografía de umbral
(un multisig k-de-n on-chain, con firmas sueltas)?

## Método

- **Esquema de umbral:** el prototipo público de **Mithril** (Celi, del Pino, Espitau, Niot, Prest;
  USENIX Security '26), en Go, commit `66e269e`, **sin modificar**. Solo se llama a su paquete
  `thmldsa44`; `firmante-go/` (un programa en Go de este test) firma 2-de-3 con cada uno de los tres
  pares posibles e imprime clave y firma en hex. La firma y la clave son las de FIPS 204 (2.420 y
  1.312 bytes).
- **Máquina:** un guest RV32IM en `geminis/predicado/vm`, **sin tocarla**, con su admisión delante y
  los dos techos del ruleset inicial (7.000.000 pasos, 96 páginas), igual que Test 9. El guest es el
  ML-DSA-44 de Test 9 **byte a byte** (mismo `sha256`), y cada veredicto de la máquina se contrasta
  con la verificación nativa del crate `ml-dsa` —otra implementación que la del firmante—.
- **El competidor:** `guest-multisig/`. La cuenta es `BLAKE2s(clave_1 || … || clave_n)`; la
  transacción trae las `n` claves, `k` firmas y los índices de quienes firmaron; el guest chequea la
  dirección, que los índices no se repitan y las `k` firmas. Mismo crate, mismo perfil y **mismo
  `Cargo.lock`** que el guest simple (ver "Una trampa").
- Mensaje: 32 bytes (el hash de una transacción), contexto vacío. 30 firmas por par (90) y 30
  comunes de otras tantas claves.

## Resultado — 17 pruebas, todas en verde

### A · la firma umbral, en la máquina

| caso | acepta | pasos (mín / mediana / máx) | páginas |
|---|:-:|---:|---:|
| **umbral 2-de-3, los tres pares** | **90 / 90** | 3.318.613 / **3.318.732** / 3.318.814 | 28 |
| firma común, un firmante (mismo fork) | 30 / 30 | 3.318.542 / **3.318.658** / 3.318.863 | 28 |
| umbral + un bit de la firma alterado | 0 / 90 | 3.318.369 / 3.318.512 / 3.318.599 | |
| umbral + mensaje que no se firmó | 0 / 90 | 3.318.399 / 3.318.518 / 3.318.600 | |
| umbral + clave alterada | 0 / 90 | 3.318.406 / 3.318.525 / 3.318.607 | |

- Los tres pares {0,1}, {0,2}, {1,2} firman bajo **la misma** clave pública: quién firma no se nota.
- Las medianas difieren en **74 pasos de 3,3 M (0,002 %)** y los rangos se solapan. El umbral **no
  tiene costo en la cadena**. La cifra publicada de Test 9 para el mismo guest, firmada por una
  implementación en Rust, es 3.318.608.
- Rechazar cuesta lo que aceptar (~3,3 M), como en Test 9.
- Por debajo del umbral no sale nada: con **una** parte activa y `t = 2`, 50 de 50 intentos terminan
  en **un `panic` del prototipo** (índice fuera de rango en `recoverShare`), no en un error ni en una
  firma; con dos partes firmando pero `Combine` recibiendo **una** respuesta, 0 de 50 firmas. Es lo
  observable desde la API; no es una prueba de seguridad (esa está en el paper).

### B · el competidor: un multisig k-de-n on-chain, firmas sueltas

| forma | pasos | pág | bajo el techo inicial | tx/bloque a 96 pág | bytes de claves + firmas |
|---|---:|---:|---|---:|---:|
| 1-de-1 (línea de base, con el hash) | 3.370.359 | 29 | acepta | 15 | 3.732 |
| 2-de-2 | 6.737.639 | 30 | acepta | 7 | 7.464 |
| **2-de-3** | **6.782.939** | 30 | acepta, **queda el 3,1 % del techo** | **7** | 8.776 |
| 3-de-3 | 10.107.025 | 31 | **`TechoExcedido`** | 5 | 11.196 |

`tx/bloque` es `g.capacidad_para(96, pasos)`, la fórmula de Genesis (margen 2×), la misma que Test 8.

- El costo es lineal en las firmas verificadas: 2,00× y 3,00× la línea de base. Importa `k`, no `n`.
- Un multisig 2-de-3 entra bajo el techo **sin margen**, gasta **2×** los pasos, **parte a la mitad**
  la capacidad (15 → 7 tx/bloque) y pesa **2,35×** en bytes (8.776 contra 3.732). Un 3-de-3 **no
  entra** en una transacción: el techo lo rechaza.
- Firma mala: se rechaza tras la primera verificación (3,46 M). Dirección mala o índice repetido:
  se rechaza **antes de gastar una verificación** (~135 k pasos).

### C · lo que el umbral le pasa al lado de la wallet

Firma local en Go en esta PC, en proceso, **sin red**, 300 firmas por forma:

| t-de-n | intentos medio (máx) | ms medio (p95) | bytes por parte por intento |
|---|---:|---:|---:|
| 2-de-2 | 1,75 (8) | 2,35 (5,51) | 10.528 |
| **2-de-3** | **1,70 (7)** | **3,43 (8,19)** | **15.776** |
| 3-de-5 | 2,00 (15) | 30,48 (75,37) | 73.504 |

Un intento son tres rondas y cada parte envía la suma de los tres mensajes; los intentos son el
rejection sampling de ML-DSA repartido entre las partes. Una wallet 2-de-3 intercambia ~27 KB por
parte por firma (15.776 × 1,70). El *tiempo* está en la red, no en la aritmética (ver Límites).

## Qué muestran los números

- **La afirmación de §10.2, medida:** para este prototipo la cadena ve una firma FIPS 204 común y
  gasta en ella los mismos pasos. No se verifica nada nuevo, así que no hay verificación compuesta que
  contar en pasos RV32IM para el segundo factor de la wallet; lo que sigue sin medirse en pasos es la
  firma compuesta de Test 7, que es otra mitigación (valor dormido sobre un umbral).
- **Por qué importa el umbral, y no por gusto:** sin él, la misma protección cuesta 2× los pasos y la
  mitad de la capacidad en 2-de-3, y en 3-de-3 no entra. El techo de 7 M es lo que hace inasequible
  una política por cuenta on-chain.
- **Qué cuesta y dónde:** en la wallet, no en la cadena — intentos, ~27 KB de intercambio y tres
  rondas por intento.

## Una trampa (un número que mide otra cosa sin avisar)

La primera compilación de `guest-multisig` dio **4.924.461 pasos para una sola verificación**, contra
3.370.359 una vez corregida. Nada del código difería: su `Cargo.lock` se había resuelto de cero y trajo
`keccak 0.2.2` en vez de `0.2.1`. **Cambiar solo ese crate** —forzándolo en un lock por lo demás
idéntico— reproduce exactamente los 4.924.461: **+46 % por una verificación, por un cambio de parche
de una dependencia transitiva.** El `Cargo.lock` del guest simple se copió a propósito y el encabezado
del archivo de resultados registra las versiones. Consecuencia para cualquier cifra de costo de este
repositorio: pertenece a un **binario**, no a un nombre de crate; y un número llevado de una
compilación a otra sin revisar el lock puede estar errado a la mitad.

## Si la prueba muerde

Ejercitado: un techo de 1 M de pasos hace que la máquina rechace las 90 (la prueba que acepta
fallaría); las tres alteraciones de la firma umbral y las tres del multisig se rechazan en la máquina
y, en el primer caso, también en la verificación nativa; el guest se compara byte a byte con el de
Test 9. **No hecho:** una máquina deliberadamente rota (que acepte todo) como en Test 9.

## Límites

- **La firma es en proceso en una máquina.** Sin red, sin dispositivos separados, sin teléfono. Los
  3,4 ms son aritmética; un 2-de-3 real paga tres viajes de ida y vuelta por intento (~1,7 intentos en
  promedio acá). Los autores reportan 751 ms para un 4-de-6 entre cuatro regiones de AWS en su
  preview; **no medido acá.**
- **Las claves las reparte un proceso desde una semilla (un dealer).** El paquete público
  `thmldsa44` en este commit expone `GenerateThresholdKey` y `NewThresholdKeysFromSeed`; **no aparecen
  en su API ni DKG ni el reparto de una clave ya existente**, aunque el preview de los autores los
  lista. Para una wallet, el dispositivo que reparte es un punto de confianza mientras conserve la
  semilla.
- **Prototipo académico, según su propio README:** "have not received careful code review, and are not
  ready for production use". Según el preview, su muestreo en hiperbolas usa punto flotante (se anuncia una
  referencia en C con punto fijo); no toca el determinismo de la cadena —solo el verificador de la
  máquina lo hace— pero tampoco es de tiempo constante. **No auditado acá.**
- **El estado de ronda es de un solo uso:** reutilizar el estado de la ronda 1 con dos desafíos revela
  la parte secreta del firmante (`z − z' = (c − c')·s`). Solo puede hacerse cumplir en memoria: un
  teléfono que persista y restaure ese estado, o que se reinicie a mitad de firma, es un riesgo. **Sin
  abortos identificables**: un dispositivo malicioso puede hacer fallar la firma sin que se sepa cuál.
- **Patentes:** PQShield declara dos solicitudes pendientes sobre los bloques en que se apoya Mithril
  (`PCT/GB2025/051022`, `2509575.3`) y promete una licencia permisiva para la implementación central.
- **La seguridad del esquema no se prueba acá** —eso es el paper y su revisión—, solo lo observable:
  la salida es una firma válida y la máquina la trata como tal. Quorus (JPMorgan, también USENIX
  Security '26) y TALUS (arXiv) **no** se corrieron.
- **Una implementación por primitiva** (crates de referencia, sin ajustar) y **solo x86-64**.
- El multisig revela las `n` claves en cada transacción; una raíz de Merkle de claves achicaría los
  bytes para `n` grande pero **no los pasos**, que son `k` verificaciones. No medido.
- El techo de 7 M es el del ruleset inicial; §6.6 congela la fórmula, no el punto.

## Reproducir

```
cd test11-umbral-mldsa/codigo
git clone https://github.com/Threshold-ML-DSA/Threshold-ML-DSA mithril
git -C mithril checkout 66e269e75dd8f5d722675a3d276a1aedc58bc4ef
cd guest-mldsa44 && cargo build --release
cp target/riscv32im-unknown-none-elf/release/guest-mldsa44-io guest.elf
cd ../guest-multisig && cargo build --release        # conservar su Cargo.lock: ver "Una trampa"
cp target/riscv32im-unknown-none-elf/release/guest-multisig guest.elf
cd ../host && cargo build --release
cd ../firmante-go && go build -o target/firmante .   # Go 1.22 o posterior; se usó go1.27.1
cd ../.. && python prueba.py
```

Corrida cruda: `resultados/2026-09-24_x86.txt`.
