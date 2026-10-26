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
from qiskit.transpiler.passes import WrapAngles

from ._registry import register_gateset

if TYPE_CHECKING:
    from qiskit.dagcircuit import DAGCircuit
    from qiskit.passmanager import Task
    from qiskit.transpiler import PassManager, Target


@register_gateset("ibm_heron")
@register_gateset("ibm_nighthawk")
def get_ibm_heron_gateset() -> list[str]:
    """Return the shared CZ basis of IBM Heron and Nighthawk."""
    return ["id", "x", "sx", "rz", "cz"]


@register_gateset("ibm_heron_fractional")
def get_ibm_heron_fractional_gateset() -> list[str]:
    """Heron with arbitrary RX and RZZ angles in [0, pi/2]."""
    return [*get_ibm_heron_gateset(), "rx", "rzz"]


def add_fractional_gates(target: Target) -> None:
    """Add fractional gates on Heron's existing sites and couplings."""
    target.add_instruction(RXGate(Parameter("theta")), deepcopy(target["sx"]))
    target.add_instruction(RZZGate(Parameter("theta")), deepcopy(target["cz"]), angle_bounds=[(0, pi / 2)])


def configure_fractional_angles(manager: PassManager, target: Target) -> None:
    """Legalize numeric RZZ angles using Qiskit's local wrapping registry."""
    if (
        not {"x", "rz", "rzz"}.issubset(target.operation_names)
        or not isinstance(target.operation_from_name("rzz"), RZZGate)
        or not target.gate_has_angle_bounds("rzz")
        or not all(target.supported_angle_bound("rzz", [angle]) for angle in (0, pi / 2))
    ):
        return

    def fold(angles: list[float], _qubits: list[int]) -> DAGCircuit:
        # Reduce modulo 4*pi without losing precision for large angles.
        angle = 4 * atan(tan(angles[0] / 4))
        folded = remainder(angle, pi)
        turns = round((angle - folded) / pi)
        circuit = QuantumCircuit(2, global_phase=turns * pi / 2)
        if folded < 0:
            circuit.x(0)
        if folded:
            circuit.rzz(abs(folded), 0, 1)
        if folded < 0:
            circuit.x(0)
        if turns % 2:
            circuit.rz(pi, 0)
            circuit.rz(pi, 1)
        return circuit.to_dag()

    def configure(task: Task) -> None:
        if isinstance(task, WrapAngles):
            task.registry = deepcopy(task.registry)
            task.registry.add_wrapper("rzz", fold)
        for child in getattr(task, "tasks", ()):
            configure(child)

    configure(manager.to_flow_controller())
