# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Benchmark registry."""

from __future__ import annotations

from typing import Callable

from qiskit.circuit import QuantumCircuit

_BenchmarkFactory = Callable[..., QuantumCircuit]
_REGISTRY: dict[str, _BenchmarkFactory] = {}


def register_benchmark(benchmark_name: str) -> Callable[[_BenchmarkFactory], _BenchmarkFactory]:
    """Decorator to register a benchmark factory under a unique `benchmark_name`.

    Arguments:
        benchmark_name: unique identifier for the benchmark (e.g., ``"ae"``).

    Returns:
        The original factory function, unmodified.

    Raises:
        ValueError: if the chosen name is already present in the registry.
    """

    def _decorator(func: _BenchmarkFactory) -> _BenchmarkFactory:
        if benchmark_name in _REGISTRY:  # pragma: no cover
            msg = f"Benchmark name '{benchmark_name}' already registered"
            raise ValueError(msg)
        _REGISTRY[benchmark_name] = func
        return func

    return _decorator


def get_benchmark_by_name(benchmark_name: str) -> _BenchmarkFactory:
    """Return the create_circuit function for a `benchmark_name`.

    Arguments:
        benchmark_name: identifier used during registration.

    Returns:
        create_circuit() function for the benchmark.

    Raises:
        KeyError: if the benchmark name is unknown.
    """
    return _REGISTRY[benchmark_name]


def benchmark_names() -> list[str]:
    """Return all registered benchmark names."""
    return list(_REGISTRY)
