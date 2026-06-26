# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Bernstein-Vazirani benchmark definition."""

from __future__ import annotations

from qiskit.circuit import QuantumCircuit

from ._reference import MetricApplicability, ObjectiveSpec, ReferenceSpec, SparseReference
from ._registry import register_benchmark, register_reference


@register_benchmark("bv", description="Bernstein-Vazirani")
def create_circuit(num_qubits: int, dynamic: bool = False, hidden_string: str | None = None) -> QuantumCircuit:
    """Create a quantum circuit for the Bernstein-Vazirani algorithm.

    Arguments:
        num_qubits: Total number of qubits in the circuit (including the flag qubit).
        dynamic: Whether to use a dynamic layout (default: False).
        hidden_string: The hidden bitstring to be found (default: alternating pattern of 1 and 0). If provided, its length must be num_qubits - 1.

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


@register_reference("bv")
def create_reference(num_qubits: int, dynamic: bool = False, hidden_string: str | None = None) -> ReferenceSpec:
    """Reference spec for the Bernstein-Vazirani circuit.

    BV is deterministic: measuring the circuit always recovers the hidden
    bitstring with probability 1.

    The hidden string is ``num_qubits - 1`` bits long (qubit 0 is the flag
    ancilla).  The default hidden string alternates 0 and 1 starting from
    qubit 1, matching the ``create_circuit`` default.

    Qiskit bit-string convention: classical bit *i* is the rightmost
    character offset by *i*, so the measured string is the hidden string
    written in *reverse* (``hidden_string[::-1]``).

    Arguments:
        num_qubits: total qubits including the flag (same as :func:`create_circuit`).
        dynamic: not used for the reference; kept for API symmetry.
        hidden_string: the secret bitstring of length ``num_qubits - 1``.
    """
    if hidden_string is None:
        hidden_string = "".join([str(i % 2) for i in range(num_qubits - 1)])

    # Qiskit big-endian
    # string is hidden_string written right-to-left.
    qiskit_string = hidden_string[::-1]

    return ReferenceSpec(
        circuit="bv",
        n_qubits=num_qubits,
        measured_qubits=list(range(1, num_qubits)),
        bit_order="qiskit-little-endian",
        reference=SparseReference(entries={qiskit_string: 1.0}),
        objective=ObjectiveSpec(type="hidden_string", value=hidden_string),
        metrics={
            "hellinger_fidelity": MetricApplicability(applicable=True, ideal=1.0),
            "tvd": MetricApplicability(applicable=True, ideal=0.0),
            "success_probability": MetricApplicability(applicable=True, ideal=1.0),
            "linear_xeb": MetricApplicability(applicable=False),
        },
    )
