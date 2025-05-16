# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""File to create a target device from the Quantinuum calibration data."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from qiskit.circuit import Parameter
from qiskit.circuit.library import Measure, RXGate, RYGate, RZGate, RZZGate
from qiskit.transpiler import InstructionProperties, Target

from .calibration import get_device_calibration_path

if TYPE_CHECKING:
    from pathlib import Path


def create_quantinuum_target(calibration_path: Path) -> Target:
    """Create a target device from the Quantinuum calibration data."""
    with calibration_path.open() as json_file:
        calib = json.load(json_file)

    num_qubits = calib["num_qubits"]
    connectivity = calib["connectivity"]
    name = calib["name"]

    oneq_fidelity = calib["fidelity"]["1q"]["mean"]
    twoq_fidelity = calib["fidelity"]["2q"]["mean"]
    spam_fidelity = calib["fidelity"]["spam"]["mean"]

    target = Target(num_qubits=num_qubits, description=name)

    # Define symbolic parameters
    theta = Parameter("theta")
    phi = Parameter("phi")
    alpha = Parameter("alpha")

    # === Add single-qubit gates ===
    rx_props = {(q,): InstructionProperties(error=1 - oneq_fidelity) for q in range(num_qubits)}
    ry_props = {(q,): InstructionProperties(error=1 - oneq_fidelity) for q in range(num_qubits)}
    rz_props = {(q,): InstructionProperties(error=0.0) for q in range(num_qubits)}
    measure_props = {(q,): InstructionProperties(error=1 - spam_fidelity) for q in range(num_qubits)}

    target.add_instruction(RXGate(theta), rx_props)
    target.add_instruction(RYGate(phi), ry_props)
    target.add_instruction(RZGate(theta), rz_props)
    target.add_instruction(Measure(), measure_props)

    # === Add two-qubit RZZ gates ===
    rzz_props = {(q1, q2): InstructionProperties(error=1 - twoq_fidelity) for q1, q2 in connectivity}
    target.add_instruction(RZZGate(alpha), rzz_props)

    return target


def get_quantinuum_target(device_name: str) -> Target:
    """Get a target device from the Quantinuum calibration data."""
    return create_quantinuum_target(get_device_calibration_path(device_name))
