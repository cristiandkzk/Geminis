# El presupuesto del nodo, y qué margen pide el lazo

**Corrido el 18/8/2026.** Reproducir con `python medicion.py`. Sin datos externos.

**La pregunta.** `θ*` se iba a fijar sobre tres supuestos sumados a ojo —128 B de
entrada + 32 B de árbol + 16 B de índice = 176 B— y sobre una simulación de
estabilidad. Se pidió medir antes de fijarlo.

**La respuesta corta: bien pedido.** Dos de los tres supuestos de bytes estaban
mal, y la simulación de C7.13 estaba mal de una forma que invalida su conclusión.
**La ley de control, corregida, no converge** — y la causa no es de sintonía sino
económica.

---

## Supuestos, todos declarados

| supuesto | valor | por qué |
|---|---|---|
| hash | 32 B | direcciones y punteros a metadata son hashes: con firmas post-cuánticas la clave pública no se guarda |
| hash en el teléfono | 100 MB/s | conservador para la capa liviana |
| presupuesto de firma | ~640 tx/s | §6.1, medido en Test 2 |
| presupuesto de disco | 2 / 4 / 8 GB | barrido |

---

## A · El layout: hay dos clases de entrada, no una

| OBJETO (el activo) | B | | SALDO (un tenedor) | B |
|---|---|---|---|---|
| dueño (hash de clave pública) | 32 | | dueño | 32 |
| identificador del activo | 8 | | identificador del activo | 8 |
| puntero a metadata (hash) | 32 | | monto | 8 |
| depósito de permanencia | 8 | | depósito de permanencia | 8 |
| bloque de creación | 8 | | bloque de creación | 8 |
| supply | 8 | | | |
| divisibilidad + flags | 4 | | | |
| **suma → alineado** | **100 → 112** | | **suma → alineado** | **64 → 64** |

Los 128 B eran correctos para el objeto. **Para un saldo sobran: son 64 B**, y esa
distinción no estaba hecha en ninguna medición anterior.

## B · El árbol: el overhead no es un dato, es una perilla

Se suponía guardar todos los nodos internos (32 B por entrada). No hace falta: se
guardan los niveles por encima de un corte `d` y se recomputa el subárbol de `2^d`
hojas. **El tope que muerde es actualizar, no probar** — actualizar pasa en cada
transacción.

| corte `d` | B por entrada | hash por operación | % del presupuesto de hash |
|---|---|---|---|
| 1 (guardar todo) | 32,0 | 0,4 KB | 0,2% |
| **6** | **1,0** | 12 KB | **7,9%** |
| 9 | 0,125 | 96 KB | 62,9% |
| 12 | 0,016 | 768 KB | 503% |

> **El árbol no cuesta 32 B por entrada: cuesta ~1 B con el corte en `d=6`**, y el
> precio son 8 puntos del presupuesto de hash del nodo. Es una decisión de
> implementación que hay que tomar, no un costo que se sufre.

> **Nota del 22/8/2026 — la tabla de bytes se reprodujo exacta, y la última frase no.**
> Construido el árbol (`geminis/estado/arbol.py`), los bytes por entrada dan
> 32,0 / 1,0 / 0,125 / 0,016 igual que acá. Lo que no se sostiene es *"decisión de
> implementación"*: **el piso de permanencia de §8.5 se deriva del costo de actualizar
> el árbol, y el piso se quema**, así que dos nodos con `d` distinto no coincidirían
> sobre cuánto se quemó al crear una entrada. `d` pasó a ser constante de Geminis
> (`CORTE_ARBOL`).
>
> Y aparece una tercera moneda que esta medición no miraba: **con `d=6` el piso es el
> 77% del depósito máximo, y con `d=7` lo supera.** El margen es más fino de lo que se
> veía mirando sólo disco y hash. Desarrollo en `geminis/estado/RESULTADOS-ARBOL.md`.

## C · El índice de desalojo

