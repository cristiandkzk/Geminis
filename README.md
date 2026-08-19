# Sucesión determinista de reglas

**Una cadena que trae escrita desde el bloque 0 cómo cambian sus propias reglas, y que
ejecuta ese cambio sin voto, sin fork político y sin intervención humana en la decisión.**

> **Qué es esto y qué te pido.** Es el diseño completo (~19.500 palabras) comprimido a un
> tercio: **unos 25 minutos**. Saqué el registro de decisiones, la historia de lo que se cayó
> en el camino y las justificaciones largas — quedó el mecanismo, los números medidos y las
> fronteras.
>
> **Si tenés poco tiempo:** §2 y §3 son el mecanismo, §7 dice qué está medido y qué no, y §10
> es el pedido concreto. Lo demás es referencia para cuando quieras pegarle a algo puntual.
>
> **No es un pitch. Es un pedido de que lo rompas.** El diseño sobrevivió a todos los ataques
> que se le corrieron, y todos los corrió quien lo escribió, que es exactamente el tipo de
> evidencia que no vale. Al final hay una lista de **dónde pegar primero**; si sólo tenés
> tiempo para una cosa, andá directo ahí.
>
> Todo lo que figura como *medido* tiene script reproducible y datos crudos.

---

## 1. El problema

Todo protocolo desplegado enfrenta tarde o temprano una condición que sus reglas originales
no manejan bien. Las tres respuestas que existen hoy ponen un humano en el lazo justo en el
momento del cambio:

| mecanismo | ejemplo | quién decide |
|---|---|---|
| fork disputado | Bitcoin / BCH | una facción escribe software nuevo; el mercado arbitra después |
| voto on-chain | Tezos, Polkadot | los tenedores, con toda la política que eso arrastra |
| obsolescencia forzada | bomba de dificultad de Ethereum | el protocolo fuerza el cambio, pero el sucesor lo escriben humanos |

Las tres funcionan. Ninguna es determinista: en las tres, **qué viene después** es una decisión
tomada en el momento, por gente, bajo presión. Y esa decisión es donde un protocolo se vuelve
político.

La propuesta: que la regla de sucesión viva dentro de Genesis y se ejecute sola cuando el
estado de la cadena cumple una condición verificable. El resultado no es una familia de
cadenas — es **una sola cadena que conmuta su ruleset por generaciones**, conservando el
estado íntegro y encadenando cada generación a su ancestro por hash.

**Cómo conviene leer lo que sigue.** El diseño tiene dos mitades con respaldo muy distinto, y
decirlo temprano es más honesto que dejarlo para el final. La **sucesión de parámetros
internos** —capacidad, emisión, tiempos de bloque— salió a buscar destinatarios afuera y los
encontró (§7). El **intérprete** y las **generaciones encadenables** —que son lo que hace
posible la evolución criptográfica de §5.6 y lo que separa esto de sus precedentes— pagan las
fronteras más caras y **todavía no tienen un caso encontrado afuera**. La primera es una
aplicación; la segunda es una apuesta.

---

## 2. El mecanismo: conmutación

La pieza que hace que esto no sea un fork disfrazado es que **el nodo no se reemplaza, se
conmuta**: el mismo proceso, con el mismo estado en memoria, ejecutando reglas distintas a
partir de un bloque determinado.

```
   ┌──────── ruleset A ────────┐ ┌─ F ─┐ ┌──── Δ ────┐ ┌─── ruleset B ───┐
                                                     ║
   ───▣───▣───▣───▣───▣───▣───▣───▣───▣───▣───▣───▣──╫──▣───▣───▣───▣───▶
                              ▲       ▲              ║
                          bloque N   N final    activación
                       TRANSITION_    LOCK-IN   conmutación efectiva
                        RULE → TRUE  irrevocable
                        (advisorio)  params on-chain

   el MISMO nodo · el MISMO estado · sin migración, sin bridge, sin snapshot
```

**Son tres tiempos, no dos**, y la separación es lo que evita que cada transición sea una
sorpresa:

1. **Disparo.** En el bloque `N`, `TRANSITION_RULE` da TRUE. No conmuta nada y no compromete
   nada: es advisorio, y una reorganización lo puede deshacer.
2. **Lock-in.** Cuando `N` es final, el disparo se vuelve irrevocable. No es ceremonia:
   `H0_B` compromete `state_trigger`, y comprometerlo antes dejaría el checkpoint apuntando a
   un estado que una reorganización puede sacar de la cadena. El lock-in emite on-chain los
   parámetros completos y la altura de activación — todo lo que un integrador necesita está
   en la cadena, `Δ` bloques antes, sin que nadie tenga que anunciarlo.
