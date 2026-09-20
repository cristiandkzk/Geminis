# Test 6 · The budget of the compute challenge

**English** · [Español](README.es.md)

> Status: **run on two machines** (local GTX 1660 SUPER and A100 80GB PCIe on Modal, five
> runs). Which model and hardware count as the reference is still to be decided. See
> RESULTS.md, §6.7.1 and the open problem of §10.3.

What §6.7.1 asks for: measure how long a compute node takes to produce **one valid
attempt** at the challenge —an inference pass with the `nonce` inside the prompt,
plus the structural filter of §6.7— in order to derive `X` (the floor of the round
window `T`). `Y` does not come out of this measurement: it is bounded by coherence
with `Δ` and with the challenge window of §6.3, not by the latency of a model.

## Why it does not run on the phone, unlike Tests 2 and 5

§6.1 separates two classes of node on purpose: PoD nodes verify and have to fit on
any hardware —hence Test 2 measuring on a Motorola Edge 40 Neo—, but **compute nodes
are GPU and RAM**, a competitive and expensive market by design. Measuring `X` on a
phone would be measuring the wrong class of node: the challenge of §6.7 is run by
compute nodes, not PoD nodes, and its reference hardware has to be the one that will
actually compete.

## What exactly it measures

One attempt at the challenge: it builds a prompt with a domain seed (language + topic
+ schema) and a `nonce`, sends it to a real model through an OpenAI-compatible API
(`/v1/chat/completions` — works with Ollama, vLLM, TGI, llama.cpp server, or any
hosted provider), times the response, and runs the reference structural filter over
the output: valid JSON, nonce repeated verbatim, minimum length, proportion of
alphabetic words above a floor, no degenerate repetition.

**This script's filter is a placeholder, not the final specification.** The production
version uses a dictionary published on-chain (§6.7); here a heuristic check is enough
so as not to confuse the latency of generating noise with that of generating a real
answer.

It runs several different domains in the same batch to see whether the type of task
moves the latency — it matters because §6.7 rotates the domain from round to round,
and if the latency varies a lot between domains, `X` has to protect against the
slowest domain, not against the average.

## How to run it

It needs a real inference server running, pointed at by `--endpoint`. With Ollama,
for example:

```
ollama serve
ollama pull <chosen-reference-model>
python medicion.py --endpoint http://localhost:11434/v1/chat/completions \
                    --model <chosen-reference-model> \
                    --intentos 30 --warmup 3
```

No external dependencies — only `urllib` from the standard library, so as not to tie
it to whichever HTTP client each machine happens to have installed.

## On a large GPU (Modal)

`modal_gpu.py` runs the measurements on an 80 GB A100 rented on Modal, without touching
`medicion.py`: it starts Ollama in a container, downloads each model once into a volume and
runs `medicion.py` against localhost inside the same container, so the network does not enter
the latency. It pins the Ollama version (`OLLAMA_TAG`, the same as in the local measurements),
the context at 4096 and one request at a time, and marks as invalid any row where the model does
not end up 100% on GPU.

```
pip install modal
python -m modal setup
python -m modal run modal_gpu.py            # llama3.1:8b, mistral:7b and llama3.1:70b, 100 attempts
python -m modal run modal_gpu.py --modelos llama3.1:8b --intentos 30
```

For another GPU, set `TEST6_GPU` (for example `H100`) before running. **Modal requires a payment
method on file to use any GPU**, although the free credit of the Starter plan ($30/month) is
applied first. The full run took about 35 minutes, which at $2.50/h for the A100 80GB is ~$1.50
as an upper bound (the real spend is in Modal's dashboard). Each run has a hard 2-hour cutoff.
Outputs land in `resultados-gpu/`.

## What has to be decided before the number means anything

The script measures latency; it does not decide which model to run. That decision is
the one left open in §10.3: what counts as the reference node whose worst case `X`
protects. Running it with several models of different sizes, on the "large" hardware
the project is going to treat as the admissible floor, is what gives that decision its
content — a single model is not enough, for the same reason two machines were not
enough for the hardware floor of §10.1.

## Output

Latency percentiles (p50/p90/p99/worst case) over the attempts that pass the filter,
the rate of attempts that pass it, and the conversion to blocks with
`tiempo_de_bloque = 6 s` (the value already fixed in §10.3) — a configurable parameter
in case that value changes. Dump the result into `RESULTS.md` together with which
model and which hardware it was run on.
