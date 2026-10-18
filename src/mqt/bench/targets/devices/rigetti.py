# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Rigetti Cepheus connectivity snapshot from Braket on 2026-10-02."""

from __future__ import annotations

from math import pi

from qiskit.circuit import Parameter
from qiskit.circuit.library import CZGate, Measure, RXGate, RZGate
from qiskit.transpiler import InstructionProperties, Target

from ._registry import register_device

CEPHEUS_PHYSICAL_QUBITS = (*range(8), *range(9, 108))
"""Provider qubit label for each dense Bench wire; physical qubit 8 is unavailable."""


@register_device("rigetti_cepheus_107")
def get_rigetti_cepheus_107() -> Target:
    """Get Cepheus's 107 active qubits with CZ connectivity and no calibration.

    The provider names the device Cepheus-1-108Q. Bench numbers active qubits
    contiguously; ``CEPHEUS_PHYSICAL_QUBITS`` maps these wires to provider labels.
    """
    num_qubits = len(CEPHEUS_PHYSICAL_QUBITS)
    target = Target(num_qubits=num_qubits, description="rigetti_cepheus_107")
    oneq_props = {(q,): InstructionProperties() for q in range(num_qubits)}
    for name, angle in (("rxpi", pi), ("rxpidg", -pi), ("rxpi2", pi / 2), ("rxpi2dg", -pi / 2)):
        target.add_instruction(RXGate(angle), oneq_props, name=name)
    target.add_instruction(RZGate(Parameter("theta")), oneq_props)
    target.add_instruction(Measure(), oneq_props)
    target.add_instruction(
        CZGate(),
        {
            (i, j): InstructionProperties()
            for i, physical_i in enumerate(CEPHEUS_PHYSICAL_QUBITS)
            for j, physical_j in enumerate(CEPHEUS_PHYSICAL_QUBITS)
            if abs(physical_i - physical_j) == 9
            or (abs(physical_i - physical_j) == 1 and physical_i // 9 == physical_j // 9)
        },
    )
    return target
