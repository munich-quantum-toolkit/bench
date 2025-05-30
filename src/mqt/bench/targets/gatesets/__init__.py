# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Handles the available native gatesets."""

from __future__ import annotations

import importlib
import importlib.resources as ir
from functools import cache
from typing import TYPE_CHECKING, cast

from qiskit.circuit import Parameter
from qiskit.circuit.library.standard_gates import get_standard_gate_name_mapping
from qiskit.providers.fake_provider import GenericBackendV2

from . import _registry as gateset_registry
from .ionq import GPI2Gate, GPIGate, MSGate, ZZGate
from .rigetti import RXPI2DgGate, RXPI2Gate, RXPIGate

if TYPE_CHECKING:
    from pathlib import Path

    from qiskit.transpiler import Target

_pkg_name = __name__
for entry in ir.files(_pkg_name).iterdir():
    path = cast("Path", entry)
    if path.suffix == ".py" and path.stem not in {"__init__", "_registry"}:
        importlib.import_module(f"{_pkg_name}.{path.stem}")


__all__ = [
    "gateset_registry",
    "get_available_gateset_names",
    "get_available_native_gatesets",
    "get_gateset",
    "get_target_for_gateset",
]


@cache
def get_available_native_gatesets() -> dict[str, list[str]]:
    """Return a dict of available native gatesets."""
    return gateset_registry.all_gatesets()


@cache
def get_available_gateset_names() -> list[str]:
    """Return a list of available gateset names."""
    return gateset_registry.gateset_names()


@cache
def get_gateset(gateset_name: str) -> list[str]:
    """Return the gateset for a given gateset name."""
    try:
        return gateset_registry.get_gateset_by_name(gateset_name)
    except KeyError:
        msg = f"Unknown gateset '{gateset_name}'. Available gatesets: {get_available_gateset_names()}"
        raise ValueError(msg) from None


@cache
def get_target_for_gateset(name: str, num_qubits: int) -> Target:
    """Return the Target object for a given native gateset name."""
    gates = get_gateset(name)

    standard_gates = []
    other_gates = []
    for gate in gates:
        if gate in get_standard_gate_name_mapping():
            standard_gates.append(gate)
        else:
            other_gates.append(gate)
    backend = GenericBackendV2(num_qubits=num_qubits, basis_gates=standard_gates)
    target = backend.target
    target.description = name

    for gate in other_gates:
        alpha = Parameter("alpha")
        beta = Parameter("beta")
        gamma = Parameter("gamma")
        if gate == "gpi":
            target.add_instruction(GPIGate(alpha))
        elif gate == "gpi2":
            target.add_instruction(GPI2Gate(alpha))
        elif gate == "ms":
            target.add_instruction(MSGate(alpha, beta, gamma))
        elif gate == "zz":
            target.add_instruction(ZZGate(alpha))
        elif gate == "rxpi":
            target.add_instruction(RXPIGate())
        elif gate == "rxpi2":
            target.add_instruction(RXPI2Gate())
        elif gate == "rxpi2dg":
            target.add_instruction(RXPI2DgGate())
        else:
            msg = f"Gate '{gate}' not found in available gatesets."
            raise ValueError(msg) from None

    return target
