"""Benchmark registry."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from qiskit.circuit import QuantumCircuit

from ._reference import ReferenceSpec

if TYPE_CHECKING:
    from collections.abc import Mapping

_BenchmarkFactory = Callable[..., QuantumCircuit]
_ReferenceFactory = Callable[..., ReferenceSpec]


@dataclass(frozen=True)
class BenchmarkInfo:
    """Benchmark information."""

    factory: _BenchmarkFactory
    description: str = ""


_REGISTRY: dict[str, BenchmarkInfo] = {}
_REFERENCE_REGISTRY: dict[str, _ReferenceFactory] = {}


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


def register_reference(benchmark_name: str) -> Callable[[_ReferenceFactory], _ReferenceFactory]:
    """Decorator to register a reference-spec factory for *benchmark_name*.

    The decorated function must accept the same positional/keyword arguments as
    the corresponding ``create_circuit`` factory and return a
    :class:`~._reference.ReferenceSpec`.

    Arguments:
        benchmark_name: registry key of the benchmark to attach the spec to.

    Returns:
        The original function.
    """

    def _decorator(func: _ReferenceFactory) -> _ReferenceFactory:
        _REFERENCE_REGISTRY[benchmark_name] = func
        return func

    return _decorator


def get_reference_factory_by_name(benchmark_name: str) -> _ReferenceFactory | None:
    """Return the ``create_reference`` function for *benchmark_name*, or ``None``.

    Arguments:
        benchmark_name: identifier used during registration.
    """
    return _REFERENCE_REGISTRY.get(benchmark_name)


def has_reference(benchmark_name: str) -> bool:
    """Return ``True`` if a reference spec is registered for *benchmark_name*."""
    return benchmark_name in _REFERENCE_REGISTRY
