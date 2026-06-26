# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Initialization of the benchmark module."""

from __future__ import annotations

import importlib
import importlib.resources as ir
from functools import cache
from typing import TYPE_CHECKING, Any

from ._reference import (
    MetricApplicability,
    NoneReference,
    ObjectiveSpec,
    ReferenceSpec,
    SimulateReference,
    SparseReference,
    UniformReference,
)
from ._registry import (
    benchmark_catalog,
    benchmark_description,
    benchmark_names,
    get_benchmark_by_name,
    get_reference_factory_by_name,
    register_benchmark,
    register_reference,
)
from ._registry import (
    has_reference as _registry_has_reference,
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
    "MetricApplicability",
    "NoneReference",
    "ObjectiveSpec",
    "ReferenceSpec",
    "SimulateReference",
    "SparseReference",
    "UniformReference",
    "create_circuit",
    "get_available_benchmark_names",
    "get_benchmark_catalog",
    "get_benchmark_description",
    "get_reference_spec",
    "has_reference",
    "register_benchmark",
    "register_reference",
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


def has_reference(benchmark_name: str) -> bool:
    """Return ``True`` if a reference spec is available for *benchmark_name*.

    Triggers lazy import of the benchmark module so that the reference registry
    is populated before the check.

    Args:
        benchmark_name: The benchmark to query.
    """
    try:
        _ensure_loaded(benchmark_name)
    except ValueError:
        return False
    return _registry_has_reference(benchmark_name)


@cache
def get_benchmark_description(benchmark_name: str) -> str:
    """Return the benchmark description given a benchmark name."""
    _ensure_loaded(benchmark_name)
    return benchmark_description(benchmark_name)


def get_benchmark_catalog() -> Mapping[str, str]:
    """Return the benchmark catalog given a benchmark name."""
    for benchmark_name in get_available_benchmark_names():
        _ensure_loaded(benchmark_name)
    return benchmark_catalog()


@cache
def _get_factory(benchmark_name: str) -> Callable[..., QuantumCircuit]:
    """Internal factory that can be cached."""
    _ensure_loaded(benchmark_name)
    return get_benchmark_by_name(benchmark_name)


@cache
def _get_reference_factory(benchmark_name: str) -> Callable[..., ReferenceSpec] | None:
    """Internal reference factory cache."""
    _ensure_loaded(benchmark_name)
    return get_reference_factory_by_name(benchmark_name)


# ruff: noqa: ANN401
def get_reference_spec(benchmark_name: str, circuit_size: int, /, *args: Any, **kwargs: Any) -> ReferenceSpec:
    """Return the reference specification for a benchmark instance.

    The spec describes the ideal, noise-free output distribution in a compact
    form that stays poly-size even for exponentially large circuits.  Call
    :meth:`ReferenceSpec.to_dict` on the result to get a JSON-serialisable dict.

    Args:
        benchmark_name: The name of the benchmark (must match the registry key).
        circuit_size: The number of qubits — same value you would pass to
            :func:`create_circuit`.
        *args: Forwarded to the benchmark's ``create_reference`` function.
        **kwargs: Forwarded to the benchmark's ``create_reference`` function.

    Returns:
        ReferenceSpec describing the noise-free output.

    Raises:
        ValueError: If the benchmark name is unknown or has no reference registered.
    """
    if circuit_size <= 0:
        msg = "`circuit_size` must be a positive integer."
        raise ValueError(msg)

    factory = _get_reference_factory(benchmark_name)
    if factory is None:
        msg = (
            f"No reference spec registered for '{benchmark_name}'. "
            "Either the benchmark does not yet have a create_reference function, "
            "or the relevant module has not been imported."
        )
        raise ValueError(msg)
    return factory(circuit_size, *args, **kwargs)


# ruff: noqa: ANN401
def create_circuit(benchmark_name: str, circuit_size: int, /, *args: Any, **kwargs: Any) -> QuantumCircuit:
    """Creates and returns a quantum circuit based on the specified benchmark name and additional arguments.

    The function retrieves the associated factory for the given
    benchmark name and uses it to construct the quantum circuit. If the benchmark
    name is not found, a ValueError is raised with the list of available benchmarks.

    Args:
        benchmark_name: The name of the benchmark to create the circuit for.
        circuit_size: The size of the quantum circuit to create.
        *args: Positional arguments to be passed to the benchmark's factory method.
        **kwargs: Keyword arguments to be passed to the benchmark's factory method.

    Returns:
        QuantumCircuit: A quantum circuit generated by the factory associated with
        the given benchmark name.

    Raises:
        ValueError: If the specified benchmark name is not in the list of available
        benchmarks.
    """
    if circuit_size <= 0:
        msg = "`circuit_size` must be a positive integer when `benchmark` is a str."
        raise ValueError(msg)

    factory = _get_factory(benchmark_name)
    return factory(circuit_size, *args, **kwargs)
