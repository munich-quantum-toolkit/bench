# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Initialization of the devices module."""

from __future__ import annotations

import copy
import importlib
import importlib.resources as ir
from functools import cache
from typing import TYPE_CHECKING, cast

from ._registry import device_names, get_device_by_name, register_device

if TYPE_CHECKING:
    from pathlib import Path

    from qiskit.transpiler import Target

_DISCOVERED_MODULES: set[str] = {
    path.stem
    for entry in ir.files(__package__).iterdir()
    if (path := cast("Path", entry)).is_file() and path.suffix == ".py" and not path.stem.startswith("_")
}

_IMPORTED_MODULES: set[str] = set()

__all__ = [
    "get_available_device_names",
    "get_device",
    "register_device",
]


def _module_from_device_name(device_name: str) -> str:
    """Return the module filename that should contain device_name.

    The rule is the same as for gatesets: take everything before the first
    underscore (``ibm_falcon_27`` → ``ibm``).  If no underscore is present, the
    whole name is assumed to be the module.
    """
    return device_name.split("_", 1)[0]


def _ensure_loaded(device_name: str) -> None:
    """Import the module expected to register device_name, if necessary."""
    if device_name in device_names():
        return  # already registered

    module_name = _module_from_device_name(device_name)
    if module_name not in _DISCOVERED_MODULES:
        msg = f"'{device_name}' is not a supported device. Known modules: {sorted(_DISCOVERED_MODULES)}"
        raise ValueError(msg)

    if module_name not in _IMPORTED_MODULES:
        importlib.import_module(f"{__package__}.{module_name}")
        _IMPORTED_MODULES.add(module_name)


def get_available_device_names() -> list[str]:
    """Return all registered devices.

    To guarantee completeness we import every not-yet-imported module once.
    """
    for module in _DISCOVERED_MODULES - _IMPORTED_MODULES:
        importlib.import_module(f"{__package__}.{module}")
        _IMPORTED_MODULES.add(module)

    return sorted(device_names()).copy()


@cache
def _get_device(device_name: str) -> Target:
    """Internal cacheable function to get a device by name.

    Arguments:
        device_name: Name of the device.
    """
    _ensure_loaded(device_name)
    return get_device_by_name(device_name)


def get_device(device_name: str) -> Target:
    """Return a deepcopy of the requested qiskit ``Target`` device."""
    return copy.deepcopy(_get_device(device_name))