3. **Activación.** `Δ` bloques después del lock-in —no después del disparo, así el aviso es
   exactamente `Δ`— el nodo conmuta.

`Δ` está fijado en Genesis **por clase de transición**: una transición de circulación tolera
ventana larga, una migración criptográfica bajo ataque necesita lo contrario.

El linaje se encadena por hash:

```
H0_B = H( H0_A ‖ state_trigger ‖ params_nuevos )
Verify( H0_B, H0_A, state_trigger, params_nuevos ) → TRUE
```

Genesis A **no conoce** el hash de B —no puede, B incorpora información que todavía no
existe— pero conoce determinísticamente cómo se calculará. `H0_B` no es el génesis de una
cadena nueva: es un marcador de checkpoint generacional dentro de la misma cadena.

---

## 3. Las cinco invariantes

Cada una elimina una forma de reintroducir al humano en el lazo. **Son el marco duro: un
ataque que las respeta es un ataque contra el diseño; uno que las viola es otro diseño.**

**I1 · El intérprete vive en Genesis y no cambia nunca.** Una transición no introduce código
de nodo: selecciona un punto de un espacio que el nodo **ya sabe ejecutar**. Lo que Genesis
fija de forma permanente no es una lista de reglas posibles sino la **máquina que las corre**.
El espacio está partido: los parámetros **internos** —emisión, fees, tamaño de bloque,
tiempos— cambian en cualquier transición; los **visibles en la interfaz** —primitiva de firma,
formato de dirección, serialización— sólo por la vía de I5.

**I2 · El trigger se computa sólo desde el estado, y su aproximación es observable.** Sin
oráculos, sin firmas, sin votos. Pero computable no alcanza: el trigger tiene que ser
**monótono en su aproximación** y exponer on-chain *cuántos bloques faltan al ritmo actual*.
Un trigger que no se puede ver venir no es admisible aunque se pueda calcular.

**I3 · El estado se conserva íntegro a través de la transición.** No hay migración de saldos,
no hay snapshot — y por lo tanto no hay bridge, que es el componente más atacado de la
industria.

**I4 · Cada generación commitea a su ancestro.** El linaje es verificable por hash y no
depende de que nadie lo atestigüe.

**I5 · Las transiciones son aditivas en la interfaz.** Toda dirección y toda transacción
llevan etiqueta de generación desde el bloque 0. Una transición puede **agregar** formatos; no
puede quitarlos.

Es la invariante que decide el modo de falla de todo **integrador externo** — un exchange, una
wallet: software que lee la cadena desde afuera, no un nodo. No significa que se quede en una
cadena vieja: **los objetos de la generación anterior nunca dejan de ser válidos**, así que el
integrador que no se actualizó los sigue procesando igual que siempre. Lo que no puede es
entender los nuevos — y ahí, como toda transacción lleva etiqueta de generación desde el bloque
0, **falla cerrado y ruidoso** (*"versión que no conozco"*) en vez de parsearlos bajo las reglas
viejas y sacar un resultado plausible y equivocado, que es la falla que pierde fondos. Eso es
degradar: funciona para lo viejo, se planta ante lo nuevo.

---

## 4. Lo que sale gratis: canonicidad

Es probablemente la propiedad más valiosa del diseño y no fue buscada: **invierte la asimetría
de legitimidad de un fork.**

En Bitcoin la posición conservadora —no cambiar nada— es el default: quien quiere cambiar las
reglas escribe software nuevo, y la cadena que sigue igual reclama ser la original. Acá es al
revés: el cliente estándar conmuta solo, así que **para no conmutar hay que modificar
activamente el software** y desactivar la regla. El que se queda en las reglas viejas no
preserva la cadena original: se desvía de Genesis, y no puede invocar a Genesis para
justificarlo.

*"Cuál es la verdadera"* deja de ser una pregunta social. Un exchange o un light client corren
la verificación de linaje, y la cadena que no conmutó no tiene checkpoint generacional válido.
Es un criterio de canonicidad objetivo, y ningún fork disputado de la historia tuvo uno.

---

## 5. La arquitectura

### 5.1 Dos clases de nodo

**Nodos de cómputo.** GPU y RAM, hostean los modelos que hacen el trabajo pedido. Hardware
caro, mercado competitivo, y **no participan del consenso**: su ingreso es el pago del pedido
que ejecutaron.

**Nodos PoD.** Verifican y liquidan, y cobran fee cada vez que dos contratos interactúan.
Corren en cualquier hardware — la verificación reproduce bit a bit en x86-64, ARM64 y un
teléfono.

**El fee es ad valorem.** Un fee fijo es regresivo en las dos direcciones: vuelve impagable el
pedido chico —que es el que una economía de agentes hace en volumen— y gratis el pedido
grande, que es donde la quema tiene que morder.

