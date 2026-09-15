# Test 6 · El presupuesto del desafío de cómputo

> Estado: **sin correr.** Falta elegir el modelo de referencia y el hardware
> "grande" con el que comparar. Ver §6.7.1 y el problema abierto de §10.3.

Lo que pide §6.7.1: medir cuánto tarda un nodo de cómputo en producir **un intento
válido** del desafío —una pasada de inferencia con el `nonce` adentro del prompt,
más el filtro estructural de §6.7— para poder derivar `X` (el piso de la ventana de
ronda `T`). `Y` no sale de esta medición: lo acota la coherencia con `Δ` y con la
ventana de impugnación de §6.3, no la latencia de un modelo.

## Por qué no corre en el teléfono, a diferencia de los Tests 2 y 5

§6.1 separa dos clases de nodo a propósito: los nodos PoD verifican y tienen que
entrar en cualquier hardware —de ahí que Test 2 midiera en un Motorola Edge 40
Neo—, pero **los nodos de cómputo son GPU y RAM**, un mercado competitivo y caro
por diseño. Medir `X` sobre un teléfono mediría la clase de nodo equivocada: el
desafío de §6.7 lo corren nodos de cómputo, no nodos PoD, y su hardware de
referencia tiene que ser el que va a competir de verdad.

## Qué mide exactamente

Un intento del desafío: arma un prompt con una semilla de dominio (idioma + tema +
schema) y un `nonce`, se lo manda a un modelo real por una API compatible con
OpenAI (`/v1/chat/completions` — funciona con Ollama, vLLM, TGI, llama.cpp server,
o cualquier proveedor hosteado), cronometra la respuesta, y corre el filtro
estructural de referencia sobre la salida: JSON válido, nonce repetido tal cual,
longitud mínima, proporción de palabras alfabéticas por encima de un piso, sin
repetición degenerada.

**El filtro de este script es un placeholder, no la especificación final.** La
versión de producción usa un diccionario publicado on-chain (§6.7); acá alcanza
con un chequeo heurístico para no confundir la latencia de generar ruido con la de
generar una respuesta de verdad.

Corre varios dominios distintos en la misma tanda para ver si el tipo de tarea
mueve la latencia — importa porque §6.7 rota el dominio ronda a ronda, y si la
latencia varía mucho entre dominios, `X` tiene que protegerse contra el dominio más
lento, no contra el promedio.

## Cómo correrlo

Necesita un servidor de inferencia real corriendo, apuntado por `--endpoint`. Con
Ollama, por ejemplo:

```
ollama serve
ollama pull <modelo-de-referencia-elegido>
python medicion.py --endpoint http://localhost:11434/v1/chat/completions \
                    --model <modelo-de-referencia-elegido> \
                    --intentos 30 --warmup 3
```

Sin dependencias externas — sólo `urllib` de la librería estándar, para no atarse a
qué cliente HTTP tenga instalado cada máquina.

## Lo que falta decidir antes de que el número signifique algo

El script mide latencia; no decide qué modelo correr. Esa decisión es la que quedó
abierta en §10.3: qué cuenta como el nodo de referencia cuyo peor caso protege `X`.
Correrlo con varios modelos de tamaños distintos, sobre el hardware "grande" que el
proyecto vaya a tratar como piso admisible, es lo que le da contenido a esa
decisión — un solo modelo no alcanza, por la misma razón que dos máquinas no
alcanzaron para el piso de hardware de §10.1.

## Salida

Percentiles de latencia (p50/p90/p99/peor caso) sobre los intentos que pasan el
filtro, tasa de intentos que lo pasan, y la conversión a bloques con
`tiempo_de_bloque = 6 s` (el valor ya fijado en §10.3) — parámetro configurable por
si ese valor cambia. Volcar el resultado a `RESULTADOS.md` junto con qué modelo y
qué hardware se corrió.
