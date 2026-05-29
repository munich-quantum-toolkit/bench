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

import numpy as np
import pytest
from pathlib import Path
from qiskit import QuantumCircuit
from qiskit.quantum_info import state_fidelity, Statevector

from mqt.bench.error_correction.shor_transpiler import ShorTranspiler
import mqt.bench.benchmark_generation as benchmark_generation
from qiskit_aer import AerSimulator # update uv requirements?
import qiskit as qk
from qiskit.circuit import CircuitInstruction, Gate
from qiskit.circuit.library import XGate



def test_shor_transpiler_structure():
    """
    Ensures the ShorTranspiler translates a basic circuit into a reasonable structure.
    Doesn't check for equivalence or correctness.
    """
    qc = QuantumCircuit(2, 1)
    qc.x(0)
    qc.z(1)
    qc.measure(1, 0)

    print("\n--- Logical Circuit ---")
    print(qc.draw(fold=-1))

    transpiler = ShorTranspiler(qc)
    transpiled_qc = transpiler.transpile()

    print("\n--- Transpiled Circuit ---")
    print(transpiled_qc)

    # 2 original qubits * 9 data qubits = 18 data qubits
    # 2 original qubits * 8 ancilla qubits = 16 ancilla qubits
    # Total qubits = 34
    assert transpiled_qc.num_qubits == 34

    # 2 original qubits * 8 classical bits = 16 syndrome bits
    # 1 measurement * 9 bits = 9 measurement bits
    # Total clbits = 25
    assert transpiled_qc.num_clbits == 25
    ##wrong expectations in the test it should check only non error correction gate mapping
    ops = [inst.operation.name for inst in transpiled_qc.data]
    assert "h" in ops
    assert "cx" in ops
    assert "measure" in ops

@pytest.mark.skip()
def test_steane_transpiler_structure():
    assert False

@pytest.mark.parametrize("code", ['shor']) #["steane", "shor"]) # double parametrize leads to crossproduct
@pytest.mark.parametrize("algorithm", ["ghz", "bv", "graphstate",]) # "qft"])
def test_errorcorrection_transpiler_equivalence(code: str, algorithm: str):
    """
    Ensures the transpiler creates error-corrected circuits which produce the same result as the orinigal logical circuit.
    Afterwards an error is introduced and the test checks, whether it is corrected.
    Iterates over a number of example algorithms.
    """
    circuit_size = 3
    # Initialize circuits
    logical_circuit = benchmark_generation.get_benchmark(
            benchmark=algorithm, level=benchmark_generation.BenchmarkLevel.ALG, circuit_size=circuit_size, encoding=code
        )
    error_corrected_circuit = logical_circuit.copy()
    transpiler = ShorTranspiler(error_corrected_circuit, add_syndromes=False)
    transpiler.transpile()
    transpiler.decode_qubits()
    error_corrected_circuit = transpiler.transpiled_qc
    error_induced_circuit = error_corrected_circuit.copy()
    error_induced_circuit = insert_error(error_induced_circuit)

    # run each circuit
    # compare results



def insert_error(qc: QuantumCircuit, gate: Gate = XGate(), index: int | None = None) -> QuantumCircuit:
    """
    Adds the specified gate at the beginning of the circuit
    Flips the first qubit right after the first barrier by default
    """
    assert qc.num_qubits >= gate.num_qubits, f'Quantum Circuit has not enough qubits to accomodate gate {gate.name}'
    assert index is None or index >= 0, f'Index must be >= 0, Index provided: {index}'
    
    # Finds the first barrier
    if index is None:
        for i, instruction in enumerate(qc.data):
            if instruction.operation.name == "barrier":
                index = i + 1
                break

    # Insert the error gate
    qubits = qc.qubits[:gate.num_qubits]
    qc.data.insert(index, CircuitInstruction(gate, qubits))

    return qc



############################################################################################################################################
############################################################################################################################################
############################################################################################################################################
############################################################################################################################################
############################################################################################################################################



