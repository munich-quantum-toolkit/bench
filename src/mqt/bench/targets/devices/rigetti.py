# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Rigetti Cepheus architecture."""

from __future__ import annotations

from math import pi

from qiskit.circuit import Parameter
from qiskit.circuit.library import CZGate, Measure, RXGate, RZGate
from qiskit.transpiler import InstructionProperties, Target

from ._registry import register_device


@register_device("rigetti_cepheus_108")
def get_rigetti_cepheus_108() -> Target:
    """Get the full 108-qubit Cepheus architecture with a 12-by-9 grid."""
    num_qubits = 108
    target = Target(num_qubits=num_qubits, description="rigetti_cepheus_108")
    oneq_props = {(q,): InstructionProperties() for q in range(num_qubits)}
    for name, angle in (("rxpi", pi), ("rxpidg", -pi), ("rxpi2", pi / 2), ("rxpi2dg", -pi / 2)):
        target.add_instruction(RXGate(angle), oneq_props, name=name)
    target.add_instruction(RZGate(Parameter("theta")), oneq_props)
    target.add_instruction(Measure(), oneq_props)
    target.add_instruction(
        CZGate(),
        {
            (i, j): InstructionProperties()
            for i in range(num_qubits)
            for j in range(num_qubits)
            if abs(i - j) == 9 or (abs(i - j) == 1 and i // 9 == j // 9)
        },
    )
    return target
