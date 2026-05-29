# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Tests for Shor Transpiler."""

from __future__ import annotations

import pytest
from qiskit import QuantumCircuit

from mqt.bench.error_correction.shor_transpiler import ShorTranspiler

# this needs mpre tests
def test_shor_transpiler() -> None:
    """Test that ShorTranspiler successfully transpiles a basic circuit."""
    qc = QuantumCircuit(2, 1)
    qc.x(0)
    qc.z(1)
    qc.measure(1, 0)

    print("\n--- Logical Circuit ---")
    print(qc.draw(fold=-1))

    transpiler = ShorTranspiler(qc)
    transpiled_qc = transpiler.transpile()

    print("\n--- Transpiled Circuit ---")
    print(transpiled_qc)

    # 2 original qubits * 9 data qubits = 18 data qubits
    # 2 original qubits * 8 ancilla qubits = 16 ancilla qubits
    # Total qubits = 34
    assert transpiled_qc.num_qubits == 34

    # 2 original qubits * 8 classical bits = 16 syndrome bits
    # 1 measurement * 9 bits = 9 measurement bits
    # Total clbits = 25
    assert transpiled_qc.num_clbits == 25
    ##wrong expectations in the test it should check only non error correction gate mapping
    ops = [inst.operation.name for inst in transpiled_qc.data]
    assert "h" in ops
    assert "cx" in ops
    assert "measure" in ops


def test_shor_transpiler_unsupported_gate() -> None:
    """Test that unsupported gates raise NotImplementedError."""
    qc = QuantumCircuit(1)
    qc.rx(0, 0)

    transpiler = ShorTranspiler(qc)
    with pytest.raises(NotImplementedError, match=r"Gate rx is not supported by ShorTranspiler\."):
        transpiler.transpile()


def test_shor_transpiler_s_gate_structure() -> None:
    """Test that the S gate teleportation circuit has the correct structure.

    Verifies that:
    - A magic state ancilla register (9 qubits) is allocated.
    - The teleportation measurement register (1 classical bit) is allocated.
    - The circuit contains the expected gates (h, s, cx, measure).
    """
    qc = QuantumCircuit(1)
    qc.s(0)

    transpiler = ShorTranspiler(qc)
    transpiled_qc = transpiler.transpile()

    # Original: 9 data + 6 bit-flip ancilla + 2 phase-flip ancilla = 17
    # S gate adds: 9 magic data = 9
    # Total = 26
    assert transpiled_qc.num_qubits == 26

    # Original: 6 bf meas + 2 pf meas = 8
    # S gate adds: 1 teleport meas = 1
    # Total = 9
    assert transpiled_qc.num_clbits == 9

    ops = [inst.operation.name for inst in transpiled_qc.data]

    # Magic state prep uses h and p on the ancilla qubit
    assert "p" in ops
    assert "h" in ops

    # Teleportation uses cx, measure
    assert "cx" in ops
    assert "measure" in ops

    # Conditional correction uses if_else
    assert "if_else" in ops

    # Verify the magic state register exists
    reg_names = [reg.name for reg in transpiled_qc.qregs]
    assert "ms0" in reg_names

    # Verify teleportation measurement register exists
    creg_names = [reg.name for reg in transpiled_qc.cregs]
    assert "tmeas0" in creg_names


def test_shor_transpiler_s_gate_followed_by_other_gates() -> None:
    """Test that gates applied after the S gate target the correct register.

    After S gate teleportation, subsequent gates should operate on the original
    data register since the teleportation gadget doesn't swap the pointers.
    """
    qc = QuantumCircuit(1, 1)
    qc.s(0)
    qc.z(0)
    qc.measure(0, 0)

    transpiler = ShorTranspiler(qc)
    transpiled_qc = transpiler.transpile()

    # Circuit should compile and run without errors
    assert transpiled_qc.num_qubits > 0
    assert transpiled_qc.num_clbits > 0

    ops = [inst.operation.name for inst in transpiled_qc.data]
    assert "p" in ops  # Magic state prep (phase)
    assert "x" in ops  # Logical Z uses physical X
    assert "measure" in ops


def test_shor_transpiler_multiple_s_gates() -> None:
    """Test that multiple S gates each allocate independent ancilla blocks.

    Two consecutive S gates should produce two independent magic state
    ancilla blocks (ms0 and ms1).
    """
    qc = QuantumCircuit(1)
    qc.s(0)
    qc.s(0)

    transpiler = ShorTranspiler(qc)
    transpiled_qc = transpiler.transpile()

    reg_names = [reg.name for reg in transpiled_qc.qregs]
    assert "ms0" in reg_names
    assert "ms1" in reg_names


