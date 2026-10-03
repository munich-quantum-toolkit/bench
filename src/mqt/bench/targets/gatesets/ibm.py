# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Handles the available native gatesets for IBM."""

from __future__ import annotations

from copy import deepcopy
from math import atan, pi, remainder, tan
from typing import TYPE_CHECKING

from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.circuit.library import RXGate, RZZGate
from qiskit.converters import circuit_to_dag
from qiskit.passmanager import ConditionalController, DoWhileController, FlowControllerLinear
from qiskit.transpiler import PassManager, Target

from ._registry import register_gateset

if TYPE_CHECKING:
    from qiskit.dagcircuit import DAGCircuit


@register_gateset("ibm_heron")
def get_ibm_heron_gateset() -> list[str]:
    """Returns the basis gates of the IBM Heron gateset."""
    return ["id", "x", "sx", "rz", "cz"]


def get_ibm_heron_fractional_gateset() -> list[str]:
    """Heron with arbitrary RX and RZZ angles in [0, pi/2]."""
    return [*get_ibm_heron_gateset(), "rx", "rzz"]


def add_fractional_gates(target: Target) -> None:
    """Add fractional gates on Heron's existing sites and couplings."""
    if not hasattr(target, "gate_has_angle_bounds"):
        msg = "Fractional Heron targets require Qiskit 2.2 or newer."
        raise ValueError(msg)
    target.add_instruction(RXGate(Parameter("rx")), deepcopy(target["sx"]))
    target.add_instruction(RZZGate(Parameter("rzz")), deepcopy(target["cz"]), angle_bounds=[(0, pi / 2)])


def configure_fractional_angles(manager: PassManager, target: Target) -> None:
    """Legalize numeric RZZ angles using Qiskit's local wrapping registry."""
    if (
        not {"x", "rz", "rzz"}.issubset(target.operation_names)
        or not hasattr(target, "gate_has_angle_bounds")
        or not target.gate_has_angle_bounds("rzz")
    ):
        return
    if not isinstance(target.operation_from_name("rzz"), RZZGate) or not all(
        target.supported_angle_bound("rzz", [angle]) for angle in (0, pi / 2)
    ):
        return
    from qiskit.transpiler.passes import WrapAngles  # ruff:ignore[import-outside-top-level]

    def fold(angles: list[float], _qubits: list[int]) -> DAGCircuit:
        angle = angles[0]
        if abs(angle) > 2 * pi:
            angle = 4 * atan(tan(angle / 4))
        folded = remainder(angle, pi)
        turns = round((angle - folded) / pi)
        circuit = QuantumCircuit(2, global_phase=-turns * pi / 2)
        if folded < 0:
            circuit.x(0)
        if folded:
            circuit.rzz(abs(folded), 0, 1)
        if folded < 0:
            circuit.x(0)
        if turns % 2:
            circuit.rz(pi, 0)
            circuit.rz(pi, 1)
            circuit.global_phase += pi
        return circuit_to_dag(circuit)

    def configure(controller: FlowControllerLinear | ConditionalController | DoWhileController) -> None:
        for task in controller.tasks:
            if isinstance(task, (FlowControllerLinear, ConditionalController, DoWhileController)):
                configure(task)
            elif isinstance(task, WrapAngles):
                task.registry = deepcopy(task.registry)
                task.registry.add_wrapper("rzz", fold)

    configure(manager.to_flow_controller())


if hasattr(Target, "gate_has_angle_bounds"):
    register_gateset("ibm_heron_fractional")(get_ibm_heron_fractional_gateset)
