# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Test the IonQ devices."""

from __future__ import annotations

import pytest
from qiskit.transpiler import Target

from mqt.bench.targets.devices.ionq import get_ionq_target


def test_ionq_target_from_calibration() -> None:
    """Test the structure of the IonQ target device."""
    target = get_ionq_target("ionq_aria_25")

    assert isinstance(target, Target)
    assert target.description == "ionq_aria_25"
    assert target.num_qubits > 0

    # Check gate support
    assert "gpi" in target.operation_names
    assert "gpi2" in target.operation_names
    assert "ms" in target.operation_names
    assert "measure" in target.operation_names

    # Single-qubit gates should have properties for all qubits
    for op_name in ["gpi", "gpi2", "measure"]:
        for (qubit,) in target[op_name]:
            props = target[op_name][qubit,]
            assert props.duration >= 0
            assert props.error >= 0

    # Two-qubit gates should have connectivity and properties
    for (q1, q2), props in target["ms"].items():
        assert q1 != q2
        assert props.duration > 0
        assert props.error > 0


def test_get_unknown_device() -> None:
    """Test the get_ionq_target function with an unknown device name."""
    with pytest.raises(ValueError, match="Unknown IonQ device: 'unknown_device'"):
        get_ionq_target("unknown_device")