Heap binario de `(vencimiento, id)`: 16 B por entrada. **Baldes por época de
vencimiento: 8 B** —el vencimiento queda implícito en el balde, sólo se guarda el
id— y además el desalojo pasa a ser O(k) sobre los k que vencen.

## D · La capacidad real

| | entrada | árbol | índice | total |
|---|---|---|---|---|
| objeto activo | 112 | 1 | 8 | **121 B** |
| saldo de tenedor | 64 | 1 | 8 | **73 B** |

**31% menos que los 176 B supuestos.**

| presupuesto | objetos | saldos | supuesto viejo |
|---|---|---|---|
| 2 GB | 17,7 M | 29,4 M | 12,2 M |
| **4 GB** | **35,5 M** | **58,8 M** | 24,4 M |
| 8 GB | 71,0 M | 117,7 M | 48,8 M |

Y el umbral de §10.1 —creaciones por día que agotan el presupuesto en diez años—
vuelve a subir a **~9.700/día**, muy cerca del 9.200 original.

---

## E · La simulación corregida tumba el resultado de C7.13

La simulación de C7.13 recalculaba la vida de **todas** las cohortes en cada época:
al subir el precio, acortaba retroactivamente plazos ya pagados. Eso no puede
pasar — el que pagó tiene su plazo. Corregido, cada cohorte vence cuando compró
vencer. Shock ×3 sostenido, 4.000 épocas, vida de referencia 200 épocas:

| k | ε | pico | cola (min–max) | `r0` final |
|---|---|---|---|---|
| 0,05 | 1,0 | 1,98× | 0,00 – 1,97 | 3.338 |
| 0,125 | 1,0 | 2,04× | 1,19 – 1,97 | 9e19 |
| 0,25 | 1,0 | 2,08× | 0,00 – 2,08 | 2e17 |

> **No converge con ninguna ganancia.** La ocupación sigue oscilando entre casi
> cero y más del doble del objetivo después de 4.000 épocas, y `r0` se va a valores
> sin sentido. El *"absorbe un shock ×3 sin oscilar"* de C7.13 era un artefacto del
> modelo.

## F · Por qué no cierra, y no es culpa del controlador

Medido sobre esa misma corrida: **`r0` bajó hasta 0,22 y la vida máxima comprada
llegó a 897 épocas** contra 200 de referencia.

> Cuando el lazo abarata para llenar, la vida que se compra por el mismo
> presupuesto **se alarga** — y esos slots quedan tomados por siglos a precio de
> saldo. El lazo después no los recupera, porque están pagados y desalojar antes
> sería confiscación.

**No es un problema de sintonía: es arbitraje intertemporal.** Prepago con precio
flotante equivale a *comprar largo cuando está barato*. Y explica de paso el tiempo
muerto: mover el precio recién se nota cuando vencen las cohortes, y un controlador
proporcional con cientos de épocas de tiempo muerto oscila por construcción.

## G · El arreglo, y el techo que deja para `θ*`

Si la vida comprable **de una vez** está topeada en `L_max` —y para seguir vivo se
recarga al precio de entonces— el arbitraje desaparece y el tiempo muerto queda
acotado por `L_max`:

| `L_max` | ε | pico | cola (min–max) | ¿cierra? |
|---|---|---|---|---|
| 10 | 1,0 | 1,43× | 1,00 – 1,00 | **sí** |
| 25 | 0,5 | 1,25× | 1,00 – 1,00 | **sí** |
| 25 | 1,0 | 1,48× | 1,00 – 1,00 | **sí** |
| 50 | 1,0 | 1,88× | 0,17 – 1,88 | no |
| 100 | 1,0 | 2,04× | 0,00 – 2,04 | no |

Con `L_max` de 25 épocas o menos el lazo **aterriza exacto en el objetivo**; con 50
es marginal y con 100 vuelve a romperse. El umbral está en el orden de **un octavo
de la vida de referencia**.