La portabilidad tiene consecuencia de gobernanza: **lo que le permite a un validador tomar de
rehén una cadena no es su convicción, es el foso de capital.** Un nodo que entra en un teléfono
no tiene foso. Pero hay un argumento mejor y no depende del costo de entrada:

> **Podés tener 3.000 nodos o 3 millones. Si no hay demanda externa, todos compiten por una
> torta que no existe.** Como la emisión no depende del trabajo (§6.1), sumar nodos no crea
> ingreso: reparte el mismo fee entre más manos. **Fabricar identidades es gratis y da
> exactamente lo mismo**, que es más robusto que hacerlo caro.

**Medido.** En un Motorola Edge 40 Neo bajo Termux, una verificación ML-DSA-44 desde bytes
corre en **391 µs** como bytecode con JIT —3,51× el nativo— y da **~640 tx/s** con un cuarto
de núcleo. Es el mismo tiempo absoluto que en un i5-9400 de escritorio. Con una salvedad: iOS
no permite JIT a terceros y el bytecode llega en tiempo de ejecución, así que un nodo en
iPhone queda forzado al intérprete, **~15× más lento**. Es política de plataforma, no
propiedad del diseño.

### 5.2 PoD verifica el predicado, no la inferencia

Un modelo no puede pasar el gate de determinismo. Ni a temperatura cero: el no determinismo de
punto flotante entre hardware distinto rompe la reproducción bit a bit.

La separación en dos capas lo vuelve irrelevante. **La GPU produce; el nodo liviano
comprueba.** El pedido no dice *"generá buen código"* — dice *"entregá algo que compile y pase
estos tests"*. La inferencia no se verifica: se verifica que **la salida satisface el
predicado**.

De ahí sale una restricción dura:

> **Todo pedido lleva un predicado de aceptación determinístico y lo bastante barato como para
> correr en la capa liviana.** Lo que no se pueda expresar así no es trabajo que la red pueda
> liquidar.

Eso convierte una advertencia difusa en una frontera nítida — y **que ese subconjunto sea lo
bastante grande como para sostener una economía es una hipótesis, no un resultado.**

Corolario que parece limitación y es lo contrario: **el cliente no elige qué nodo ejecuta su
pedido, y no lo necesita.** La calidad no se asegura seleccionando de antemano sino en la
aceptación: si la salida no satisface el predicado, no hay pago.

### 5.3 Orden sin consenso global

Verificar y ordenar no son la misma operación. Si Alice firma dos transacciones que gastan los
mismos 100 tokens, **las dos son individualmente válidas**; sólo el orden decide cuál gana.

Pero el orden **global** no hace falta: cada cuenta lleva su propia secuencia y su dueño es el
único que puede agregarle; comprometer fondos en un contrato los saca del saldo disponible, así
que no se pueden comprometer dos veces; y una interacción queda firme cuando pasa una **ventana
de impugnación** sin que nadie presente prueba de conflicto.

**La ventana no se puede tapar, y el motivo no es el precio:**

> **Llenar es serial; drenar es paralelo.** Una impugnación no existe hasta que entra en un
> bloque, así que el techo para llenar es la capacidad de la cadena — un solo caño. Drenar lo
> hacen todos los nodos PoD **a la vez**.

El margen es `N · h / γ`. Con `γ ≈ 1` —que es lo que garantiza el techo de pasos de VM— y 10%
de headroom por nodo, **alcanzan diez nodos PoD** para que la cola no acumule atraso. Dos
condiciones lo sostienen y ninguna es automática: **cualquier nodo PoD resuelve cualquier
impugnación**, y la cola es **por orden de llegada con bono plano** — si se ordenara por tamaño
de bono, el capital compraría prioridad.

El bono no tiene que ser grande, sólo distinto de cero: **el del impugnador honesto vuelve** y
**el del atacante se quema**.

### 5.4 La equivocación no se prohíbe: se vuelve suicida

Que una firma sea infalsificable no impide que su dueño firme **dos mensajes distintos**.
Ningún esquema lo evita. Pero en Schnorr y ECDSA, firmar dos mensajes con el **mismo nonce**
permite despejar la clave privada de las dos firmas — así se perdió la clave de la PS3.

Convertido en regla de diseño: **el nonce es función determinística del índice de la cuenta.**
Firmar dos veces en el mismo índice no es una infracción que haya que probar y sancionar — **es
publicar la propia clave privada.**

El castigo no necesita regla de protocolo ni árbitro, se verifica en un teléfono, y **el
vigilante se financia solo**: la recompensa por pescar la infracción es el saldo del infractor.

### 5.5 Toda transferencia es bilateral

