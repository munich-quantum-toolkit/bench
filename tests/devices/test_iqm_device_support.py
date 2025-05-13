# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Test of the IQM target device."""

from __future__ import annotations

from qiskit.transpiler import Target

from mqt.bench.devices.iqm import get_iqm_target


def test_iqm_target_from_calibration() -> None:
    """Test the structure of the IQM target device."""
    target = get_iqm_target("iqm_adonis")  # or "iqm_apollo" depending on available calibration

    assert isinstance(target, Target)
    assert target.num_qubits > 0
    assert "iqm" in target.description.lower()

    # Expected gate types
    expected_ops = {"r", "cz", "measure"}
    assert expected_ops.issubset(set(target.operation_names))

    # Check single-qubit RGate properties
    for (qubit,) in target["r"]:
        props = target["r"][qubit,]
        assert props.duration > 0
        assert 0 <= props.error < 1

    # Check measurement properties
    for (qubit,) in target["measure"]:
        props = target["measure"][qubit,]
        assert props.duration > 0
        assert 0 <= props.error < 1

    # Check CZ gate symmetry and properties
    for (q1, q2), props in target["cz"].items():
        assert q1 != q2
        assert props.duration > 0
        assert 0 <= props.error < 1
        # Also ensure the reverse pair is present (symmetry)
        assert (q2, q1) in target["cz"]