> **El tope a la vida comprable deja de ser una recomendación económica y pasa a
> ser condición de estabilidad del mecanismo.**

Y recién con el lazo cerrando, `θ*` tiene un techo derivado. El peor pico entre las
configuraciones que cierran es **1,48×**:

| θ\* | pico de ocupación | ¿entra en el presupuesto? |
|---|---|---|
| 25% | 37% | sí |
| **50%** | **74%** | **sí** |
| 65% | 96% | sí, al filo |
| 75% | 111% | **no** |
| 90% | 134% | **no** |

> **`θ* ≤ 67%`**, y eso es un techo, no una recomendación. El margen entre θ\* y
> 100% no es holgura: es donde vive el pico del primer shock sostenido.

---

## H · La subasta de admisión, simulada contra el mismo shock

**Corrido el 1/9/2026**, agregado a `medicion.py` (`bloque_h`). Candidata a reemplazar la ley
indexada a ocupación, discutida en `CONTEXTO.md` C22.4: en vez de mover `r0` por el error
`(θ − θ*)`, cada época se admite un **cupo fijo** de estado nuevo —no depende de `θ`— y el
precio de esa época es el que hace que la demanda deseada iguale exactamente ese cupo: una
subasta de precio uniforme leída sobre la curva de demanda. Toda entrada admitida vive
**exactamente `L_max` épocas**, sin vida variable, así que el canal de arbitraje intertemporal de
E/F queda eliminado por construcción y no por un tope externo.

Mismo shock que en E: ×3 sostenido desde la época 100, 4.000 épocas, cupo calibrado para
`θ* = 1,0` con `L_max = 25` (`cupo = 1/25`):

| `ε` | `r0` pre-shock | `r0` en shock | ocupación (min–max) |
|---|---|---|---|
| 0,25 | 1,00 | **81,00** | 1,0000 – 1,0000 |
| 0,50 | 1,00 | 9,00 | 1,0000 – 1,0000 |
| 1,00 | 1,00 | 3,00 | 1,0000 – 1,0000 |
| 2,00 | 1,00 | 1,73 | 1,0000 – 1,0000 |

**La ocupación no se mueve del objetivo en ningún momento** —ni el mínimo ni el máximo
post-shock se apartan de 1,0000—, porque el cupo es fijo: `θ = cupo × L_max` en todo `t` a partir
de `L_max`. Toda la señal del shock la absorbe el **precio**, no la cantidad — al revés que la ley
vieja, donde la cantidad absorbía la señal y el precio se quedaba sin información sobre si el
nivel tenía sentido (C14.3).

**Comparado contra G con el mismo `L_max = 25`:** ahí la cola también cierra en 1,00–1,00, pero
el **pico** durante el shock llega a 1,25×–1,48× — hay overshoot real, aunque transitorio, y
`θ* ≤ 67%` existe justamente para absorberlo. Acá no hay pico que absorber: la cantidad nunca se
mueve.

**Tampoco hay tiempo de vuelta a banda ni parámetro de sintonía** (`k`, clamp): el precio salta al
valor de clearing en la misma época del shock y vuelve en la misma época en que el shock termina,
porque no hay integrador ni memoria — se resuelve la ecuación de esa época, no se corrige un
error acumulado.

> **Evita el fallo de C14.3** (ocupación pegada al target, sin lectura de si el nivel de `r0`
> tiene sentido) **y el de E/F** (arbitraje por vida variable). **Lo que no resuelve —y no
> puede—** es el nivel absoluto: el resultado sigue siendo un número en unidades de `r0`
> normalizado, igual que la ley vieja. Eso lo fija C22 (`CONTEXTO.md`), no esto.

**Lo que queda para simular antes de proponerla como reemplazo, no como candidata:** esto asume
una curva de demanda agregada continua y conocida (la misma simplificación que ya usaba E/F, no
una nueva); una subasta real coordina pujas discretas de bidders individuales, y valdría la pena
correr una versión con bids discretos y ver si el resultado de clearing se sostiene con pocos
participantes. También falta decidir el cupo cuando `θ*` cambie por una transición —acá quedó
constante durante toda la corrida— y qué pasa si la demanda deseada cae **por debajo** del cupo
(el cupo sobrante: ¿se quema, se acumula, se regala?).

