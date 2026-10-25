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
- `circuit_size`: Number of qubits in the circuit. IQPE is the exception: it
  always uses two physical qubits and estimates `circuit_size - 1` phase bits.
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

## Benchmark options and sizes

Additional keyword arguments go to the selected benchmark's `create_circuit`
function. For example, use `hidden_string="10"` for BV, `kind="fixed"` for an
adder, or `seed=42` for graph-state generation. See each factory's API page for
its supported options.

All named benchmarks require a positive size. Other constraints are:

| Benchmarks                                                                                 | Size constraint                                                 |
| ------------------------------------------------------------------------------------------ | --------------------------------------------------------------- |
| `bv`, `dj`, `grover`, `qwalk`, `qpeexact`, `qpeinexact`, `iqpe`, `ae`, `superdense_coding` | At least 2                                                      |
| `hhl`                                                                                      | At least 3                                                      |
| `bell`, `bmw_quark_copula`, `simon`                                                        | Positive even size                                              |
| `teleportation`, `seven_qubit_steane_code`, `shors_nine_qubit_code`                        | Positive multiples of 3, 13, and 17, respectively               |
| `shor`                                                                                     | 18, 42, 58, or 74                                               |
| `graphstate`                                                                               | `0 <= degree < circuit_size`, with even `degree * circuit_size` |

Arithmetic widths depend on the adder kind or multiplier. Their factory
reference documents include the register and helper-qubit constraints. Qwalk
depth can be zero but cannot be negative. AE probabilities must lie in `[0, 1]`.
BV and Simon hidden strings must be binary; character `i` corresponds to
classical bit `i`.

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
