# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

# TODO:
# uv requirements to be added: mqt.qcec, qiskit_aer


# What do we want to test:
# 1 function for each, split steane and shor for hardcoded sanity, combine for equvalencies
# transpilers work as intended (simply sanity checks) ✅
# transpilers produce correct logical circuits (equivalency & simulation)
# produce circuits lead to correct results (equivalency (possible?) & simulations)
# works for all 4 given algorithms (maybe incorporate into correctness and error correction)

# Have the ability to save the created circuits (utility function)
## save to file vs print vs logging?

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from qiskit import QuantumCircuit, transpile
from qiskit.circuit import CircuitInstruction
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
    if gate.name == "s" and code == "shor":
        # this SGate entails non-unitary elements and can therefore not be evaluated properly
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


@pytest.mark.parametrize("code", ["shor", "steane"])  #  "shor",  double parametrize leads to crossproduct
@pytest.mark.parametrize("algorithm", ["ghz", "bv", "graphstate"])  # , , "bv", "graphstate""qft"])
@pytest.mark.parametrize("Error", [XGate(), ZGate()])  # , , "bv", "graphstate""qft"])
@pytest.mark.parametrize("MeasureBaseX", [True, False])  # , , "bv", "graphstate""qft"])
def test_errorcorrection_transpiler_correctness(code: str, algorithm: str, Error, MeasureBaseX: bool) -> None:
    """Ensures the transpiler creates error-corrected circuits which produce the same result as the orinigal logical circuit.
    Afterwards an error is introduced and the test checks, whether it is corrected.
    Iterates over a number of example algorithms.
    """
    if algorithm == "qft" and code == "shor":
        # this takes a little longer....
        return
    circuit_size = 3
    # Initialize circuits
    logical_circuit = benchmark_generation.get_benchmark(
        benchmark=algorithm, level=benchmark_generation.BenchmarkLevel.ALG, circuit_size=circuit_size, encoding=code
    )

    if MeasureBaseX:
        logical_circuit = add_h_before_measurements(logical_circuit)

    if algorithm == "qft":
        basis = ["h", "s", "t", "x", "z", "cx", "cz"]

        logical_circuit = transpile(logical_circuit, basis_gates=basis)
        print(logical_circuit.decompose().count_ops())

    # Strip measure gates to avoid intermediate measurements collapsing the state before decoding
    stripped_logical_circuit = QuantumCircuit(*logical_circuit.qregs)
    for inst in logical_circuit.data:
        if inst.operation.name != "measure":
            stripped_logical_circuit.append(inst.operation, inst.qubits, [])
    logical_circuit = stripped_logical_circuit

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
    # error_induced_circuit = insert_error(error_induced_circuit ,gate=XGate())
    error_induced_circuit = insert_error_after_barrier(
        error_corrected_circuit,
        barrier_label="Encoding",
        gate=Error,
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

    # log_circuits({f'log_{code}_{algorithm}':logical_circuit,
    #              f'corrected_{code}_{algorithm}':error_corrected_circuit,
    #              f'induced_{code}_{algorithm}':error_induced_circuit,})

    # print(corrected_counts)
    print("condensed:", condense_counts(error_corrected_circuit, corrected_counts))
    print("Logical", logical_counts)

    assert logical_corrected_fidelity >= 0.99, (
        f"Error corrected circuit created by {code} transpiler for Algorithm {algorithm} does not match its logical circuit well enough."
    )
    assert corrected_induced_fidelity >= 0.99, (
        f"Error corrected circuit created by {code} transpiler for Algorithm {algorithm} does not correct the bitflip well enough."
    )


def insert_error_after_barrier(
    qc: QuantumCircuit,
    barrier_label: str,
    gate: Gate = XGate(),
    qubit_index: int = 0,
) -> QuantumCircuit:
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


def insert_error(qc: QuantumCircuit, gate: Gate = XGate(), index: int | None = None) -> QuantumCircuit:
    """Adds the specified gate at the beginning of the circuit
    Flips the first qubit right after the first barrier by default.
    """
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
        raise Exception(msg)

    return qc


def check_equivalence(qc1: qk.QuantumCircuit, qc2: qk.QuantumCircuit) -> bool:
    """Uses MQT QCEC to verify if qc1 and qc2 are equivalent."""
    import mqt.qcec
    from mqt.qcec.pyqcec import EquivalenceCriterion as EC

    verification_results = mqt.qcec.verify(qc1, qc2)
    accepted_equivalencies = [EC.equivalent, EC.equivalent_up_to_global_phase, EC.probably_equivalent]
    return verification_results.equivalence in accepted_equivalencies


def run_circuit(qc: QuantumCircuit, shots: int = 1024) -> tuple[dict, QuantumCircuit]:
    """Simulates the circuit using AerSimulator.

    Adds measurements to all qubits, adds new classical registers for each.
    Reads out ONLY those measurements and returns their counts

    Returns:
        counts of all quantum registers

        qc with measure_all()
    """
    sampler = SamplerV2()
    qc.measure_all()
    job = sampler.run([qc], shots=shots)
    result = job.result()

    # Grabbing only the desired outcomes
    pub_result = result[0]
    meas_bit_counts = pub_result.data.meas.get_counts()
    # outputs reversed bitstrings, we just reverse them right back,
    # so their indices align with the qubit indices
    meas_bit_counts = {k[::-1]: v for k, v in meas_bit_counts.items()}

    return meas_bit_counts, qc


def compare_distributions(
    qc1: QuantumCircuit, qc2: QuantumCircuit, counts1: dict, counts2: dict, code1: str = "None", code2: str = "None"
) -> float:
    """Simulates 2 circuits and computes the Hellinger Fidelity between their count distributions
    1 = the same, 0 = no overlap.

    If code is set to either 'steane' or 'shor' circuit error's result will be interpreted logically
    """
    if code1 in ["steane", "shor"]:
        counts1 = condense_counts(qc1, counts1)
    if code2 in ["steane", "shor"]:
        counts2 = condense_counts(qc2, counts2)

    return hellinger_fidelity(counts1, counts2)


def parse_qubits(qc: qk.QuantumCircuit, physical_qubits: str):
    """Takes in a measurement in physical qubits and returns the corresponding logical measurement.

    Underlying circuit must use registers named 'qx' (x in int) for each logical qubit, with results in qx[0]
    """
    # remove blanks caused by classical registers
    physical_qubits = physical_qubits.replace(" ", "")

    # indices
    import re

    def is_q_integer(s: str) -> bool:
        """Checks if s is of form 'qx' where x in int (e.g. 'q1', 'q23')."""
        return bool(re.fullmatch(r"q\d+", s))

    data_indices = [qc.find_bit(register[0]).index for register in qc.qregs if is_q_integer(register.name)]

    # condensing
    logical_qubits = ""
    for index in data_indices:
        logical_qubits += physical_qubits[index]

    return logical_qubits


def condense_counts(qc: qk.QuantumCircuit, counts: dict[str, int]) -> dict[str, int]:
    """Takes in a result dict of a decoded physical measurement and returns logical measurements
    Requires decode to place the result in the first qubit of each register named 'qx', with x an integer (e.g. 'q2').
    """
    # assert code in ['shor', 'steane'], f'Unsupported error code in condense_counts(): {code}'
    logical_counts = {}
    for physical_measurement, count in counts.items():
        logical_measurement = parse_qubits(qc, physical_measurement)
        logical_counts[logical_measurement] = logical_counts.get(logical_measurement, 0) + count

    return logical_counts


def log_circuits(circuits: dict[str, QuantumCircuit]) -> None:
    log_dir = Path(__file__).parent / "circuit_drawings"
    log_dir.mkdir(exist_ok=True)

    for name, circuit in circuits.items():
        with Path(log_dir / f"{name}_transpiled.txt").open("w", encoding="utf-8") as f:
            f.write(f"number of qubits {circuit.num_qubits}\n")
            f.write(f"--- Transpiled Circuit for {name.upper()} ---\n\n")
            f.write(str(circuit.draw(fold=-1)) + "\n")

        import matplotlib.pyplot as plt

        fig = circuit.draw(output="mpl", fold=-1)
        fig.savefig(log_dir / f"{name}_transpiled.png", dpi=150, bbox_inches="tight")
        plt.close(fig)
