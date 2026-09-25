# El cargador bajo un adversario — criterios de aprobado

**Español** *(traducción al inglés pendiente)*

**Escritos el 25/9/2026, antes de tocar `admision.rs`.** Es la regla de la sección 4 del `ROADMAP.es.md` y sigue valiendo: un
criterio escrito después de ver el resultado se acomoda al resultado. Este archivo **no se edita después de correr**; lo medido va
a `RESULTS-CARGADOR.es.md`. Es la segunda ronda de Test 5 (§12): los criterios de `CRITERIA.es.md` (C1-C7) **no se tocan**.

## El hueco

Test 5 probó que ninguna entrada hace `panic` (C4) y cerró dos amplificaciones: 64 MiB reservados antes de validar una cabecera, y
128 MiB de predecodificado por una cabecera de sección alterada. Una revisión externa empujó a probar el resto
de `admitir` con entradas **construidas y bien formadas**, no con bytes mutados de un ELF legítimo. Aparecieron cinco familias donde el
trabajo depende de lo que el ELF **declara** y no de sus bytes. Medido el 25/9/2026, release, x86 de escritorio, sobre el código
actual:

| | familia | entrada | admisión |
|---|---|---|---|
| **A** | segmento y sección declarados de 64 MiB, con 4 bytes en el archivo | 168 B | **197 ms** (+26 ms por cada sección de 40 B que repite el rango) |
| **B** | código en una dirección alta: el predecodificado abarca toda la distancia | 168 B | 23 ms |
| **C** | segmentos `PT_LOAD` superpuestos, cada uno copia el mismo trozo | 1 MB, 1 024 segmentos | 563 ms, cuadrático |
| **D** | tabla de símbolos con nombres sin NUL: cada símbolo recorre hasta el final | 880 KB, 30 000 símbolos | **9 682 ms**, cuadrático |
| **E** | N segmentos × N secciones: cada sección busca su segmento recorriéndolos todos | 2,9 MB, N = 40 000 | 1 195 ms, cuadrático |

Un predicado real de 275 KB se admite en 1,2 ms. **El techo de pasos (~100 ms) no cubre nada de esto**: la admisión corre antes del
primer paso. Y D es la peor y la menos defendible, porque leer símbolos es *comodidad del arnés, no del protocolo* (dice
`leer_simbolos`) y corre igual en cada admisión.

## El principio

> **La admisión es trabajo, y todo trabajo va bajo el medidor.** El costo de admitir un ELF es una función de sus bytes, no de lo
> que declara, y se paga del mismo techo que la ejecución.

Y su corolario para el código: **nada del camino de consenso depende de un tamaño declarado**, y lo que es comodidad del arnés
no está en ese camino.

## El medidor y la regla de formato, declarados antes de escribirlos

**Unidad:** la palabra de 4 bytes, y **una palabra cuesta un paso**. Eso sobrecobra a propósito —una palabra tarda ~1-3 ns y un
paso ~14 ns a `R_declarado` = 70 M pasos/s—, y es el lado correcto del error: `R_declarado` tiene que estar por debajo del hardware
real (§10.3).

```
costo = Σ ⌈filesz/4⌉  sobre todo PT_LOAD                copiar
      + Σ ⌈largo/4⌉   sobre la unión de secciones de código   barrer opcodes reservados
      + 2 · palabras  del rango predecodificado          reservar + decodificar
      + 4 · (phnum + shnum)                               recorrer cabeceras
```

Se calcula **solo desde las cabeceras, antes de reservar nada**, y el techo de la máquina pasa a ser `techo − costo`: *el techo
cubre la evaluación entera*. Los conteos de pasos de la ejecución no cambian (`pasos` sigue siendo ejecución).

**Regla de formato (F1):** una sección de código tiene que estar respaldada por bytes del archivo, o sea caer dentro de `filesz` de
un segmento ejecutable. Un ELF que declara código donde no hay bytes no es un predicado admisible.

**API:** `costo_de_admision(elf)`; `admitir_para_consenso(elf, techo)`, que **no lee símbolos**; y `admitir`, el arnés, que sigue
devolviendo `(Maquina, símbolos)` con nombres acotados a 256 bytes. Los 27 sitios que llaman a `admitir` no cambian.

## Los criterios

### L1 · Cada una de las cinco familias queda bajo el medidor

**Aprobado si**, con cada familia construida y bien formada: **A** se rechaza con una variante propia de F1; **B** y **C** con
1 024 segmentos se rechazan con `AdmisionExcedeElTecho` **sin haber reservado memoria**; **D** se admite en el camino de consenso
con un costo lineal en el tamaño del archivo (≤ 4 palabras por palabra de archivo, más una constante), sin recorrer símbolos; y en
**E**, con N = 60 000 segmentos y secciones, `costo_de_admision` termina en menos de un segundo. **Reprobado si** alguna se admite
pagando un costo que crece con lo declarado y no con los bytes.

> **E tiene un chequeo grueso de tiempo a propósito:** es la única familia cuya falla no cambia ningún valor devuelto, solo el
> tiempo, y sin un tiempo la prueba pasaría con el cuadrático. Con 60 000 la versión cuadrática tarda del orden de 3 s.

### L2 · Medido, no solo contado

`src/bin/cargador.rs` corre el corpus completo. **Aprobado si** ninguna admisión ni rechazo del corpus supera **25 ms**, un cuarto
del techo de ~100 ms, en la máquina de referencia de esta fase (x86 de escritorio; el teléfono queda como la corrida pendiente de
siempre, y las cifras no se citan como si lo fueran). **Reprobado si** alguna lo supera.

