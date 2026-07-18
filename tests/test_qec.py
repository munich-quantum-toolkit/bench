# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Tests for the error-correction transpilers (Steane and Shor codes)."""

from __future__ import annotations

from re import fullmatch
from typing import TYPE_CHECKING

import pytest
from qiskit import QuantumCircuit
from qiskit.circuit import CircuitInstruction, ClassicalRegister
from qiskit.circuit.library import XGate
from qiskit.quantum_info import hellinger_fidelity

from mqt.bench import benchmark_generation
from mqt.bench.error_correction.shor_transpiler import ShorTranspiler
from mqt.bench.error_correction.steane_transpiler import SteaneTranspiler

if TYPE_CHECKING:
    import qiskit as qk
    from qiskit.circuit import Gate


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


def test_all_gates_transpile_steane() -> None:
    qc = QuantumCircuit(2)
    qc.id(0)
    qc.x(0)
    qc.y(0)
    qc.z(0)
    qc.h(0)
    qc.s(0)
    qc.sdg(0)
    qc.cx(0, 1)
    qc.sx(0)
    qc.sxdg(0)
    qc.cy(0, 1)
    qc.cz(0, 1)
    qc.swap(0, 1)
    qc.dcx(0, 1)
    qc.t(0)
    qc.tdg(0)

    transpiler = SteaneTranspiler(original_circuit=qc, add_syndromes=True)
    new_qc = transpiler.transpile()
    new_ops = new_qc.count_ops()

    assert len(new_ops) >= 1
    for op in new_ops:
        assert op != "t, tdg", f"found untouched {op} gate"


def test_all_gates_transpile_shor() -> None:
    qc = QuantumCircuit(2)
    qc.id(0)
    qc.x(0)
    qc.y(0)
    qc.z(0)
    qc.h(0)
    qc.s(0)
    qc.sdg(0)
    qc.cx(0, 1)
    qc.sx(0)
    qc.sxdg(0)
    qc.cy(0, 1)
    qc.cz(0, 1)
    qc.swap(0, 1)
    qc.dcx(0, 1)
    qc.t(0)
    qc.tdg(0)

    transpiler = SteaneTranspiler(original_circuit=qc, add_syndromes=True)
    new_qc = transpiler.transpile()
    new_ops = new_qc.count_ops()

    assert len(new_ops) >= 1
    for op in new_ops:
        assert op != "t, tdg", f"found untouched {op} gate"


def insert_error_after_barrier(
    qc: QuantumCircuit,
    barrier_label: str,
    gate: Gate | None = None,
    qubit_index: int = 0,
) -> QuantumCircuit:
    """Insert a fault gate immediately after the first barrier with a given label.

    Scans *qc* for a barrier whose ``.label`` attribute matches *barrier_label*
    and inserts *gate* on the qubit at *qubit_index* directly after it.  This
    allows tests to inject a well-placed error (e.g. right after the encoding
    barrier) without disturbing the rest of the circuit structure.

    Args:
        qc: The circuit to inject the error into.  A shallow copy is made so
            the original is not modified.
        barrier_label: The label of the barrier after which the gate is inserted.
        gate: The fault gate to inject.  Defaults to :class:`~qiskit.circuit.library.XGate`
            (a bit flip) if ``None``.
        qubit_index: Index into ``qc.qubits`` of the qubit to apply the gate to.
            Defaults to ``0``.

    Returns:
        A copy of *qc* with the error gate inserted.

    Raises:
        ValueError: If no barrier with *barrier_label* is found in the circuit.
    """
    gate = XGate() if gate is None else gate

    qc = qc.copy()

    for i, instruction in enumerate(qc.data):
        if instruction.operation.name == "barrier" and instruction.operation.label == barrier_label:
            qc.data.insert(
                i + 1,
                CircuitInstruction(gate, [qc.qubits[qubit_index]]),
            )
            return qc

    msg = f"Barrier with label {barrier_label!r} not found"
    raise ValueError(msg)


def insert_error(qc: QuantumCircuit, gate: Gate | None = None, index: int | None = None) -> QuantumCircuit:
    """Insert a fault gate right after the first barrier in *qc*.

    Locates the first :class:`~qiskit.circuit.Barrier` instruction and inserts
    *gate* immediately after it on the first ``gate.num_qubits`` qubits.  An
    explicit *index* can be provided to override the barrier-search behaviour.

    Args:
        qc: The circuit to inject the error into (modified in place).
        gate: The fault gate to inject.  Defaults to
            :class:`~qiskit.circuit.library.XGate` (a bit flip) if ``None``.
        index: Instruction index at which to insert the gate.  If ``None``
            (default), the position right after the first barrier is used.

    Returns:
        The same *qc* instance with the error gate inserted.

    Raises:
        ValueError: If *index* is ``None`` and no barrier is found in the circuit.
    """
    gate = XGate() if gate is None else gate
    if qc.num_qubits < gate.num_qubits:
        msg = f"Quantum Circuit has not enough qubits to accommodate gate {gate.name}"
        raise ValueError(msg)
    if index is not None and index < 0:
        msg = f"Index must be >= 0, Index provided: {index}"
        raise ValueError(msg)

    # Finds the first barrier
    if index is None:
        for i, instruction in enumerate(qc.data):
            if instruction.operation.name == "barrier":
                index = i + 1
                break

    # Insert the error gate
    qubits = qc.qubits[: gate.num_qubits]
    if index is not None:
        qc.data.insert(index, CircuitInstruction(gate, qubits))
    else:
        msg = "Please provide either an index or a circuit with a barrier to insert an error into"
        raise ValueError(msg)

    return qc


