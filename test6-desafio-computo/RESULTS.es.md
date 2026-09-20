# Test 6 · El presupuesto del desafío de cómputo

[English](RESULTS.md) · **Español**

> Estado: **cinco corridas hechas: dos modelos en una GPU chica (GTX 1660 SUPER) y tres
> en un A100 80GB.** Falta decidir qué modelo y hardware cuentan como referencia; §10.3
> sigue abierto.

## Lo que falta antes de que un número acá signifique algo

1. **Elegir el modelo (o los modelos) de referencia.** §10.3 deja explícito que
   esto no es una medición pura: es primero una decisión de qué nodo de cómputo
   cuenta como el peor caso legítimo que `X` tiene que seguir dejando competir.
   Un solo modelo no alcanza para fijarlo, igual que dos máquinas no alcanzaron
   para el piso de hardware de §10.1.
2. **Más de un punto de hardware "grande".** Hay un solo A100 80GB PCIe alquilado en
   Modal; no se corrió un H100 ni una GPU de consumo grande, y el único motor
   probado es Ollama con una petición a la vez.
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

## Corridas

### 2026-09-20 · `mistral:7b` · GTX 1660 SUPER

```
Fecha: 2026-09-20
Modelo: mistral:7b (Q4_K_M, 7.2B) vía Ollama
Hardware: Intel Core i5-9400 (6 núcleos), 15.9 GB RAM, NVIDIA GTX 1660 SUPER (6 GB VRAM)
Endpoint: http://localhost:11434/v1/chat/completions
Intentos válidos / totales: 23 / 30  (77%; +3 de warmup descartados)

Latencia (s):  p50 = 14.20   p90 = 20.80   p99 = 24.49   peor caso = 25.03
Por dominio:   es-producto p50 = 18.24 (n=8)   pt-tecnologia p50 = 13.05 (n=6)
               es-cocina   p50 = 14.72 (n=5)   en-historia   p50 =  9.35 (n=4)

X_bloques (peor caso / 6s) = 5
```

Comando: `python medicion.py --endpoint http://localhost:11434/v1/chat/completions --model mistral:7b --intentos 30`

- **Rechazos del filtro (7 de 30):** 3 por debajo del piso de palabras alfabéticas
  (los 3 en `es-cocina`), 3 por JSON inválido (2 `en-historia`, 1 `pt-tecnologia`) y
  1 por campos faltantes (`en-historia`). `es-producto` pasó 8/8.
- **Esto es el extremo chico del rango, no el hardware "grande".** `ollama ps` mostró
  el modelo repartido 83% GPU / 17% CPU con contexto 4096: no entra entero en los
  6 GB de VRAM, así que parte de la inferencia corrió en CPU.
- **Los percentiles salen solo de los intentos válidos (n=23).** Con una muestra así de
  chica, `p99` es casi el máximo; el número que importa para §10.3 es el peor caso.
- **Intentos secuenciales:** tiempo esperado hasta el primer válido ≈ p50 / tasa =
  14.20 / 0.77 ≈ 18.5 s, no 14.20 s.
- Un solo modelo en una sola máquina: no fija `X` (ver el punto 1 arriba).

### 2026-09-20 · `llama3.1:8b` · GTX 1660 SUPER

```
Fecha: 2026-09-20
Modelo: llama3.1:8b (Q4_K_M, 8.0B) vía Ollama
Hardware: Intel Core i5-9400 (6 núcleos), 15.9 GB RAM, NVIDIA GTX 1660 SUPER (6 GB VRAM)
Endpoint: http://localhost:11434/v1/chat/completions
Intentos válidos / totales: 30 / 30  (100%; +3 de warmup descartados)

Latencia (s):  p50 = 13.25   p90 = 18.20   p99 = 21.25   peor caso = 21.59
Por dominio:   es-producto   p50 = 15.78 (n=8)   es-cocina     p50 = 15.21 (n=8)
               pt-tecnologia p50 = 11.30 (n=7)   en-historia   p50 =  9.42 (n=7)

X_bloques (peor caso / 6s) = 4
```

