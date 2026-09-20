# Test 6 · The budget of the compute challenge

**English** · [Español](RESULTS.es.md)

> Status: **five runs done: two models on a small GPU (GTX 1660 SUPER) and three on an A100
> 80GB.** Which model and hardware count as the reference is still to be decided; §10.3 stays
> open.

## What is missing before a number here means anything

1. **Choosing the reference model (or models).** §10.3 makes it explicit that this is not a pure
   measurement: it is first a decision about which compute node counts as the legitimate worst case
   that `X` has to keep letting compete. A single model is not enough to fix it, just as two
   machines were not enough for the hardware floor of §10.1.
2. **More than one "large" hardware point.** There is a single A100 80GB PCIe rented on Modal;
   no H100 or large consumer GPU was run, and the only engine tried is Ollama with one request at
   a time.
3. Running `medicion.py` against each chosen model/hardware combination and dumping the results
   table here: date, model, hardware, endpoint used, filter pass rate, latency percentiles per
   domain, and the conversion to blocks with `tiempo_de_bloque = 6 s`.

## Expected format of each run (to be completed on running)

```
Date:
Model:
Hardware:
Endpoint:
Valid / total attempts:

Latency (s):   p50 = ?   p90 = ?   p99 = ?   worst case = ?
Per domain:    <name> p50 = ?  (n=?)  ...

X_blocks (worst case / 6s) = ?
```

Repeat for each model/hardware run. Once there are at least two or three independent data points,
close the open problem of §10.3 here with the same criterion Test 2 used: declare the measured worst
case, not the average, and leave the formula of §6.7.1 unchanged — what changes is the number, never
the sum.

## Runs

### 2026-09-20 · `mistral:7b` · GTX 1660 SUPER

```
Date: 2026-09-20
Model: mistral:7b (Q4_K_M, 7.2B) via Ollama
Hardware: Intel Core i5-9400 (6 cores), 15.9 GB RAM, NVIDIA GTX 1660 SUPER (6 GB VRAM)
Endpoint: http://localhost:11434/v1/chat/completions
Valid / total attempts: 23 / 30  (77%; +3 warmup discarded)

Latency (s):   p50 = 14.20   p90 = 20.80   p99 = 24.49   worst case = 25.03
Per domain:    es-producto p50 = 18.24 (n=8)   pt-tecnologia p50 = 13.05 (n=6)
               es-cocina   p50 = 14.72 (n=5)   en-historia   p50 =  9.35 (n=4)

X_blocks (worst case / 6s) = 5
```

Command: `python medicion.py --endpoint http://localhost:11434/v1/chat/completions --model mistral:7b --intentos 30`

- **Filter rejections (7 of 30):** 3 below the alphabetic-word floor (all 3 in `es-cocina`),
  3 invalid JSON (2 `en-historia`, 1 `pt-tecnologia`) and 1 missing fields (`en-historia`).
  `es-producto` passed 8/8.
- **This is the small end of the range, not the "large" hardware.** `ollama ps` showed the model
  split 83% GPU / 17% CPU with a 4096 context: it does not fit entirely in the 6 GB of VRAM, so
  part of the inference ran on CPU.
- **Percentiles come from valid attempts only (n=23).** With a sample this small, `p99` is almost
  the maximum; the number that matters for §10.3 is the worst case.
- **Sequential attempts:** expected time to the first valid one ≈ p50 / success rate =
  14.20 / 0.77 ≈ 18.5 s, not 14.20 s.
- One model on one machine: it does not fix `X` (see point 1 above).

### 2026-09-20 · `llama3.1:8b` · GTX 1660 SUPER

