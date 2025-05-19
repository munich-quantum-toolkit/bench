# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""File to create a target device from the IQM calibration data."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from qiskit.circuit import Parameter
from qiskit.circuit.library import CZGate, Measure, RGate
from qiskit.transpiler import InstructionProperties, Target

from .calibration import get_device_calibration_path

if TYPE_CHECKING:
    from pathlib import Path


def create_iqm_target(calibration_path: Path) -> Target:
    """Create a target device from the IQM calibration data."""
    with calibration_path.open() as json_file:
        calib = json.load(json_file)

    num_qubits = calib["num_qubits"]
    connectivity = calib["connectivity"]
    name = calib["name"]

    oneq_errors = calib["error"]["one_q"]
    twoq_errors = calib["error"]["two_q"]
    readout_errors = calib["error"]["readout"]

    oneq_duration = calib["timing"]["one_q"] * 1e-9
    twoq_duration = calib["timing"]["two_q"] * 1e-9
    readout_duration = calib["timing"]["readout"] * 1e-9

    target = Target(num_qubits=num_qubits, description=name)

    theta = Parameter("theta")
    phi = Parameter("phi")

    # === Single-qubit R gate with per-qubit fidelity ===
    r_props = {
        (q,): InstructionProperties(duration=oneq_duration, error=oneq_errors[str(q)]) for q in range(num_qubits)
    }
    target.add_instruction(RGate(theta, phi), r_props)

    # === Per-qubit measurement ===
    measure_props = {
        (q,): InstructionProperties(duration=readout_duration, error=readout_errors[str(q)]) for q in range(num_qubits)
    }
    target.add_instruction(Measure(), measure_props)

    # === Two-qubit CZ gate with per-direction errors ===
    cz_props = {}
    for q1, q2 in connectivity:
        key_direct = f"{q1}-{q2}"
        key_reverse = f"{q2}-{q1}"
        if key_direct in twoq_errors:
            error = twoq_errors[key_direct]
        elif key_reverse in twoq_errors:
            error = twoq_errors[key_reverse]
        else:
            continue
        props = InstructionProperties(duration=twoq_duration, error=error)

        # Add both directions
        cz_props[q1, q2] = props
        cz_props[q2, q1] = props  # assume symmetric for now

    target.add_instruction(CZGate(), cz_props)

    return target


def get_iqm_target(device_name: str) -> Target:
    """Get a target device from the IQM calibration data."""
    return create_iqm_target(get_device_calibration_path(device_name))
