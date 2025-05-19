# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Test the Quantinuum device."""

from __future__ import annotations

from qiskit.transpiler import Target

from mqt.bench.targets.devices.quantinuum import get_quantinuum_target


def test_quantinuum_target_structure() -> None:
    """Test the structure of the Quantinuum H2 target device."""
    target = get_quantinuum_target("quantinuum_h2")

    # Basic metadata
    assert isinstance(target, Target)
    assert target.description == "quantinuum_h2"
    assert target.num_qubits == 32  # adjust if your calibration changes

    # Ensure all expected gates are supported
    expected_gates = {"rx", "ry", "rz", "rzz", "measure"}
    assert expected_gates.issubset(set(target.operation_names))

    # === Single-qubit gates ===
    for op in ["rx", "ry", "rz"]:
        insts = target[op]
        assert all(len(qargs) == 1 for qargs in insts), f"{op} not single-qubit"
        for props in insts.values():
            assert 0 <= props.error < 1

    # === Measurement ===
    insts = target["measure"]
    assert all(len(qargs) == 1 for qargs in insts)
    for props in insts.values():
        assert 0 <= props.error < 1

    # === Two-qubit gates ===
    insts = target["rzz"]
    assert all(len(qargs) == 2 for qargs in insts)
    for (q0, q1), props in insts.items():
        assert q0 != q1
        assert 0 <= props.error < 1

    # Symmetry check (if assumed)
    # This is optional, depending on your calibration assumption
    for q0, q1 in insts:
        assert (q1, q0) in insts