def errorcode_testing(alg: str = 'ghz', code: str = 'shor', qubits: int = 3):
    assert qubits >= 3

    base_circuit = benchmark_generation.get_benchmark(
                benchmark=alg, level=benchmark_generation.BenchmarkLevel.ALG, circuit_size=qubits, encoding=code
            )
    error_circuit = base_circuit.copy(name='error_circuit')
    error_circuit = insert_error_gate(error_circuit)
    uncorrected_circuit = benchmark_generation.get_benchmark(
                benchmark=alg, level=benchmark_generation.BenchmarkLevel.ALG, circuit_size=qubits
            )


    ### Equivalence checking
    equivalent = check_equivalence(base_circuit, error_circuit)
    #assert equivalent, 'Insertion of an error (flipped qubit) has lead to a new, no longer equivalent circuit'
    print(f'Circuits are equivalent: {equivalent}')

    
    
    ### Simulated probabilistic similarity Base vs. Error-Inserted
    error_fidelity = compare_distributions(base_circuit, error_circuit)
    threshold = 0.95 # arbitrary guess
    #assert fidelity > threshold, f'Simulated Hellinger Fidelity between base and error circuit is too low. Measured: {fidelity}, >Expected: {threshold}'
    print(f'Hellinger Fidelity with error: {error_fidelity}')

    ### Simulated probabilistic similarity Uncorrected vs. Error-Inserted
    # TODO: put in error corrected circuit
    #### Example for condensing qubits
    example = {'00000001111111': 3, '10101011111111': 1, '11111111010101': 2, '10101011111110' : 7}
    print(condense_counts(example,'stean'))

    """
    uncorrected_fidelity = compare_distributions(uncorrected_circuit, error_circuit, code='shor')
    threshold = threshold # arbitrary guess
    #assert fidelity > threshold, f'Simulated Hellinger Fidelity between uncorrected and error circuit is too low. Measured: {uncorrected_fidelity}, Expected: >{threshold}'
    print(f'Hellinger Fidelity with error: {uncorrected_fidelity}')
    """


def run_circuit(qc: qk.QuantumCircuit, shots: int = 1024):
    """
    Simulates the circuit using AerSimulator

    Returns:
        job.result()

        transpiled circuit qc
    """
    simulator = AerSimulator()
    transpiled_circuit = qk.transpile(qc, simulator)
    job = simulator.run(transpiled_circuit, shots=shots) 
    
    return job.result(), transpiled_circuit

def insert_error_gate(qc: qk.QuantumCircuit, gate: Gate = XGate(), index: int | None = None) -> qk.QuantumCircuit:
    """
    Adds the specified gate at the beginning of the circuit
    Flips the first qubit after the first barrier by default
    """
    assert qc.num_qubits >= gate.num_qubits, f'Quantum Circuit has not enough qubits to accomodate gate {gate.name}'
    assert index >= 0, f'Index must be >= 0, Index provided: {index}'

    qubits = qc.qubits[:gate.num_qubits]
    qc.data.insert(index, CircuitInstruction(gate, qubits))

    return qc

def check_equivalence(qc1: qk.QuantumCircuit, qc2: qk.QuantumCircuit) -> bool:
    """
    Uses MQT QCEC to verify if qc1 and qc2 are equivalent
    """
    import mqt.qcec
    from mqt.qcec.pyqcec import EquivalenceCriterion as EC

    verification_results = mqt.qcec.verify(qc1, qc2)
    accepted_equivalencies = [
        EC.equivalent, 
        EC.equivalent_up_to_global_phase, 
        EC.probably_equivalent
        ]
    
    equivalent = verification_results.equivalence in accepted_equivalencies
    return equivalent

def compare_distributions(base: qk.QuantumCircuit, error: qk.QuantumCircuit, shots:int = 1024, code: str = 'None') -> float:
    """
    Simulates 2 circuits and computes the Hellinger Fidelity between their count distributions
    1 = the same, 0 = no overlap

    If code is set to either 'stean' or 'shor' circuit error's result will be interpreted logically
    """
    from qiskit.quantum_info import hellinger_fidelity
    
    result1, base = run_circuit(base, shots)
    result2, error = run_circuit(error, shots)
    counts1 = result1.get_counts(base)
    counts2 = result2.get_counts(error)
    # to be removed due to decoding
    #if code in ['stean', 'shor']:
    #    counts2 = condense_counts(counts2, code)

    fidelity = hellinger_fidelity(counts1, counts2)
    return fidelity