No existe el envío unilateral: Alice ofrece, Bob acepta, y recién ahí la transferencia existe.
Hay dos clases de oferta. Una transferencia común es **dirigida**. Un pedido de trabajo es
**abierto**: no nombra a nadie, y ahí está todo el mecanismo de asignación del sistema:

> **Nadie asigna pedidos.** El cliente publica predicado, precio y plazo con los fondos ya
> comprometidos; el nodo que puede cumplirlo lo acepta. Es *pull*, no *push* — el nodo se
> autoselecciona porque conoce su propio hardware, y se autofiltra solo, porque aceptar un
> pedido que no puede cumplir es fallar el predicado y no cobrar.

De ahí salen tres cosas gratis: **no hay cómputo duplicado**, **un nodo saturado simplemente no
acepta**, y **el cliente no puede dirigir trabajo a un nodo elegido**.

El costo está declarado: no se le puede pagar a alguien que está offline, y la finalidad se
mide en minutos u horas, no en segundos.

### 5.6 Evolución criptográfica sin fondo de escalera

Toda primitiva termina cediendo. El problema es que *"la primitiva se rompió"* no está en el
estado, así que no puede ser trigger (I2); y una **lista** de reemplazos se agota y exige un
fork humano.

**El canario convierte la rotura en un hecho del estado.** Genesis publica una versión
deliberadamente debilitada con recompensa on-chain. Si alguien la rompe y la reclama, eso sí es
estado. El trigger no lee *"la criptografía se rompió"* — lee *"el canario fue reclamado"*. Una
**escalera** de canarios gradúa la respuesta: el débil cede años antes y dispara una migración
con `Δ` largo.

**El intérprete quita el fondo de la escalera.** Como Genesis fija la máquina y no la lista, una
primitiva nueva es **bytecode**, no código de nodo.

**Quién lo escribe: es un pedido de trabajo.** Cuando el canario cae, el protocolo publica el
pedido y los agentes compiten. **Quién dice que es segura: nadie puede**, así que se prueba a
los golpes:

> **El guante.** Toda candidata entra con una instancia debilitada y una recompensa on-chain
> durante una ventana fija. Si alguien la rompe, queda descartada y pasa la siguiente. La que
> sobrevive se instala. Es el mismo canario usado como examen de ingreso.

**El guante mide seguridad; el costo lo mide otra cláusula.** Una implementación correcta e
irrompible pero diez veces más cara sobrevive la ventana y queda instalada para siempre — y ahí
el presupuesto de §5.1 se rompe *desde adentro del protocolo*. Por eso el predicado lleva **dos**
cláusulas: pasar los vectores **y** verificar por debajo de un **techo de pasos de VM** — pasos
ejecutados, no tiempo de reloj, porque el conteo de instrucciones es idéntico entre
arquitecturas (medido) y el reloj sería un oráculo.

**Convergencia previa.** Justin Drake propuso *cryptographic canaries* en Ethereum Research en
febrero de 2018: bounty, prueba de amenaza, conmutación automática a un respaldo. Este diseño se
concibió independientemente. La diferencia es la profundidad: el respaldo de Drake es precableado
y de **un solo escalón**; acá el sucesor se deriva dentro de un espacio definido en Genesis y el
intérprete permite **encadenar generaciones**. Eso contesta la objeción que dejó aquella idea sin
avanzar —que calibrar el canario obliga a estimaciones tan conservadoras que la automatización se
vuelve redundante con la supervisión manual—: con un solo escalón, una transición prematura
consume el único recurso de recuperación y el trigger tiene que ser casi perfecto; encadenable,
sólo consume una generación que puede generar la siguiente.

---

## 6. La moneda

### 6.1 Tres mecanismos que no hay que fundir

| mecanismo | qué hace |
|---|---|
| **fees** | remuneran trabajo — demanda → fee → nodos |
| **emisión** | regula el estado monetario, **independiente del trabajo** |
| **PoD** | valida qué trabajo y qué transición son válidos |

> **Ninguna unidad nueva se crea porque un nodo decidió hacer más trabajo.**

Reparto de la fee, con porcentajes de ejemplo y no de diseño: 70% proveedores / 20% quema / 10%
reserva. **La quema es la única pieza irreemplazable.**

### 6.2 La distribución del día 1

Sacar la emisión de la ecuación del trabajo deja una pregunta sin la cual el resto no arranca:
**quién tiene tokens antes de que exista el primer fee.** Las tres respuestas clásicas la
contestan mal, y el motivo es un teorema:

> **Una distribución de tokens nuevos indexada a una acción rinde a lo sumo lo que cuesta esa
> acción, o es farmeable.** Si paga menos que el costo, nadie la reclama; si paga más, se
> farmea. Bitcoin pudo porque hashear tiene costo externo, físico e imposible de fingir.