def test_shor_transpiler_t_gate_structure() -> None:
    """Test that the T gate teleportation circuit has the correct structure.

    Verifies that:
    - A magic state ancilla register for T (9 qubits) is allocated.
    - The teleportation measurement register for T (1 classical bit) is allocated.
    - Because of the S correction, another S ancilla and measurement are also allocated conditionally.
    """
    qc = QuantumCircuit(1)
    qc.t(0)

    transpiler = ShorTranspiler(qc)
    transpiled_qc = transpiler.transpile()

    # Original: 17 qubits
    # T gate adds: 9 magic data for T + 9 magic data for S = 18
    # Total = 35
    assert transpiled_qc.num_qubits == 35

    # Original: 8 clbits
    # T gate adds: 1 for T + 1 for S = 2
    # Total = 10
    assert transpiled_qc.num_clbits == 10

    ops = [inst.operation.name for inst in transpiled_qc.data]

    # Magic state prep uses p and h
    assert "p" in ops
    assert "h" in ops

    # Verify the T-magic state register exists
    reg_names = [reg.name for reg in transpiled_qc.qregs]
    assert "anc_t_1" in reg_names
    assert "ms0" in reg_names  # from the S correction


def test_shor_transpiler_barrier() -> None:
    """Test logical barrier translates to physical barrier on all involved qubits."""
    qc = QuantumCircuit(2)
    qc.barrier(0)

    transpiler = ShorTranspiler(qc)
    transpiled_qc = transpiler.transpile()

    ops = [inst.operation.name for inst in transpiled_qc.data]
    assert "barrier" in ops


def test_shor_transpiler_measure() -> None:
    """Test logical measure maps to 9 physical measurements."""
    qc = QuantumCircuit(1, 1)
    qc.measure(0, 0)

    transpiler = ShorTranspiler(qc)
    transpiled_qc = transpiler.transpile()

    measure_count = sum(1 for inst in transpiled_qc.data if inst.operation.name == "measure")
    # At least 9 physical measurements for the single logical measurement
    assert measure_count >= 9


def test_shor_transpiler_h_gate() -> None:
    """Test logical H gate."""
    qc = QuantumCircuit(1)
    qc.h(0)

    transpiler = ShorTranspiler(qc)
    transpiled_qc = transpiler.transpile()

    ops = [inst.operation.name for inst in transpiled_qc.data]
    assert "h" in ops
    assert "swap" in ops


def test_shor_transpiler_x_gate() -> None:
    """Test logical X gate uses Z transversally."""
    qc = QuantumCircuit(1)
    qc.x(0)

    transpiler = ShorTranspiler(qc)
    transpiled_qc = transpiler.transpile()

    ops = [inst.operation.name for inst in transpiled_qc.data]
    # Shor code logical X = Z_0 Z_3 Z_6
    assert "z" in ops


def test_shor_transpiler_z_gate() -> None:
    """Test logical Z gate uses X transversally."""
    qc = QuantumCircuit(1)
    qc.z(0)

    transpiler = ShorTranspiler(qc)
    transpiled_qc = transpiler.transpile()

    ops = [inst.operation.name for inst in transpiled_qc.data]
    # Shor code logical Z = X_0 X_1 X_2
    assert "x" in ops


def test_shor_transpiler_cx_gate() -> None:
    """Test logical CX gate."""
    qc = QuantumCircuit(2)
    qc.cx(0, 1)

    transpiler = ShorTranspiler(qc)
    transpiled_qc = transpiler.transpile()

    ops = [inst.operation.name for inst in transpiled_qc.data]
    assert "cx" in ops


def test_shor_transpiler_cz_gate() -> None:
    """Test logical CZ gate."""
    qc = QuantumCircuit(2)
    qc.cz(0, 1)

    transpiler = ShorTranspiler(qc)
    transpiled_qc = transpiler.transpile()

    ops = [inst.operation.name for inst in transpiled_qc.data]
    # CZ is implemented via H, CX, H
    assert "h" in ops
    assert "cx" in ops
    assert "swap" in ops


def test_shor_transpiler_encode_decode() -> None:
    """Test static encoding and decoding methods directly."""
    from qiskit import QuantumRegister
    qc = QuantumCircuit()
    reg = QuantumRegister(9, "q")
    qc.add_register(reg)

    ShorTranspiler._apply_shor_encoding(qc, reg)
    ops_enc = [inst.operation.name for inst in qc.data]
    assert len(ops_enc) > 0

    ShorTranspiler._apply_shor_decoding(qc, reg)
    ops_dec = [inst.operation.name for inst in qc.data]
    assert len(ops_dec) > len(ops_enc)


def test_shor_transpiler_prepare_magic() -> None:
    """Test _prepare_magic directly."""
    from qiskit import QuantumRegister
    import numpy as np

    qc = QuantumCircuit()
    anc = QuantumRegister(9, "anc")
    qc.add_register(anc)

    ShorTranspiler._prepare_magic(qc, anc, np.pi/2)
    ops = [inst.operation.name for inst in qc.data]
    assert "h" in ops
    assert "p" in ops