def parse_qubits(physical_qubits: str, code: str):
        """ 
        Takes in a measurement in physical qubits and returns the corresponding logical measurement.
        
        Returns:         
        Logical Measurement if possible, 'x' otherwise
        """
        
        from textwrap import wrap

        logical_qubits = ''
        logical_0 = []
        logical_1 = []
        length = 0
        if code == 'stean':
            length = 7
            logical_0 = ['0000000', '1010101', '0110011', '1100110', 
                         '0001111', '1011010', '0111100', '1101001']
            logical_1 = ['1111111', '0101010', '1001100', '0011001', 
                         '1110000', '0100101', '1000011', '0010110']
        elif code == 'shor':
            length = 9
            logical_0 = []
            logical_1 = []
        else:
            raise Exception('Wrong error correction code provided to qubit condensing')
        assert len(physical_qubits)%length == 0, f'Result contains wrong number of physical qubits. \nExpected: Multiple of {length}\nReceived: {len(physical_qubits)}'

        qubits = wrap(physical_qubits, length)
        for qubit in qubits:
            if qubit in logical_0:
                logical_qubits += '0'
            elif qubit in logical_1:
                logical_qubits += '1'
            else: 
                return 'x'
            
        return logical_qubits

def condense_counts(counts: dict[str, int], code: str) -> dict[str, int]:
    """
    Kinda unnecessariy considering decoding...

    Takes in a result dict of physical measurements and returns logical measurements according to code. 
    Incoherent results will be grouped under 'x'

    Supports codes 'shor' and 'stean'

    Example: Code 'stean'
    
    Input: {'00000001111111': 3, '10101011111111': 1, '11111111010101': 2, '10101011111110' : 7}
    Output: {'01': 4, '10': 2, 'x': 7}
    """
    assert code in ['shor', 'stean'], f'Unsupported error code in condense_counts() {code}'
    logical_counts = {}
    for physical_measurement, count in counts.items():
        logical_measurement = parse_qubits(physical_measurement, code)
        logical_counts[logical_measurement] = logical_counts.get(logical_measurement, 0) + count
        
    return logical_counts


############################################################################################################################################
############################################################################################################################################
############################################################################################################################################
############################################################################################################################################
############################################################################################################################################


"""Equivalence tests for Shor Transpiler gates."""



def verify_gate_equivalence(gate_name: str, num_qubits: int) -> None:
    """Verify that a transpiled gate is mathematically equivalent to the logical gate.

    Args:
        gate_name: The name of the gate to test ('h', 'x', 'z', 's', 't', 'cx', 'cz').
        num_qubits: The number of qubits the gate acts on.
    """
    # Create the logical circuit and initialize it in a non-trivial state (|+> state)
    qc_logical = QuantumCircuit(num_qubits)
    # Apply the gate
    if gate_name == "h":
        qc_logical.h(0)
    elif gate_name == "x":
        qc_logical.x(0)
    elif gate_name == "z":
        qc_logical.z(0)
    elif gate_name == "s":
        qc_logical.s(0)
    elif gate_name == "t":
        qc_logical.t(0)
    elif gate_name == "cx":
        qc_logical.cx(0, 1)
    elif gate_name == "cz":
        qc_logical.cz(0, 1)
    else:
        msg = f"Unknown gate {gate_name}"
        raise ValueError(msg)

    # Get the expected density matrix
    qc_logical_sim = qc_logical.copy()
    # expected logical state
    expected_sv_init = Statevector.from_instruction(qc_logical)

    # Transpile the circuit
    # We set add_syndromes=False to prevent statevector simulation from blowing up in memory
    transpiler = ShorTranspiler(qc_logical, add_syndromes=False)
    transpiled_qc = transpiler.transpile()

    drawing = transpiled_qc.draw(fold=-1)
    print(f"\n--- Transpiled Circuit for {gate_name.upper()} ---")
    print(drawing)

    # Save to file to ensure it can be viewed regardless of pytest-xdist capturing stdout
    output_dir = Path("tests/circuit_drawings")
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / f"{gate_name}_transpiled.txt", "w", encoding="utf-8") as f:
        f.write(f"number of qubits {num_qubits}\n")
        f.write(f"--- Transpiled Circuit for {gate_name.upper()} ---\n\n")
        f.write(str(drawing) + "\n")
    # Apply decoding so the logical state collapses back to the first physical qubit of each block
    transpiler.decode_qubits()

    transpiled_qc.save_statevector()

    sim = AerSimulator(method="statevector")
    result_transpiled = sim.run(transpiled_qc).result()
    assert result_transpiled.success, f"Simulation failed: {result_transpiled.status}"
    actual_sv = result_transpiled.get_statevector()

    # Extract the density matrix of the physical qubits holding the logical state
    # These are the 0-th qubits of each physical data register
    logical_qubits_physical = [
        transpiled_qc.find_bit(transpiler.physical_data_registers[i][0]).index
        for i in range(num_qubits)
    ]

    from qiskit.quantum_info import partial_trace
    all_qubits = list(range(transpiled_qc.num_qubits))
    trace_qubits = [q for q in all_qubits if q not in logical_qubits_physical]

    actual_rho = partial_trace(actual_sv, trace_qubits)

    from qiskit.quantum_info import DensityMatrix
    expected_rho_init = DensityMatrix(expected_sv_init)

    try:
        actual_sv_reduced = actual_rho.to_statevector()
    except Exception:
        actual_sv_reduced = None

    # Compare the density matrices
    fidelity = state_fidelity(expected_sv_init, actual_rho)

    # Save the resulting density matrices and state vectors to the text file for visual inspection
    with open(output_dir / f"{gate_name}_transpiled.txt", "a", encoding="utf-8") as f:
        f.write("\n\n=== LOGICAL EXPECTED DENSITY MATRIX ===\n")
        f.write(str(np.round(expected_rho_init.data, 3)) + "\n")
        f.write("\n=== ACTUAL TRANSPILED DENSITY MATRIX (REDUCED) ===\n")
        f.write(str(np.round(actual_rho.data, 3)) + "\n")

        if actual_sv_reduced is not None:
            f.write("\n\n=== LOGICAL EXPECTED STATE VECTOR ===\n")
            f.write(str(np.round(expected_sv_init.data, 3)) + "\n")
            f.write("\n=== ACTUAL TRANSPILED STATE VECTOR (REDUCED) ===\n")
            f.write(str(np.round(actual_sv_reduced.data, 3)) + "\n")

        f.write(f"\nSTATE FIDELITY: {fidelity:.6f}\n")

    assert fidelity > 0.999, f"Fidelity too low: {fidelity}"


