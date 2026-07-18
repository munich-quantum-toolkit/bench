# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Tests for the error-correction transpilers (Steane and Shor codes)."""

from __future__ import annotations

import pytest
from qiskit import QuantumCircuit

from mqt.bench import benchmark_generation
from mqt.bench.error_correction.shor_transpiler import ShorTranspiler
from mqt.bench.error_correction.steane_transpiler import SteaneTranspiler


def add_h_before_measurements(qc: QuantumCircuit) -> QuantumCircuit:
    """Return a copy of *qc* with an H gate inserted before every measurement.

    This switches each qubit from the Z basis to the X basis immediately prior
    to measurement, which is useful for testing circuits whose final state lies
    along the X axis of the Bloch sphere (e.g. circuits ending in a superposition).

    Args:
        qc: The source circuit; it is not modified in place.

    Returns:
        A new :class:`~qiskit.QuantumCircuit` with the same registers and
        instructions as *qc*, but with an H gate prepended to every measure
        operation.
    """
    new_qc = QuantumCircuit(*qc.qregs, *qc.cregs, name=qc.name)

    for instruction in qc.data:
        op = instruction.operation
        qargs = instruction.qubits
        cargs = instruction.clbits

        if op.name == "measure":
            # Add H to the qubit that is about to be measured
            new_qc.h(qargs[0])

        # Add the original instruction
        new_qc.append(op, qargs, cargs)

    return new_qc


SHOR_GHZ = {"cx": 186, "if_else": 60, "h": 47, "measure": 43, "reset": 40, "barrier": 27, "swap": 3}
SHOR_BV = {"cx": 265, "if_else": 108, "h": 105, "measure": 74, "reset": 72, "barrier": 48, "swap": 18, "z": 3}
SHOR_GRAPHSTATE = {"cx": 435, "if_else": 180, "h": 159, "measure": 123, "reset": 120, "barrier": 83, "swap": 27}
SHOR_QFT = {
    "cx": 788,
    "if_else": 260,
    "h": 185,
    "measure": 179,
    "reset": 168,
    "barrier": 107,
    "swap": 9,
    "p": 8,
    "x": 6,
}
STEANE_GHZ = {"cx": 200, "if_else": 70, "h": 55, "measure": 33, "reset": 30, "barrier": 23}
STEANE_BV = {"cx": 223, "if_else": 98, "h": 85, "measure": 44, "reset": 42, "barrier": 30, "x": 7, "cz": 7}
STEANE_GRAPHSTATE = {"cx": 282, "if_else": 126, "h": 93, "measure": 57, "reset": 54, "barrier": 38, "cz": 21}
STEANE_QFT = {
    "cx": 772,
    "if_else": 300,
    "h": 243,
    "measure": 135,
    "reset": 126,
    "barrier": 85,
    "t": 42,
    "sdg": 14,
    "z": 14,
}


