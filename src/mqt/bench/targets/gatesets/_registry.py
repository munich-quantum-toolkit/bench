# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Gateset registry."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from . import _GatesetFactory

_REGISTRY: dict[str, _GatesetFactory] = {}


def register_gateset(gateset_name: str) -> Callable[[_GatesetFactory], _GatesetFactory]:
    """Register a gateset factory under a unique name."""

    def _decorator(func: _GatesetFactory) -> _GatesetFactory:
        if gateset_name in _REGISTRY:
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