def test_h_equivalence() -> None:
    """Test equivalence for logical H gate."""
    verify_gate_equivalence("h", 1)


def test_x_equivalence() -> None:
    """Test equivalence for logical X gate."""
    verify_gate_equivalence("x", 1)


def test_z_equivalence() -> None:
    """Test equivalence for logical Z gate."""
    verify_gate_equivalence("z", 1)


def test_s_equivalence() -> None:
    """Test equivalence for logical S gate."""
    verify_gate_equivalence("s", 1)


@pytest.mark.skip(reason="Slow test, takes >10 mins due to 27 qubit simulation")
def test_t_equivalence() -> None:
    """Test equivalence for logical T gate."""
    verify_gate_equivalence("t", 1)


def test_cx_equivalence() -> None:
    """Test equivalence for logical CX gate."""
    verify_gate_equivalence("cx", 2)

def test_cz_equivalence() -> None:
    """Test equivalence for logical CZ gate."""
    verify_gate_equivalence("cz", 2)


############################################################################################################################################
############################################################################################################################################
############################################################################################################################################
############################################################################################################################################
############################################################################################################################################


"""Tests for Shor Transpiler."""

#from __future__ import annotations

import pytest
from qiskit import QuantumCircuit

from mqt.bench.error_correction.shor_transpiler import ShorTranspiler

# this needs mpre tests
def test_shor_transpiler() -> None:
    """Test that ShorTranspiler successfully transpiles a basic circuit."""
    qc = QuantumCircuit(2, 1)
    qc.x(0)
    qc.z(1)
    qc.measure(1, 0)

    print("\n--- Logical Circuit ---")
    print(qc.draw(fold=-1))

    transpiler = ShorTranspiler(qc)
    transpiled_qc = transpiler.transpile()

    print("\n--- Transpiled Circuit ---")
    print(transpiled_qc)

    # 2 original qubits * 9 data qubits = 18 data qubits
    # 2 original qubits * 8 ancilla qubits = 16 ancilla qubits
    # Total qubits = 34
    assert transpiled_qc.num_qubits == 34

    # 2 original qubits * 8 classical bits = 16 syndrome bits
    # 1 measurement * 9 bits = 9 measurement bits
    # Total clbits = 25
    assert transpiled_qc.num_clbits == 25
    ##wrong expectations in the test it should check only non error correction gate mapping
    ops = [inst.operation.name for inst in transpiled_qc.data]
    assert "h" in ops
    assert "cx" in ops
    assert "measure" in ops


