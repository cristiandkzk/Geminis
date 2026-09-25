# El sorteo del proponente contra la ventana de finalidad — resultados

**Español**

**Corrida el 25/9/2026.** Los criterios están en `CRITERIA.es.md`, escritos antes de la primera línea de código. Ver §10.2 del paper.

```
cd sorteo-proponente
python simulacion.py verificar   # V1-V4, y una verificación extra
python simulacion.py             # las tablas
```

| criterio | veredicto |
|---|---|
| **V1** la forma cerrada es exacta | **aprobado**, contra la enumeración de todos los `(n ≤ 10, a, W)` |
| **V2** el proceso simulado coincide, con cesión | **aprobado**: cerrada 0,1651, simulada 0,1636 ± 0,0012 (1,3 σ) |
| **V3** la prueba tiene filo | **aprobado**: V1 caza la fórmula que cuenta ventanas en vez de rachas |
| **V4** el borde de época importa poco | **aprobado**: razón 1,08 (rango pedido 0,75–1,25) |
| **M1** ¿aguanta como está? | **reprobado**, como estaba predicho: `s*` = 23 % / 19,5 % / 19,1 % contra el 33 % pedido |
| **M2** el `W` que lo arregla | **W = 16 a 18** |
| **M3** el efecto de ceder | **marcado**: con `q = 0,5`, `s*` baja un 44 % |

## Lo que dice el número

`s*` es la mayor fracción de asientos que puede tener un atacante con un riesgo anual ≤ 1 % de poder enterrar una impugnación
más allá de la ventana (12 bloques de 6 s, 5,26 M bloques por año).

| n | W = 12 | W = 44 (12 + 32) | W = 130 |
|---|---|---|---|
| 100 | 23,0 % (23 asientos) | 73,0 % | — (W > n) |
| 1 000 | **19,5 %** (195) | 65,6 % | 87,9 % |
| 10 000 | 19,1 % (1 914) | 65,0 % | 87,1 % |

Y cuánto tarda el primer evento, con `n = 1 000` y la ventana base:

| asientos del atacante | riesgo por bloque | primer evento |
|---|---|---|
| 25 % | 3,7·10⁻⁸ | ~5,2 años |
| 33 % | 1,1·10⁻⁶ | **~64 días** |
| 50 % | 1,1·10⁻⁴ | **~15 horas** |

**La predicción de CRITERIA estaba bien:** ≈ 20 % para W = 12 (salió 19–23 %) y ≈ 85 % para W = 130 (salió 87 %).

> **Es la potencia 12.** El riesgo por bloque va como `(1 − s)·s¹²`, y esa curva es un acantilado: pasar de un cuarto a un
> tercio de los asientos lo multiplica por treinta. Por eso el sorteo solo, con la ventana de 12, no da una garantía de
> tipo BFT: aguanta a un atacante chico y cae rápido cuando crece.

## Lo que este resultado NO dice

1. **El 1/3 es una convención** (CRITERIA lo dice): mide si hace falta *algo más* además del sorteo, no si el diseño es
   "seguro". La pregunta real es cuánto cuesta un asiento contra el daño que compra, y eso no salió de acá.
2. **La conclusión no depende de la imprecisión del borde de época.** Como el riesgo va como `s¹²`, un error de ±25 % en el
   riesgo (el rango de V4) mueve `s*` solo entre −2 % y +3 % relativo. Medido, `n = 1 000` y `10 000`.
3. **Cota determinística (con `q = 0`).** Cada época contiene todos los asientos honestos, así que una racha del atacante no
   puede abarcar una época entera: cruza a lo sumo un borde y vale `cola + cabeza ≤ 2a`. **Un atacante con menos de W/2 = 6
   asientos no puede enterrar una ventana de 12 bloques, por mala que sea la suerte.** Es una propiedad del sorteo sin reposición
   que un sorteo independiente no tiene, y `s*` no la refleja porque mide probabilidad. La cota sale del argumento; la
   simulación no la contradice (máximos observados 6 de 10, 12 de 20 y 5 de 12), pero en las muestras no es ajustada. **Se rompe
   con `q > 0`:** si los honestos ceden, una época puede quedarse sin ninguno.
4. **No modela**: la espera en la cola tras entrar la impugnación (suma demora, así que el resultado es optimista para la
   defensa), el sesgo de la semilla por el proponente anterior, un atacante que también cede, asientos que entran
   y salen del pool, y el costo de los asientos.

## Ceder el turno tiene un precio (M3)

| `q` (fracción de turnos cedidos) | `s*` con `n = 1 000` | relativo |
|---|---|---|
| 0 | 19,5 % | — |
| 0,2 | 16,3 % | −16 % |
| 0,5 | 11,0 % | **−44 %** |

