# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Benchmark registry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from . import _BenchmarkFactory


@dataclass(frozen=True)
class BenchmarkInfo:
    """Benchmark information."""

    factory: _BenchmarkFactory
    description: str = ""


_REGISTRY: dict[str, BenchmarkInfo] = {}


def register_benchmark(benchmark_name: str, description: str = "") -> Callable[[_BenchmarkFactory], _BenchmarkFactory]:
    """Register a benchmark factory under a unique name."""

    def _decorator(func: _BenchmarkFactory) -> _BenchmarkFactory:
        if benchmark_name in _REGISTRY:
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
