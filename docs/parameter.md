---
file_format: mystnb
kernelspec:
  name: python3
mystnb:
  number_source_lines: true
---

# Parameter Space

Use {func}`~mqt.bench.get_benchmark` to generate a named benchmark or compile
your own Qiskit circuit.

- **`benchmark` and `circuit_size`**: For a
  {doc}`named benchmark <benchmark_selection>`, supply the size accepted by its
  factory. This is usually the circuit width. For example, `iqpe` uses two
  qubits and runs `circuit_size - 1` iterations. For an existing
  `QuantumCircuit`, omit `circuit_size` or pass `None`.
- **`level` and `target`**: Choose one of the four {doc}`abstraction_levels`.
  `BenchmarkLevel.ALG` returns the algorithmic circuit. `BenchmarkLevel.INDEP`
  optimizes without a hardware target. `BenchmarkLevel.NATIVEGATES` and
  `BenchmarkLevel.MAPPED` both require a Qiskit `Target`. Native compilation
  uses its instructions across the circuit width. Mapped compilation also uses
  its physical qubits and connectivity.
- **`compiler`** selects `"qiskit"` (default) or `"mqt"` at compilation levels.
- **`opt_level`** sets the Qiskit optimization level from 0 to 3 (default 2).
- **`compiler_options`** accepts MQT Core `CompilationOptions` with
  `compiler="mqt"`.
- **`random_parameters` and `seed`**: By default, MQT Bench binds free circuit
  parameters to random angles. Set `random_parameters=False` to skip this
  binding. Bind the angles before compiling to a target that requires numerical
  rotations, such as `clifford+t`. An explicit `seed` controls parameter binding
  and is passed to named benchmark factories that accept it. Without an explicit
  seed, each factory uses its own default and parameter binding uses seed 10.
- **Benchmark options**: Pass options such as `depth` or `hidden_string` as
  keyword arguments when generating a named benchmark. The
  {doc}`catalogue <benchmark_selection>` links to each factory's options and
  size limits.
- **`generate_mirror_circuit`**: Set to `True` to remove final measurements,
  append the inverse circuit, and measure the active qubits. Choose a circuit
  that can be inverted after its final measurements are removed. Mid-circuit
  measurements and resets, for example, prevent inversion and raise
  `ValueError`.

## MQT Core compiler

MQT Bench depends on MQT Core. In a Bench checkout, `uv sync` builds the pinned
Core revision from source. Core needs a C++ compiler and downloads its LLVM/MLIR
SDK during the build.

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

Use `get_target_for_gateset(name, num_qubits)` to construct a native gate-set
target for your circuit width. The available sets and their basis gates are:

```{code-cell} ipython3
:tags: [hide-input]
from mqt.bench.targets import get_gateset, get_available_gateset_names

for name in get_available_gateset_names():
    print(f"{name}: {', '.join(get_gateset(name))}")
```

Gate angles use radians. Rigetti's `rxpi`, `rxpidg`, `rxpi2`, and `rxpi2dg` fix
RX angles to pi, -pi, pi/2, and -pi/2. Fractional Heron targets accept RZZ
angles in `[0, pi/2]`; bind symbolic parameters before compilation so Qiskit can
fold angles into this interval.

## Device Support

Use `get_device(name)` to obtain a target for mapped compilation. The table
lists the built-in devices. `get_available_device_names()` returns the names
available in your installation.

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