def test_shor_transpiler_unsupported_gate() -> None:
    """Test that unsupported gates raise NotImplementedError."""
    qc = QuantumCircuit(1)
    qc.rx(0, 0)

    transpiler = ShorTranspiler(qc)
    with pytest.raises(NotImplementedError, match=r"Gate rx is not supported by ShorTranspiler\."):
        transpiler.transpile()


def test_shor_transpiler_s_gate_structure() -> None:
    """Test that the S gate teleportation circuit has the correct structure.

    Verifies that:
    - A magic state ancilla register (9 qubits) is allocated.
    - The teleportation measurement register (1 classical bit) is allocated.
    - The circuit contains the expected gates (h, s, cx, measure).
    """
    qc = QuantumCircuit(1)
    qc.s(0)

    transpiler = ShorTranspiler(qc)
    transpiled_qc = transpiler.transpile()

    # Original: 9 data + 6 bit-flip ancilla + 2 phase-flip ancilla = 17
    # S gate adds: 9 magic data = 9
    # Total = 26
    assert transpiled_qc.num_qubits == 26

    # Original: 6 bf meas + 2 pf meas = 8
    # S gate adds: 1 teleport meas = 1
    # Total = 9
    assert transpiled_qc.num_clbits == 9

    ops = [inst.operation.name for inst in transpiled_qc.data]

    # Magic state prep uses h and p on the ancilla qubit
    assert "p" in ops
    assert "h" in ops

    # Teleportation uses cx, measure
    assert "cx" in ops
    assert "measure" in ops

    # Conditional correction uses if_else
    assert "if_else" in ops

    # Verify the magic state register exists
    reg_names = [reg.name for reg in transpiled_qc.qregs]
    assert "ms0" in reg_names

    # Verify teleportation measurement register exists
    creg_names = [reg.name for reg in transpiled_qc.cregs]
    assert "tmeas0" in creg_names


def test_shor_transpiler_s_gate_followed_by_other_gates() -> None:
    """Test that gates applied after the S gate target the correct register.

    After S gate teleportation, subsequent gates should operate on the original
    data register since the teleportation gadget doesn't swap the pointers.
    """
    qc = QuantumCircuit(1, 1)
    qc.s(0)
    qc.z(0)
    qc.measure(0, 0)

    transpiler = ShorTranspiler(qc)
    transpiled_qc = transpiler.transpile()

    # Circuit should compile and run without errors
    assert transpiled_qc.num_qubits > 0
    assert transpiled_qc.num_clbits > 0

    ops = [inst.operation.name for inst in transpiled_qc.data]
    assert "p" in ops  # Magic state prep (phase)
    assert "x" in ops  # Logical Z uses physical X
    assert "measure" in ops


def test_shor_transpiler_multiple_s_gates() -> None:
    """Test that multiple S gates each allocate independent ancilla blocks.

    Two consecutive S gates should produce two independent magic state
    ancilla blocks (ms0 and ms1).
    """
    qc = QuantumCircuit(1)
    qc.s(0)
    qc.s(0)

    transpiler = ShorTranspiler(qc)
    transpiled_qc = transpiler.transpile()

    reg_names = [reg.name for reg in transpiled_qc.qregs]
    assert "ms0" in reg_names
    assert "ms1" in reg_names


def test_shor_transpiler_t_gate_structure() -> None:
    """Test that the T gate teleportation circuit has the correct structure.

    Verifies that:
    - A magic state ancilla register for T (9 qubits) is allocated.
    - The teleportation measurement register for T (1 classical bit) is allocated.
    - Because of the S correction, another S ancilla and measurement are also allocated conditionally.
    """
    qc = QuantumCircuit(1)
    qc.t(0)

    transpiler = ShorTranspiler(qc)
    transpiled_qc = transpiler.transpile()

    # Original: 17 qubits
    # T gate adds: 9 magic data for T + 9 magic data for S = 18
    # Total = 35
    assert transpiled_qc.num_qubits == 35

    # Original: 8 clbits
    # T gate adds: 1 for T + 1 for S = 2
    # Total = 10
    assert transpiled_qc.num_clbits == 10

    ops = [inst.operation.name for inst in transpiled_qc.data]

    # Magic state prep uses p and h
    assert "p" in ops
    assert "h" in ops

    # Verify the T-magic state register exists
    reg_names = [reg.name for reg in transpiled_qc.qregs]
    assert "anc_t_1" in reg_names
    assert "ms0" in reg_names  # from the S correction


