---
file_format: mystnb
kernelspec:
  name: python3
mystnb:
  execution_in_temp: true
---

# Error Correction

Use the `encoding` option of {func}`~mqt.bench.get_benchmark` or
{func}`~mqt.bench.get_benchmark_alg` to encode a circuit with Steane's
seven-qubit code or Shor's nine-qubit code. Each logical qubit becomes a data
register plus ancillas for syndrome extraction.

| `encoding` | Data qubits | Syndrome ancillas | Total qubits per logical qubit |
| ---------- | ----------- | ----------------- | ------------------------------ |
| `"steane"` | 7           | 6                 | 13                             |
| `"shor"`   | 9           | 8                 | 17                             |

Encoding applies at `BenchmarkLevel.ALG`. At other levels, the option is ignored
with a `UserWarning`. The default `encoding=""` leaves the circuit unencoded.

## Generate an Encoded Circuit

This example encodes a two-qubit QFT circuit using Steane's code. The result has
26 qubits, including syndrome ancillas.

```{code-cell} ipython3
from mqt.bench import BenchmarkLevel, get_benchmark

circuit = get_benchmark("qft", BenchmarkLevel.ALG, 2, encoding="steane")
circuit.num_qubits
```

The transpiler adds encoding, syndrome extraction, conditional corrections, and
decoding before measurements. Input control flow, resets, and delays raise
`ValueError`. Gates or further measurements on a measured qubit also raise
`ValueError`. Rotations are approximated while decomposing the input into the
code's basis using Qiskit's `approximation_degree=0.95`. Gate counts can
therefore differ between Qiskit versions.

## Opaque Logical Gates

Steane's logical `t` and `tdg` operations become opaque placeholders. Shor's
code also uses a placeholder for logical `h`. Their names follow the form
`<code>_ideal_logical_<gate>`, such as `steane_ideal_logical_t`.

Each placeholder counts as one instruction and has no circuit definition. Its
gate count omits the physical cost of implementing the logical operation.
Circuits containing placeholders require gate definitions for simulation or
compilation, including compilation with MQT Core. OpenQASM 3 and QIR export also
fail when placeholders are present.

## Save as QPY

QPY preserves the placeholders and circuit structure for inspection. Save the
encoded circuit through {func}`~mqt.bench.output.write_circuit`.

```{code-cell} ipython3
from pathlib import Path

from mqt.bench.output import OutputFormat, write_circuit

write_circuit(circuit, Path("encoded.qpy"), BenchmarkLevel.ALG, fmt=OutputFormat.QPY)
```

Load the saved circuit with `qiskit.qpy.load`.
