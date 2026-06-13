# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Tests for the error-correction transpilers (Steane and Shor codes)."""

from __future__ import annotations

import json
from pathlib import Path
from re import fullmatch
from typing import TYPE_CHECKING

import mqt.qcec
import pytest
from mqt.qcec.pyqcec import EquivalenceCriterion
from qiskit import QuantumCircuit
from qiskit.circuit import CircuitInstruction, ClassicalRegister
from qiskit.circuit.library import CXGate, CZGate, HGate, SGate, XGate, ZGate
from qiskit.quantum_info import hellinger_fidelity
from qiskit_aer.primitives import SamplerV2

import mqt.bench.benchmark_generation as benchmark_generation
from mqt.bench.error_correction.shor_transpiler import ShorTranspiler
from mqt.bench.error_correction.steane_transpiler import SteaneTranspiler

if TYPE_CHECKING:
    import qiskit as qk
    from qiskit.circuit import Gate


@pytest.mark.parametrize("code", ["steane", "shor"])
@pytest.mark.parametrize("gate", [XGate(), ZGate(), HGate(), SGate()])
def test_errorcorrection_transpiler_gate_equivalence(code: str, gate: Gate) -> None:
    """Verify that the error-correction transpiler preserves gate semantics.

    For each supported single-qubit gate, builds a minimal logical circuit
    containing only that gate, transpiles it with syndrome extraction disabled,
    decodes the physical qubits back to logical qubits, and then checks via
    MQT QCEC that the resulting circuit is unitarily equivalent to the original.
    """
    if gate.name == "s" and code == "shor":
        # this SGate includes non-unitary elements and can therefore not be evaluated properly
        return

    num_qubits = gate.num_qubits
    logical_circuit = QuantumCircuit(num_qubits)
    logical_circuit.append(gate, qargs=list(range(num_qubits)))

    error_corrected_circuit = logical_circuit.copy()
    if code == "shor":
        transpiler = ShorTranspiler(error_corrected_circuit, add_syndromes=False)
    else:
        transpiler = SteaneTranspiler(error_corrected_circuit, add_syndromes=False)
    transpiler.transpile()
    transpiler.decode_qubits()
    error_corrected_circuit = transpiler.transpiled_qc

    assert check_equivalence(logical_circuit, error_corrected_circuit), (
        f"Transpiler {code} does not convert Gate {gate.name} to its logical equivalent"
    )


@pytest.mark.parametrize("code", ["steane", "shor"])
@pytest.mark.parametrize("gate", [XGate(), ZGate(), HGate(), SGate(), CXGate(), CZGate()])
def test_errorcorrection_transpiler_gate_correctness(code: str, gate: Gate) -> None:
    """Verify that the transpiler actually corrects an introduced bit-flip error.

    Builds a minimal single-gate logical circuit, transpiles it with full syndrome
    extraction enabled, and then creates a copy in which a bit-flip (X gate) is
    injected after the first barrier. Both the clean and the error-induced circuits
    are simulated, and the test asserts that:

    1. The error-corrected circuit matches the logical circuit.
    2. The error-induced circuit still matches the clean corrected circuit.
    """
    if gate.name == "s" and code == "shor":
        # this takes a little longer....
        return

    num_qubits = gate.num_qubits
    logical_circuit = QuantumCircuit(num_qubits)
    logical_circuit.append(gate, qargs=list(range(num_qubits)))
    error_corrected_circuit = logical_circuit.copy()
    if code == "shor":
        transpiler = ShorTranspiler(error_corrected_circuit, add_syndromes=True)
    else:
        transpiler = SteaneTranspiler(logical_circuit, add_syndromes=True)
    transpiler.transpile()
    transpiler.decode_qubits()
    error_corrected_circuit = transpiler.transpiled_qc

    error_induced_circuit = error_corrected_circuit.copy()
    # this is for inserting phase flip in steane after the first Hadamard
    # error_induced_circuit = insert_error(error_induced_circuit ,gate=ZGate(), index=16)
    error_induced_circuit = insert_error(error_induced_circuit, gate=XGate())

    logical_counts, logical_circuit = run_circuit(logical_circuit)
    corrected_counts, error_corrected_circuit = run_circuit(error_corrected_circuit)
    induced_counts, error_induced_circuit = run_circuit(error_induced_circuit)

    logical_corrected_fidelity = compare_distributions(
        logical_circuit, error_corrected_circuit, logical_counts, corrected_counts, "none", code
    )
    corrected_induced_fidelity = compare_distributions(
        error_corrected_circuit, error_induced_circuit, corrected_counts, induced_counts, code, code
    )

    assert logical_corrected_fidelity >= 0.99, (
        f"Error corrected circuit created by {code} transpiler for Gate {gate.name} does not match its logical circuit well enough."
    )
    assert corrected_induced_fidelity >= 0.99, (
        f"Error corrected circuit created by {code} transpiler for Gate {gate.name} does not correct the bitflip well enough."
    )


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


