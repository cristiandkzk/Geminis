# El cargador bajo un adversario — resultados

**Español** *(traducción al inglés pendiente)*

**Corrida el 25/9/2026.** Los criterios están en `CRITERIA-CARGADOR.es.md`, escritos antes de tocar `admision.rs`. Ese archivo tiene
**dos correcciones a L3 con fecha** y ninguna al resto; van explicadas abajo.

```
cd predicado/vm
cargo test --release                  # 34 criterios: los 22 de la Fase 4 y 12 del cargador
cargo run --release --bin cargador    # L2, L3 y L6, con reloj
```

| criterio | veredicto |
|---|---|
| **L1** las cinco familias quedan bajo el medidor | **aprobado** (5 pruebas + la de secciones repetidas) |
| **L2** ninguna admisión ni rechazo pasa de 25 ms | **aprobado**: el máximo del corpus es **14,8 ms** (el peor caso que el medidor deja entrar) |
| **L3** el medidor no subcobra | **aprobado, después de reprobar una vez**: cazó que las cabeceras estaban cobradas de menos (abajo) |
| **L4** lo legítimo entra y no se mueve un paso | **aprobado**: los tres guests entran con costo ≤ 3,7 % del techo; `steps_per_verify` sigue en 3.339.364; 7 de 7 vectores reproducen bit a bit en x86_64 |
| **L5** el techo cubre la evaluación, en los bordes exactos | **aprobado**: `costo − 1` rechaza, `costo` admite con techo 0, `costo + 1 000` deja 1 000 |
| **L6** los símbolos no están en el camino de consenso | **aprobado**: consenso 0,04 ms; el arnés 4,45 ms (límite 25) |
| **L7** nada anterior se ablanda | **aprobado**: `criterios.rs` sin cambiar una línea; `verificar.py` 342 en verde |
| **M** los dientes | **9 de 9 mutaciones cazadas** |

## Antes y después, el mismo equipo y el mismo día

| familia | antes | después |
|---|---|---|
| **A** · 64 MiB declarados, 168 B | **197 ms** (+26 ms por sección repetida) | rechazada por F1, 0,00 ms |
| **B** · código en la última dirección, 168 B | 23 ms | rechazada por el medidor (costo 33,5 M contra 7 M), 0,00 ms |
| **C** · 1 024 segmentos superpuestos, 1 MB | 563 ms | rechazada por el medidor (costo 256 M), 0,03 ms |
| **C** · 16 segmentos, 1 MB | 9 ms | **admitida pagando 4,0 M del techo**, 0,84 ms |
| **D** · 30 000 símbolos sin NUL, 880 KB | **9 682 ms** | 0,04 ms en consenso (costo 86 palabras); 4,45 ms en el arnés |
| **E** · 60 000 segmentos × 60 000 secciones, 4,3 MB | 1 195 ms con 40 000; con 60 000, cuadrático, ~2,7 s *(estimado, no medido)* | admitida, costo 1,98 M, **13,0 ms** |
| **peor caso admitido** · 6,9 MB de código, costo 6,90 M | — | **14,8 ms** |
| guest real de Test 2 (275 KB) | 1,2 ms | 0,8–1,1 ms, costo 254 836 palabras |

Lo que dice la última fila: **el medidor no elimina el trabajo, lo acota.** Un atacante que arme el ELF más caro que cabe en el techo
paga **~15 ms de escritorio** de admisión, y como eso sale del mismo techo, **la ejecución de ese predicado tiene 0 pasos**: la
evaluación entera no pasa de unos 15 ms, no de 15 ms *más* 100.

## Lo que L3 encontró

Con 4 palabras por cabecera, la familia E (120 000 cabeceras) estaba cobrada por 540 009 palabras, o sea **7,7 ms** a `R_declarado`, y
tardaba **13 ms**: el medidor le regalaba trabajo al atacante. Medido, una cabecera cuesta ~108 ns, unas 7,6 palabras. Se declaró
**16**, el doble redondeado a potencia de dos, por lo mismo que `R_declarado` se declara por debajo del hardware real. Como la medición
es un binario y no se afirma en `cargo test`, el valor calibrado quedó fijado además por `l3_el_cobro_por_cabecera_no_baja_de_lo_medido`
(≥ 8).

## Las dos correcciones que tuvo mi criterio L3