---

## I · La subasta con pujas discretas — el ruido no lo controla la sobresuscripción

**Corrido el 1/9/2026** (`bloque_i`). H asume una curva de demanda continua y conocida. Acá cada
época hay `N_cand` candidatos con valuación propia —Pareto(`x_min`, `ε`), calibrada para que el
precio de clearing sin shock dé ~1,0 en promedio, igual convención que H— y el precio de esa
época es la puja **k-ésima más alta** entre los que se presentaron: sin curva, solo pujas
ordenadas y un corte en el cupo. Mismo shock ×3 desde la época 100, 100 épocas de ventana
post-shock, 40 corridas por celda.

| `k` | oversub | `ε` | `r0` teórico | `r0` medido | cv |
|---|---|---|---|---|---|
| 10 | 2 | 0,50 | 9,00 | 12,13 | 0,71 |
| 10 | 5 | 0,50 | 9,00 | 12,59 | 0,85 |
| 10 | 20 | 0,50 | 9,00 | 12,53 | 0,91 |
| 10 | 2 | 1,00 | 3,00 | 3,32 | 0,32 |
| 40 | 2 | 0,50 | 9,00 | 9,74 | 0,30 |
| 40 | 20 | 0,50 | 9,00 | 9,69 | 0,33 |

**La hipótesis con la que arrancó esta sección —"con más candidatos por cupo el ruido baja"— es
falsa, medida.** Para `k=10, ε=0,50` el `cv` se queda en 0,71–0,91 tanto con oversub=2 como con
oversub=20: no hay tendencia. Lo que sí lo baja es **el cupo `k` mismo**. Confirmado aislando la
variable, mismo `ε=0,50`, oversub fijo en 5:

| `k` | `r0` medido | cv |
|---|---|---|
| 10 | 12,37 | 0,77 |
| 40 | 9,69 | 0,32 |
| 200 | 9,15 | 0,14 |
| 1.000 | 9,04 | 0,06 |

**Por qué es así, y no al revés:** es un resultado de estadística de extremos, no de tamaño de
muestra. La puja k-ésima de una distribución de cola pesada (Pareto, `ε` chico) no converge por
tener más candidatos por encima del corte — converge por tener **más ganadores para promediar**.
Con `ε=0,5` la cola es más pesada que con `ε=1,0`, y por eso el ruido es sistemáticamente peor a
igual `k`.

> **Con el ritmo de creación ya calculado para régimen (~9.700/día, bloque D), `k` está en el
> orden de miles por época y el ruido de precio no debería ser un problema real.** Donde sí lo
> es: **el arranque**, cuando la red tiene poca actividad y `k` real puede ser apenas unos pocos
> por día — ahí el `cv` medido es 0,7–0,9, un precio que puede saltar varias veces su valor de
> una época a otra. Y la salida no es "conseguir más candidatos" —ya se midió que eso no ayuda—:
> es la misma que usa TLM en RN-12 §15 problema 2 (*thin markets*): **una reserva del protocolo
> que amortigua el precio cuando el cupo orgánico es chico, no más participantes.**

**Lo que se sostiene igual que en H:** la ocupación sigue sin moverse del objetivo pase lo que
pase con el precio —el cupo admitido es una cuenta, no el resultado de la subasta— y eso no
cambia con pujas discretas. Lo único que la subasta real le agrega de riesgo al diseño de H es
ruido de precio en el arranque, con un arreglo ya conocido en la literatura que motivó esto.

---

## J · La reserva de arranque — suavizar en el tiempo lo que falta en ganadores

