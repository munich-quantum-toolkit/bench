# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License


def test_iqpeexact_structure() -> None:
    """Test that the Iterative Quantum Phase Estimation code circuit has the expected structure.

    Verifies:
        - Quantum registers: 1 target qubit and 1 ancillary qubit (2 qubits)
        - Classical register: num_qubits - 1 (for a 5 qubit input)
        - 4 resets and 6 conditional operations
    """
    qc = create_circuit(5)

    assert len(qc.qubits) == 2
    assert qc.cregs[0].size == 4

    assert qc.count_ops().get("reset") == 4
    if_else_count = sum(1 for inst in qc.data if isinstance(inst.operation, IfElseOp))
    assert if_else_count == 6, f"Expected 6 conditional operations, found {if_else_count}"

    assert qc.count_ops().get("measure") == 4


if __name__ == "__main__":
    print("\nRunning structural test...")
    try:
        test_iqpeexact_structure()
        print("Test finished successfully")
    except AssertionError as e:
        print(f"Test failed: {e}")
