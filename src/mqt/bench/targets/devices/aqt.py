# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""AQT IBEX Q1 capabilities and mean calibration from Braket on 2026-10-02."""

from __future__ import annotations

from qiskit.circuit import Parameter
from qiskit.circuit.library import Measure, RGate, RXXGate, RZGate
from qiskit.transpiler import InstructionProperties, Target

from ._registry import register_device


@register_device("aqt_ibex_12")
def get_aqt_ibex_12() -> Target:
    """Get the 12-qubit IBEX Q1 architecture with all-to-all RXX interactions."""
    num_qubits = 12
    target = Target(num_qubits=num_qubits, description="aqt_ibex_12")
    theta, phi = Parameter("theta"), Parameter("phi")
    oneq_props = {(q,): InstructionProperties(duration=45e-6) for q in range(num_qubits)}
    target.add_instruction(RGate(theta, phi), oneq_props)
    target.add_instruction(RZGate(theta), {(q,): InstructionProperties(duration=0, error=0) for q in range(num_qubits)})
    target.add_instruction(Measure(), {(q,): InstructionProperties(duration=1e-3) for q in range(num_qubits)})
    target.add_instruction(
        RXXGate(theta),
        {
            (i, j): InstructionProperties(duration=335e-6, error=0.017)
            for i in range(num_qubits)
            for j in range(num_qubits)
            if i != j
        },
    )
    return target
