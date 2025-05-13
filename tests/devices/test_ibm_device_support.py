# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Test the IBM devices."""

from __future__ import annotations

import pytest
from qiskit.transpiler import Target

from mqt.bench.devices.ibm import get_ibm_target


@pytest.mark.parametrize(
    ("device_name", "num_qubits", "expected_2q_gate"),
    [
        ("ibm_montreal", 27, "cx"),
        ("ibm_washington", 127, "cx"),
        ("ibm_torino", 133, "cz"),
    ],
)
def test_ibm_target_structure(device_name: str, num_qubits: int, expected_2q_gate: str) -> None:
    """Test structure and basic gate support for IBM targets."""
    target = get_ibm_target(device_name)

    assert isinstance(target, Target)
    assert target.description == device_name
    assert target.num_qubits == num_qubits

    # === Gate presence check ===
    expected_1q_gates = {"sx", "rz", "x", "measure"}
    assert expected_1q_gates.issubset(set(target.operation_names))
    assert expected_2q_gate in target.operation_names

    # === Validate available qubits for single-qubit gates
    for gate in expected_1q_gates:
        for (q,) in target[gate]:
            assert isinstance(q, int)
            # Optional: check that props are present (but allow None)
            props = target[gate][q,]
            assert props is not None

    # === Validate two-qubit gate connections
    for (q0, q1), props in target[expected_2q_gate].items():
        assert isinstance(q0, int)
        assert isinstance(q1, int)
        assert q0 != q1
        assert props is not None

    # === Validate measure connections
    for (q,) in target["measure"]:
        assert isinstance(q, int)
        props = target["measure"][q,]
        assert props is not None
