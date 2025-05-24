# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Public wrapper API for level-specific benchmark retrieval in **MQT Bench**."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .benchmark_generation import (
    CompilerSettings,
    QiskitSettings,
    get_benchmark,
)

if TYPE_CHECKING:  # pragma: no cover
    from qiskit.circuit import QuantumCircuit
    from qiskit.transpiler import Target


def get_alg_benchmark(
    benchmark_name: str,
    circuit_size: int | None = None,
    *,
    benchmark_instance_name: str | None = None,
) -> QuantumCircuit:
    """Return an algorithm-level benchmark circuit.

    Arguments:
            benchmark_name: name of the to be generated benchmark
            circuit_size: Input for the benchmark creation, in most cases this is equal to the qubit number
            benchmark_instance_name: Input selection for some benchmarks, namely "shor"

    Returns:
            Qiskit::QuantumCircuit representing the raw benchmark circuit without any hardware-specific compilation or mapping.
    """
    return get_benchmark(
        benchmark_name=benchmark_name,
        level="alg",
        circuit_size=circuit_size,
        benchmark_instance_name=benchmark_instance_name,
    )


def get_indep_benchmark(
    benchmark_name: str,
    circuit_size: int | None = None,
    *,
    benchmark_instance_name: str | None = None,
) -> QuantumCircuit:
    """Return a target-independent benchmark circuit.

    Arguments:
            benchmark_name: name of the to be generated benchmark
            circuit_size: Input for the benchmark creation, in most cases this is equal to the qubit number
            benchmark_instance_name: Input selection for some benchmarks, namely "shor"

    Returns:
            Qiskit::QuantumCircuit expressed in a generic basis gate set, still unmapped to any physical device.
    """
    return get_benchmark(
        benchmark_name=benchmark_name,
        level="indep",
        circuit_size=circuit_size,
        benchmark_instance_name=benchmark_instance_name,
    )


def get_native_gates_benchmark(
    benchmark_name: str,
    circuit_size: int | None = None,
    *,
    benchmark_instance_name: str | None = None,
    opt_level: int = 1,
    target: Target,
) -> QuantumCircuit:
    """Return a benchmark compiled to the target's native gate set.

    Arguments:
            benchmark_name: name of the to be generated benchmark
            circuit_size: Input for the benchmark creation, in most cases this is equal to the qubit number
            benchmark_instance_name: Input selection for some benchmarks, namely "shor"
            opt_level: Optimization level for Qiskit
            target: `~qiskit.transpiler.target.Target` for the benchmark generation

    Returns:
            Qiskit::QuantumCircuit whose operations are restricted to ``target``'s native gate set but are **not** yet qubit-mapped to a concrete device topology.
    """
    settings = CompilerSettings(QiskitSettings(opt_level))
    return get_benchmark(
        benchmark_name=benchmark_name,
        level="nativegates",
        circuit_size=circuit_size,
        benchmark_instance_name=benchmark_instance_name,
        compiler_settings=settings,
        target=target,
    )


def get_mapped_benchmark(
    benchmark_name: str,
    circuit_size: int | None = None,
    *,
    benchmark_instance_name: str | None = None,
    opt_level: int = 1,
    target: Target,
) -> QuantumCircuit:
    """Return a benchmark fully compiled and qubit-mapped to a device.

    Arguments:
            benchmark_name: name of the to be generated benchmark
            circuit_size: Input for the benchmark creation, in most cases this is equal to the qubit number
            benchmark_instance_name: Input selection for some benchmarks, namely "shor"
            opt_level: Optimization level for Qiskit
            target: `~qiskit.transpiler.target.Target` for the benchmark generation

    Returns:
            Qiskit::QuantumCircuit that has been decomposed and routed onto the topology described by ``target``.
    """
    settings = CompilerSettings(QiskitSettings(opt_level))
    return get_benchmark(
        benchmark_name=benchmark_name,
        level="mapped",
        circuit_size=circuit_size,
        benchmark_instance_name=benchmark_instance_name,
        compiler_settings=settings,
        target=target,
    )
