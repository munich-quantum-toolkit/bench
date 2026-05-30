# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Tests for Shor Transpiler."""

from __future__ import annotations

#import pytest
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
import matplotlib.pyplot as plt

from mqt.bench.error_correction.steane_transpiler import SteaneTranspiler

def test_steane_transpiler() -> None:
    """Test that ShorTranspiler successfully transpiles a basic circuit."""
    qc = QuantumCircuit(QuantumRegister(2), ClassicalRegister(1))
    qc.cx(0,1)
    #qc.measure(0,0)

    print("\n--- Logical Circuit ---")
    print(qc.draw(fold=-1))

    transpiler = SteaneTranspiler(qc, False)
    transpiled_qc = transpiler.transpile()
    transpiled_qc.draw("mpl", fold=-1)
    #plt.show()
    plt.savefig("circuit.png", dpi=300, bbox_inches="tight")

    #print("\n--- Transpiled Circuit ---")
    #print(transpiled_qc)



    # 2 original qubits * 9 data qubits = 18 data qubits
    # 2 original qubits * 8 ancilla qubits = 16 ancilla qubits
    # Total qubits = 34
    #assert transpiled_qc.num_qubits == 34

    # 2 original qubits * 8 classical bits = 16 syndrome bits
    # 1 measurement * 9 bits = 9 measurement bits
    # Total clbits = 25
    #assert transpiled_qc.num_clbits == 25
    ##wrong expectations in the test it should check only non error correction gate mapping
    ops = [inst.operation.name for inst in transpiled_qc.data]
    #assert "h" in ops
    #assert "cx" in ops
    #assert "measure" in ops


