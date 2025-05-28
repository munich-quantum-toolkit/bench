# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Module for the benchmark generation and benchmark retrieval."""

from __future__ import annotations

from enum import Enum, auto
from importlib import import_module
from typing import TYPE_CHECKING, overload

import numpy as np
from qiskit import generate_preset_pass_manager
from qiskit.circuit import QuantumCircuit, SessionEquivalenceLibrary
from qiskit.compiler import transpile
from qiskit.transpiler import Target
from typing_extensions import assert_never

from .targets.gatesets import get_target_for_gateset, ionq, rigetti

if TYPE_CHECKING:  # pragma: no cover
    from types import ModuleType

    from qiskit.transpiler import Target


class BenchmarkLevel(Enum):
    """Enum representing different levels."""

    ALG = auto()
    INDEP = auto()
    NATIVEGATES = auto()
    MAPPED = auto()


def get_supported_benchmarks() -> list[str]:
    """Returns a list of all supported benchmarks."""
    return [
        "ae",
        "bv",
        "dj",
        "ghz",
        "graphstate",
        "grover",
        "qaoa",
        "qft",
        "qftentangled",
        "qnn",
        "qpeexact",
        "qpeinexact",
        "bmw_quark_cardinality",
        "bmw_quark_copula",
        "qwalk",
        "randomcircuit",
        "shor",
        "vqe_real_amp",
        "vqe_su2",
        "vqe_two_local",
        "wstate",
    ]


def get_module_for_benchmark(benchmark_name: str) -> ModuleType:
    """Returns the module for a specific benchmark."""
    return import_module("mqt.bench.benchmarks." + benchmark_name)


def _get_circuit(
    benchmark: str | QuantumCircuit,
    circuit_size: int | None,
    random_parameters: bool = True,
) -> QuantumCircuit:
    """Creates a raw quantum circuit based on the specified benchmark.

    This function generates a quantum circuit according to the specifications of the
    desired benchmark.

    Arguments:
        benchmark: Name of the benchmark for which the circuit is to be created.
        circuit_size: Size of the circuit to be created, required for benchmarks other than "shor".
        random_parameters: If True, assigns random parameters to the circuit's parameters if they exist.

    Returns:
        QuantumCircuit: Constructed quantum circuit based on the given parameters.
    """
    if isinstance(benchmark, QuantumCircuit):
        if circuit_size is not None:
            msg = "`circuit_size` must be omitted or None when `benchmark` is a QuantumCircuit."
            raise ValueError(msg)
        qc = benchmark
    else:
        if circuit_size is None or circuit_size <= 0:
            msg = "`circuit_size` must be a positive integer when `benchmark` is a str."
            raise ValueError(msg)

        if benchmark not in get_supported_benchmarks():
            msg = f"'{benchmark}' is not a supported benchmark. Valid names: {get_supported_benchmarks()}"
            raise ValueError(msg)

        lib = get_module_for_benchmark(benchmark)
        qc = lib.create_circuit(circuit_size)

    if len(qc.parameters) > 0 and random_parameters:
        rng = np.random.default_rng(10)
        param_dict = {param: rng.uniform(0, 2 * np.pi) for param in qc.parameters}
        qc.assign_parameters(param_dict, inplace=True)

    assert len(qc.parameters) == 0, "Parameters should be empty after assignment."
    return qc


def _validate_opt_level(opt_level: int) -> None:
    """Validate optimization level.

    Arguments:
        opt_level: User-defined optimization level.
    """
    if not 0 <= opt_level <= 3:
        msg = f"Invalid `opt_level` '{opt_level}'. Must be in the range [0, 3]."
        raise ValueError(msg)


@overload
def get_benchmark_alg(
    benchmark: str,
    circuit_size: int,
    random_parameters: bool = True,
) -> QuantumCircuit: ...


@overload
def get_benchmark_alg(
    benchmark: QuantumCircuit,
    circuit_size: None = None,
    random_parameters: bool = True,
) -> QuantumCircuit: ...


