# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Tests for quantum walks on two nodes."""

from __future__ import annotations

import pytest
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator
from qiskit.transpiler import PassManager
from qiskit.transpiler.passes import UnrollForLoops

from mqt.bench.benchmark_generation import BenchmarkLevel, get_benchmark
from mqt.bench.benchmarks import create_circuit


@pytest.mark.parametrize("depth", [1, 2, 3])
@pytest.mark.parametrize("for_loop", [False, True])
def test_two_qubit_quantum_walk(depth: int, *, for_loop: bool) -> None:
    """On two nodes, each step flips the node regardless of the coin state."""
    circuit = create_circuit("qwalk", 2, depth=depth, for_loop=for_loop)
    assert circuit.num_qubits == 2
    assert circuit.count_ops()["measure"] == 2
    circuit.remove_final_measurements()
    circuit = PassManager(UnrollForLoops()).run(circuit)

    expected = QuantumCircuit(2)
    for _ in range(depth):
        expected.h(1)
        expected.x(0)
    assert Operator(circuit).equiv(Operator(expected))


def test_two_qubit_quantum_walk_mirror() -> None:
    """A two-qubit quantum walk followed by its inverse acts as the identity."""
    circuit = get_benchmark("qwalk", BenchmarkLevel.ALG, 2, generate_mirror_circuit=True)
    circuit.remove_final_measurements()
    assert Operator(circuit).equiv(Operator(QuantumCircuit(2)))
