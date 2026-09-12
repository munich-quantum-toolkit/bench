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
  `get_target_for_gateset(gateset_name)` or based on a device using
  `get_device(device_name)`. Possible values for `gateset_name`:

```{code-cell} ipython3
:tags: [hide-input]
from mqt.bench.targets import get_available_gateset_names

print(get_available_gateset_names())
```

(required for "nativegates" level)

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
  `"mqt"`, leave this at `2`; Core uses its own default pipeline.
- `random_parameters`: Assign random parameters to the circuit's parameters if
  they exist.
- `generate_mirror_circuit`: Generate the mirror version (U @ U.inverse()) of
  the benchmark.

## MQT Core compiler

Install the optional compiler with `pip install "mqt-bench[mqt]"`. This requires
MQT Core 4.x and Qiskit 2.5.x. The base installation keeps its broader Qiskit
version support.

```python
from mqt.bench import BenchmarkLevel, get_benchmark
from mqt.bench.targets import get_device

circuit = get_benchmark(
    "ghz",
    BenchmarkLevel.MAPPED,
    3,
    target=get_device("iqm_crystal_5"),
    compiler="mqt",
)
```

The return type remains `QuantumCircuit`. Circuit generation uses Qiskit;
optimization, native synthesis, and routing use MQT Core. The importer converts
permutation gates to swaps with Qiskit's permutation utility before Core import;
Core 4.0 cannot directly import their array parameters. Composite controlled
gates use their existing circuit definitions before Core compilation. The
level-specific functions also accept `compiler="mqt"`.

- `INDEP` decomposes multi-controlled operations and runs Core's default
  target-independent optimization pipeline.
- `NATIVEGATES` uses the target's gate set with all-to-all connectivity and the
  input circuit's width. It ignores physical gate placements.
- `MAPPED` uses the device's width, connectivity, and ordered gate placements.
  The result uses physical wires. Core does not emit Qiskit `TranspileLayout`
  metadata; measurements retain their classical destinations.

Core supports the bundled IBM, IQM, Quantinuum, and Clifford+T+rotations gate
sets. IonQ and Rigetti custom native gates are not supported by this adapter.
Core does not provide Qiskit's approximate Clifford+T synthesis. Unsupported
instructions, parameter restrictions, or synthesis requests raise an error. Core
never falls back to Qiskit transpilation. Dynamic circuits and structured loops
use Core's supported translation and target control-flow capabilities; Core can
unroll loops when required by the target.

Mirrors are formed from the compiled circuit and compiled again with Core when a
target is supplied. The barrier between both halves prevents cancellation. Core
uses its own fixed pipeline; `opt_level=0`, `1`, or `3` raises an error. The
mapper uses Core's default seed and CPU-dependent number of layout trials, so
mapped results can differ across machines.

The CLI accepts the same selection:

```bash
mqt-bench --compiler mqt --algorithm ghz --num-qubits 3 \
  --level mapped --target iqm_crystal_5 --save
```

Core filenames contain `_mqt_` and omit Qiskit's optimization level. QASM
headers and QPY metadata record the compiler version. Existing Qiskit filenames
remain unchanged.

## Native Gate-Set Support

So far, MQT Bench supports the following native gatesets:

```{code-cell} ipython3
:tags: [hide-input]
from mqt.bench.targets import get_gateset, get_available_gateset_names

for num, gateset_name in enumerate(get_available_gateset_names()):
    print(f"{num+1}: {gateset_name} → {get_gateset(gateset_name)}")
```

## Device Support

So far, MQT Bench supports the following devices:

```{code-cell} ipython3
:tags: [hide-input]
from mqt.bench.targets import get_device, get_available_device_names

for num, device_name in enumerate(get_available_device_names()):
    print(f"{num+1}: {device_name} with {get_device(device_name).num_qubits} qubits")
```

Examples how to use the {func}`~.mqt.bench.get_benchmark` method for all four
abstraction levels can be found on the
{doc}`Quickstart jupyter notebook <quickstart>`.