**Está marcado.** Ceder saca del medio a los honestos lentos y deja al atacante, que nunca cede, sobrerrepresentado entre quienes
efectivamente producen. Con la mitad de los honestos cediendo, el margen se reduce a casi la mitad. La política de ceder que
se adoptó sigue siendo la correcta frente a la alternativa de reclamar por velocidad; esto dice lo que
cuesta.

## La ventana adaptativa no ayuda acá

Con `W = 44` o `130` el margen sería de 65–88 %, pero **hoy nada estira la ventana ante la censura del proponente**: el detector
de §6.3 cuenta impugnaciones que están en el estado, y una omitida por el proponente no entró a ningún bloque. Es lectura de §6.3 y
de `nodo/pod.py::_ventana_efectiva`, no una medición. Por eso M1 se evaluó contra la ventana base.

## Qué queda como decisión (no se movió nada)

Ninguna constante de Geminis cambia por esto. Lo que el número pone sobre la mesa:

- **`W` base ≥ 16–18** devolvería un tercio (M2). Cuesta latencia de finalidad (18 bloques contra 12) y toca una constante que la ventana adaptativa (§6.3)
  ya calibró contra la cola.
- **Un costo por asiento** (Parte 2). Con `n = 1 000` el atacante necesita ~195 asientos para llegar al 1 % anual. La
  pregunta que decide es cuánto rinde enterrar una impugnación contra lo que cuestan ~195 cuentas con su renta de permanencia
  (§8.5). **Ese cociente no está calculado.**
- **Hacer visible la censura al detector de la ventana adaptativa.** Hoy es invisible por construcción, y no encontré cómo hacerla visible sin un
  hecho de consenso sobre lo que un proponente omitió.

---

# Parte 2 — el costo del asiento contra el botín

**Corrida el 25/9/2026.** Criterios y predicción en `CRITERIA.es.md` (Parte 2), escritos antes de calcular.

```
python costo.py verificar   # V5
python costo.py             # las tablas
```

| criterio | veredicto |
|---|---|
| **V5** el costo reproduce las cuentas ya hechas de la tasa inicial | **aprobado**: `D_25(0)` = 0,000257 token (cuentas previas: 0,000257); llenar el estado 25 épocas = 9 183 tokens contra ~9 110 de las cuentas previas (0,8 %, la diferencia es 35,8 M de entradas de 120 B contra 35,5 M) |
| **C1** ¿el costo por asientos defiende? | **reprobado**: `X*` = 3,1·10⁻⁷ del supply contra la vara de 10⁻⁴, **por un factor de ~327** (predicción: 2,8·10⁻⁷ y ~350×) |
| extra: la actividad no suma costo | verificado: una transferencia de hasta 4 unidades mínimas no quema nada (`fee_quema_ppm` = 20 % con división entera); con 5 quema 1 |

## Lo que dice el número

Un asiento cuesta **10⁻⁵ token por día** de renta más **6,6·10⁻⁶** de piso al crearlo. Un atacante con un tercio de los asientos,
`W = 12` y 1 000 honestos necesita 500 asientos y espera ~60 días: **0,31 token en total**, o 3,1·10⁻⁷ del supply. Contra ese costo,
un botín de 100 tokens rinde **327 veces** lo que costó, y uno de 10 000 rinde 32 731 veces.

`X*` (costo esperado de un ataque exitoso, en tokens y como fracción del supply), con `s` fijo:

| atacante | n_h = 100 | n_h = 1 000 | n_h = 10 000 | n_h = 1 000 000 |
|---|---|---|---|---|
| un cuarto, W = 12 | 2,41 (2·10⁻⁶) | 5,92 (6·10⁻⁶) | 52,5 (5·10⁻⁵) | 5 181 (5·10⁻³) |
| **un tercio, W = 12** | 0,074 (7·10⁻⁸) | **0,31 (3·10⁻⁷)** | 2,83 (3·10⁻⁶) | 280 (3·10⁻⁴) |
| la mitad, W = 12 | 0,0015 (10⁻⁹) | 0,0125 (10⁻⁸) | 0,12 (10⁻⁷) | 12,3 (10⁻⁵) |

## El atacante elige `s`, y la vara era demasiado generosa (extra, no estaba en CRITERIA)

C1 fija `s = 1/3`, pero con asientos casi gratis el atacante no se queda ahí: la espera baja como `s^W` y los asientos suben
como `s/(1−s)`, así que **le conviene tener muchos más**. El ataque más barato:

