# Test 6 · El presupuesto del desafío de cómputo

> Estado: **sin correr.**

## Lo que falta antes de que un número acá signifique algo

1. **Elegir el modelo (o los modelos) de referencia.** §10.3 deja explícito que
   esto no es una medición pura: es primero una decisión de qué nodo de cómputo
   cuenta como el peor caso legítimo que `X` tiene que seguir dejando competir.
   Un solo modelo no alcanza para fijarlo, igual que dos máquinas no alcanzaron
   para el piso de hardware de §10.1.
2. **Conseguir el hardware "grande"** contra el que comparar — esta carpeta
   corre en cualquier máquina con GPU/RAM razonable vía `--endpoint`, pero el
   extremo alto del rango (GPU de datacenter) todavía no se corrió.
3. Correr `medicion.py` contra cada combinación modelo/hardware elegida y volcar
   acá la tabla de resultados: fecha, modelo, hardware, endpoint usado, tasa de
   paso del filtro, percentiles de latencia por dominio, y la conversión a
   bloques con `tiempo_de_bloque = 6 s`.

## Formato esperado de cada corrida (completar al correr)

```
Fecha:
Modelo:
Hardware:
Endpoint:
Intentos válidos / totales:

Latencia (s):  p50 = ?   p90 = ?   p99 = ?   peor caso = ?
Por dominio:   <nombre> p50 = ?  (n=?)  ...

X_bloques (peor caso / 6s) = ?
```

Repetir por cada modelo/hardware corrido. Cuando haya al menos dos o tres puntos
de datos independientes, cerrar acá el problema abierto de §10.3 con el mismo
criterio que usó Test 2: declarar el peor caso medido, no el promedio, y dejar
la fórmula de §6.7.1 igual — lo que cambia es el número, nunca la cuenta.
