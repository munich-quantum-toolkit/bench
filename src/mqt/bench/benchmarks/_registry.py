# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Benchmark registry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

from qiskit.circuit import QuantumCircuit

if TYPE_CHECKING:
    from collections.abc import Mapping

_BenchmarkFactory = Callable[..., QuantumCircuit]


@dataclass(frozen=True)
class BenchmarkInfo:
    """Benchmark information."""

    factory: _BenchmarkFactory
    description: str = ""


_REGISTRY: dict[str, BenchmarkInfo] = {}


def register_benchmark(benchmark_name: str, description: str = "") -> Callable[[_BenchmarkFactory], _BenchmarkFactory]:
    """Decorator to register a benchmark factory under a unique `benchmark_name`.

    Arguments:
        benchmark_name: unique identifier for the benchmark (e.g., ``"ae"``).
        description: One-line description.

    Returns:
        The original factory function, unmodified.

    Raises:
        ValueError: if the chosen name is already present in the registry.
    """

    def _decorator(func: _BenchmarkFactory) -> _BenchmarkFactory:
        if benchmark_name in _REGISTRY:  # pragma: no cover
            msg = f"Benchmark name '{benchmark_name}' already registered"
            raise ValueError(msg)
        _REGISTRY[benchmark_name] = BenchmarkInfo(func, description)
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
    return _REGISTRY[benchmark_name].factory


def benchmark_description(benchmark_name: str) -> str:
    """Return the description for a benchmark.

    Arguments:
        benchmark_name: identifier used during registration.

    Returns:
        the benchmark description.
    """
    return _REGISTRY[benchmark_name].description


def benchmark_names() -> list[str]:
    """Return all registered benchmark names."""
    return list(_REGISTRY)


def benchmark_catalog() -> Mapping[str, str]:
    """Mapping *name → description* to feed into a CLI help table, GUI, etc."""
    return {name: info.description for name, info in _REGISTRY.items()}
