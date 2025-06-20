# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Handles the available native gatesets."""

from __future__ import annotations

import copy
import importlib
import importlib.resources as ir
from functools import cache
from typing import TYPE_CHECKING, cast

from qiskit.circuit import Parameter
from qiskit.circuit.library.standard_gates import get_standard_gate_name_mapping
from qiskit.providers.fake_provider import GenericBackendV2

from ._registry import gateset_names, get_gateset_by_name, register_gateset

if TYPE_CHECKING:
    from pathlib import Path

    from qiskit.circuit import Gate
    from qiskit.transpiler import Target

_DISCOVERED_MODULES: set[str] = {
    path.stem
    for entry in ir.files(__package__).iterdir()
    if (path := cast("Path", entry)).is_file() and path.suffix == ".py" and not path.stem.startswith("_")
}

_IMPORTED_MODULES: set[str] = set()

__all__ = [
    "get_available_gateset_names",
    "get_gateset",
    "get_target_for_gateset",
    "register_gateset",
]

_SPECIAL_NAME_TO_MODULE = {
    "clifford+t": "clifford_t",
    "clifford+t+rotations": "clifford_t",
}


def _module_from_gateset_name(gateset_name: str) -> str:
    """Map a gateset name like ``ibm_falcon`` to the module ``ibm``.

    The rule is the same as for devices: take everything before the first
    underscore (``ibm_falcon`` → ``ibm``).  If no underscore is present, the
    whole name is assumed to be the module.
    """
    if gateset_name in _SPECIAL_NAME_TO_MODULE:
        return _SPECIAL_NAME_TO_MODULE[gateset_name]

    return gateset_name.split("_", 1)[0]


def _ensure_loaded(gateset_name: str) -> None:
    """Import the module that should register gateset_name."""
    if gateset_name in gateset_names():
        return  # already present

    module_name = _module_from_gateset_name(gateset_name)

    if module_name not in _DISCOVERED_MODULES:
        msg = f"'{gateset_name}' is not a supported gateset. Known modules: {sorted(_DISCOVERED_MODULES)}"
        raise ValueError(msg)

    if module_name not in _IMPORTED_MODULES:
        importlib.import_module(f"{__package__}.{module_name}")
        _IMPORTED_MODULES.add(module_name)


def get_available_gateset_names() -> list[str]:
    """Return a list of available gateset names."""
    for module in _DISCOVERED_MODULES - _IMPORTED_MODULES:
        importlib.import_module(f"{__package__}.{module}")
        _IMPORTED_MODULES.add(module)

    return sorted(gateset_names()).copy()


@cache
def _get_gateset(gateset_name: str) -> list[str]:
    """Internal cacheable access. Ensures *lazy* loading."""
    _ensure_loaded(gateset_name)
    return get_gateset_by_name(gateset_name)


def get_gateset(gateset_name: str) -> list[str]:
    """Return the basis-gate list for gateset_name."""
    return _get_gateset(gateset_name).copy()


def _lazy_custom_gates() -> dict[str, Gate]:
    """Import custom gates only when needed."""
    from .ionq import GPI2Gate, GPIGate, MSGate, ZZGate  # noqa: PLC0415
    from .rigetti import RXPI2DgGate, RXPI2Gate, RXPIGate  # noqa: PLC0415

    return {
        "gpi": lambda: GPIGate(Parameter("alpha")),
        "gpi2": lambda: GPI2Gate(Parameter("alpha")),
        "ms": lambda: MSGate(Parameter("alpha"), Parameter("beta"), Parameter("gamma")),
        "zz": lambda: ZZGate(Parameter("alpha")),
        "rxpi": RXPIGate,
        "rxpi2": RXPI2Gate,
        "rxpi2dg": RXPI2DgGate,
    }


@cache
def _get_target_for_gateset(gateset_name: str, num_qubits: int) -> Target:
    """Return the Target object for a given native gateset name."""
    gates = get_gateset(gateset_name)

    standard_gates = []
    other_gates = []
    for gate in gates:
        if gate in get_standard_gate_name_mapping():
            standard_gates.append(gate)
        else:
            other_gates.append(gate)
    backend = GenericBackendV2(num_qubits=num_qubits, basis_gates=standard_gates)
    target = backend.target
    target.description = gateset_name

    custom_factory = _lazy_custom_gates()
    for gate_name in other_gates:
        if gate_name not in custom_factory:
            msg = f"Gate '{gate_name}' not found in available custom gates."
            raise ValueError(msg)
        target.add_instruction(custom_factory[gate_name]())

    return target


def get_target_for_gateset(name: str, num_qubits: int) -> Target:
    """Return a deepcopy of a Target object for a given native gateset name."""
    return copy.deepcopy(_get_target_for_gateset(name, num_qubits))
