---
file_format: mystnb
kernelspec:
  name: python3
mystnb:
  number_source_lines: true
---

```{code-cell} ipython3
:tags: [remove-cell]
%config InlineBackend.figure_formats = ['svg']
```

# Parameter Space

The {func}`~mqt.bench.get_benchmark` function has the following signature:

- `benchmark` (see {doc}`details <benchmark_selection>`):

```{code-cell} ipython3
:tags: [hide-input]
from mqt.bench.benchmarks import get_available_benchmark_names

print(get_available_benchmark_names())
```

- `level`: BenchmarkLevel.ALG, BenchmarkLevel.INDEP, BenchmarkLevel.NATIVEGATES,
  BenchmarkLevel.MAPPED
- `circuit_size`: Define the number of qubits in the circuit.
- `target`: Target, which can also be instantiated based on gatesets using
  `get_target_for_gateset(gateset_name, num_qubits)` or based on a device using
  `get_device(device_name)`. Possible values for `gateset_name`:

```{code-cell} ipython3
:tags: [hide-input]
from mqt.bench.targets import get_available_gateset_names

print(get_available_gateset_names())
```

(required for "nativegates" level)

Native gate-set targets make instructions available on all qubits without device
connectivity or calibration data. Native compilation uses only a target's
instructions, including when the caller supplies a device target. The mapped
level applies the device constraints.

Possible values for `device_name`:

```{code-cell} ipython3
:tags: [hide-input]
from mqt.bench.targets import get_available_device_names

print(get_available_device_names())
```

(required for "mapped" level)

- `opt_level`: Optimization level for `"qiskit"` (`0`-`3`).
- `random_parameters`: Assign random parameters to the circuit's parameters if
  they exist.
- `generate_mirror_circuit`: Generate the mirror version (U @ U.inverse()) of
  the benchmark. Final measurements are removed before inversion and added after
  the mirror. Circuits that Qiskit cannot invert, for example those with
  mid-circuit measurements, resets, or unsupported control flow, raise
  `ValueError`. Use `False` to generate these circuits without a mirror.
- `encoding`: Error correction code applied to the output. Encoding of
  non-transversal gates uses placeholders: opaque logical gadgets named
  `<code>_ideal_logical_<gate>`, for example `shor_ideal_logical_h`. Steane's
  code uses placeholders for T and Tdg. Shor's code also uses one for H.
  OpenQASM 3 export fails for circuits that contain placeholders, so export
  these circuits as QPY. Because the encoding approximates rotations, gate
  counts can differ between Qiskit versions. The generation record stores the
  code name under `encoding`.

Possible values for `encoding`:

```{code-cell} ipython3
:tags: [hide-input]
from mqt.bench.error_correction import get_available_encoding_names

print(get_available_encoding_names())
```

## Native Gate-Set Support

```{code-cell} ipython3
:tags: [hide-input]
from mqt.bench.targets import get_gateset, get_available_gateset_names

for num, gateset_name in enumerate(get_available_gateset_names()):
    print(f"{num+1}: {gateset_name} → {get_gateset(gateset_name)}")
```

Gate angles use radians. Rigetti's `rxpi`, `rxpidg`, `rxpi2`, and `rxpi2dg` fix
RX angles to pi, -pi, pi/2, and -pi/2. Fractional Heron targets accept RZZ
angles in `[0, pi/2]`; bind symbolic parameters before compilation so Qiskit can
fold angles into this interval.

## Device Support

| Device                     | Architecture                  |
| -------------------------- | ----------------------------- |
| `aqt_ibex_12`              | IBEX Q1, all-to-all           |
| `ibm_heron_156`            | Heron, heavy-hex              |
| `ibm_heron_156_fractional` | Heron with [fractional gates] |
| `ibm_nighthawk_120`        | Nighthawk, 12-by-10 grid      |
| `ionq_forte_36`            | Forte, all-to-all             |
| `iqm_crystal_5`            | IQM Spark                     |
| `iqm_crystal_20`           | Garnet                        |
| `iqm_crystal_54`           | Emerald                       |
| `quantinuum_h2_56`         | H2, all-to-all                |
| `rigetti_cepheus_108`      | [Cepheus], 12-by-9 grid       |

See the {doc}`Quickstart <quickstart>` for examples at all four abstraction
levels.

[Cepheus]: https://aws.amazon.com/blogs/quantum-computing/amazon-braket-launches-rigetti-cepheus-1-108q-superconducting-device/
[fractional gates]: https://quantum.cloud.ibm.com/docs/en/guides/fractional-gates