**La forma elegida toma la tercera, acotada al bloque 0.** Genesis publica pools con tope por
clase, y **reclamar se paga demostrando la capacidad que se reclama**: la clase de cómputo
resuelve una tarea de referencia con predicado determinista; la clase PoD verifica un lote de
referencia dentro del techo de pasos de VM.

No necesita identidad —el costo es externo y físico—, hace **verificable la separación por
clase** —decir *"soy un nodo de cómputo"* es gratis, resolver su tarea no—, y **el trabajo no se
tira**: reclamar es un ensayo del producto real. **Lo no reclamado se quema**, y de ahí sale la
mejor propiedad:

> **La oferta inicial no la fija el creador — la fija cuánta capacidad real apareció.**

**Sin adornos: sigue siendo una subasta pagada en cómputo**, y el que tiene más hardware se
lleva más. No es reparto igualitario y no hay que venderlo como tal. Es **abierto**, que es otra
cosa, y es la propiedad que tuvo el lanzamiento de Bitcoin.

Cada claim emite además un **certificado transferible** de haber participado. **No es dinero y
no es licencia**: si diera derecho a tokens sería concentrar la base monetaria inicial; si hiciera
falta para cobrar fees, la cantidad de nodos se volvería artificialmente escasa.

**Sin decidir: el costo exacto del claim, la duración de la ventana y los topes por clase.**

### 6.3 Por qué el circuito cerrado pierde

El ataque a descartar no depende de que nadie se disfrace: Alice tiene nodos propios, se manda
trabajo a sí misma y cobra sus propias fees. La pregunta correcta no es si el protocolo puede
detectarla —no puede— sino si le conviene.

| nodos de Alice | neto por ciclo | saldo tras 1.000 ciclos, desde 1.000.000 |
|---|---|---|
| 2 de 3.000 | −0,000900 | 406.486 |
| 99% de la red | −0,000603 | 547.068 |
| **el 100%** | **−0,000600** | **548.713** |

**Pierde incluso siendo toda la red.** La cantidad de nodos sólo mueve su tajada de la reserva;
la quema queda fuera de su alcance siempre. Con quema en cero, el ataque pasa a ser gratis.

> **El protocolo no distingue a Alice de un cliente real. No lo intenta.** Hace que el circuito
> cerrado **pierda plata**, y la aritmética no necesita saber quién es nadie.

**Una oferta acotada banca actividad ilimitada.** Con supuestos hostiles —finalidad de 6 horas y
sólo 20% del circulante en vuelo— el techo de velocidad da **292 vueltas al año**, contra 1,2 de
M2 de EE.UU. y ~12 de Bitcoin on-chain. Entre 25× y 250× de aire.

**La concentración de tokens no da poder de protocolo.** I2 prohíbe que el trigger lea cualquier
cosa que no sea `emitido − quemado` del token nativo, y señalizar preparación es información,
nunca compuerta. Un actor con el 90% de los tokens tiene el 90% del dinero y cero poder sobre
las reglas.

### 6.4 Crear activos: el cargo va en la permanencia

Se admite **una primitiva de creación de forma fija**, no una máquina abierta al estado de
terceros. La cadena ya ejecuta código ajeno —el predicado de §5.2— pero un predicado corre,
contesta y muere; acá se admite que un objeto **persista**. Con forma libre, el tamaño de una
entrada lo elige el usuario y el estado deja de tener unidad de medida. Una sola primitiva cubre
fungible y no fungible: **un no fungible es `supply = 1`, indivisible**.

**El cargo no va en la creación, y es lo menos obvio del arreglo:**

> **Un cargo a la creación no reduce la creación — reduce la registración de la creación.**

Si crear adentro lleva cargo propio, se mintea **afuera**, y ahí se pierde todo lo que el
mercado nativo argumenta. La asimetría es de aplicabilidad, no sólo de incentivos: **el cargo a
la creación se evade minteando afuera; el de permanencia no, porque el estado que existe lo ven
todos los nodos.**

Entonces la tarifa tiene dos partes. Un **piso** que se quema, y no es una perilla: es el costo
fijo del ciclo crear + desalojar, medido contra el presupuesto de un nodo, unas **dieciséis horas
de guardado** (0,2% de lo que cuesta tener el objeto un año). Y un **depósito de permanencia**
que se consume quemándose época a época, lineal en **tamaño × tiempo**. Es el depósito, no el
piso, lo que hace de antispam.

