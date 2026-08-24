# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Quantum-walk benchmark using structured loop control flow."""

from __future__ import annotations

from qiskit.circuit import ForLoopOp, QuantumCircuit, QuantumRegister

from ._registry import register_benchmark
from .qwalk import _append_walk_step


@register_benchmark("qwalk_for_loop", description="Quantum Walk with For-Loop Control Flow")
def create_circuit(
    num_qubits: int,
    depth: int = 3,
    coin_state_preparation: QuantumCircuit | None = None,
) -> QuantumCircuit:
    """Create a quantum-walk circuit using a Qiskit ``ForLoopOp``.

    Arguments:
        num_qubits: Number of qubits in the returned circuit.
        depth: Number of quantum-walk steps.
        coin_state_preparation: Optional circuit preparing the coin state.

    Returns:
        A quantum-walk circuit with its repeated steps represented by a
        structured ``ForLoopOp``.
    """
    node = QuantumRegister(num_qubits - 1, "node")
    coin = QuantumRegister(1, "coin")
    qc = QuantumCircuit(node, coin, name="qwalk_for_loop")

    if coin_state_preparation is not None:
        qc.append(coin_state_preparation, coin[:])

    body = QuantumCircuit(node, coin)
    _append_walk_step(body, node, coin)
    qc.append(ForLoopOp(range(depth), None, body), qc.qubits)

    qc.measure_all()
    return qc
