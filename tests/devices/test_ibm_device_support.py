# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Test the IBMProvider class and the IBM Washington and IBM Montreal devices."""

from __future__ import annotations

import pytest
from qiskit.transpiler import Target

from mqt.bench.devices.ibm import get_ibm_target


@pytest.mark.parametrize(
    ("device_name", "num_qubits"),
    [("ibm_washington", 127), ("ibm_montreal", 27)],
)
def test_ibm_target_structure(device_name: str, num_qubits: int) -> None:
    """Test the structure of the IBM target device."""
    target = get_ibm_target(device_name)

    assert isinstance(target, Target)
    assert target.description == device_name
    assert target.num_qubits == num_qubits

    # === Single-qubit gates ===
    expected_1q_gates = {"id", "rz", "sx", "x", "measure"}
    assert expected_1q_gates.issubset(set(target.operation_names))

    for gate in expected_1q_gates:
        for (q,) in target[gate]:
            props = target[gate][q,]
            assert 0 <= props.error < 1
            assert props.duration >= 0

    # === Two-qubit gates ===
    assert "cx" in target.operation_names
    for (q0, q1), props in target["cx"].items():
        assert q0 != q1
        assert 0 <= props.error <= 1
        assert props.duration >= 0

    # === Readout
    for (q,) in target["measure"]:
        props = target["measure"][q,]
        assert 0 <= props.error <= 1
        assert props.duration >= 0
