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
from qiskit_aer.primitives import SamplerV2

from mqt.bench.error_correction.shor_transpiler import ShorTranspiler
from mqt.bench.error_correction.steane_transpiler import SteaneTranspiler
from tests.test_error_correction import insert_error
from qiskit.circuit import CircuitInstruction, Gate
from qiskit.circuit.library import XGate, HGate, ZGate
from qiskit.quantum_info import hellinger_fidelity


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


def run_circuit(qc: QuantumCircuit, shots: int = 1024) -> tuple[dict, QuantumCircuit]:
    """
    Simulates the circuit using AerSimulator.

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

    If code is set to either 'steane' or 'shor' circuit error's result will be interpreted logically
    """
        
    #print(counts1)
    if code1 in ['steane', 'shor']:
        counts1 = condense_counts(qc1, counts1)
    #print(counts1)
    
    #print(counts2)
    if code2 in ['steane', 'shor']:
        counts2 = condense_counts(qc2, counts2)
    #print(counts2)
    
    fidelity = hellinger_fidelity(counts1, counts2)
    return fidelity

def parse_qubits(qc: qk.QuantumCircuit, physical_qubits: str):
        """ 
        Takes in a measurement in physical qubits and returns the corresponding logical measurement.
        
        Underlying circuit must use registers named 'qx' (x in int) for each logical qubit, with results in qx[0]
        """
        # remove blanks caused by classical registers
        physical_qubits = physical_qubits.replace(' ', '')

        # indices
        import re
        def is_q_integer(s: str) -> bool:
            """ checks if s is of form 'qx' where x in int (e.g. 'q1', 'q23') """
            return bool(re.fullmatch(r'q\d+', s))
        
        data_indices = []
        for register in qc.qregs:
            if is_q_integer(register.name):
                data_indices.append(qc.find_bit(register[0]).index) 
        
        # condensing
        logical_qubits = ""
        for index in data_indices:
            logical_qubits += physical_qubits[index]

        return logical_qubits


#def get_logical_classical_indices(qc, name):
#    logical_cregs = sorted(
#        [cr for cr in qc.cregs if cr.name.startswith(name)],
#        key=lambda cr: int(cr.name.replace(name, ""))
#    )
#
#    indices = []
#
#    for cr in logical_cregs:
#        # assuming each logical register has size 1
#        indices.append(qc.find_bit(cr[0]).index)
#
#    return indices

def condense_counts(qc:qk.QuantumCircuit, counts: dict[str, int]) -> dict[str, int]:
    """
    Takes in a result dict of a decoded physical measurement and returns logical measurements 
    Requires decode to place the result in the first qubit of each register named 'qx', with x an integer (e.g. 'q2')
    """
    #assert code in ['shor', 'steane'], f'Unsupported error code in condense_counts(): {code}'
    logical_counts = {}
    for physical_measurement, count in counts.items():
        logical_measurement = parse_qubits(qc, physical_measurement)
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


    algorithm = 'ghz'
    code = 'shor'
    # Initialize circuits
    t_circuit = QuantumCircuit(1)
    t_circuit.h(0)
    t_circuit.t(0)
    t_circuit.h(0)
    
    xcx_circuit = QuantumCircuit(2)
    #xcx_circuit.x(0)
    xcx_circuit.cx(0,1)

    h_circuit = QuantumCircuit(1)
    h_circuit.z(0)
    #h_circuit.h(0)

    logical_circuit = h_circuit
    
    #logical_circuit = benchmark_generation.get_benchmark(
    #        benchmark=algorithm, level=benchmark_generation.BenchmarkLevel.ALG, circuit_size=circuit_size, encoding=code
    #    )
    error_corrected_circuit = logical_circuit.copy()
    code = 'steane'
    shor_transpiler = ShorTranspiler(error_corrected_circuit, add_syndromes=False)
    steane_transpiler = SteaneTranspiler(logical_circuit, add_syndromes=False)
    if code == 'shor':
        transpiler = shor_transpiler
    else:
        transpiler = steane_transpiler
    transpiler.transpile()
    transpiler.decode_qubits()
    error_corrected_circuit = transpiler.transpiled_qc

    error_induced_circuit = error_corrected_circuit.copy()
    # this is for inserting phase flip in steane after the first Hadamard
    #error_induced_circuit = insert_error(error_induced_circuit ,gate=ZGate(), index=16)
    error_induced_circuit = insert_error(error_induced_circuit ,gate=XGate())


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

    print(check_equivalence(logical_circuit, error_corrected_circuit))
    #print(check_equivalence(error_corrected_circuit, error_induced_circuit))

    logical_counts, logical_circuit = run_circuit(logical_circuit)
    corrected_counts, error_corrected_circuit = run_circuit(error_corrected_circuit)
    induced_counts, error_induced_circuit = run_circuit(error_induced_circuit)


    print(compare_distributions(logical_circuit, error_corrected_circuit, logical_counts, corrected_counts, 'none', code))
    print(compare_distributions(error_corrected_circuit, error_induced_circuit, corrected_counts, induced_counts, code, code))