**La vida comprable de una vez tiene tope, `L_max`, y es condición de estabilidad y no
recomendación.** Sin tope, un pago finito grande compra siglos. Y como la tasa no puede quedar
congelada —es un precio nominal sobre un recurso real—, prepagar sin límite es apostar contra la
regla que la mueva: cuando la tasa baja, comprar largo captura slots a precio de saldo que no se
recuperan sin confiscar. **Medido: con `L_max` = 25 épocas el lazo aterriza en el objetivo; con
50 es marginal; con 100 se rompe.**

**El cargo es por entrada, no por objeto.** Un fungible es una entrada más un saldo por cada
tenedor, y esa cuenta crece con la adopción: un token con un millón de tenedores ocupa el **3%**
del disco de un nodo — **treinta y tres tokens exitosos llenan la cadena**. Así que **toda
entrada de estado paga permanencia, y la funda quien la crea**. Eso cierra de paso un agujero que
no era del minteo: **las cuentas del token nativo también son entradas de estado**, y como el fee
es ad valorem, sobre polvo tiende a cero.

> **En la cadena no existe ningún objeto cuyo costo futuro no tenga a alguien pagándolo. Nadie
> puede comprar espacio perpetuo con un pago finito.**

**Cambio de carácter que hay que declarar: tener un saldo deja de ser gratis.** Es demurrage
sobre el estado y no sobre el monto — una billetera chica y quieta termina desalojada,
recuperable con prueba.

**Desalojar no es destruir, y el residuo tiene que ser O(1).** El objeto sale del conjunto activo
y el tenedor lo revive con una prueba, pagando el costo de entonces. Pero el compromiso contra el
que se prueba no puede ser uno por objeto: una lápida de 32 bytes por objeto son **1 GB por nodo
para siempre**, un cuarto del presupuesto. El desalojo **agrega a un acumulador único de
sólo-append** — unos **800 bytes en total**, no por objeto.

**No hay deuda ni remate.** Rematar obliga a la cadena a saber cuánto vale el activo, o sea a leer
el pool, que es exactamente lo que I2 prohíbe y es manipulable en la dirección obvia. La
liquidación la hace el mercado: quien no puede sostener el saldo vende antes del desalojo.

**Ocupación objetivo `θ* = 50%`** de un presupuesto de disco declarado —del orden de pocos GB—
que sólo una transición puede mover. El techo derivado es `θ* ≤ 67%`, porque el pico de un shock
sostenido llega a **1,48×** antes de que el precio muerda. El sesgo conservador es deliberado:
quedarse corto se corrige subiendo el número; pasarse expulsa a los nodos chicos y **eso no se
revierte**, porque el que se fue no vuelve.

---

## 7. Qué está medido y qué no

Esta sección es la que decide cuánto vale todo lo anterior.

**Medido contra el mundo (evidencia externa):**

- **El mecanismo tiene cliente.** Ethereum recalibra los parámetros de capacidad de blobs
  (`blobSchedule`) y construyó un tipo de fork dedicado a abaratar ese cambio (EIP-7892) porque
  *"los cambios grandes e infrecuentes generan costos e ineficiencias"* — pero el disparo sigue
  siendo un timestamp escrito a mano. En mayo de 2026 el patrón se repitió sobre el gas limit
  (EIP-8261), con un cronograma que declara explícitamente **no** ser regla de consenso.
  Corroboran la bomba de dificultad —retrasada por hard fork **seis veces en cinco años** para
  instalar un entero que la cadena podía calcular sola— y la emisión terminal, que Monero
  escribió por adelantado y obtuvo sin fork, mientras Bitcoin hoy no puede tenerla a ningún
  precio.
- **Precedentes.** Drake 2018 (canarios criptográficos) y BIP-103 de Pieter Wuille, 2015
  —función determinista para el límite de tamaño de bloque, sin voto de mineros—. Ninguno cierra
  el hueco: en Drake el respaldo es de un solo escalón; en BIP-103 el disparo es tiempo y no
  estado, y no hay encadenamiento. **Trabajo concurrente a vigilar:** *Post-Quantum Blockchains
  with Agility in Mind*, Tectonic Labs, IACR eprint 2026/609, marzo de 2026.
- **El presupuesto del intérprete entra**, medido en hardware real (§5.1). Lo que lo decide es que
  **determinismo e interpretación son separables**: para código entero el JIT es tan determinístico
  como el intérprete y cuesta ~3× en vez de ~29×.

**Y ahora lo que hay que decir sin adornos.** La corrección al alcance del primer punto: **ninguno
de los tres clientes encontrados necesita el intérprete, ni las generaciones encadenables, ni la
evolución criptográfica.** Son parámetros internos sobre espacios de enteros. Lo que tiene demanda
demostrada por terceros es la mitad que **no** paga las fronteras caras. La otra mitad —incluido el
diferenciador declarado frente a Drake— sigue sin destinatario encontrado.

