# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""IonQ Forte architecture with average calibration values."""

from __future__ import annotations

from qiskit.circuit import Parameter
from qiskit.circuit.library import Measure, RZGate, RZZGate
from qiskit.transpiler import InstructionProperties, Target

from ..gatesets.ionq import GPI2Gate, GPIGate
from ._registry import register_device


@register_device("ionq_forte_36")
def get_ionq_forte_36() -> Target:
    """Get the Forte architecture, including arbitrary virtual Z rotations.

    Pulse-only provider serializers must lower virtual Z rotations into pulse
    phases. Bench returns circuits; it does not submit them to a provider.
    """
    num_qubits = 36
    target = Target(num_qubits=num_qubits, description="ionq_forte_36")
    theta = Parameter("theta")
    singleq_props = {(q,): InstructionProperties(duration=130e-6, error=0.0002) for q in range(num_qubits)}
    rz_props = {(q,): InstructionProperties(duration=0, error=0) for q in range(num_qubits)}
    measure_props = {(q,): InstructionProperties(duration=150e-6, error=0.0041) for q in range(num_qubits)}
    target.add_instruction(RZGate(theta), rz_props)
    target.add_instruction(GPIGate(theta), singleq_props)
    target.add_instruction(GPI2Gate(theta), singleq_props)
    target.add_instruction(Measure(), measure_props)
    target.add_instruction(
        RZZGate(theta),
        {
            (i, j): InstructionProperties(duration=970e-6, error=0.0068)
            for i in range(num_qubits)
            for j in range(num_qubits)
            if i != j
        },
    )
    return target
