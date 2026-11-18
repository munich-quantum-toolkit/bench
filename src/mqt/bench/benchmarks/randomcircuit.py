# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Random benchmark definition."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qiskit.circuit.random import random_circuit

from ._registry import register_benchmark

if TYPE_CHECKING:
    from qiskit.circuit import QuantumCircuit


@register_benchmark("randomcircuit", description="Random Quantum Circuit")
def create_circuit(num_qubits: int, seed: int | None = 10) -> QuantumCircuit:
    """Build a random circuit with up to four qubits per gate.

    Args:
        num_qubits: Circuit width. The requested gate depth is twice this value,
            before final measurements.
        seed: Seed for circuit construction. Use an integer to reproduce the gates.

    Returns:
        A circuit with final measurements on all qubits.
    """
    qc = random_circuit(num_qubits, num_qubits * 2, measure=False, seed=seed)
    qc.measure_all()
    qc.name = "randomcircuit"
    return qc