Comando: `python medicion.py --endpoint http://localhost:11434/v1/chat/completions --model llama3.1:8b --intentos 30`

- **Ningún rechazo del filtro (0 de 30).** Con `mistral:7b` habían sido 7 de 30.
- **Mismo hardware chico, con más carga en CPU:** `ollama ps` mostró el modelo repartido
  75% GPU / 25% CPU con contexto 4096 (`mistral:7b` había sido 83% / 17%).
- **El warmup en frío costó 28.15 s** (el primer intento, carga del modelo); los otros dos
  de warmup y todos los medidos quedaron entre 7 y 22 s.
- **Intentos secuenciales:** con tasa 100%, el tiempo hasta el primer válido es
  p50 = 13.25 s.

### 2026-09-20 · A100 80GB PCIe (Modal) · tres modelos

Hardware y motor comunes a las tres corridas: NVIDIA A100 80GB PCIe (81 920 MiB, driver
580.95.05) en un contenedor de Modal, con Ollama 0.34.2 —la misma versión que las
corridas locales—, contexto 4096 y una petición a la vez. `medicion.py` corrió dentro del
mismo contenedor, contra localhost, así que la red no entra en la latencia. 100 intentos
+ 3 de warmup por modelo. La carga del modelo (10–55 s) se hace antes y queda fuera de la
medición. En las tres, `ollama ps` mostró `100% GPU` con contexto 4096. `llama3.1:8b` y
`mistral:7b` tienen el mismo ID de modelo que en local (`46e0c10c039e` y `6577803aa9a0`),
o sea el mismo archivo. Script: `modal_gpu.py`; salidas crudas en `resultados-gpu/`.

```
Fecha: 2026-09-20
Modelo: llama3.1:8b (Q4_K_M, 8.0B) vía Ollama
Hardware: NVIDIA A100 80GB PCIe (Modal)
Endpoint: http://127.0.0.1:11434/v1/chat/completions (dentro del contenedor)
Intentos válidos / totales: 93 / 100  (93%; +3 de warmup descartados)

Latencia (s):  p50 = 1.41   p90 = 1.94   p99 = 2.26   peor caso = 2.33
Por dominio:   es-producto   p50 = 1.76 (n=22)   es-cocina     p50 = 1.54 (n=22)
               pt-tecnologia p50 = 1.31 (n=24)   en-historia   p50 = 1.22 (n=25)

X_bloques (peor caso / 6s) = 1
```

```
Fecha: 2026-09-20
Modelo: mistral:7b (Q4_K_M, 7.2B) vía Ollama
Hardware: NVIDIA A100 80GB PCIe (Modal)
Endpoint: http://127.0.0.1:11434/v1/chat/completions (dentro del contenedor)
Intentos válidos / totales: 78 / 100  (78%; +3 de warmup descartados)

Latencia (s):  p50 = 1.52   p90 = 2.20   p99 = 2.76   peor caso = 3.04
Por dominio:   es-producto   p50 = 1.72 (n=25)   es-cocina     p50 = 1.62 (n=21)
               pt-tecnologia p50 = 1.63 (n=14)   en-historia   p50 = 1.08 (n=18)

X_bloques (peor caso / 6s) = 1
```

```
Fecha: 2026-09-20
Modelo: llama3.1:70b (70B, 43 GB en memoria) vía Ollama
Hardware: NVIDIA A100 80GB PCIe (Modal)
Endpoint: http://127.0.0.1:11434/v1/chat/completions (dentro del contenedor)
Intentos válidos / totales: 98 / 100  (98%; +3 de warmup descartados)

Latencia (s):  p50 = 9.21   p90 = 13.58   p99 = 18.05   peor caso = 27.68
Por dominio:   es-producto   p50 = 10.90 (n=24)   es-cocina     p50 = 11.30 (n=24)
               en-historia   p50 =  8.06 (n=25)   pt-tecnologia p50 =  6.81 (n=25)

X_bloques (peor caso / 6s) = 5
```