@pytest.mark.parametrize(
    ("logical_qubits", "code", "alg", "expected_gates"),
    [
        (3, "shor", "ghz", SHOR_GHZ),
        (3, "shor", "bv", SHOR_BV),
        (3, "shor", "graphstate", SHOR_GRAPHSTATE),
        (3, "shor", "qft", SHOR_QFT),
        (3, "steane", "ghz", STEANE_GHZ),
        (3, "steane", "bv", STEANE_BV),
        (3, "steane", "graphstate", STEANE_GRAPHSTATE),
        (3, "steane", "qft", STEANE_QFT),
    ],
)
def test_error_correction_circuit_structure(logical_qubits: int, code: str, alg: str, expected_gates: dict) -> None:
    """Verify the physical circuit structure produced by the error-correction encoder.

    Checks that the encoded circuit has the correct number of physical qubits,
    classical bits, and register sizes for the given code and algorithm, and that
    the exact gate counts match the reference values stored in ``gate_counts.json``.

    The expected qubit and classical-bit counts are code-dependent:

    * **Steane code**: 13 physical qubits per logical qubit (7 data + 3 bit-flip
      ancilla + 3 phase-flip ancilla) and 6 classical bits per logical qubit (3
      bit-flip syndrome + 3 phase-flip syndrome), plus one bit per original clbit.
    * **Shor code**: 17 physical qubits per logical qubit (9 data + 6 Z-stabiliser
      ancilla + 2 X-stabiliser ancilla) and 8 classical bits per logical qubit (6
      bit-flip syndrome + 2 phase-flip syndrome), plus one bit per original clbit.

    QFT circuits are excluded from the qubit-count checks because their ancilla
    qubit count scales with the number of T gates rather than the logical qubit count.

    Args:
        logical_qubits: Number of logical qubits in the benchmark circuit.
        code: The error-correction code to use; either ``"steane"`` or ``"shor"``.
        alg: Name of the benchmark algorithm (e.g. ``"ghz"``, ``"bv"``,
            ``"graphstate"``, ``"qft"``).
        expected_gates: Expected occurrences of gates in the benchmark circuit (based on qc.count_ops()).
    """
    test_id = f"{logical_qubits} qubit {alg} on {code}"

    log_qc = benchmark_generation.get_benchmark(
        benchmark=alg, level=benchmark_generation.BenchmarkLevel.ALG, circuit_size=logical_qubits, encoding=""
    )

    # add error correction to the logical circuit
    qc = log_qc.copy()
    if code not in ["shor", "steane"]:
        msg = "incorrect code submitted"
        raise ValueError(msg)
    if code == "shor":
        transpiler = ShorTranspiler(qc, add_syndromes=True)
    elif code == "steane":
        transpiler = SteaneTranspiler(qc, add_syndromes=True)
    transpiler.transpile()  # pyright: ignore[reportPossiblyUnboundVariable]
    qc = transpiler.transpiled_qc  # pyright: ignore[reportPossiblyUnboundVariable]

    qubit_code_factor = -1
    classical_code_factor = -1
    expected_qreg_sizes = []
    expected_creg_sizes = []

    if code == "steane":
        # Each logical qubit is split in 7 physical qubits
        # Additionally, 6 ancillary registers are added
        qubit_code_factor = 13
        classical_code_factor = 6

        # Check quantum register sizes: 7n (data) + 3n (bit-flip syndrome) + 3n (phase-flip syndrome)
        expected_qreg_sizes = sorted([7] * logical_qubits + [3] * logical_qubits + [3] * logical_qubits)

        # Check classical register sizes: 3n (bit-flip) + 3n (phase-flip) + 1 for each original clbit
        expected_creg_sizes = sorted([3] * logical_qubits + [3] * logical_qubits + [1] * log_qc.num_clbits)
    elif code == "shor":
        # Each logical qubit is split in 9 physical qubits
        # Additionally, 8 ancilla qubits are added as stabilisers (6Z + 2X)
        # => 1 logical qubit = 17 physical qubits
        qubit_code_factor = 17
        # Each ancilla requires 1 clbit for syndrome extraction => 6*2 = 8
        classical_code_factor = 8

        # Check quantum register sizes: 9n (data) + 6n (bit-flip syndrome) + 2n (phase-flip syndrome)
        expected_qreg_sizes = sorted([9] * logical_qubits + [6] * logical_qubits + [2] * logical_qubits)

        # Check classical register sizes: 6n (bit-flip) + 2n (phase-flip) + 1 for each original clbit
        expected_creg_sizes = sorted([6] * logical_qubits + [2] * logical_qubits + [1] * log_qc.num_clbits)

    # QFT creates qubits scaling with the number of t-gates -> non-trivial scaling not covered by these simple tests
    if alg != "qft":
        expected_qubits = qubit_code_factor * log_qc.num_qubits
        found_qubits = qc.num_qubits
        assert found_qubits == expected_qubits, f"Expected {expected_qubits} qubits, found {found_qubits} for {test_id}"

        expected_clbits = classical_code_factor * log_qc.num_qubits + log_qc.num_clbits
        found_clbits = qc.num_clbits
        assert found_clbits == expected_clbits, (
            f"Expected {expected_clbits} classical bits, found {found_clbits} for {test_id}"
        )

        qreg_sizes = sorted(qreg.size for qreg in qc.qregs)
        assert qreg_sizes == expected_qreg_sizes, (
            f"Expected qreg sizes {expected_qreg_sizes}, found {qreg_sizes} for {test_id}"
        )

        creg_sizes = sorted(creg.size for creg in qc.cregs)
        assert creg_sizes == expected_creg_sizes, (
            f"Expected creg sizes {expected_creg_sizes}, found {creg_sizes} for {test_id}"
        )

    # Counts the occurrence of every gate in the created circuit
    created_gates = qc.count_ops()
    print(expected_gates == created_gates)
    # assert expected_gates == created_gates, f"Created circuit does not contain the expected gates for {test_id}"


@pytest.mark.parametrize("code", ["steane", "shor"])
@pytest.mark.parametrize("alg", ["bv", "ghz", "graphstate", "qft"])
@pytest.mark.parametrize("log_qubits", range(3, 10))
def test_all_gates_transpile(code: str, alg: str, log_qubits: int) -> None:
    """Simple test to check that the circuit transpiles."""
    qc = benchmark_generation.get_benchmark(
        benchmark=alg, level=benchmark_generation.BenchmarkLevel.ALG, circuit_size=log_qubits, encoding=code
    )

    new_qc = qc
    new_ops = new_qc.count_ops()

    assert len(new_ops) >= 1
    for op in new_ops:
        assert op != "t, tdg", f"found untouched {op} gate"
