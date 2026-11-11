# Upgrade Guide

This document describes breaking changes and how to upgrade. For a complete list
of changes including minor and patch releases, please refer to the
[changelog](CHANGELOG.md).

## [Unreleased]

### Dependencies

MQT Bench requires MQT Core 4.2 and Qiskit 2.5.2 or newer. Update dependency
pins and upgrade with [uv](https://docs.astral.sh/uv/):

```console
uv pip install --upgrade "mqt-core>=4.2" "qiskit>=2.5.2,<3"
```

Qiskit's Linux wheels require glibc 2.28 or newer. To import OpenQASM 3 with
Qiskit, install `qiskit[qasm3-import]` explicitly; MQT Bench no longer includes
it. QASM 3 export is unchanged.

### Targets and native gates

- Replace `rigetti_ankaa_84` with `rigetti_cepheus_108`.
- Replace the `ionq_aria` gate set with `ionq_forte` and the `ionq_aria_25`
  device with `ionq_forte_36`.
- The `ibm_falcon` and `ibm_eagle` gate sets and `ibm_falcon_27`,
  `ibm_falcon_127`, `ibm_eagle_127`, and `ibm_heron_133` devices are removed.
  Use `ibm_heron` and `ibm_heron_156`, or a custom target for older hardware.
- IonQ GPI/GPI2 phases now use radians: multiply old values in turns by
  `2 * pi`. The custom `MSGate` and `ZZGate` classes are removed; replace
  `ZZGate(theta)` with Qiskit's `RZZGate(2 * pi * theta)`.
- Rigetti uses Qiskit's `RXGate` instead of the custom RX classes, with target
  names `rxpi`, `rxpidg`, `rxpi2`, and `rxpi2dg`. Its entangling gate is now
  `cz` instead of `iswap`.

### Custom target factories

Factories run on every lookup. `register_gateset` factories must return a fresh
list; `register_device` factories must return a fresh target with independent
mutable gates and calibration data. Allocate results inside the factory.

### Benchmark results

- Arithmetic benchmarks measure only the sum or product into `result`. Read
  `pub_result.data.result` instead of `pub_result.data.meas`. Carry-out, when
  present, is the most-significant bit. Mirrors still measure all active qubits.
- HHL adds a `success` register. Read the system bit in `c` only for shots where
  `success[0]` is one.
- IQPE uses ordinary QPE bit order: remove any reversal of result strings.
  Inexact IQPE now selects the same phase as `qpeinexact` with the default seed,
  so previously generated instances differ.
- Fixed-width `vbe_ripple_carry_adder` now handles carry propagation correctly.
  Regenerate reference results for affected inputs.
- QAOA now adds final measurements. Remove extra `measure_all()` calls, or use
  `qc.remove_final_measurements(inplace=True)` to omit measurements.

To measure all arithmetic qubits, apply this before compilation:

```python
qc.remove_final_measurements()
qc.measure_all()
```

### Seeds and input validation

An explicit `seed` now controls both construction and random parameter binding.
Seeded variational circuits therefore have different numeric parameters. Without
an explicit seed, parameter binding still uses seed 10.

Width and option-range checks now raise `ValueError` before construction. In
particular, `bv`, `dj`, `grover`, and `qwalk` require at least two qubits. Use
positive multiples of 13 for `seven_qubit_steane_code` and 17 for
`shors_nine_qubit_code`, and nonnegative depths and repetitions. Check the
[benchmark catalogue](https://mqt.readthedocs.io/projects/bench/en/latest/benchmark_selection.html)
for each factory's constraints.

### Compilation and QASM exports

Target-independent and native circuits retain qubit permutations as gates.
Remove manual permutation corrections from their QASM exports.

`get_target_for_gateset` no longer adds simulated calibration or connectivity.
Native compilation ignores connectivity, calibration, and device capacity,
including for mirrors. Use the mapped level to apply placement constraints.

Qiskit's native Clifford+T compilation uses gridsynth and optimizes after
synthesis at nonzero optimization levels, including in loops and mirrors. The
Solovay-Kitaev fallback is removed. Gate sequences and counts can differ between
Qiskit versions.

Loop jumps use Qiskit's names `break_loop` and `continue_loop` instead of
`break` and `continue`.

Encoded circuits may contain opaque logical gates. See the
[error-correction guide](https://mqt.readthedocs.io/projects/bench/en/latest/error_correction.html)
for the `encoding` option's compilation and export limits.

## [2.3.0]

### Qiskit 2.1 minimum

The minimum Qiskit version increases from **2.0.0 to 2.1.0**, dropping support
for Qiskit 2.0. Upgrade Qiskit to 2.1.0 or newer.

### End of support for Python 3.10

Starting with this release, MQT Bench no longer supports Python 3.10. As a
result, MQT Bench is no longer tested under Python 3.10 and requires Python 3.11
or later.

### macOS support

Starting with this release, x86 macOS is no longer tested in CI; we cannot
guarantee that MQT Bench installs and runs correctly on those systems.

## [2.2.0]

### Dynamic benchmarks and device support for control flow

**Summary:** This release grows the catalog of **dynamic** quantum circuits
(mid-circuit measurement and classical branching). New benchmarks include
**`ghz_dynamic`** (constant-depth GHZ via intermediate measurements and
`if_test`), **`shors_nine_qubit_code`**, and **`seven_qubit_steane_code`**
(syndrome extraction and conditional recovery using control flow).

**Compilation:** Dynamic circuits that use Qiskit control flow (`if_test`,
`IfElseOp`) can be compiled to **every** bundled native gateset and **every**
bundled device target.

**Device models:** All bundled **device** `Target` definitions now declare the
**`if_else`** (IfElse) instruction, so the transpiler can treat dynamic circuits
as mappable to those backends. (IBM-style targets enable this through Qiskit’s
control-flow support on the target; other backends add `IfElseOp` explicitly.)

### Minimum Qiskit version

This release requires **Qiskit 2.0.0 or later**. After upgrading MQT Bench or
pulling an updated `uv.lock`, run **`uv sync`** so your environment matches the
lockfile.

If you already depend on MQT Bench and **only need to refresh Qiskit** (for
example your lockfile still pins Qiskit 1.x), upgrade it in one step:

```bash
uv sync --upgrade-package qiskit
```

That updates the lockfile and installs the new resolution. If you only want to
install what is already locked, use **`uv sync`** without `--upgrade-package`.

### `multiplier` and `vbe_ripple_carry_adder` circuit sizes

Bug fixes changed how `num_state_qubits` is derived from the requested
`num_qubits` / `circuit_size` for the respective benchmarks. As a result,
**generated circuits can have a different width than in 2.1.0** for the same
arguments.

## [2.1.0]

### End of support for Python 3.9

Starting with this release, MQT Bench no longer supports Python 3.9. This is in
line with the scheduled end of life of the version. As a result, MQT Bench is no
longer tested under Python 3.9 and requires Python 3.10 or later.

## [2.0.1]

This release renames the CLI from `mqt.bench.cli` to `mqt-bench`. While we keep
the old CLI for compatibility, we recommend using the new name for future
development. The documentation on how to use the CLI has been rewritten to
reflect this change.

## [2.0.0]

This major release introduces several breaking changes and a redesigned API.
While the codebase remains familiar, several design decisions were made to
improve modularity, extensibility, and alignment with upstream standards. The
following sections describe the most important changes and how to adapt your
code accordingly. We intend to provide a more comprehensive migration guide for
future releases.

### Migration to Qiskit's `Target` Class

**Old:** MQT Bench-specific `Device` and `Gateset` classes.

**New:** Qiskit's
[`Target`](https://docs.quantum.ibm.com/api/qiskit/qiskit.transpiler.Target)
class.

So far, we used our own Device and Gateset classes to represent devices and
native gatesets. In this release, we have switched to using Qiskit's `Target`
class as the intermediate representation for both devices and native gatesets.
This change allows us a more consistent and standardized way to represent
quantum devices and their capabilities, modularity, and extensibility.

Most previously used devices and gatesets are still available, but they are now
provided as `Target` objects. You can retrieve the available names using:

```python
from mqt.bench.targets import get_available_gateset_names, get_available_device_names

gateset_names = get_available_gateset_names()
device_names = get_available_device_names()
```

Similarly, you can retrieve the corresponding `Target` objects by name:

```python
from mqt.bench.targets import get_target_for_gateset, get_device

gateset = get_target_for_gateset("ibm_falcon", num_qubits=5)
device = get_device("ibm_falcon_27")
```

This change allows you to use any device or gateset that is compatible with
Qiskit's `Target` class, providing greater flexibility and compatibility with
other Qiskit components.

## Changes to the `get_benchmark` function

The `get_benchmark` function has been redesigned to provide a more modular and
extensible way to retrieve benchmarks. As a consequence, the function signature
has changed. Please see the
[API documentation](https://mqt.readthedocs.io/projects/bench/en/stable/parameter.html)
for the updated function signature and the examples provided below.

```python
from mqt.bench import get_benchmark, BenchmarkLevel
from mqt.bench.targets import get_target_for_gateset, get_device

benchmark_alg_level = get_benchmark(benchmark="dj", level=BenchmarkLevel.ALG, circuit_size=5)
benchmark_independent_level = get_benchmark(benchmark="dj", level=BenchmarkLevel.INDEP, circuit_size=5)
benchmark_native_gates_level = get_benchmark(
    benchmark="dj",
    level=BenchmarkLevel.NATIVEGATES,
    circuit_size=5,
    target=get_target_for_gateset(name="ionq_forte", num_qubits=5),
    opt_level=2,
)
benchmark_device_level = get_benchmark(
    benchmark="dj",
    level=BenchmarkLevel.MAPPED,
    circuit_size=5,
    target=get_device(name="ionq_forte_36"),
    opt_level=2,
)
```

As shown above, the `level` parameter is now an enum `BenchmarkLevel` instead of
a string or integer.

Additionally, distinct functions are provided for each benchmark level to make
the usage of MQT Bench easier and more intuitive. These functions are also
internally used when calling the `get_benchmark` function.

```python
from mqt.bench import (
    get_benchmark_alg,
    get_benchmark_indep,
    get_benchmark_native_gates,
    get_benchmark_mapped,
)
from mqt.bench.targets import get_target_for_gateset, get_device

benchmark_alg = get_benchmark_alg(benchmark="dj", circuit_size=5)
benchmark_independent = get_benchmark_indep(benchmark="dj", circuit_size=5)
benchmark_native_gates = get_benchmark_native_gates(
    benchmark="dj",
    circuit_size=5,
    target=get_target_for_gateset(name="ionq_forte", num_qubits=5),
    opt_level=2,
)
benchmark_device = get_benchmark_mapped(
    benchmark="dj", circuit_size=5, target=get_device(name="ionq_forte_36"), opt_level=2
)
```

## Removed TKET as a Compiler

With this release, we have removed TKET as a compiler. This allows us to focus
on Qiskit's native compilation capabilities and simplifies the codebase.

## Removed the local MQT Bench server deployment

The local MQT Bench server interface has been removed due to low usage and to
reduce maintenance overhead. This feature was rarely used and added complexity
to the codebase.

### General

MQT Bench has moved to the
[munich-quantum-toolkit](https://github.com/munich-quantum-toolkit) GitHub
organization under <https://github.com/munich-quantum-toolkit/bench>. While most
links should be automatically redirected, please update any links in your code
to point to the new location. All links in the documentation have been updated
accordingly.

<!-- Version links -->

[unreleased]: https://github.com/munich-quantum-toolkit/bench/compare/v2.3.0...HEAD
[2.3.0]: https://github.com/munich-quantum-toolkit/bench/compare/v2.2.3...v2.3.0
[2.2.0]: https://github.com/munich-quantum-toolkit/bench/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/munich-quantum-toolkit/bench/compare/v2.0.1...v2.1.0
[2.0.1]: https://github.com/munich-quantum-toolkit/bench/compare/v2.0.0...v2.0.1
[2.0.0]: https://github.com/munich-quantum-toolkit/bench/compare/v1.1.9...v2.0.0