### L3 · El medidor no subcobra

**Aprobado si** para toda entrada **admitida** del corpus (real y hostil), `tiempo_real − T₀ ≤ costo × (1 s / 70 M)`, o sea que una
palabra cobrada no cuesta más en reloj que un paso a `R_declarado`, **descontando `T₀`**: el tiempo que tarda en la misma corrida
admitir un ELF mínimo (la reserva fija de 64 MiB, que no se cobra). **Reprobado si** alguna lo supera: entonces el medidor le está
regalando trabajo al atacante y hay que subir el cobro por palabra.

> **Corregido el 25/9/2026, antes de la primera corrida de este criterio:** la versión anterior no descontaba `T₀` y exigía
> `tiempo_real ≤ costo × 14,3 ns` a secas, con lo que reprobaba por construcción a todo ELF chico —la reserva fija no se cobra, y
> este mismo archivo lo declara más abajo—. Fue un error de este criterio y no de la máquina; se corrige acá, con fecha, y no se toca
> ninguno de los otros.
>
> **Corregido por segunda vez el 25/9/2026, en la primera corrida:** el criterio no tenía una **banda de ruido**. Una entrada que
> cuesta 86 palabras tiene permitido 1,2 µs, y el reloj sobre la mediana de 7 corridas no resuelve nada por debajo de decenas de
> microsegundos, así que una diferencia de 1,6 µs contra `T₀` reprobó a la familia D por ruido. La comparación pasa a ser
> `tiempo_real − T₀ ≤ costo / 70 M + 0,05 ms`. **La banda no esconde un subcobro real:** 0,05 ms es el 0,05 % del techo de ~100 ms,
> y el subcobro que L3 tiene que cazar —el que ya cazó en la misma corrida, en las cabeceras de la familia E— es de milisegundos.

### L4 · Lo legítimo entra y no se mueve un paso

**Aprobado si** los tres guests reales (`GUEST_RV`, `GUEST_SHA`, `GUEST_BLAKE2S`) entran bajo `TECHO_INICIAL` con un costo de
admisión ≤ 5 % de él, y `steps_per_verify` sigue siendo **3.339.364** (la regresión que ya existe y no se toca).
**Reprobado si** un legítimo no entra o el conteo se mueve.

### L5 · El techo cubre la evaluación entera, en los bordes exactos

**Aprobado si**, para un ELF fijo: el costo es idéntico en corridas repetidas; con `techo = costo − 1` se rechaza con
`AdmisionExcedeElTecho`; con `techo = costo` se admite con techo de máquina **0** y `pasos == 0`; con `techo = costo + 1 000` el
techo de la máquina es **1 000**. **Reprobado si** cualquier borde se desplaza en uno.

### L6 · Los símbolos no están en el camino de consenso

**Aprobado si** `admitir_para_consenso` no devuelve símbolos y admite la familia D en tiempo constante respecto de sus símbolos; y
`admitir` (arnés) acota cada nombre a 256 bytes, con lo que la familia D tarda **menos de 25 ms** también ahí. **Reprobado si**
el camino de consenso recorre la tabla.

### L7 · Nada anterior se ablanda

**Aprobado si** C2 y C4 de `CRITERIA.es.md` siguen pasando **sin cambiar una línea de `criterios.rs`**, y `python verificar.py`
sigue en verde (incluye la prueba que impide un `f32`, un `f64` o un literal decimal en el crate).

## Los dientes — M

Un criterio que existe y no prueba nada es el patrón que ya costó tres veces en este proyecto. **Cada regla tiene su mutación**, aplicada
a una **copia** del crate, y **tiene que caer al menos un criterio**:

| | mutación | criterio que la tiene que cazar |
|---|---|---|
| M1 | quitar F1 (aceptar código sin bytes en el archivo) | L1 A |
| M2 | barrer las secciones una por una, sin unirlas | L1 (costo con secciones repetidas) |
| M3 | no descontar el costo del techo de la máquina | L5 |
| M4 | leer símbolos también en `admitir_para_consenso` | L6 |
| M5 | buscar el segmento de cada sección recorriéndolos todos | L1 E |
| M6 | cobrar `⌈filesz/4⌉` solo una vez por byte de archivo, no por segmento | L1 C |

## Lo que no cubre, y se declara

- **La reserva fija de 64 MiB por evaluación no se cobra.** Es constante y no crece con la entrada; en x86 con Windows mide 0,0 ms
  porque el cero es diferido. **En ARM/Android no está medido**: si el asignador no difiere el cero, son unos milisegundos fijos por
  evaluación.
- **El teléfono.** Ninguna cifra de esta ronda se midió ahí.
- **`PALABRAS_POR_PASO = 1` y el `4` por cabecera son constantes declaradas** y cambian con el formato del predicado, o sea con
  Genesis. Tocarlas antes del bloque 0 es barato y después no.
- **Este medidor cubre `admitir`**, no el parseo de la transacción que contiene el ELF: queda fuera de esta ronda.
- **El corpus es el que se pensó.** Que estas cinco familias estén cubiertas no dice que no haya una sexta; dice que las cinco
  que una revisión y una lectura del código encontraron están bajo el medidor.

## Predicción, escrita antes de correr

Todas las familias se rechazan sin trabajo o cuestan menos de 5 ms; D se admite en el camino de consenso en menos de 1 ms; el
costo de admisión de los guests reales queda por debajo del 3 % de `TECHO_INICIAL`. Si alguna cifra sale distinta, o el modelo o esta
predicción están mal, y se escribe en `RESULTS-CARGADOR.es.md` sin tocar este archivo.
