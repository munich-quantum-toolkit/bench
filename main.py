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

def insert_error_gate(qc: qk.QuantumCircuit) -> qk.QuantumCircuit:
    """
    Flips bit 0 at the beginning of the circuit
    """
    from qiskit.circuit import CircuitInstruction
    from qiskit.circuit.library import XGate

    gate = XGate()
    qubits = [qc.qubits[0]] 
    insert_index = 0

    qc.data.insert(insert_index, CircuitInstruction(gate, qubits))

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

    errorcode_testing()