def get_benchmark_alg(
    benchmark: str | QuantumCircuit,
    circuit_size: int | None = None,
    random_parameters: bool = True,
) -> QuantumCircuit:
    """Return an algorithm-level benchmark circuit.

    Arguments:
            benchmark: QuantumCircuit or name of the benchmark to be generated
            circuit_size: Input for the benchmark creation, in most cases this is equal to the qubit number
            random_parameters: If True, assigns random parameters to the circuit's parameters if they exist.

    Returns:
            Qiskit::QuantumCircuit representing the raw benchmark circuit without any hardware-specific compilation or mapping.
    """
    return _get_circuit(benchmark, circuit_size, random_parameters)


@overload
def get_benchmark_indep(
    benchmark: str,
    circuit_size: int,
    opt_level: int = 2,
    random_parameters: bool = True,
) -> QuantumCircuit: ...


@overload
def get_benchmark_indep(
    benchmark: QuantumCircuit,
    circuit_size: None = None,
    opt_level: int = 2,
    random_parameters: bool = True,
) -> QuantumCircuit: ...


def get_benchmark_indep(
    benchmark: str | QuantumCircuit,
    circuit_size: int | None = None,
    opt_level: int = 2,
    random_parameters: bool = True,
) -> QuantumCircuit:
    """Return a target-independent benchmark circuit.

    Arguments:
            benchmark: QuantumCircuit or name of the benchmark to be generated
            circuit_size: Input for the benchmark creation, in most cases this is equal to the qubit number
            opt_level: Optimization level to be used by the transpiler.
            random_parameters: If True, assigns random parameters to the circuit's parameters if they exist.

    Returns:
            Qiskit::QuantumCircuit expressed in a generic basis gate set, still unmapped to any physical device.
    """
    _validate_opt_level(opt_level)

    circuit = _get_circuit(benchmark, circuit_size, random_parameters)
    return transpile(circuit, optimization_level=opt_level, seed_transpiler=10)


@overload
def get_benchmark_native_gates(
    benchmark: str,
    circuit_size: int,
    target: Target,
    opt_level: int = 2,
    random_parameters: bool = True,
) -> QuantumCircuit: ...


@overload
def get_benchmark_native_gates(
    benchmark: QuantumCircuit,
    circuit_size: None,
    target: Target,
    opt_level: int = 2,
    random_parameters: bool = True,
) -> QuantumCircuit: ...


def get_benchmark_native_gates(
    benchmark: str | QuantumCircuit,
    circuit_size: int | None,
    target: Target,
    opt_level: int = 2,
    random_parameters: bool = True,
) -> QuantumCircuit:
    """Return a benchmark compiled to the target's native gate set.

    Arguments:
            benchmark: QuantumCircuit or name of the benchmark to be generated
            circuit_size: Input for the benchmark creation, in most cases this is equal to the qubit number
            target: `~qiskit.transpiler.target.Target` for the benchmark generation
            opt_level: Optimization level to be used by the transpiler.
            random_parameters: If True, assigns random parameters to the circuit's parameters if they exist.

    Returns:
            Qiskit::QuantumCircuit whose operations are restricted to ``target``'s native gate set but are **not** yet qubit-mapped to a concrete device connectivity.
    """
    _validate_opt_level(opt_level)

    circuit = _get_circuit(benchmark, circuit_size, random_parameters)

    if target.description == "clifford+t":
        from qiskit.transpiler import PassManager  # noqa: PLC0415
        from qiskit.transpiler.passes.synthesis import SolovayKitaev  # noqa: PLC0415

        # Transpile the circuit to single- and two-qubit gates including rotations
        clifford_t_rotations = get_target_for_gateset("clifford+t+rotations", num_qubits=circuit.num_qubits)
        compiled_for_sk = transpile(
            circuit,
            target=clifford_t_rotations,
            optimization_level=opt_level,
            seed_transpiler=10,
        )
        # Synthesize the rotations to Clifford+T gates
        # Measurements are removed and added back after the synthesis to avoid errors in the Solovay-Kitaev pass
        pm = PassManager(SolovayKitaev())
        circuit = pm.run(compiled_for_sk.remove_final_measurements(inplace=False))
        circuit.measure_all()

    if "rigetti" in target.description:
        rigetti.add_equivalences(SessionEquivalenceLibrary)
    elif "ionq" in target.description:
        ionq.add_equivalences(SessionEquivalenceLibrary)
    pm = generate_preset_pass_manager(optimization_level=opt_level, target=target, seed_transpiler=10)
    pm.layout = None
    pm.routing = None
    pm.scheduling = None

    return pm.run(circuit)