| ventana | n_h = 100 | n_h = 1 000 | n_h = 10 000 | n_h = 1 000 000 |
|---|---|---|---|---|
| W = 12 | 0,0011 @57 % | **0,0105 @56 %** | 0,105 @56 % | 10,5 @55 % |
| W = 44 | 0,0062 @88 % | 0,060 @88 % | 0,60 @87 % | 59,9 @88 % |
| W = 130 | 0,024 @96 % | 0,238 @96 % | 2,37 @96 % | 493 @94 % |

Con `W = 12` y 1 000 honestos, **1 289 asientos (56 %) bastan para una racha de 12 cada ~4 horas, por 0,0105 token
(10⁻⁸ del supply)**. C1 reprobaría por ~9 500×. Los `s*` de 65–88 % que la Parte 1 daba para W = 44 y 130 se leían como margen; **en costo no lo
son**: con `s` libre, pasar de 12 a 130 (11×) multiplica el costo por ~23 y **aun así queda en 0,24 token** con 1 000 honestos.

**La razón:** el costo está dominado por `a · F`, o sea por cuántos asientos hay que crear, y `a` es proporcional a los honestos.
Es una función de `n_h · F` y casi no de `W`. **La seguridad del sorteo escala con la población honesta y con el precio del
asiento, y ese precio es el piso de crear+desalojar (§8.5), que se derivó para otra cosa.**

## No se arregla subiendo `r0`

Para que C1 aprobara con 1 000 honestos, `r0` tendría que multiplicarse por ~327. Con eso llenar el estado 25 épocas costaría
**3,0 millones de tokens, tres veces el supply**, y un usuario con 1 000 entradas pagaría 84 tokens por ciclo (hoy 0,26).
Es incompatible con el trade-off de §10.3, que eligió ×1 000 sobre el piso justamente para que el uso normal no lo notara.

## Lo que este resultado NO dice

1. **`X*` crece con la población honesta, y casi linealmente para n_h ≥ 10⁴.** Con un tercio de los asientos, C1 pasaría con ~350 000
   asientos honestos (extrapolado de la tabla entre 10⁴ y 10⁶); con el ataque más barato haría falta del orden de 10⁷, que ya
   excede la capacidad del estado (17,9 M de entradas en `θ*`). Con pocos honestos el crecimiento es menor que lineal. El sorteo
   es débil **al arranque**, el régimen que §6.3 ya trata aparte para la cola de impugnaciones (con menos de una docena de nodos
   la cola satura y la cadena tiene problemas más grandes que ése).
2. **El botín no está acotado por el protocolo**, y el 10⁻⁴ es una convención. La escalera de `X*` es lo que no depende de esa
   elección.
3. **No modela** el capital adelantado para el fraude, lo que el atacante pierde después de la racha (§6.4 acotado al saldo que
   exponga), la competencia con la demanda honesta por el cupo de admisión (715 827 entradas por época), el `r0` posterior a
   Geminis (lo fija una subasta que hoy no se conoce) ni el fraude de una transición. Los supuestos de supply (1 M) y de
   divisibilidad (1e8) son los de `parametros-mint/`, no decisiones.
4. **Supone que el atacante conserva los asientos mientras espera** la racha. Si pudiera unirse al pool conociendo ya la
   permutación de la época, pagaría menos. Depende de que el pool se fije antes que la semilla.

## La lectura de fondo

El paper defiende contra una coalición que se niega con un argumento de entrada barata: *reemplazarla cuesta un teléfono* (§6.1).
Vale contra quien se **niega**, porque se excluye solo. **No vale contra quien diluye**: entrar barato también le permite a un
atacante inundar los asientos y bajar la fracción honesta. El mismo hecho que sostiene una defensa rompe la otra.

## Qué queda como decisión (no se movió nada)

**Decidido el 25/9:** se declara el límite en §10.2 (segunda opción de la lista) y la fianza plana queda como
estudio, sin arrancar. Lo que sigue es lo que se ofreció, para el registro.

Las dos palancas de costo, en las condiciones de arriba, **no alcanzan**: ni `W` más largo ni `r0` más caro. Lo que queda son
opciones de otra clase, cada una con su costo de diseño:

- **Una fianza plana por asiento**, la misma para todos, que se retiene y no se quema. No pesa por tenencia (un asiento, un
  turno), pero es capital inmovilizado y roza la tesis de §6.1 (*sin foso de capital*). §6.3 ya acepta una fianza plana para las
  impugnaciones.
- **Declarar el límite** en §10.2 con estos números: la resistencia a la censura del proponente crece con la población honesta, y
  con pocos asientos cuesta centésimas de token.
- **Sacar la inclusión de las manos del proponente**, para que una racha suya no entierre nada. No encontré cómo sin un hecho de
  consenso sobre lo que un proponente omitió.