```
Date: 2026-09-20
Model: llama3.1:8b (Q4_K_M, 8.0B) via Ollama
Hardware: Intel Core i5-9400 (6 cores), 15.9 GB RAM, NVIDIA GTX 1660 SUPER (6 GB VRAM)
Endpoint: http://localhost:11434/v1/chat/completions
Valid / total attempts: 30 / 30  (100%; +3 warmup discarded)

Latency (s):   p50 = 13.25   p90 = 18.20   p99 = 21.25   worst case = 21.59
Per domain:    es-producto   p50 = 15.78 (n=8)   es-cocina     p50 = 15.21 (n=8)
               pt-tecnologia p50 = 11.30 (n=7)   en-historia   p50 =  9.42 (n=7)

X_blocks (worst case / 6s) = 4
```

Command: `python medicion.py --endpoint http://localhost:11434/v1/chat/completions --model llama3.1:8b --intentos 30`

- **No filter rejections (0 of 30).** With `mistral:7b` it had been 7 of 30.
- **Same small hardware, with more load on the CPU:** `ollama ps` showed the model split
  75% GPU / 25% CPU with a 4096 context (`mistral:7b` had been 83% / 17%).
- **The cold warmup cost 28.15 s** (the first attempt, model load); the other two warmup
  attempts and every measured one fell between 7 and 22 s.
- **Sequential attempts:** with a 100% rate, the time to the first valid one is
  p50 = 13.25 s.

### 2026-09-20 · A100 80GB PCIe (Modal) · three models

Hardware and engine common to the three runs: NVIDIA A100 80GB PCIe (81,920 MiB, driver 580.95.05)
in a Modal container, with Ollama 0.34.2 —the same version as the local runs—, a 4096 context and
one request at a time. `medicion.py` ran inside the same container, against localhost, so the
network does not enter the latency. 100 attempts + 3 warmup per model. Model load (10–55 s) is done
beforehand and left out of the measurement. In all three, `ollama ps` showed `100% GPU` with a 4096
context. `llama3.1:8b` and `mistral:7b` have the same model ID as locally (`46e0c10c039e` and
`6577803aa9a0`), that is, the same file. Script: `modal_gpu.py`; raw outputs in `resultados-gpu/`.

```
Date: 2026-09-20
Model: llama3.1:8b (Q4_K_M, 8.0B) via Ollama
Hardware: NVIDIA A100 80GB PCIe (Modal)
Endpoint: http://127.0.0.1:11434/v1/chat/completions (inside the container)
Valid / total attempts: 93 / 100  (93%; +3 warmup discarded)

Latency (s):   p50 = 1.41   p90 = 1.94   p99 = 2.26   worst case = 2.33
Per domain:    es-producto   p50 = 1.76 (n=22)   es-cocina     p50 = 1.54 (n=22)
               pt-tecnologia p50 = 1.31 (n=24)   en-historia   p50 = 1.22 (n=25)

X_blocks (worst case / 6s) = 1
```

```
Date: 2026-09-20
Model: mistral:7b (Q4_K_M, 7.2B) via Ollama
Hardware: NVIDIA A100 80GB PCIe (Modal)
Endpoint: http://127.0.0.1:11434/v1/chat/completions (inside the container)
Valid / total attempts: 78 / 100  (78%; +3 warmup discarded)

Latency (s):   p50 = 1.52   p90 = 2.20   p99 = 2.76   worst case = 3.04
Per domain:    es-producto   p50 = 1.72 (n=25)   es-cocina     p50 = 1.62 (n=21)
               pt-tecnologia p50 = 1.63 (n=14)   en-historia   p50 = 1.08 (n=18)

X_blocks (worst case / 6s) = 1
```

```
Date: 2026-09-20
Model: llama3.1:70b (70B, 43 GB in memory) via Ollama
Hardware: NVIDIA A100 80GB PCIe (Modal)
Endpoint: http://127.0.0.1:11434/v1/chat/completions (inside the container)
Valid / total attempts: 98 / 100  (98%; +3 warmup discarded)

Latency (s):   p50 = 9.21   p90 = 13.58   p99 = 18.05   worst case = 27.68
Per domain:    es-producto   p50 = 10.90 (n=24)   es-cocina     p50 = 11.30 (n=24)
               en-historia   p50 =  8.06 (n=25)   pt-tecnologia p50 =  6.81 (n=25)

X_blocks (worst case / 6s) = 5
```

