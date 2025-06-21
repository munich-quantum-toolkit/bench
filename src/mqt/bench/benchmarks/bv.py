# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Bernstein-Vazirani benchmark definition."""

from __future__ import annotations

from qiskit.circuit import QuantumCircuit

from ._registry import register_benchmark


@register_benchmark("bv", description="Bernstein-Vazirani")
def create_circuit(num_qubits: int, dynamic: bool = False, hidden_string: str | None = None) -> QuantumCircuit:
    """Create a quantum circuit for the Bernstein-Vazirani algorithm.

    Arguments:
        num_qubits: Total number of qubits in the circuit (including the flag qubit).
        dynamic: Whether to use a dynamic layout (default: False).
        hidden_string: The hidden bitstring to be found (default: alternating pattern of 1 and 0).

    Returns:
        QuantumCircuit: Circuit implementing the Bernstein-Vazirani algorithm.
    """
    # Generate a default hidden string if not provided
    if hidden_string is None:
        hidden_string = "".join([str(i % 2) for i in range(num_qubits - 1)])

    # Ensure the hidden string matches the number of input qubits (excluding the flag qubit)
    if len(hidden_string) != num_qubits - 1:
        msg = "Length of hidden_string must be num_qubits - 1."
        raise ValueError(msg)

    # Create a quantum circuit: num_qubits (flag + inputs) and num_qubits - 1 classical bits
    circuit = QuantumCircuit(num_qubits, num_qubits - 1)

    # Prepare the flag qubit in the |1⟩ state
    circuit.x(0)

    if dynamic:
        # Dynamic layout: process one input qubit at a time
        for i in range(num_qubits - 1):
            # Apply Hadamard to the working qubit
            circuit.h(1)

            # Apply controlled-Z based on the hidden bitstring
            if hidden_string[i] == "1":
                circuit.cz(1, 0)

            # Apply Hadamard to the working qubit again
            circuit.h(1)

            # Measure the working qubit
            circuit.measure(1, i)

            # Reset the working qubit if more rounds are needed
            if i < num_qubits - 2:
                circuit.reset(1)
    else:
        # Static layout: process all input qubits at once
        # Apply Hadamard to all input qubits
        for i in range(1, num_qubits):
            circuit.h(i)

        # Apply controlled-Z gates based on the hidden bitstring
        for i in range(1, num_qubits):
            if hidden_string[i - 1] == "1":
                circuit.cz(i, 0)

        # Apply Hadamard to all input qubits again
        for i in range(1, num_qubits):
            circuit.h(i)

        # Measure all input qubits
        for i in range(1, num_qubits):
            circuit.measure(i, i - 1)
    circuit.name = "bv"

    return circuit
