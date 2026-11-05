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

- `compiler`: `"qiskit"` (default) or `"mqt"`. The algorithm level does not
  compile.
- `opt_level`: Optimization level for `"qiskit"` (`0`-`3`, default `2`). For
  `"mqt"`, this option has no effect.
- `compiler_options`: Core `CompilationOptions` for `compiler="mqt"` at a
  compilation level. Defaults to seed `10` and eight mapping trials.
- `random_parameters`: Assign random parameters to the circuit's parameters if
  they exist.
- `generate_mirror_circuit`: Generate the mirror version (U @ U.inverse()) of
  the benchmark. Final measurements are removed before inversion and added after
  the mirror. Circuits that Qiskit cannot invert, for example those with
  mid-circuit measurements, resets, or unsupported control flow, raise
  `ValueError`. Use `False` to generate these circuits without a mirror.

## MQT Core compiler

MQT Core is installed with MQT Bench. Qiskit remains the default compiler;
select MQT Core with `compiler="mqt"` or `--compiler mqt`.

The development dependency is pinned to a Core Git commit and builds from
source. It requires a C++ compiler; Core downloads its LLVM/MLIR SDK during the
build.

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

All compilers return `QuantumCircuit`. For MQT Core:

- `INDEP` runs the default target-independent optimization pipeline.
- `NATIVEGATES` uses the target's gates and the input width. It ignores device
  placement and returns logical wire order without layout metadata.
- `MAPPED` enforces device capacity, connectivity, and gate placements. It
  returns physical wires without layout metadata and preserves measurement
  destinations.

`opt_level` has no effect on MQT Core. The defaults are seed `10` and eight
mapping trials. `compiler_options`, part of `ConfigurationOptions`, replaces
these defaults and also applies when recompiling mirrors. The benchmark's `seed`
controls circuit generation and parameter binding separately.

In the CLI, use `--compiler-seed` and `--mapping-trials`:

```bash
mqt-bench --compiler mqt --algorithm ghz --num-qubits 3 \
  --level mapped --target iqm_crystal_5 --compiler-seed 17 --mapping-trials 8 --save
```

Targets must provide a supported synthesis basis. Unsupported constraints and
compilation failures raise errors; MQT Core does not fall back to Qiskit or
provide approximate Clifford+T synthesis. See its [target compilation guide] for
supported bases and control flow.

MQT Core output filenames contain `_mqt_`. Circuit metadata and QASM/QPY exports
record the compiler version and effective options.

[target compilation guide]: https://github.com/munich-quantum-toolkit/core/blob/fcad9c4cad29bbdfd08486b034fc099e48fefa2d/docs/mlir/target_compilation.md

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