def test_shor_transpiler_barrier() -> None:
    """Test logical barrier translates to physical barrier on all involved qubits."""
    qc = QuantumCircuit(2)
    qc.barrier(0)

    transpiler = ShorTranspiler(qc)
    transpiled_qc = transpiler.transpile()

    ops = [inst.operation.name for inst in transpiled_qc.data]
    assert "barrier" in ops


def test_shor_transpiler_measure() -> None:
    """Test logical measure maps to 9 physical measurements."""
    qc = QuantumCircuit(1, 1)
    qc.measure(0, 0)

    transpiler = ShorTranspiler(qc)
    transpiled_qc = transpiler.transpile()

    measure_count = sum(1 for inst in transpiled_qc.data if inst.operation.name == "measure")
    # At least 9 physical measurements for the single logical measurement
    assert measure_count >= 9


def test_shor_transpiler_h_gate() -> None:
    """Test logical H gate."""
    qc = QuantumCircuit(1)
    qc.h(0)

    transpiler = ShorTranspiler(qc)
    transpiled_qc = transpiler.transpile()

    ops = [inst.operation.name for inst in transpiled_qc.data]
    assert "h" in ops
    assert "swap" in ops


def test_shor_transpiler_x_gate() -> None:
    """Test logical X gate uses Z transversally."""
    qc = QuantumCircuit(1)
    qc.x(0)

    transpiler = ShorTranspiler(qc)
    transpiled_qc = transpiler.transpile()

    ops = [inst.operation.name for inst in transpiled_qc.data]
    # Shor code logical X = Z_0 Z_3 Z_6
    assert "z" in ops


def test_shor_transpiler_z_gate() -> None:
    """Test logical Z gate uses X transversally."""
    qc = QuantumCircuit(1)
    qc.z(0)

    transpiler = ShorTranspiler(qc)
    transpiled_qc = transpiler.transpile()

    ops = [inst.operation.name for inst in transpiled_qc.data]
    # Shor code logical Z = X_0 X_1 X_2
    assert "x" in ops


def test_shor_transpiler_cx_gate() -> None:
    """Test logical CX gate."""
    qc = QuantumCircuit(2)
    qc.cx(0, 1)

    transpiler = ShorTranspiler(qc)
    transpiled_qc = transpiler.transpile()

    ops = [inst.operation.name for inst in transpiled_qc.data]
    assert "cx" in ops


def test_shor_transpiler_cz_gate() -> None:
    """Test logical CZ gate."""
    qc = QuantumCircuit(2)
    qc.cz(0, 1)

    transpiler = ShorTranspiler(qc)
    transpiled_qc = transpiler.transpile()

    ops = [inst.operation.name for inst in transpiled_qc.data]
    # CZ is implemented via H, CX, H
    assert "h" in ops
    assert "cx" in ops
    assert "swap" in ops


def test_shor_transpiler_encode_decode() -> None:
    """Test static encoding and decoding methods directly."""
    from qiskit import QuantumRegister
    qc = QuantumCircuit()
    reg = QuantumRegister(9, "q")
    qc.add_register(reg)

    ShorTranspiler._apply_shor_encoding(qc, reg)
    ops_enc = [inst.operation.name for inst in qc.data]
    assert len(ops_enc) > 0

    ShorTranspiler._apply_shor_decoding(qc, reg)
    ops_dec = [inst.operation.name for inst in qc.data]
    assert len(ops_dec) > len(ops_enc)


def test_shor_transpiler_prepare_magic() -> None:
    """Test _prepare_magic directly."""
    from qiskit import QuantumRegister
    import numpy as np

    qc = QuantumCircuit()
    anc = QuantumRegister(9, "anc")
    qc.add_register(anc)

    ShorTranspiler._prepare_magic(qc, anc, np.pi/2)
    ops = [inst.operation.name for inst in qc.data]
    assert "h" in ops
    assert "p" in ops