**Corrido el 1/9/2026** (`bloque_j`). I midió el problema (ruido de precio con `k` chico) y
descartó la salida obvia (más candidatos no ayuda). TLM (RN-12 §11) resuelve el mismo problema
con una reserva de protocolo a curva publicada, que amortigua el precio sin desplazar el
descubrimiento de precio cuando sí hay participantes. La versión de esto para una subasta de
admisión no necesita capacidad extra — necesita **promediar sobre más épocas** cuando promediar
sobre pocos ganadores no alcanza: la misma estadística que encontró I, movida del eje de
participantes al eje de tiempo.

**Mecanismo:** `r0_efectivo(t) = α·r0_crudo(t) + (1−α)·r0_efectivo(t−1)`, con `α = min(1, k/k_ref)`.
Con `k` grande, `α→1` y el precio crudo pasa casi sin tocar; con `k` chico, `α` chico integra más
épocas — pide prestados "ganadores" del pasado en vez de pedir más candidatos ahora, que ya se
midió que no sirve. Es I2-compatible: usa solo la propia serie de precios del protocolo.

**Parte 1 — el trade-off ruido/rezago**, `k=10` fijo, `ε=0,50`, shock ×3 en la época 100, ventana
de 700 épocas, 40 corridas:

| `α` | cv pre-shock | cv post-shock | épocas de rezago |
|---|---|---|---|
| 1,00 | 0,71 | 0,84 | no asienta |
| 0,50 | 0,39 | 0,45 | no asienta |
| 0,30 | 0,28 | 0,31 | 464,0 |
| 0,15 | 0,18 | 0,22 | 225,1 |
| 0,10 | 0,15 | 0,17 | 231,1 |
| 0,05 | 0,10 | 0,11 | 128,3 |
| **0,02** | **0,07** | **0,05** | **39,6** |
| 0,01 | 0,06 | 0,04 | 77,1 |

**El rezago NO crece monótono al bajar `α` — mide dos cosas mezcladas.** Cuánto tarda en moverse
la media del suavizado (baja con `α` alto) y cuánto tarda en quedarse adentro de la banda de
±20% con el ruido que queda (baja con `α` bajo, porque hay menos ruido que la saque). Un `α`
intermedio puede perder en las dos: se mueve más lento que uno alto y sigue ruidoso. El óptimo
medido está en **`α ≈ 0,02`** (rezago mínimo, ~40 épocas, con `cv` ya bajo a 0,05-0,07) — no en
ningún extremo, y no se podía asumir sin la tabla completa: con solo `α ∈ {0,30; 0,15; 0,05}` (la
primera corrida) parecía monótono decreciente y la conclusión habría sido la contraria.

**Parte 2 — por qué conviene que `α` sea adaptativo y no fijo.** Simulado: `k=10` por 200 épocas
(arranque) y después `k=1.000` (régimen), sin shock de demanda —solo crecimiento orgánico—,
`k_ref=200`:

| épocas | `k` | cv de la ventana |
|---|---|---|
| 0–200 | 10 | 0,10 |
| 200–400 | 1.000 | 0,06 |

Con `k=1.000`, `α = min(1, 1000/200) = 1,0`: la reserva deja de tocar el precio por sí sola apenas
la red crece, sin que nadie la apague a mano. Es la propiedad que le falta a un `α` fijo: uno que
alcance para `k=10` sigue de largo suavizando —y atrasando— el precio mucho después de que dejó
de hacer falta.

> **La reserva de arranque queda especificada, no solo nombrada:** EWMA sobre la propia serie de
> `r0`, `α = min(1, k/k_ref)`, con `k_ref` en el orden de 200–500 para el caso medido (`k=10`,
> `ε=0,50`, shock ×3) — no en el extremo más suave, que empeora el rezago de nuevo. **No es
> capacidad extra ni más participantes: es memoria, y se retira sola.** Falta repetir el barrido
> para otros `k` y otros tamaños de shock antes de fijar un `k_ref` único — este número se midió
> para un caso, no para todos.

---

