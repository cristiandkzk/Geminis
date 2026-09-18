# Test 6 · The budget of the compute challenge

> Status: **not run.**

## What is missing before a number here means anything

1. **Choosing the reference model (or models).** §10.3 makes it explicit that this is not a pure
   measurement: it is first a decision about which compute node counts as the legitimate worst case
   that `X` has to keep letting compete. A single model is not enough to fix it, just as two
   machines were not enough for the hardware floor of §10.1.
2. **Getting hold of the "large" hardware** to compare against — this folder runs on any machine
   with reasonable GPU/RAM via `--endpoint`, but the high end of the range (datacenter GPU) has not
   been run yet.
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