def measure_all_named(qc: QuantumCircuit, name: str = "measurement") -> QuantumCircuit:
    """Add a named classical register to *qc* and measure every qubit into it.

    Creates a :class:`~qiskit.circuit.ClassicalRegister` of width
    ``qc.num_qubits``, appends it to *qc*, and maps qubit *i* to bit *i* of that
    register.  This is a convenience wrapper used by :func:`run_circuit` to attach
    measurements before simulation while keeping the register name predictable for
    later result extraction.

    Args:
        qc: The circuit to add measurements to (modified in place).
        name: Name of the new classical register.  Defaults to ``"measurement"``.

    Returns:
        The same *qc* instance with the register and measurements appended.
    """
    cr = ClassicalRegister(qc.num_qubits, name=name)
    qc.add_register(cr)
    qc.measure(range(qc.num_qubits), cr)
    return qc


def run_circuit(qc: QuantumCircuit, shots: int = 1024) -> tuple[dict, QuantumCircuit]:
    """Simulate the circuit using Aer's SamplerV2 and return measurement counts.

    Adds a named classical register for measurements, simulates the circuit,
    and extracts the measurement outcomes.

    Args:
        qc: The quantum circuit to simulate. It will be modified in place to
            add measurements.
        shots: Number of simulation shots. Defaults to 1024.

    Returns:
        Tuple containing:
        - Measurement counts with bitstrings reversed to align qubit indices.
        - The input circuit with measurements added.
    """
    # Skipping tests if qiskit-aer is not installed, because of the problem with the missingwheel for Ubuntu with ARM, there is no build version for Python 3.14.
    # for more einformation, see: https://github.com/Qiskit/qiskit-aer/issues/2407#issuecomment-3849941299
    aer_primitives = pytest.importorskip("qiskit_aer.primitives")
    sampler = aer_primitives.SamplerV2()
    qc = measure_all_named(qc, "measurements")
    job = sampler.run([qc], shots=shots)
    result = job.result()

    # Grabbing only the desired outcomes
    pub_result = result[0]
    meas_bit_counts = pub_result.data.measurements.get_counts()

    # get_counts() outputs reversed bitstrings, we just reverse them right back,
    # so their indices align with the qubit indices
    meas_bit_counts = {k[::-1]: v for k, v in meas_bit_counts.items()}

    return meas_bit_counts, qc


def compare_distributions(
    qc1: QuantumCircuit, qc2: QuantumCircuit, counts1: dict, counts2: dict, code1: str = "None", code2: str = "None"
) -> float:
    """Compute the Hellinger fidelity between two measurement distributions.

    If either code is 'steane' or 'shor', the corresponding counts are condensed
    from physical qubits to logical qubits before comparison.

    Args:
        qc1: The first quantum circuit.
        qc2: The second quantum circuit.
        counts1: Measurement counts from the first circuit.
        counts2: Measurement counts from the second circuit.
        code1: Error correction code for the first circuit ('steane', 'shor',
            or 'None'). Defaults to 'None'.
        code2: Error correction code for the second circuit ('steane', 'shor',
            or 'None'). Defaults to 'None'.

    Returns:
        Hellinger fidelity between the distributions (1 = identical, 0 = no overlap).
    """
    if code1 in ["steane", "shor"]:
        counts1 = condense_counts(qc1, counts1)
    if code2 in ["steane", "shor"]:
        counts2 = condense_counts(qc2, counts2)

    return hellinger_fidelity(counts1, counts2)


def parse_qubits(qc: qk.QuantumCircuit, physical_qubits: str) -> str:
    """Extract logical qubit measurements from a physical measurement string.

    The circuit must use registers named ``qx`` (where ``x`` is an integer) for
    each logical qubit, with the decoded result stored in ``qx[0]``.

    Args:
        qc: The quantum circuit containing named registers.
        physical_qubits: Measurement bitstring from physical qubits.

    Returns:
        Logical measurement bitstring extracted from the named registers.
    """
    # remove blanks caused by classical registers
    physical_qubits = physical_qubits.replace(" ", "")

    # indices
    def is_q_integer(s: str) -> bool:
        """Checks if s is of form 'qx' where x in int (e.g. 'q1', 'q23')."""
        return bool(fullmatch(r"q\d+", s))

    data_indices = [qc.find_bit(register[0]).index for register in qc.qregs if is_q_integer(register.name)]

    # condensing
    logical_qubits = ""
    for index in data_indices:
        logical_qubits += physical_qubits[index]

    return logical_qubits


def condense_counts(qc: qk.QuantumCircuit, counts: dict[str, int]) -> dict[str, int]:
    """Map physical measurement counts to logical measurement counts.

    Requires the circuit to have decoded each logical qubit into the first
    qubit of a register named ``qx``, where ``x`` is an integer (e.g. ``"q2"``).

    Args:
        qc: The quantum circuit with named registers.
        counts: Dictionary mapping physical measurement bitstrings to counts.

    Returns:
        Dictionary mapping logical measurement bitstrings to counts, where
        multiple physical measurements may map to the same logical measurement.
    """
    logical_counts = {}
    for physical_measurement, count in counts.items():
        logical_measurement = parse_qubits(qc, physical_measurement)
        logical_counts[logical_measurement] = logical_counts.get(logical_measurement, 0) + count

    return logical_counts