@pytest.mark.parametrize("code", ["shor", "steane"])
@pytest.mark.parametrize("algorithm", ["ghz", "bv", "graphstate"])  # "qft" is unfeasible
@pytest.mark.parametrize("error", [XGate(), ZGate()])
@pytest.mark.parametrize("measure_base_x", [True, False])
@pytest.mark.parametrize("circuit_size", [3])  # range(3, 11))
def test_errorcorrection_transpiler_correctness(
    code: str, algorithm: str, error: Gate, measure_base_x: bool, circuit_size: int
) -> None:
    """Ensures the transpiler creates error-corrected circuits which produce the same result as the original logical circuit.

    Afterwards an error is introduced and the test checks, whether it is corrected.
    Iterates over a number of example algorithms.
    """
    test_id = f"{circuit_size} qubit {algorithm} on {code} with ZBasis {measure_base_x} and error {error.name}"

    # Initialize circuits
    logical_circuit = benchmark_generation.get_benchmark(
        benchmark=algorithm, level=benchmark_generation.BenchmarkLevel.ALG, circuit_size=circuit_size, encoding=""
    )

    if measure_base_x:
        logical_circuit = add_h_before_measurements(logical_circuit)

    # Strip measure gates to avoid intermediate measurements collapsing the state before decoding
    stripped_logical_circuit = QuantumCircuit(*logical_circuit.qregs, *logical_circuit.cregs)
    for inst in logical_circuit.data:
        if inst.operation.name != "measure":
            stripped_logical_circuit.append(inst.operation, inst.qubits, inst.clbits)
    logical_circuit = stripped_logical_circuit

    if code == "shor":
        transpiler = ShorTranspiler(logical_circuit.copy(), add_syndromes=True)
    else:
        transpiler = SteaneTranspiler(logical_circuit.copy(), add_syndromes=True)
    transpiler.transpile()
    transpiler.decode_qubits()
    error_corrected_circuit = transpiler.transpiled_qc

    error_induced_circuit = error_corrected_circuit.copy()
    error_induced_circuit = insert_error_after_barrier(
        error_corrected_circuit,
        barrier_label="Encoding",
        gate=error,
        qubit_index=0,
    )

    logical_counts, logical_circuit = run_circuit(logical_circuit)
    corrected_counts, error_corrected_circuit = run_circuit(error_corrected_circuit)
    induced_counts, error_induced_circuit = run_circuit(error_induced_circuit)

    logical_corrected_fidelity = compare_distributions(
        logical_circuit, error_corrected_circuit, logical_counts, corrected_counts, "none", code
    )
    corrected_induced_fidelity = compare_distributions(
        error_corrected_circuit, error_induced_circuit, corrected_counts, induced_counts, code, code
    )

    assert logical_corrected_fidelity >= 0.99, (
        f"Error corrected circuit created does not match its logical circuit well enough for {test_id}"
    )
    assert corrected_induced_fidelity >= 0.99, (
        f"Error induced circuit created does not match correct the error well enough for {test_id}"
    )


