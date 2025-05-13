# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""File to create a target device from the IonQ calibration data."""
# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from qiskit.circuit import Parameter
from qiskit.circuit.library import Measure, RXGate, RXXGate, RYGate, RZGate
from qiskit.transpiler import InstructionProperties, Target

from .calibration import get_device_calibration_path

if TYPE_CHECKING:
    from pathlib import Path


def create_ionq_target(calibration_path: Path) -> Target:
    """Create a target device from the IonQ calibration data."""
    with calibration_path.open() as json_file:
        calib = json.load(json_file)

    target = Target(num_qubits=calib["num_qubits"], description=calib["name"])
    num_qubits = calib["num_qubits"]
    connectivity = calib["connectivity"]

    # Gate durations and fidelities
    oneq_fidelity = calib["fidelity"]["1q"]["mean"]
    twoq_fidelity = calib["fidelity"]["2q"]["mean"]
    spam_fidelity = calib["fidelity"]["spam"]["mean"]
    calib["timing"]["t1"]
    calib["timing"]["t2"]

    oneq_duration = calib["timing"]["1q"]
    twoq_duration = calib["timing"]["2q"]
    readout_duration = calib["timing"]["readout"]

    theta = Parameter("theta")
    phi = Parameter("phi")
    lam = Parameter("lambda")

    # === Add single-qubit gates ===
    rx_props = {(q,): InstructionProperties(duration=oneq_duration, error=1 - oneq_fidelity) for q in range(num_qubits)}
    ry_props = {(q,): InstructionProperties(duration=oneq_duration, error=1 - oneq_fidelity) for q in range(num_qubits)}
    rz_props = {(q,): InstructionProperties(duration=0.0, error=0.0) for q in range(num_qubits)}
    measure_props = {
        (q,): InstructionProperties(duration=readout_duration, error=1 - spam_fidelity) for q in range(num_qubits)
    }

    target.add_instruction(RXGate(theta), rx_props)
    target.add_instruction(RYGate(phi), ry_props)
    target.add_instruction(RZGate(lam), rz_props)
    target.add_instruction(Measure(), measure_props)

    # === Add two-qubit gates ===
    alpha = Parameter("alpha")
    rxx_props = {
        (q1, q2): InstructionProperties(duration=twoq_duration, error=1 - twoq_fidelity) for q1, q2 in connectivity
    }
    target.add_instruction(RXXGate(alpha), rxx_props)

    return target


def get_ionq_target(device_name: str) -> Target:
    """Get a target device from the IonQ calibration data."""
    return create_ionq_target(get_device_calibration_path(device_name))
