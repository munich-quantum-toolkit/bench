# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Handles the available native gatesets."""

# ruff: file-ignore[non-empty-init-module]

from __future__ import annotations

import importlib
import importlib.resources as ir
from functools import cache
from math import pi
from typing import TYPE_CHECKING

from qiskit.circuit import BreakLoopOp, ContinueLoopOp, Parameter, get_control_flow_name_mapping
from qiskit.circuit.library.standard_gates import RXGate, get_standard_gate_name_mapping
from qiskit.transpiler import Target

from ._registry import gateset_names, get_gateset_by_name, register_gateset

if TYPE_CHECKING:
    from collections.abc import Callable

    from qiskit.circuit import Gate

_DISCOVERED_MODULES: set[str] = {
    entry.name.removesuffix(".py")
    for entry in ir.files(__name__).iterdir()
    if entry.is_file() and entry.name.endswith(".py") and not entry.name.startswith("_")
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
    """Map a gateset name like ``ibm_heron`` to the module ``ibm``.

    The rule is the same as for devices: take everything before the first
    underscore (``ibm_heron`` → ``ibm``).  If no underscore is present, the
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


def _lazy_custom_gates() -> dict[str, Callable[[], Gate]]:
    """Import custom gates only when needed."""
    from .ionq import GPI2Gate, GPIGate  # ruff:ignore[import-outside-top-level]

    return {
        "gpi": lambda: GPIGate(Parameter("alpha")),
        "gpi2": lambda: GPI2Gate(Parameter("alpha")),
        "rxpi": lambda: RXGate(pi),
        "rxpidg": lambda: RXGate(-pi),
        "rxpi2": lambda: RXGate(pi / 2),
        "rxpi2dg": lambda: RXGate(-pi / 2),
    }


def get_target_for_gateset(name: str, num_qubits: int) -> Target:
    """Return a native gate-set target without hardware constraints."""
    target = Target(description=name, num_qubits=num_qubits)
    standard_gates = get_standard_gate_name_mapping()
    custom_factory = _lazy_custom_gates()
    for gate_name in dict.fromkeys([*get_gateset(name), "reset", "delay", "measure"]):
        if name == "ibm_heron_fractional" and gate_name in {"rx", "rzz"}:
            continue
        if gate_name in standard_gates:
            instruction = standard_gates[gate_name]
        elif gate_name in custom_factory:
            instruction = custom_factory[gate_name]()
        else:
            msg = f"Gate '{gate_name}' not found in available custom gates."
            raise ValueError(msg)
        target.add_instruction(instruction, name=gate_name)

    if name == "ibm_heron_fractional":
        from .ibm import add_fractional_gates  # ruff:ignore[import-outside-top-level]

        add_fractional_gates(target)

    for name, instruction_class in get_control_flow_name_mapping().items():
        target.add_instruction(instruction_class, name=name)
    target.add_instruction(BreakLoopOp, name="break_loop")
    target.add_instruction(ContinueLoopOp, name="continue_loop")

    return target
