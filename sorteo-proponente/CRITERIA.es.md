# El sorteo del proponente contra la ventana de finalidad — criterios de aprobado

**Español** *(traducción al inglés pendiente)*

**Escritos el 25/9/2026, antes de la primera línea de código.** Ver §10.2 del paper.

## La pregunta

La regla candidata: el proponente de cada bloque se sortea **sin reposición por época** entre los asientos de un pool (los que ya
propusieron quedan excluidos hasta que el pool se renueva), y un nodo lento **cede** el turno. El estado no ve nodos, ve
asientos.

**¿Cuántos asientos puede tener un atacante antes de poder enterrar una impugnación legítima más allá de la ventana de
finalidad?** Es la cuenta que faltaba para decidir si vale armar una red de prueba sobre este mecanismo.

## El modelo, declarado antes de correr

- `n` asientos, `a` del atacante, `s = a/n`.
- **Época:** permutación uniforme de los `n` asientos. Al agotarse, otra nueva. El pool no cambia de tamaño (simplificación).
- Un turno, un bloque. El asiento del atacante **propone siempre y omite la impugnación objetivo**; el honesto la incluye.
- **Cesión:** cada asiento honesto cede con probabilidad `q` (nodo lento u offline) y su turno se consume; el turno pasa al
  siguiente de la lista. El atacante nunca cede. No hay límite `k`: se salta hasta el primer asiento que produce. No hay
  timeouts, que necesitarían reloj (I2): la cesión es política local y el rango decide.
- **El atacante conoce la permutación de la época** (la semilla es pública) **y elige el momento**: comete el fraude al
  comienzo de su racha más larga. El fraude prospera si la impugnación no entra a un bloque en `W` bloques, o sea si hay una
  racha de **≥ W bloques seguidos propuestos por el atacante**. Es más duro que medir una impugnación que llega en un momento
  cualquiera, y es el atacante que el paper tiene que resistir.
- La ventana está **en bloques**: los turnos cedidos no la consumen, solo cambian *quién* produce los bloques.

**Lo que este modelo no incluye, y por qué la cota que sale es favorable a la defensa:** la espera en la cola una vez que la
impugnación entró (suma demora), el sesgo de la semilla por el proponente anterior (grindeo), el atacante que
también cede, la renovación del pool con asientos que entran y salen, y el costo de los asientos (la Parte 2 de este archivo). Las rachas que
cruzan el borde de una época se cuentan en V4.

## Qué se mide

- `E(n, a, W)`: cantidad esperada de rachas máximas de **≥ W** asientos del atacante en una época. Se calcula en forma cerrada
  (permutación sin reposición). Con cesión, el número de asientos honestos que producen es binomial y se promedia.
- `λ`: riesgo por bloque = eventos esperados por época / bloques esperados por época.
- `P_año = 1 − exp(−λ · B)`, con `B` = bloques en un año al tiempo de bloque declarado en `genesis.py`.
- `s*(n, W, q)`: la mayor fracción de asientos del atacante con `P_año ≤ 1 %`.

## Validación del simulador — V

**V1 · la forma cerrada es exacta.** **Aprobado si** para todo `n ≤ 10`, todo `a`, todo `W ≤ n`, la esperanza cerrada (en
fracciones exactas) es igual a la que sale de enumerar las `C(n,a)` ubicaciones. **Reprobado si** difiere en algún caso.

**V2 · el proceso simulado coincide con la forma cerrada, con cesión.** **Aprobado si** en un caso donde el evento se resuelve
(`E` entre 0,05 y 0,5 por época) la media de una simulación de Monte Carlo cae a menos de 3 errores estándar de la forma
cerrada. **Reprobado si** no.