@overload
def get_benchmark_mapped(
    benchmark: str,
    circuit_size: int,
    target: Target,
    opt_level: int = 2,
    random_parameters: bool = True,
) -> QuantumCircuit: ...


@overload
def get_benchmark_mapped(
    benchmark: QuantumCircuit,
    circuit_size: None,
    target: Target,
    opt_level: int = 2,
    random_parameters: bool = True,
) -> QuantumCircuit: ...


def get_benchmark_mapped(
    benchmark: str | QuantumCircuit,
    circuit_size: int | None,
    target: Target,
    opt_level: int = 2,
    random_parameters: bool = True,
) -> QuantumCircuit:
    """Return a benchmark fully compiled and qubit-mapped to a device.

    Arguments:
            benchmark: QuantumCircuit or name of the benchmark to be generated
            circuit_size: Input for the benchmark creation, in most cases this is equal to the qubit number
            target: `~qiskit.transpiler.target.Target` for the benchmark generation
            opt_level: Optimization level to be used by the transpiler.
            random_parameters: If True, assigns random parameters to the circuit's parameters if they exist.

    Returns:
            Qiskit::QuantumCircuit that has been decomposed and routed onto the connectivity described by ``target``.
    """
    _validate_opt_level(opt_level)

    circuit = _get_circuit(benchmark, circuit_size, random_parameters)

    if "rigetti" in target.description:
        rigetti.add_equivalences(SessionEquivalenceLibrary)
    elif "ionq" in target.description:
        ionq.add_equivalences(SessionEquivalenceLibrary)

    return transpile(
        circuit,
        target=target,
        optimization_level=opt_level,
        seed_transpiler=10,
    )


@overload
def get_benchmark(
    benchmark: str,
    level: BenchmarkLevel,
    circuit_size: int,
    target: Target | None = None,
    opt_level: int = 2,
) -> QuantumCircuit: ...


@overload
def get_benchmark(
    benchmark: QuantumCircuit,
    level: BenchmarkLevel,
    circuit_size: None,
    target: Target | None = None,
    opt_level: int = 2,
) -> QuantumCircuit: ...


def get_benchmark(
    benchmark: str | QuantumCircuit,
    level: BenchmarkLevel,
    circuit_size: int | None = None,
    target: Target | None = None,
    opt_level: int = 2,
) -> QuantumCircuit:
    """Returns one benchmark as a qiskit.QuantumCircuit object.

    Arguments:
        benchmark: QuantumCircuit or name of the benchmark to be generated
        level: Choice of level, either as a string ("alg", "indep", "nativegates" or "mapped") or as a number between 0-3 where 0 corresponds to "alg" level and 3 to "mapped" level
        circuit_size: Input for the benchmark creation, in most cases this is equal to the qubit number
        target: `~qiskit.transpiler.target.Target` for the benchmark generation (only used for "nativegates" and "mapped" level)
        opt_level: Optimization level to be used by the transpiler.

    Returns:
        Qiskit::QuantumCircuit object representing the benchmark with the selected options
    """
    if level is BenchmarkLevel.ALG:
        return get_benchmark_alg(
            benchmark,
            circuit_size=circuit_size,
        )
    if level is BenchmarkLevel.INDEP:
        return get_benchmark_indep(
            benchmark,
            circuit_size,
            opt_level,
        )
    if level is BenchmarkLevel.NATIVEGATES:
        return get_benchmark_native_gates(
            benchmark,
            circuit_size,
            target,
            opt_level,
        )
    if level is BenchmarkLevel.MAPPED:
        return get_benchmark_mapped(
            benchmark,
            circuit_size,
            target,
            opt_level,
        )

    assert_never(level)
