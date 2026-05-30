# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

import mqt.bench.benchmark_generation as benchmark_generation
from qiskit_aer import AerSimulator # update uv requirements?
import qiskit as qk
from qiskit import QuantumCircuit
from qiskit.result.result import Result

from mqt.bench.error_correction.shor_transpiler import ShorTranspiler
from tests.test_error_correction import insert_error
from qiskit.circuit import CircuitInstruction, Gate
from qiskit.circuit.library import XGate, HGate


# uv requirements to be added: mqt.qcec, qiskit_aer


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
    #error_fidelity = compare_distributions(base_circuit, error_circuit)
    #threshold = 0.95 # arbitrary guess
    #assert fidelity > threshold, f'Simulated Hellinger Fidelity between base and error circuit is too low. Measured: {fidelity}, >Expected: {threshold}'
    #print(f'Hellinger Fidelity with error: {error_fidelity}')

    ### Simulated probabilistic similarity Uncorrected vs. Error-Inserted
    # TODO: put in error corrected circuit
    #### Example for condensing qubits
    #example = {'00000001111111': 3, '10101011111111': 1, '11111111010101': 2, '10101011111110' : 7}
    #print(condense_counts(example,'stean'))

    """
    uncorrected_fidelity = compare_distributions(uncorrected_circuit, error_circuit, code='shor')
    threshold = threshold # arbitrary guess
    #assert fidelity > threshold, f'Simulated Hellinger Fidelity between uncorrected and error circuit is too low. Measured: {uncorrected_fidelity}, Expected: >{threshold}'
    print(f'Hellinger Fidelity with error: {uncorrected_fidelity}')
    """


def run_circuit(qc: QuantumCircuit, shots: int = 1024) -> tuple[Result, QuantumCircuit]:
    """
    Simulates the circuit using AerSimulator.

    Adds measurements to all qubits.

    Returns:
        job.result()

        transpiled circuit qc
    """
    simulator = AerSimulator()
    qc.measure_all()
    transpiled_circuit = qk.transpile(qc, simulator)
    job = simulator.run(transpiled_circuit, shots=shots) 
    
    return job.result(), transpiled_circuit

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

def compare_distributions(qc1: QuantumCircuit, qc2: QuantumCircuit, counts1: dict, counts2: dict, code1: str = 'None', code2: str = 'None') -> float:
    """
    Simulates 2 circuits and computes the Hellinger Fidelity between their count distributions
    1 = the same, 0 = no overlap

    If code is set to either 'stean' or 'shor' circuit error's result will be interpreted logically
    """
    from qiskit.quantum_info import hellinger_fidelity
    # to be removed due to decoding
    if code1 in ['stean', 'shor']:
        counts1 = condense_counts(qc1, counts1, code1)
    if code2 in ['stean', 'shor']:
        counts2 = condense_counts(qc2, counts2, code2)

    fidelity = hellinger_fidelity(counts1, counts2)
    return fidelity

def parse_qubits(qc: qk.QuantumCircuit, physical_qubits: str):
        """ 
        Takes in a measurement in physical qubits and returns the corresponding logical measurement.
        
        Underlying circuit must use registers named 'qx' (x in int) for each logical qubit, with results in qx[0]
        """
        # indices
        import re
        def is_q_integer(s: str) -> bool:
            """ checks if s is of form 'qx' where x in int (e.g. 'q1', 'q23') """
            return bool(re.fullmatch(r'q\d+', s))

        data_indices = []
        for register in qc.qregs:
            print(register)
            if is_q_integer(register.name):
                data_indices.append(qc.find_bit(register[-1]).index) # qiskit is little-endian

        print(data_indices)

        # condesning
        logical_qubits = ""
        for index in data_indices:
            logical_qubits += physical_qubits[index]

        print(logical_qubits)

        return logical_qubits

def condense_counts(qc:qk.QuantumCircuit, counts: dict[str, int], code: str) -> dict[str, int]:
    """
    Takes in a result dict of a decoded physical measurement and returns logical measurements according to code. 

    Supports codes 'shor' and 'stean'
    """
    assert code in ['shor', 'stean'], f'Unsupported error code in condense_counts(): {code}'
    logical_counts = {}
    for physical_measurement, count in counts.items():
        logical_measurement = parse_qubits(qc, physical_measurement)
        logical_counts[logical_measurement] = logical_counts.get(logical_measurement, 0) + count
        
    print(logical_counts)
    return logical_counts



if __name__ == "__main__":
    for alg in ["ghz", "bv", "graphstate"]:  # add QFT
        for code in ["shor", "stean"]:
            # for qubits in range(3, 5):
            qubits = 3
            #print(code)
            qc = benchmark_generation.get_benchmark(
                benchmark=alg, level=benchmark_generation.BenchmarkLevel.ALG, circuit_size=qubits, encoding=code
            )
            #print(qc)
            #print("   _________   ")

    #errorcode_testing()

    circuit_size = 1
    algorithm = 'ghz'
    code = 'shor'
    # Initialize circuits
    logical_circuit = qk.QuantumCircuit(circuit_size)
    logical_circuit.h(0)
    
    #logical_circuit = benchmark_generation.get_benchmark(
    #        benchmark=algorithm, level=benchmark_generation.BenchmarkLevel.ALG, circuit_size=circuit_size, encoding=code
    #    )
    error_corrected_circuit = logical_circuit.copy()
    transpiler = ShorTranspiler(error_corrected_circuit, add_syndromes=True)
    transpiler.transpile()
    transpiler.decode_qubits()
    error_corrected_circuit = transpiler.transpiled_qc
    error_induced_circuit = error_corrected_circuit.copy()
    #error_induced_circuit = insert_error(error_induced_circuit)
    error_induced_circuit = insert_error(error_induced_circuit,gate=HGate())
    


           
           
    #print("   __________________________________________________________________________________________   ")
    #print('Logical Circuit:')
    #print(logical_circuit)
    #print("   __________________________________________________________________________________________   ")
    #print('Error corrected Circuit:')
    #print(error_corrected_circuit)
    #print("   __________________________________________________________________________________________   ")
    #print('Error Induced Circuit')
    #print(error_induced_circuit)
    #print("   __________________________________________________________________________________________   ")

    #print(check_equivalence(logical_circuit, error_corrected_circuit))
    #print(check_equivalence(error_corrected_circuit, error_induced_circuit))

    logical_result, logical_circuit = run_circuit(logical_circuit)
    corrected_result, error_corrected_circuit = run_circuit(error_corrected_circuit)
    induced_result, error_induced_circuit = run_circuit(error_induced_circuit)

    logical_counts = logical_result.get_counts(logical_circuit)
    corrected_counts = corrected_result.get_counts(error_corrected_circuit)
    induced_counts = induced_result.get_counts(error_induced_circuit)

    print(logical_counts)
    print(corrected_counts)
    print(induced_counts)

    print(compare_distributions(logical_circuit, error_corrected_circuit, logical_counts, corrected_counts, 'none', 'shor'))
    print(compare_distributions(error_corrected_circuit, error_induced_circuit, corrected_counts, induced_counts,'shor', 'shor'))