- **Filter rejections.** `llama3.1:8b`: 7 of 100, all for invalid JSON (3 `es-cocina`, 3
  `es-producto`, 1 `pt-tecnologia`). `mistral:7b`: 22 of 100, 14 for invalid JSON, 4 for missing
  fields and 4 for the alphabetic-word floor (11 `pt-tecnologia`, 7 `en-historia`, 4 `es-cocina`,
  none in `es-producto`). `llama3.1:70b`: 2 of 100, one for the alphabetic floor (`es-cocina`) and
  one for the minimum word count (`es-producto`), both from short answers (5.7 and 5.1 s).
- **The 70B's worst case is a single attempt:** 27.68 s on attempt 97 (`es-cocina`). The second
  slowest was 17.75 s, and only 1 of the 98 valid ones went over 18 s. Without that attempt the
  worst case would be 17.75 s, that is, X = 3. The cause is unknown: the script does not record the
  output length.

### Joint reading of the five runs

| Hardware | Model | Valid | p50 | p90 | p99 | Worst case | X (blocks) |
|---|---|---|---|---|---|---|---|
| GTX 1660 SUPER (6 GB) | `mistral:7b` | 23/30 (77%) | 14.20 s | 20.80 s | 24.49 s | 25.03 s | 5 |
| GTX 1660 SUPER (6 GB) | `llama3.1:8b` | 30/30 (100%) | 13.25 s | 18.20 s | 21.25 s | 21.59 s | 4 |
| A100 80GB PCIe | `mistral:7b` | 78/100 (78%) | 1.52 s | 2.20 s | 2.76 s | 3.04 s | 1 |
| A100 80GB PCIe | `llama3.1:8b` | 93/100 (93%) | 1.41 s | 1.94 s | 2.26 s | 2.33 s | 1 |
| A100 80GB PCIe | `llama3.1:70b` | 98/100 (98%) | 9.21 s | 13.58 s | 18.05 s | 27.68 s | 5 |

- **Hardware effect** (same model, same engine, same model file): the A100 is ~9× faster at p50
  (13.25 → 1.41 s on `llama3.1:8b`, 9.4×; 14.20 → 1.52 s on `mistral:7b`, 9.3×) and 8–9× at the
  worst case. X drops from 4 and 5 to 1.
- **Size effect** (same A100): the 70B has a p50 6.5× the 8B's (9.21 vs. 1.41 s) and a worst case
  11.9× (27.68 vs. 2.33 s).
- **With the criterion of §10.3 (declare the measured worst case, not the average), the worst case
  of the five runs gives X ≈ 5**, and it comes from two opposite combinations: the 70B on the A100
  (27.68 s) and the 7B on the GTX 1660 SUPER (25.03 s). A large model on large hardware and a small
  model on small hardware land in the same order of latency. What fixes `X` is which model/hardware
  combination is admitted as the reference, and that is the decision of §10.3, not something the
  measurement settles.
- **The pass rate depends on the model, not on the hardware.** `mistral:7b` gave 77% locally and
  78% on the A100. `llama3.1:8b` gave 100% (n=30) and 93% (n=100); with a true rate of 93%,
  getting 30 out of 30 happens 1 time in 9 (0.93^30 ≈ 11%), so that difference distinguishes
  nothing. On `mistral:7b` the per-domain pattern repeats across machines: `es-producto` never
  failed and the `es-cocina` rejections are all for the alphabetic-word floor.
- **Limits.** A single rented A100 PCIe (cloud, no control of the host), with no H100 or large
  consumer GPU. A single large model, served by Ollama with one request at a time: it does not
  measure a node serving in parallel or another engine (vLLM). The local runs have n=23–30 and
  the A100 ones n=98–100, so the local `p99` is almost the maximum.