**Medido sólo contra sí mismo (evidencia propia, que es de otra clase):** toda la moneda. El
ataque de auto-pago, la velocidad de circulación, la cola de impugnaciones, los parámetros de la
permanencia, `θ*` y `L_max`. Sobrevivieron a todos los ataques que se les corrieron, y **todos los
corrió quien escribió el diseño**.

Vale una muestra de lo frágil que es esa clase de evidencia, porque pasó acá adentro: la primera
versión de la regla que mueve la tasa de permanencia parecía estable y absorbía un shock de 3×.
Lo que la tumbó no fue un ataque — fue **corregir un detalle del modelo con que se la había
probado**: trataba como acortables unos plazos que el protocolo promete respetar. Con plazos
respetados oscila entre casi cero y más del doble del objetivo, con cualquier ganancia.

**Nada está construido.** El diseño no corrió nunca.

---

## 8. Fronteras declaradas

No son problemas a resolver: son el precio de propiedades que el diseño quiere, y se sostienen a
sabiendas. Las que más pesan:

- **La adaptación está acotada a lo que Genesis anticipó.** Si la condición que dispara la
  transición es algo no previsto, no hay ruleset que cargar. **Y el determinismo saca el freno de
  emergencia**: una transición mal anticipada es exactamente el escenario donde los humanos
  querrían negarse, y la respuesta del diseño es *"entonces sos un fork"*.
- **El conjunto de futuros posibles deja de ser auditable.** Es el precio del intérprete. Con una
  lista finita, cualquiera podía leer Genesis y saber en qué se puede convertir la cadena.
- **El intérprete es un punto único de falla que no se puede parchear nunca.** Si tiene un bug, no
  hay transición que lo arregle, porque toda transición corre sobre él. Es la única pieza donde la
  verificación formal no es opcional.
- **Sobrevivir el guante no es sobrevivir quince años de criptoanálisis.**
- **El protocolo no tiene noción de identidad, así que toda palanca que mueva, la mueve para
  todos.** Explica de una sola vez por qué murieron cuatro arreglos distintos —graduar el subsidio,
  bloquearlo un tiempo, repartir por rol, bono de impugnación superlineal—: cada uno necesitaba
  distinguir al honesto del atacante, y lo único que el protocolo ve son firmas y montos. **Toda
  propuesta de la forma "que el bueno pague menos" es una propuesta de introducir identidad.**
- **El split es ilegítimo, no imposible.** Ethereum Classic existe. La asimetría no mata a la
  cadena disidente — la hace chica.
- **El hash que encadena el linaje no se puede reemplazar**, porque lo que habría que migrar es el
  pasado. Le pasa a cualquier cadena que comprometa su historia con un hash.
- **El protocolo no puede obligar a que exista archivo.** Puede garantizar que un activo
  desalojado *se puede* revivir; no que alguien vaya a tener con qué. Alcanza para un agente
  permanentemente online y no alcanza para una persona, que va a depender de un servicio de
  archivo — o sea de mercado y no de protocolo.
- **Se puede pagar por acercar una transición, aunque no por cambiar cuál.** Al indexar la tasa de
  permanencia a la ocupación, quien ocupa disco acelera la quema ajena, y la quema es lo que lee el
  trigger. Con `s` la fracción de estado que ocupa el atacante y `ε` la elasticidad de la demanda
  honesta, la quema ajena por unidad de quema propia es `((1−s)/s)·((R−1)/R)` con
  `R = (1/(1−s))^(1/ε)`:

  | `s` | `ε` = 0,25 | `ε` = 0,5 | `ε` = 1,0 | `ε` = 2,0 |
  |---|---|---|---|---|
  | 5% | **3,52** | 1,85 | 0,95 | 0,48 |
  | 25% | 2,05 | 1,31 | 0,75 | 0,40 |
  | 50% | 0,94 | 0,75 | 0,50 | 0,29 |

  **La palanca es del orden de `1/ε`**, y `ε` no se conoce sin red corriendo. Se declara en vez de
  cerrarse: lo acota que **se compra la fecha y no el contenido** —el sucesor está escrito de
  antemano y por I3 el estado cruza intacto—. Lo reabre una medición: si la demanda de guardado
  resulta marcadamente inelástica, hay que cerrarlo por definición y pagar la primera excepción a
  *circulante es emitido menos quemado*.
- **El canario paga por delatar, y quien puede romper la primitiva gana más callándose.** El que
  puede falsificar firmas puede tomar la cadena entera, y eso vale más que cualquier bounty. Lo
  acota que el canario no necesita atraer al adversario óptimo sino a **cualquiera** que llegue
  primero — que es lo que históricamente pasó con DES, MD5 y SHA-1. **Es un supuesto empírico sobre
  cómo se difunde el criptoanálisis, no una propiedad del diseño.**
