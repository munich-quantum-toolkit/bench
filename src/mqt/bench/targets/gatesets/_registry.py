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


def register_gateset(gateset_name: str) -> Callable[[_GatesetFactory], _GatesetFactory]:
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
