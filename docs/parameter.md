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
- `compiler_options`: Core `CompilationOptions` for `compiler="mqt"` at a
  compilation level. Defaults to seed `10` and four mapping trials.
- `random_parameters`: Assign random parameters to the circuit's parameters if
  they exist.
- `generate_mirror_circuit`: Generate the mirror version (U @ U.inverse()) of
  the benchmark.

## MQT Core compiler

Install the optional compiler with `pip install "mqt-bench[mqt]"`. The extra
pins Core's development commit `1a0c32f7cf3e264af9143146bf764fd669aa772d` and
requires Qiskit 2.5.x. Core builds from source and requires a C++20 compiler and
LLVM/MLIR 23.1 or newer; follow [Core's build instructions][core-build] and set
`MLIR_DIR` before installing. The base installation keeps its broader Qiskit
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
import, optimization, native synthesis, and routing use MQT Core. Core handles
permutation gates and preserves parameter identities and vector membership. The
level-specific functions also accept `compiler="mqt"`.

- `INDEP` decomposes multi-controlled operations and runs Core's default
  target-independent optimization pipeline.
- `NATIVEGATES` uses the target's gate set with all-to-all connectivity and the
  input circuit's width. Operations wider than the circuit are omitted; physical
  gate placements are ignored.
- `MAPPED` uses the device's width, connectivity, and ordered gate placements.
  The result uses physical wires. Core does not emit Qiskit `TranspileLayout`
  metadata; measurements retain their classical destinations.

Core supports the bundled IBM, IQM, Quantinuum, IonQ, Rigetti, and
Clifford+T+rotations gate sets. IonQ capabilities use Core's direct GPI, GPI2,
MS, and ZZ targets; their parameters stay in turns. Native input gates retain
their parameters and definitions through repeated compilation. Rigetti pulses
map to fixed RX capabilities, and Bench restores their target names on export.
Core does not provide Qiskit's approximate Clifford+T synthesis. Target
parameters may be independent free parameters or finite fixed values; relations
between parameters are unsupported. Synthesis requires a basis that Core
recognizes, including one arbitrary RX/RY/RZ rotation and a fixed pulse about a
different axis. Other unsupported instructions or synthesis requests raise an
error. Core never falls back to Qiskit transpilation. Dynamic circuits and
structured loops use Core's supported translation and target control-flow
capabilities; Core can unroll loops when required by the target.

Mirrors are formed from the compiled circuit and compiled again with Core when a
target is supplied. The barrier between both halves prevents cancellation. Core
uses its own fixed pipeline; `opt_level=0`, `1`, or `3` raises an error.

Bench sets seed `10` and four mapping trials so defaults do not depend on the
CPU count. To change compiler controls, pass Core's `CompilationOptions`:

```python
from mqt.core.mlir import CompilationOptions, MappingOptions

circuit = get_benchmark(
    "ghz",
    BenchmarkLevel.MAPPED,
    3,
    target=get_device("iqm_crystal_5"),
    compiler="mqt",
    compiler_options=CompilationOptions(
        seed=17,
        mapping=MappingOptions(trials=8, iterations=2, lookahead=10),
    ),
)
```

Options also apply to mirror recompilation. Supplied options replace Bench's
defaults: `CompilationOptions()` uses Core's default seeds and CPU-dependent
trial count. Core also exposes timing, statistics, and routing search-memory
controls. `compiler_options` is rejected with the Qiskit compiler or at the
algorithm level, where no compilation runs. Benchmark-generation `seed` remains
separate from the compilation seed. Fixed options do not promise identical
results across Core versions or platforms.

[core-build]: https://mqt.readthedocs.io/projects/core/en/latest/installation.html#setting-up-mlir

The CLI accepts the same selection:

```bash
mqt-bench --compiler mqt --algorithm ghz --num-qubits 3 \
  --level mapped --target iqm_crystal_5 --save
```

Core filenames contain `_mqt_` and omit Qiskit's optimization level. QASM
headers and QPY metadata record the compiler version. Existing Qiskit filenames
remain unchanged.

## QIR and LLVM output

The `mqt` extra also enables QIR export for circuits generated with either
compiler. QIR uses LLVM IR: `qir` and `llvm` both emit LLVM text (`.ll`), while
`qir-bitcode` emits LLVM bitcode (`.bc`). These files contain quantum runtime
calls and require a compatible QIR runtime to execute.

```bash
# Print LLVM text to stdout; add --save to write a .ll file.
mqt-bench --compiler mqt --algorithm ghz --num-qubits 3 \
  --level indep --output-format qir

# Binary output is always saved; the CLI prints its path.
mqt-bench --compiler mqt --algorithm ghz_dynamic --num-qubits 3 \
  --level indep --output-format qir-bitcode --qir-profile adaptive
```

The existing Python export functions accept the same formats:

```python
from pathlib import Path

from mqt.bench import BenchmarkLevel, get_benchmark
from mqt.bench.output import OutputFormat, write_circuit

circuit = get_benchmark("ghz", BenchmarkLevel.INDEP, 3, compiler="mqt")
write_circuit(circuit, Path("ghz.ll"), BenchmarkLevel.INDEP, OutputFormat.QIR)
write_circuit(
    circuit,
    Path("ghz.bc"),
    BenchmarkLevel.INDEP,
    OutputFormat.QIR_BITCODE,
    qir_profile="base",
)
```

`save_circuit` also accepts `qir_profile`. The default `base` profile handles
static circuits. Select `adaptive` for measurement feedback and supported
classical control flow. Core reports an error when a circuit cannot be lowered
to the chosen profile. Bind all free circuit parameters before QIR export.

Export lowers the supplied circuit through Core without running another
optimization or mapping pipeline. QIR lowering can decompose gates and assign
QIR resource identifiers; the output is not a device-native payload guaranteed
to preserve the target gate set or physical qubit numbering. A runtime must
support the emitted QIS calls, QIR version, and profile capabilities.

LLVM text uses `;` comments for the Bench header and records the QIR exporter
version separately from the circuit compiler. Bitcode contains Core's QIR
metadata but no Bench header. QASM and QPY output remain available without the
`mqt` extra.

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
