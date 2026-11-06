# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Initialization of the benchmark module."""

# ruff: file-ignore[non-empty-init-module]

from __future__ import annotations

import importlib
import importlib.resources as ir
from functools import cache
from inspect import Parameter, signature
from typing import TYPE_CHECKING, Any

from ._registry import (
    benchmark_catalog,
    benchmark_description,
    benchmark_names,
    get_benchmark_by_name,
    register_benchmark,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from qiskit.circuit import QuantumCircuit


_DISCOVERED_BENCHMARKS: set[str] = {
    entry.name.removesuffix(".py")
    for entry in ir.files(__name__).iterdir()
    if entry.is_file() and entry.name.endswith(".py") and not entry.name.startswith("_")
}

_IMPORTED_BENCHMARKS: set[str] = set()

__all__ = [
    "create_circuit",
    "get_available_benchmark_names",
    "get_benchmark_catalog",
    "get_benchmark_description",
    "register_benchmark",
]


def _ensure_loaded(benchmark_name: str) -> None:
    """Ensures that the specified benchmark is loaded and registered.

    If the benchmark is already registered, the function exits early. If the benchmark
    is not supported or cannot be found, a ValueError is raised. Otherwise, the module
    corresponding to the benchmark is imported, triggering its registration.

    Args:
        benchmark_name (str): The name of the benchmark to ensure is loaded. It must be a valid and supported benchmark name.

    Raises:
        ValueError: If the provided benchmark name is not supported or not available in the discovered benchmarks.
    """
    if benchmark_name in benchmark_names():
        return  # already imported and registered

    if benchmark_name not in _DISCOVERED_BENCHMARKS:
        msg = (
            f"'{benchmark_name}' is not a supported benchmark. Available benchmarks: {get_available_benchmark_names()}"
        )
        raise ValueError(msg)

    if benchmark_name not in _IMPORTED_BENCHMARKS:
        importlib.import_module(f"{__name__}.{benchmark_name}")
        _IMPORTED_BENCHMARKS.add(benchmark_name)


def get_available_benchmark_names() -> list[str]:
    """Return a list of available benchmark names."""
    return sorted(_DISCOVERED_BENCHMARKS | set(benchmark_names())).copy()


@cache
def get_benchmark_description(benchmark_name: str) -> str:
    """Return the benchmark description given a benchmark name."""
    _ensure_loaded(benchmark_name)
    return benchmark_description(benchmark_name)


def get_benchmark_catalog() -> Mapping[str, str]:
    """Return a mapping of benchmark names to their descriptions."""
    for benchmark_name in get_available_benchmark_names():
        _ensure_loaded(benchmark_name)
    return benchmark_catalog()


@cache
def _get_factory(benchmark_name: str) -> Callable[..., QuantumCircuit]:
    """Internal factory that can be cached."""
    _ensure_loaded(benchmark_name)
    return get_benchmark_by_name(benchmark_name)


# ruff:file-ignore[any-type]
def create_circuit(benchmark_name: str, circuit_size: int, /, *args: Any, **kwargs: Any) -> QuantumCircuit:
    """Call the factory for a named benchmark.

    Args:
        benchmark_name: Registered benchmark name.
        circuit_size: Positive size accepted by the factory.
        *args: Additional positional arguments for the factory.
        **kwargs: Factory options. Factories that do not accept a seed ignore it.

    Returns:
        The circuit produced by the selected benchmark factory.

    Raises:
        ValueError: If the specified benchmark name is not available.
    """
    if circuit_size <= 0:
        msg = "`circuit_size` must be a positive integer when `benchmark` is a str."
        raise ValueError(msg)

    factory = _get_factory(benchmark_name)
    if "seed" in kwargs:
        parameters = signature(factory).parameters
        if "seed" not in parameters and not any(p.kind == Parameter.VAR_KEYWORD for p in parameters.values()):
            kwargs.pop("seed")
    return factory(circuit_size, *args, **kwargs)