- **Rechazos del filtro.** `llama3.1:8b`: 7 de 100, todos por JSON inválido (3 `es-cocina`,
  3 `es-producto`, 1 `pt-tecnologia`). `mistral:7b`: 22 de 100, 14 por JSON inválido, 4 por
  campos faltantes y 4 por el piso de palabras alfabéticas (11 `pt-tecnologia`, 7
  `en-historia`, 4 `es-cocina`, ninguno en `es-producto`). `llama3.1:70b`: 2 de 100, uno por
  el piso alfabético (`es-cocina`) y uno por el mínimo de palabras (`es-producto`), los dos
  de respuestas cortas (5.7 y 5.1 s).
- **El peor caso del 70B es un solo intento:** 27.68 s en el intento 97 (`es-cocina`). El
  segundo más lento fue 17.75 s, y solo 1 de los 98 válidos pasó de 18 s. Sin ese intento,
  el peor caso sería 17.75 s, o sea X = 3. No se sabe la causa: el script no registra el
  largo de la salida.

### Lectura conjunta de las cinco corridas

| Hardware | Modelo | Válidos | p50 | p90 | p99 | Peor caso | X (bloques) |
|---|---|---|---|---|---|---|---|
| GTX 1660 SUPER (6 GB) | `mistral:7b` | 23/30 (77%) | 14.20 s | 20.80 s | 24.49 s | 25.03 s | 5 |
| GTX 1660 SUPER (6 GB) | `llama3.1:8b` | 30/30 (100%) | 13.25 s | 18.20 s | 21.25 s | 21.59 s | 4 |
| A100 80GB PCIe | `mistral:7b` | 78/100 (78%) | 1.52 s | 2.20 s | 2.76 s | 3.04 s | 1 |
| A100 80GB PCIe | `llama3.1:8b` | 93/100 (93%) | 1.41 s | 1.94 s | 2.26 s | 2.33 s | 1 |
| A100 80GB PCIe | `llama3.1:70b` | 98/100 (98%) | 9.21 s | 13.58 s | 18.05 s | 27.68 s | 5 |

- **Efecto del hardware** (mismo modelo, mismo motor, mismo archivo de modelo): el A100 es
  ~9× más rápido en p50 (13.25 → 1.41 s en `llama3.1:8b`, 9.4×; 14.20 → 1.52 s en
  `mistral:7b`, 9.3×) y 8–9× en el peor caso. X baja de 4 y 5 a 1.
- **Efecto del tamaño** (mismo A100): el 70B tiene un p50 de 6.5× el del 8B (9.21 vs.
  1.41 s) y un peor caso de 11.9× (27.68 vs. 2.33 s).
- **Con el criterio de §10.3 (declarar el peor caso medido, no el promedio), el peor caso
  de las cinco corridas da X ≈ 5**, y sale de dos combinaciones opuestas: el 70B en el A100
  (27.68 s) y el 7B en la GTX 1660 SUPER (25.03 s). Un modelo grande en hardware grande y un
  modelo chico en hardware chico caen en el mismo orden de latencia. Lo que fija `X` es qué
  combinación modelo/hardware se admite como referencia, y esa es la decisión de §10.3, no
  algo que la medición resuelva.
- **La tasa de paso depende del modelo, no del hardware.** `mistral:7b` dio 77% en local y
  78% en el A100. `llama3.1:8b` dio 100% (n=30) y 93% (n=100); con una tasa real de 93%,
  sacar 30 de 30 pasa 1 de cada 9 veces (0.93^30 ≈ 11%), así que esa diferencia no distingue
  nada. En `mistral:7b` el patrón por dominio se repite entre máquinas: `es-producto` nunca
  falló y los rechazos de `es-cocina` son todos por el piso de palabras alfabéticas.
- **Límites.** Un solo A100 PCIe alquilado (nube, sin control del host), sin H100 ni GPU de
  consumo grande. Un solo modelo grande, servido por Ollama con una petición a la vez: no mide
  un nodo que sirva en paralelo ni otro motor (vLLM). Las corridas locales tienen n=23–30 y
  las del A100 n=98–100, así que el `p99` local es casi el máximo.