**V3 · la prueba tiene filo.** **Aprobado si** una forma cerrada deliberadamente rota (se le saca la condición *"el asiento
anterior es honesto"*, que es lo que cuenta cada racha una sola vez) **es cazada por V1**. **Reprobado si** V1 pasa con la
fórmula rota — sería un V1 vacío, el patrón que ya costó tres veces en este proyecto.

**V4 · el borde de época importa poco.** **Aprobado si** el riesgo por bloque medido en un flujo continuo de épocas queda entre
0,75× y 1,25× el de la forma cerrada, para `n = 60`, `W = 6`, `s = 0,5`, `q = 0`. **Reprobado si** sale de ese rango, porque
entonces la forma cerrada por época no sirve como cota y hay que medir el flujo.

## Decisión — M

**M1 · ¿aguanta como está?** **Aprobado si** `s*(n, W = VENTANA_FINALIDAD, q = 0) ≥ 1/3` para `n ∈ {100, 1000, 10000}`.
**Reprobado si** alguno queda por debajo.

> **El 1/3 es una convención, no una derivación:** es la tolerancia de los protocolos BFT clásicos. El criterio real es cuánto
> cuesta un asiento contra cuánto vale el daño que compra, y eso esta simulación no lo puede fijar. Sirve de vara para saber si
> hace falta *algo más* además del sorteo.

**M2 · si reprueba M1, ¿qué `W` lo arregla?** Se informa el menor `W` con `s* ≥ 1/3`. Es un **insumo** para la decisión de
diseño, no una decisión: no se mueve ninguna constante de Geminis por esto.

**M3 · el efecto de ceder.** Se informa `s*` para `q ∈ {0, 0,2, 0,5}`. **Se marca** si `q = 0,5` baja `s*` más de un 20 %
relativo: sería que los nodos baratos que se caen le regalan turnos al atacante.

## Lo que no se simula, y se declara

**La ventana adaptativa de §6.3 no reacciona a la censura del proponente.** Estira la ventana cuando `backlog_impugnaciones`
supera el umbral, y ese backlog cuenta impugnaciones **que están en el estado**; una impugnación omitida por el proponente no
entró a ningún bloque, así que no está. Es lectura de §6.3 y de `nodo/pod.py::_ventana_efectiva`, no una medición. Por eso M1
se evalúa contra la ventana **base** (12), no contra el tope.

## Predicción, escrita antes de correr

De `(1 − s)·s^W ≈ 1,9·10⁻⁹` (1 % en un año a 6 s por bloque): **`s*` ≈ 20 % para `W = 12`** y ≈ 85 % para `W = 130`.
**M1 debería reprobar.** Si la corrida da otra cosa, o el modelo o esta predicción están mal, y cualquiera de las dos cosas se
escribe en `RESULTS.es.md` sin tocar este archivo.

---

# Parte 2 — el costo del asiento contra el botín

**Escrita el 25/9/2026, después de M1 y antes de calcular nada de esto.** Es la segunda palanca posible: M1 dijo *cuántos* asientos
hacen falta; esto dice *cuánto cuestan*.

## La pregunta

Un asiento es una cuenta con actividad en la ventana. ¿Cuánto cuesta el conjunto de asientos que le da a un atacante el
`s` de M1, contra lo que rinde enterrar una impugnación?

## El modelo, declarado antes de calcular

- **Costo de un asiento** = `F + r0 · T`: el piso de creación (se quema) más la renta de permanencia durante `T`, con los valores
  declarados en §10.3 y `parametros-mint/` (`r0(0)` = 1 000 unidades mínimas por época y por entrada, `F(0)` = 15,8 h de guardado). Divisibilidad 1e8,
  supply ~1e6 (los supuestos de `parametros-mint/`).
- **La actividad no suma costo:** el fee es una quema proporcional (`fee_quema_ppm`, 20 %) con división entera, así que una
  transferencia de polvo quema cero. Se verifica en el cálculo, no se supone.
- **Botín `X`**: lo que un atacante con una racha de ≥ W bloques puede hacer final, o sea el valor que una contraparte suelta
  confiando en una finalidad de W bloques. **El protocolo no lo acota** (no lee precios, I2), así que se expresa como fracción del
  supply, que es la única unidad interna.
- **Costo esperado de un ataque exitoso** = `a · (F + r0 · T_esp)`, con `a` asientos del atacante y `T_esp` = tiempo esperado hasta
  la primera racha de ≥ W (`1 / riesgo por bloque` de la Parte 1). El atacante conserva los asientos mientras espera.
- **Botín de equilibrio `X*`** = ese costo: el ataque conviene si el botín lo supera.
- `a = n_h · s / (1 − s)`: el atacante **se suma** a `n_h` asientos honestos.

## Validación — V5

**V5 · el costo reproduce las cuentas ya hechas de la tasa inicial.** **Aprobado si** con las mismas constantes salen `D_25(0)` ≈ 0,000257
token por asiento y ~9 110 tokens para llenar el estado entero durante 25 épocas (35,5 M de objetos), a menos del 1 %.
**Reprobado si** no: entonces el modelo de costo no es el de esas cuentas.

## Decisión — C1

**C1 · ¿el costo por asientos defiende?** **Aprobado si** `X* ≥ 10⁻⁴` del supply (~100 tokens) con `s = 1/3`, `W = 12` y
`n_h = 1 000`. **Reprobado si** `X*` queda por debajo.

> **El 10⁻⁴ es una convención**, como el 1/3: es un fraude "ordinario" para una red de pagos chicos entre agentes. No hay forma
> interna de fijarlo, y por eso se informa además la escalera completa de `X*`, para que se compare contra el botín que se elija.

## Lo que no se modela, y se declara

El capital que el atacante necesita adelantado para el fraude (`X`, que recupera), lo que pierde después de la racha (§6.4: la
cuenta que firmó dos veces se vacía, acotado al saldo que el atacante eligió exponer), la competencia con la demanda real de
guardado por el cupo de admisión (§8.6), el `r0` posterior a Geminis (lo fija una subasta y hoy no se conoce), y el fraude
de una transición (su botín no es cuantificable: es el control de las reglas).

## Predicción, escrita antes de calcular

Con `r0(0)` ≈ 10⁻⁵ token por día y por asiento, `s = 1/3` y `n_h = 1 000` hacen `a = 500` asientos y ~56 días de espera:
`X* ≈ 500 · (10⁻⁵ · 56 + 6,6·10⁻⁶) ≈ 0,28 token ≈ 2,8·10⁻⁷ del supply`. **C1 debería reprobar por un factor de ~350.**
