# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Grover benchmark with structured control flow."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ._registry import register_benchmark
from .grover import _create_circuit

if TYPE_CHECKING:
    from qiskit.circuit import QuantumCircuit


@register_benchmark("grover_for_loop", description="Grover's Algorithm with For-Loop Control Flow")
def create_circuit(num_qubits: int) -> QuantumCircuit:
    """Return a Grover circuit whose iterations use a Qiskit for-loop operation.

    Arguments:
        num_qubits: number of qubits of the returned quantum circuit
    """
    return _create_circuit(num_qubits, use_for_loop=True, name="grover_for_loop")
