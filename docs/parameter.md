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

Use these options with {func}`~mqt.bench.get_benchmark`.

- `benchmark` (see {doc}`details <benchmark_selection>`):

```{code-cell} ipython3
:tags: [hide-input]
from mqt.bench.benchmarks import get_available_benchmark_names

print(get_available_benchmark_names())
```

- `level`: `BenchmarkLevel.ALG` returns the raw circuit. `INDEP`, `NATIVEGATES`,
  and `MAPPED` compile it.
- `circuit_size`: Number of qubits in the circuit.
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

- `compiler`: `"qiskit"` (default) or `"mqt"`. Applies only at compilation
  levels.
- `opt_level`: Qiskit optimization level (`0`-`3`, default `2`).
- `compiler_options`: Core `CompilationOptions` for `compiler="mqt"` at a
  compilation level.
- `random_parameters`: Bind circuit parameters to random values.
- `generate_mirror_circuit`: Generate the mirror version (U @ U.inverse()) of
  the benchmark. Final measurements are removed before inversion and added after
  the mirror. Circuits that Qiskit cannot invert, for example those with
  mid-circuit measurements, resets, or unsupported control flow, raise
  `ValueError`. Use `False` to generate these circuits without a mirror.

## MQT Core compiler

MQT Bench installs MQT Core. The development pin builds Core from source and
requires a C++ compiler. Core downloads its LLVM/MLIR SDK during the build.

```python
from mqt.bench import BenchmarkLevel, get_benchmark
from mqt.bench.targets import get_device
from mqt.core.mlir import CompilationOptions, MappingOptions

circuit = get_benchmark(
    "ghz",
    BenchmarkLevel.MAPPED,
    3,
    target=get_device("iqm_crystal_5"),
    compiler="mqt",
    compiler_options=CompilationOptions(seed=17, mapping=MappingOptions(trials=8)),
)
```

With MQT Core, `INDEP` optimizes without a target. `NATIVEGATES` uses the
target's gates and returns logical wire order. `MAPPED` enforces device
constraints and returns physical wires with the original measurement
destinations. Both target levels return circuits without layout metadata.

MQT Bench uses compilation seed `10` and eight mapping trials by default.
`compiler_options` replaces these defaults for the benchmark and any mirror
recompilation. The benchmark `seed` controls circuit generation and parameter
binding.

```bash
mqt-bench --compiler mqt --algorithm ghz --num-qubits 3 \
  --level mapped --target iqm_crystal_5 --compiler-seed 17 --mapping-trials 8 --save
```

See the [target compilation guide] for supported bases and control flow. MQT
Core requires an exact decomposition for Clifford+T compilation.

MQT Core output filenames contain `_mqt_`. Circuit metadata and QASM/QPY exports
record the compiler version and requested options.

[target compilation guide]: https://github.com/munich-quantum-toolkit/core/blob/69877d981620219d0bd124af005801f26dd77468/docs/mlir/target_compilation.md

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
