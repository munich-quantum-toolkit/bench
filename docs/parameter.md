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
  `"mqt"`, leave this at `2`; Core uses its own default pipeline.
- `compiler_options`: Core `CompilationOptions` for `compiler="mqt"` at a
  compilation level. Defaults to seed `10` and four mapping trials.
- `random_parameters`: Assign random parameters to the circuit's parameters if
  they exist.
- `generate_mirror_circuit`: Generate the mirror version (U @ U.inverse()) of
  the benchmark. Final measurements are removed before inversion and added after
  the mirror. Circuits that Qiskit cannot invert, for example those with
  mid-circuit measurements, resets, or unsupported control flow, raise
  `ValueError`. Use `False` to generate these circuits without a mirror.

## MQT Core compiler

Install the optional compiler with `pip install "mqt-bench[mqt]"`. The extra
installs MQT Core 4.1.1 and Qiskit 2.5.x. Core wheels include the compiler
runtime. Qiskit remains the default compiler, and both compilers return
`QuantumCircuit`.

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

The level-specific functions also accept `compiler="mqt"`:

- `INDEP` decomposes multi-controlled operations and runs Core's default
  target-independent optimization pipeline.
- `NATIVEGATES` uses the target's gate set with all-to-all connectivity and the
  input circuit's width. Operations wider than the circuit are omitted; physical
  gate placements are ignored. The result retains layout metadata needed to
  interpret its logical wire order; use `Operator.from_circuit` for its unitary.
- `MAPPED` uses the device's width, connectivity, and ordered gate placements.
  The result uses physical wires without layout metadata; measurements retain
  their classical destinations. Recompilation treats the current wires as
  inputs.

Core supports the bundled IBM, IQM, Quantinuum, IonQ, AQT, Rigetti, and
Clifford+T+rotations gate sets. The target must supply a synthesis basis that
Core supports, including an entangling gate for multi-qubit compilation, even
for already-native inputs. Unsupported target constraints raise an error. Core
does not provide Qiskit's approximate Clifford+T synthesis or fall back to
Qiskit transpilation. See Core's [target compilation guide] for synthesis and
control-flow support.

All MQT Bench gate parameters use radians. IonQ targets include GPI, GPI2, RZZ,
and arbitrary virtual RZ. Virtual RZ represents a phase-frame update; a provider
submission layer must absorb it into GPI/GPI2 gate phases when required by the
provider. MQT Bench returns compiler-level circuits and does not submit them to
hardware.

Mirrors are formed from the compiled circuit and compiled again with Core when a
target is supplied. The barrier between both halves prevents cancellation. Core
uses its own fixed pipeline; `opt_level=0`, `1`, or `3` raises an error.

MQT Bench sets seed `10` and four mapping trials so defaults do not depend on
the CPU count. Python `compiler_options` replace these defaults and also apply
to mirror recompilation. A bare `CompilationOptions()` uses Core's defaults,
including a CPU-dependent trial count. These options require the MQT compiler at
a compilation level. The benchmark-generation seed is separate from the
compilation seed. Fixed options do not guarantee identical results across Core
versions or platforms.

The CLI exposes `--compiler-seed` and `--mapping-trials`. Omitted values retain
MQT Bench's defaults:

```bash
mqt-bench --compiler mqt --algorithm ghz --num-qubits 3 \
  --level mapped --target iqm_crystal_5 --compiler-seed 17 --mapping-trials 8 --save
```

Core filenames contain `_mqt_` and omit Qiskit's optimization level. QASM
headers and QPY metadata record the compiler version. Existing Qiskit filenames
remain unchanged.

[target compilation guide]: https://github.com/munich-quantum-toolkit/core/blob/v4.1.1/docs/mlir/target_compilation.md

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

LLVM text uses `;` comments for the MQT Bench header and records the QIR
exporter version separately from the circuit compiler. Bitcode contains Core's
QIR metadata but no MQT Bench header. QASM and QPY output remain available
without the `mqt` extra.

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
