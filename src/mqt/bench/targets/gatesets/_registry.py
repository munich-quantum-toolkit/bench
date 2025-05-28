# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Gateset registry."""

from __future__ import annotations

from typing import Callable

_GatesetFactory = Callable[[], list[str]]
_REGISTRY: dict[str, _GatesetFactory] = {}


def register(gateset_name: str) -> Callable[[_GatesetFactory], _GatesetFactory]:
    """Decorator to register a gateset factory under a unique gateset_name.

    Arguments:
        gateset_name: unique identifier for the gateset (e.g., ``"ibm_falcon"``).

    Returns:
        The original factory function, unmodified.

    Raises:
        ValueError: if the chosen name is already present in the registry.
    """

    def _decorator(func: _GatesetFactory) -> _GatesetFactory:
        if gateset_name in _REGISTRY:  # pragma: no cover
            msg = f"Gateset name '{gateset_name}' already registered"
            raise ValueError(msg)
        _REGISTRY[gateset_name] = func
        return func

    return _decorator


def get_gateset_by_name(gateset_name: str) -> list[str]:
    """Return a gateset for a gateset_name.

    Arguments:
        gateset_name: identifier used during registration.

    Returns:
        Gateset.

    Raises:
        KeyError: if the gateset name is unknown.
    """
    return _REGISTRY[gateset_name]()


def gateset_names() -> list[str]:
    """Return all registered gateset names.

    Returns:
        List of strings in registration order.
    """
    return list(_REGISTRY)


def all_gatesets() -> dict[str, list[str]]:
    """Provides a dictionary containing predefined gate sets.

    This function returns a dictionary that maps the names of predefined gatesets
    to their respective lists of gate names. Each gate set in the
    dictionary is represented as a key, with its value being the list of gate
    names belonging to that set.

    Returns:
        dict[str, list[str]]: A dictionary where keys are the names of
        gate sets and values are lists of gate names.
    """
    return {n: f() for n, f in _REGISTRY.items()}