@pytest.mark.parametrize("logical_qubits", range(3, 10))  # multiple parametrize lead to crossproducts
@pytest.mark.parametrize("alg", ["ghz", "bv", "graphstate", "qft"])
@pytest.mark.parametrize("code", ["shor", "steane"])
def test_error_correction_circuit_structure(code: str, alg: str, logical_qubits: int) -> None:
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
    """
    test_id = f"{logical_qubits} qubit {alg} on {code}"

    qc = benchmark_generation.get_benchmark(
        benchmark=alg, level=benchmark_generation.BenchmarkLevel.ALG, circuit_size=logical_qubits, encoding=code
    )
    log_qc = benchmark_generation.get_benchmark(
        benchmark=alg, level=benchmark_generation.BenchmarkLevel.ALG, circuit_size=logical_qubits, encoding=""
    )

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

    expected_gate_counts = None

    json_location = Path(__file__).parent / "gate_counts.json"
    with Path(f"{json_location}").open("r", encoding="utf-8") as json_data:
        expected_gate_counts = json.load(json_data)
        json_data.close()

    assert expected_gate_counts is not None, f"Failure reading respective gate counts for {test_id}"
    expected_gate_counts = expected_gate_counts[code][alg][f"{logical_qubits}"]

    # Counts the occurrence of every gate in the created circuit
    created_gate_counts = qc.count_ops()
    assert expected_gate_counts == created_gate_counts, (
        f"Created circuit does not contain the expected gates for {test_id}"
    )


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
        *qc* with the error gate inserted.

    Raises:
        ValueError: If *index* is ``None`` and no barrier is found in the circuit.
    """
    gate = XGate() if gate is None else gate
    assert qc.num_qubits >= gate.num_qubits, f"Quantum Circuit has not enough qubits to accommodate gate {gate.name}"
    assert index is None or index >= 0, f"Index must be >= 0, Index provided: {index}"

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


def check_equivalence(qc1: qk.QuantumCircuit, qc2: qk.QuantumCircuit) -> bool:
    """Uses MQT QCEC to verify if qc1 and qc2 are equivalent."""
    verification_results = mqt.qcec.verify(qc1, qc2, check_partial_equivalence=True)
    accepted_equivalencies = [
        EquivalenceCriterion.equivalent,
        EquivalenceCriterion.equivalent_up_to_global_phase,
        EquivalenceCriterion.probably_equivalent,
    ]
    return verification_results.equivalence in accepted_equivalencies


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
    """Simulates the circuit using AerSimulator.

    Adds measurements to all qubits, adds new classical registers for each.
    Reads out ONLY those measurements and returns their counts

    Returns:
        counts of all quantum registers

        qc with measure_all()
    """
    sampler = SamplerV2()
    qc = measure_all_named(qc, "measurements")
    job = sampler.run([qc], shots=shots)
    result = job.result()

    # Grabbing only the desired outcomes
    pub_result = result[0]
    meas_bit_counts = pub_result.data.measurements.get_counts()  # ty: ignore[unresolved-attribute]

    # outputs reversed bitstrings, we just reverse them right back,
    # so their indices align with the qubit indices
    meas_bit_counts = {k[::-1]: v for k, v in meas_bit_counts.items()}

    return meas_bit_counts, qc


def compare_distributions(
    qc1: QuantumCircuit, qc2: QuantumCircuit, counts1: dict, counts2: dict, code1: str = "None", code2: str = "None"
) -> float:
    """Simulates 2 circuits and computes the Hellinger Fidelity between their count distributions.

    Hellinger Fidelity: 1 = the same, 0 = no overlap.
    If code is set to either 'steane' or 'shor' circuit error's result will be interpreted logically
    """
    if code1 in ["steane", "shor"]:
        counts1 = condense_counts(qc1, counts1)
    if code2 in ["steane", "shor"]:
        counts2 = condense_counts(qc2, counts2)

    return hellinger_fidelity(counts1, counts2)


def parse_qubits(qc: qk.QuantumCircuit, physical_qubits: str) -> str:
    """Takes in a measurement in physical qubits and returns the corresponding logical measurement.

    Underlying circuit must use registers named 'qx' (x in int) for each logical qubit, with results in qx[0]
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
    """Takes in a result dict of a decoded physical measurement and returns logical measurements.

    Requires decode to place the result in the first qubit of each register named 'qx', with x an integer (e.g. 'q2').
    """
    logical_counts = {}
    for physical_measurement, count in counts.items():
        logical_measurement = parse_qubits(qc, physical_measurement)
        logical_counts[logical_measurement] = logical_counts.get(logical_measurement, 0) + count

    return logical_counts
