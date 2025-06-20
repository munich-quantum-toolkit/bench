# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Device registry."""

from __future__ import annotations

from typing import Callable

from qiskit.transpiler import Target

_DeviceFactory = Callable[[], Target]
_REGISTRY: dict[str, _DeviceFactory] = {}


def register_device(device_name: str) -> Callable[[_DeviceFactory], _DeviceFactory]:
    """Decorator to register a device factory under a unique device_name.

    Arguments:
        device_name: unique identifier for the device (e.g., ``"ibm_falcon_27"``).

    Returns:
        The original factory function, unmodified.

    Raises:
        ValueError: if the chosen name is already present in the registry.
    """

    def _decorator(func: _DeviceFactory) -> _DeviceFactory:
        if device_name in _REGISTRY:  # pragma: no cover
            msg = f"Device name '{device_name}' already registered"
            raise ValueError(msg)
        _REGISTRY[device_name] = func
        return func

    return _decorator


def get_device_by_name(device_name: str) -> Target:
    """Return an instantiated `Target` for a device_name.

    Arguments:
        device_name: identifier used during registration.

    Returns:
        Instantiated `~qiskit.transpiler.Target`.

    Raises:
        KeyError: if the device name is unknown.
    """
    return _REGISTRY[device_name]()


def device_names() -> list[str]:
    """Return all registered device names."""
    return list(_REGISTRY)
