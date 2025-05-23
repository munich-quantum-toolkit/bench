# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Test the Rigetti Ankaa 3 device."""

from __future__ import annotations

import pytest
from qiskit.transpiler import Target

from mqt.bench.targets.devices.rigetti import get_rigetti_target


def test_rigetti_ankaa_3_target_structure() -> None:
    """Test the structure of the Rigetti Ankaa 3 target device."""
    target = get_rigetti_target("rigetti_ankaa_3")

    assert isinstance(target, Target)
    assert target.description == "rigetti_ankaa_3"
    assert target.num_qubits == 84

    expected_single_qubit_gates = {"rx_pi", "rx_pi_by_2", "rx_pi_by_minus_2", "rz", "measure"}
    expected_two_qubit_gates = {"iswap"}

    assert expected_single_qubit_gates.issubset(set(target.operation_names))
    assert any(g in target.operation_names for g in expected_two_qubit_gates)

    # === Single-qubit gate properties ===
    for gate in expected_single_qubit_gates:
        if gate not in target.operation_names:
            continue
        for props in target[gate].values():
            assert 0 <= props.error < 1

    # === Two-qubit gate properties ===
    for gate in expected_two_qubit_gates:
        if gate not in target.operation_names:
            continue
        for (q0, q1), props in target[gate].items():
            assert q0 != q1
            assert 0 <= props.error < 1

    # === Readout fidelity ===
    if "measure" in target.operation_names:
        for props in target["measure"].values():
            assert 0 <= props.error < 1


def test_get_unknown_device() -> None:
    """Test the get_rigetti_target function with an unknown device name."""
    with pytest.raises(ValueError, match="Unknown Rigetti device: 'unknown_device'"):
        get_rigetti_target("unknown_device")