## K · Generalizando `k_ref` — la razón `α/k` se sostiene, el argmin ingenuo no

**Corrido el 1/9/2026** (`bloque_k`). J midió el óptimo para un solo caso (`k=10`). Antes de
proponer `k_ref` como constante del protocolo hay que ver si el óptimo en **razón `α/k`** se
sostiene cuando `k` cambia. Mismo `ε=0,50`, shock ×3, ventana de 600 épocas, 25 corridas por
celda, cuatro razones `α/k` por cada `k`:

| `k` | mejor `α/k` | `cv` en ese punto | `k_ref` implícito (argmin crudo) |
|---|---|---|---|
| 10 | 0,0020 | 0,061 | 5.000 |
| 20 | 0,0020 | 0,058 | 10.000 |
| 40 | 0,0040 | 0,092 | 10.000 |
| 80 | 0,0020 | 0,064 | 40.000 |

**El `k_ref` implícito de la última columna es un artefacto y no es el resultado.** Es el argmin
de una métrica ruidosa (rezago, 25 corridas) sobre un mínimo bastante chato entre `α/k=0,002` y
`0,004` — invertirlo (`k_ref = k/razón`) amplifica cualquier empate en un número que salta de
5.000 a 40.000 sin ningún patrón real. **La columna que sí hay que leer es el `cv` a razón fija
`0,002`: 0,061 / 0,058 / — / 0,064 para `k=10/20/—/80`** — prácticamente el mismo valor en un
rango de `k` que varía 8×. Confirma la cuenta: la memoria efectiva del EWMA es ~`k/α` "ganadores"
acumulados, así que `cv ~ sqrt(α/k)` depende del **cociente**, no de `k` por separado.

> **`k_ref` sí generaliza en el rango probado (`k=10` a `80`):** una razón `α/k ≈ 0,002–0,004`
> (`k_ref ≈ 250–500`) sirve para todo ese rango — no hace falta una función de `k`, una constante
> alcanza.

**Por qué no hace falta probar `k` de régimen (miles) para cerrar esto — se resuelve por
análisis, no por simulación nueva:** con `k_ref≈250-500` y el `k` de régimen (~9.700/día, bloque
D), `α = min(1, k/k_ref) = 1` — la reserva queda **apagada por diseño**, pasando el precio crudo
sin tocar. Y "precio crudo con `k` grande" es exactamente lo que bloque I ya midió (`cv≈0,06` en
`k=1.000`). La pregunta de si `k_ref` "aguanta" en régimen no aplica: ahí la reserva no actúa, y
el comportamiento sin reserva ya está medido. El rango que sí importaba probar —donde `α<1`— es
el que este bloque ya cubrió.

**Condición inicial, para que no quede implícita:** `r0_efectivo(0) = r0(0)`, la constante
declarada en C22 — el EWMA arranca en el mismo número que la ley cruda, sin ambigüedad.

> **Con esto la reserva de arranque queda cerrada como pieza:** mecanismo, óptimo del trade-off
> ruido/rezago, generalización en `k`, comportamiento en régimen y condición inicial — todo
> medido o resuelto por análisis directo de lo ya medido, nada supuesto. Lo que sigue abierto
> (cupo bajo transición de `θ*`, demanda por debajo del cupo) es de la subasta en general, no de
> la reserva.

---

## Veredicto

1. **Los 176 B estaban mal por dos lados.** El árbol es ~1 B con `d=6`, no 32; el
   índice es 8 B con baldes, no 16. El layout de 128 B era correcto para el objeto,
   pero **un saldo son 64 B**. Capacidad real con 4 GB: **35,5 M objetos**.
2. **La ley de control de C7.13 no cierra**, y su resultado anterior era un
   artefacto de simulación.
3. **La causa es económica:** prepago con precio flotante es arbitraje
   intertemporal — se compran vidas de 897 épocas cuando el precio cae, y esos
   slots no se recuperan sin confiscar.
