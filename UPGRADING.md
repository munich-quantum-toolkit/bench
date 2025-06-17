# Upgrade Guide

This document describes breaking changes and how to upgrade. For a complete list of changes including minor and patch releases, please refer to the [changelog](CHANGELOG.md).

## [Unreleased]

## [2.0.0]

This major release introduces several breaking changes and a redesigned API. While the codebase remains familiar, several design decisions were made to improve modularity, extensibility, and alignment with upstream standards.
The following sections describe the most important changes and how to adapt your code accordingly.
We intend to provide a more comprehensive migration guide for future releases.

### Migration to Qiskit's `Target` Class

**Old:** MQT Bench-specific `Device` and `Gateset` classes.

**New:** Qiskit's [`Target`](https://docs.quantum.ibm.com/api/qiskit/qiskit.transpiler.Target) class.

So far, we used our own Device and Gateset classes to represent devices and native gatesets.
In this release, we have switched to using Qiskit's `Target` class as the intermediate representation for both devices and native gatesets.
This change allows us a more consistent and standardized way to represent quantum devices and their capabilities, modularity, and extensibility.

Most previously used devices and gatesets are still available, but they are now provided as `Target` objects.
You can retrieve the available names using:

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

This change allows you to use any device or gateset that is compatible with Qiskit's `Target` class, providing greater flexibility and compatibility with other Qiskit components.

## Changes to the `get_benchmark` function

The `get_benchmark` function has been redesigned to provide a more modular and extensible way to retrieve benchmarks.
As a consequence, the function signature has changed.
Please see the [API documentation](https://mqt.readthedocs.io/projects/bench/en/latest/parameter.html) for the updated function signature and the examples provided below.

```python
from mqt.bench import get_benchmark, BenchmarkLevel
from mqt.bench.targets import get_target_for_gateset, get_device

benchmark_alg_level = get_benchmark(
    benchmark="dj", level=BenchmarkLevel.ALG, circuit_size=5
)
benchmark_independent_level = get_benchmark(
    benchmark="dj", level=BenchmarkLevel.INDEP, circuit_size=5
)
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

As shown above, the `level` parameter is now an enum `BenchmarkLevel` instead of a string or integer.

Additionally, distinct functions are provided for each benchmark level to make the usage of MQT Bench easier and more intuitive.
These functions are also internally used when calling the `get_benchmark` function.

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

With this release, we have removed TKET as a compiler.
This allows us to focus on Qiskit's native compilation capabilities and simplifies the codebase.

## Removed the local MQT Bench server deployment

The local MQT Bench server interface has been removed due to low usage and to reduce maintenance overhead.
This feature was rarely used and added complexity to the codebase.

### General

MQT Bench has moved to the [munich-quantum-toolkit](https://github.com/munich-quantum-toolkit) GitHub organization under https://github.com/munich-quantum-toolkit/bench.
While most links should be automatically redirected, please update any links in your code to point to the new location.
All links in the documentation have been updated accordingly.

[unreleased]: https://github.com/munich-quantum-toolkit/bench/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/munich-quantum-toolkit/bench/compare/v1.1.9...v2.0.0