Las dos son defectos **de mi criterio**, no de la máquina, están fechadas dentro de `CRITERIA-CARGADOR.es.md` y no se tocó ningún otro
criterio:

1. **Antes de la primera corrida:** exigía `tiempo ≤ costo × 14,3 ns` a secas, y la reserva fija de 64 MiB **no se cobra** —el propio
   archivo lo declara—, así que reprobaba por construcción a todo ELF chico. Se descuenta `T₀` (0,03 ms).
2. **En la primera corrida:** la familia D cuesta 86 palabras, permitido 1,2 µs, y el reloj no resuelve nada por debajo de decenas de
   µs; 1,6 µs de diferencia reprobó por ruido. Se agregó una banda de 0,05 ms, el 0,05 % del techo. **No esconde un subcobro real**: el
   que L3 cazó a continuación, en las cabeceras, era de milisegundos.

## Los dientes

Aplicadas a una **copia** del crate (con la misma profundidad de carpetas, para que resuelvan los `include_bytes!`); la base sin mutar
está en verde y **cada mutación tiene que hacer caer al menos un criterio**:

| | mutación | la caza |
|---|---|---|
| M1 | quitar F1 | `l1_a_…_por_f1` |
| M2 | no unir las secciones de código | `l1_las_secciones_repetidas_solo_cuestan_sus_cabeceras` |
| M3 | no descontar el costo del techo | `l1_c`, `l4`, `l5` |
| M4 | leer símbolos también en consenso | `l6_el_camino_de_consenso_no_recorre_los_simbolos` |
| M5 / M5b | buscar el segmento recorriéndolos todos (los dos chequeos) | `l1_e_…_no_es_cuadratico` |
| M6 | cobrar la copia una vez por byte de archivo y no por segmento | `l1_c_…` |
| M7 | no cobrar el predecodificado | `l1_b_…_por_el_medidor` |
| M8 | volver a 4 palabras por cabecera | `l3_el_cobro_por_cabecera_…` **y** el binario (código 1, `L3 REPRUEBA` en E) |

**M8 primero se escapó de `cargo test`**, porque L3 es una medición con reloj y no una prueba; se cerró con la prueba que fija el
valor calibrado. Y **M4 solo se caza por tiempo**: como los nombres ya están acotados, leer símbolos en consenso no cambia ningún valor
devuelto; la prueba compara contra el arnés (el consenso tiene que ser ≥ 10× más rápido, medido ~150×).

## Dos predicciones mías que fallaron

Las escribí en `CRITERIA-CARGADOR.es.md` antes de correr:

- **"Todas las familias cuestan menos de 5 ms":** la E cuesta 13 ms. Es real —parsear 120 000 cabeceras—, y está cobrada (1,98 M
  palabras, ~28 ms a `R_declarado`).
- **"Los guests reales quedan por debajo del 3 % del techo":** el de Test 2 queda en 3,6 % (254 836 de 7 M). Es el 2× del
  predecodificado más las cabeceras a 16. L4 pedía ≤ 5 % y pasa.

## Lo que sigue abierto, y se declara

- **El teléfono.** Ninguna cifra de acá se midió en un teléfono, y `R_declarado` = 70 M pasos/s es justamente un número de teléfono. Si
  el binario reprueba L3 ahí, el cobro por palabra sube. **Es una sola corrida:** `cargo run --release --bin cargador` en Termux, con
  el mismo procedimiento que `vectores`.
- **La reserva fija de 64 MiB por evaluación no se cobra.** Es constante y en x86 con Windows mide 0,03 ms (`T₀`) porque el cero es
  diferido; en ARM/Android no está medida.
- **`PALABRAS_POR_CABECERA = 16` y "una palabra = un paso" son constantes declaradas** del formato del predicado; cambian con Genesis.
  Tocarlas antes del bloque 0 es barato y después no.
- **El techo pasó a cubrir la evaluación entera** (admisión + ejecución). La fórmula de §6.6.1 no cambia; cambia cómo se lee.
- **Integración pendiente:** `nodo/predicado.py` todavía usa `MaquinaDoble` y no llama a la máquina real (véase `nodo/predicado.py`). Cuando se conecte,
  **tiene que llamar a `admitir_para_consenso`, no a `admitir`**: el segundo lee símbolos y existe solo para el arnés.
- **El parseo de la transacción que trae el ELF** queda fuera de esta ronda.
- **El corpus es el que se pensó.** Cinco familias cubiertas no dicen que no haya una sexta.