4. **El arreglo es `L_max`**, un tope a la vida comprable de una vez. Con 25 épocas
   el lazo aterriza exacto.
5. **`θ*` tiene techo derivado en ~67%**, y 50% deja margen real contra el error de
   estimación que esta misma medición acaba de demostrar que es posible.
6. **La subasta de admisión con cupo fijo y vida fija en `L_max` (bloque H) evita los dos
   fallos conocidos**, en la misma simulación: la ocupación queda clavada en el objetivo sin
   overshoot (elimina el pico de 1,25×–1,48× de G) y el precio, no la cantidad, carga toda la
   información del shock (evita el fallo de C14.3). No resuelve el nivel absoluto de `r0` —eso
   sigue siendo C22.
7. **Con pujas discretas (bloque I) el mecanismo se sostiene, con un límite nuevo y medido:** el
   ruido de precio depende del **cupo `k`**, no de cuánta gente puja por él —una hipótesis previa
   que la medición descartó—. Con `k` en el orden de miles (régimen) el ruido es chico (`cv`
   ~0,06); con `k` chico (arranque) el `cv` es 0,7–0,9. El arreglo es una reserva de protocolo,
   no más participantes — mismo mecanismo que usa TLM para el mismo problema (RN-12 §15.2).
8. **La reserva de arranque (bloque J) queda especificada, no solo nombrada:** un EWMA sobre la
   propia serie de `r0` con ganancia adaptativa `α = min(1, k/k_ref)` — se retira sola cuando `k`
   crece, sin apagarlo a mano. El trade-off ruido/rezago **no es monótono**: barrer solo tres
   valores de `α` habría dado la conclusión contraria a la que da la tabla completa. El óptimo
   medido para `k=10` está en `α≈0,02`, no en el extremo más suave.
9. **`k_ref` generaliza (bloque K), pero no por el camino obvio:** el argmin ingenuo del rezago
   por fila da números que saltan de 5.000 a 40.000 sin patrón —es ruido amplificado, no una
   dependencia real en `k`—. La columna estable es el `cv` a razón `α/k` fija: prácticamente
   idéntico (0,058–0,064) en un rango de `k` de 8×, confirmando que el ruido depende del
   **cociente** `α/k` y no de `k` por separado. `k_ref ≈ 250–500` sirve para todo el rango
   probado.
10. **La reserva de arranque queda cerrada como pieza.** El único ítem que había quedado
    pendiente —`k_ref` en régimen— se resuelve por análisis: con `k` de miles, `α=min(1,k/k_ref)`
    queda capado en 1, la reserva se apaga sola por diseño, y ese caso ya lo midió el bloque I
    (`cv≈0,06`). Condición inicial explícita: `r0_efectivo(0)=r0(0)` (C22). Sigue abierto, pero ya
    no es de la reserva sino de la subasta en general: el cupo bajo transición de `θ*` y qué pasa
    si la demanda cae por debajo del cupo.
11. **Y esos dos últimos también se cierran por análisis, sin simulación nueva.** El cupo bajo
    transición de `θ*` no es una decisión: es la cuenta `cupo=θ*/L_max`, recalculada sola en cada
    activación —misma jugada que el techo de pasos—; el reacomodo tras un cambio dura como mucho
    `L_max` épocas y nunca compromete el techo físico, porque la ocupación heredada ya estaba, por
    construcción, bajo el `θ*≤67%` de la generación anterior. Y la demanda por debajo del cupo no
    es un caso especial: el cupo es un techo, no una cuota — si la demanda no lo llena, `r0` cae a
    su piso y la ocupación queda bajo `θ*` esa época, sin nada que quemar, acumular ni regalar.
    **Con esto la subasta de admisión queda especificada por completo como candidata** —cupo fijo
    y vida fija (H), pujas discretas (I), reserva de arranque (J, K), transición y demanda
    insuficiente (11)—; falta solo adoptarla, que es decisión del autor, no cuenta pendiente.
