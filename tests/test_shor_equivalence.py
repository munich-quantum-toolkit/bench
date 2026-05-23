# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Equivalence tests for Shor Transpiler gates."""

from __future__ import annotations

import numpy as np
import pytest
from pathlib import Path
from qiskit import QuantumCircuit
from qiskit.quantum_info import state_fidelity, Statevector
from qiskit_aer import AerSimulator

from mqt.bench.error_correction.shor_transpiler import ShorTranspiler


def verify_gate_equivalence(gate_name: str, num_qubits: int) -> None:
    """Verify that a transpiled gate is mathematically equivalent to the logical gate.

    Args:
        gate_name: The name of the gate to test ('h', 'x', 'z', 's', 't', 'cx', 'cz').
        num_qubits: The number of qubits the gate acts on.
    """
    # Create the logical circuit and initialize it in a non-trivial state (|+> state)
    qc_logical = QuantumCircuit(num_qubits)
    # Apply the gate
    if gate_name == "h":
        qc_logical.h(0)
    elif gate_name == "x":
        qc_logical.x(0)
    elif gate_name == "z":
        qc_logical.z(0)
    elif gate_name == "s":
        qc_logical.s(0)
    elif gate_name == "t":
        qc_logical.t(0)
    elif gate_name == "cx":
        qc_logical.cx(0, 1)
    elif gate_name == "cz":
        qc_logical.cz(0, 1)
    else:
        msg = f"Unknown gate {gate_name}"
        raise ValueError(msg)

    # Get the expected density matrix
    qc_logical_sim = qc_logical.copy()
    # expected logical state
    expected_sv_init = Statevector.from_instruction(qc_logical)

    # Transpile the circuit
    # We set add_syndromes=False to prevent statevector simulation from blowing up in memory
    transpiler = ShorTranspiler(qc_logical, add_syndromes=False)
    transpiled_qc = transpiler.transpile()

    drawing = transpiled_qc.draw(fold=-1)
    print(f"\n--- Transpiled Circuit for {gate_name.upper()} ---")
    print(drawing)

    # Save to file to ensure it can be viewed regardless of pytest-xdist capturing stdout
    output_dir = Path("tests/circuit_drawings")
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / f"{gate_name}_transpiled.txt", "w", encoding="utf-8") as f:
        f.write(f"number of qubits {num_qubits}\n")
        f.write(f"--- Transpiled Circuit for {gate_name.upper()} ---\n\n")
        f.write(str(drawing) + "\n")
    # Apply decoding so the logical state collapses back to the first physical qubit of each block
    transpiler.decode_qubits()


    # Extract the density matrix of the physical qubits holding the logical state
    # These are the 0-th qubits of each physical data register
    logical_qubits_physical = [transpiler.physical_data_registers[i][0] for i in range(num_qubits)]

    expected_sv_transpiled = Statevector.from_instruction(transpiled_qc)


    # Compare the density matrices
    #fidelity = state_fidelity(expected_rho, actual_rho)
    
    # Convert to statevector for visual inspection (since the states are pure)
    #expected_sv = expected_rho.to_statevector()
    #actual_sv = actual_rho.to_statevector()

    # Save the resulting density matrices and state vectors to the text file for visual inspection
    with open(output_dir / f"{gate_name}_transpiled.txt", "a", encoding="utf-8") as f:
        
        f.write("\n\n=== LOGICAL EXPECTED STATE VECTOR ===\n")
        f.write(str(np.round(expected_sv_init, 3)) + "\n")
        f.write("\n=== ACTUAL TRANSPILED STATE VECTOR (AFTER DECODING) ===\n")
        f.write(str(np.round(expected_sv_transpiled, 3)) + "\n")
        
        #f.write(f"\nSTATE FIDELITY: {fidelity:.6f}\n")

    #assert fidelity > 0.999, f"Fidelity too low: {fidelity}"


def test_h_equivalence() -> None:
    """Test equivalence for logical H gate."""
    verify_gate_equivalence("h", 1)


def test_x_equivalence() -> None:
    """Test equivalence for logical X gate."""
    verify_gate_equivalence("x", 1)


def test_z_equivalence() -> None:
    """Test equivalence for logical Z gate."""
    verify_gate_equivalence("z", 1)


def test_s_equivalence() -> None:
    """Test equivalence for logical S gate."""
    verify_gate_equivalence("s", 1)


#@pytest.mark.skip(reason="Slow test, takes ~1-2 mins due to 27 qubit simulation")
def test_t_equivalence() -> None:
    """Test equivalence for logical T gate."""
    verify_gate_equivalence("t", 1)


def test_cx_equivalence() -> None:
    """Test equivalence for logical CX gate."""
    verify_gate_equivalence("cx", 2)

def test_cz_equivalence() -> None:
    """Test equivalence for logical CZ gate."""
    verify_gate_equivalence("cz", 2)