- **No hay incentivo pagado por el protocolo a correr un nodo antes de que exista demanda.** El
  claim compra la cohorte del día 1 y después el ingreso es fee de demanda real o nada. Es una
  elección deliberada entre dos fallas: el diseño viejo arrancaba seguro y se auto-farmeaba; éste
  no se auto-farmea y **puede no arrancar**.

---

## 9. Los dos problemas abiertos

Ninguno es un mecanismo: son un número, dónde vive ese número, y una regla sin elegir.

**1 · El techo de pasos de VM no está calibrado, y tiene dos filos.** Muy apretado, y la cadena no
puede adoptar una primitiva futura legítimamente más cara. Muy holgado, y vuelve el caso exacto que
el techo existe para bloquear. La salida elegante hay que resistirla: anclarlo a lo entregado en la
misma ronda —*el mejor candidato por un múltiplo*— es determinístico y nunca queda corto, pero se
rebasa en cada generación, y un 2× por transición son 1.024× a las diez.

**Y el número está acoplado a dónde vive.** Congelado en la máquina hay que elegirlo generoso —tiene
que sobrevivir veinte años de primitivas que no existen— y generoso es justamente lo que deja pasar
la implementación lenta; apretado obliga a que sea parámetro interno, y un parámetro interno es una
palanca que alguien va a querer mover. **El número y su ubicación son un solo problema.**

**2 · La regla que mueve la tasa de permanencia, y el nivel del que parte.** Que la tasa no puede
quedar congelada ya está dicho. La única variable a la que puede indexarse sin violar I2 es la
**ocupación del estado** — un hecho del estado, no una lectura de mercado. Lo que falta es qué regla
se escribe.

Y falta algo más que la forma: **falta el nivel del que parte.** Una ley de control dice cómo se
mueve la tasa, no dónde empieza, y dónde empieza es un precio —cuánto vale una época de guardado en
unidades del token— que la cadena no puede leer sin violar I2. O se fija a mano en Genesis, y
entonces lo único que el diseño promete es que la regla lo corrija si estaba mal, o hay que anclarlo
a algo que esté en el estado y todavía no aparece qué.

---

## 10. Dónde pegar

Lo que más sirve es que ataques acá. Van en orden de cuánto costaría descubrirlo tarde.

**A · ¿El subconjunto de trabajo verificable es una economía o un nicho?** Todo el ingreso de la red
depende de que existan pedidos con predicado determinista barato (§5.2). Hoy la mayor parte del valor
económico de un modelo está en salidas sin predicado barato. **Es la hipótesis más cara del diseño y
es la única que nunca se salió a falsar.** Pregunta concreta: ¿pagarías por esto, contra un proveedor
centralizado que responde en segundos, con finalidad de horas?

**B · ¿El claim recluta operadores o reclutantes?** El reclamante óptimo de §6.2 es una flota de GPU
alquilada durante la ventana, que se devuelve cuando cierra. El diseño demuestra que el hardware
**existió**, no que se **queda** — y como la emisión está desacoplada del trabajo, tener tokens no da
ninguna razón para seguir trabajando. El claim además es **irrepetible**.

**C · ¿La tarea de referencia es replayable?** Si la instancia es fija y publicada en Genesis, el
primero que la resuelve publica la solución y el costo del claim colapsa a cero para todos los demás.
Se arreglaría derivando la instancia de la clave del reclamante — no está escrito.

**D · En `t = 0` todas las defensas están denominadas en una unidad sin precio.** El fee es ad
valorem, el piso y el depósito son nominales, y el nivel inicial de la tasa es el problema abierto 2.
En la ventana en que la cadena es más frágil, el antispam vale aproximadamente nada.

**E · El escenario peligroso es el éxito, no el fracaso.** Si la moneda se aprecia —que es lo que pasa
si se adopta— el guardado se vuelve prohibitivo en términos reales y el estado se vacía. Lo que lo
compensa es la regla que no está escrita, y la primera versión de esa regla ya se cayó.

**F · El guante instala criptografía de consenso escrita por un postor anónimo**, con *"nadie rompió
una instancia debilitada en una ventana fija"* como único filtro. ¿Alcanza?

**G · El intérprete no se puede parchear nunca.** ¿Es realista verificar formalmente una VM
determinista completa, y qué pasa el día que aparezca un bug?

**H · El diseño no puede corregir un error económico del día 1**, por construcción, y un lanzamiento
es exactamente el momento en que se descubre qué no se anticipó. Toda otra cadena arregla eso por
gobernanza. ¿Es sostenible?

Si algo de esto ya está contestado en el documento largo y no se ve acá, es culpa del resumen: pedí
la sección completa y te la mando.
