import qiskit
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit.quantum_info import partial_trace

qc = QuantumCircuit(2, 1)
qc.h(0)
qc.cx(0, 1)
qc.measure(0, 0)
with qc.if_test((qc.clbits[0], 1)):
    qc.x(1)
qc.save_statevector()

sim = AerSimulator(method="statevector")
result = sim.run(qc).result()
sv = result.get_statevector()
print("Statevector:")
print(sv)

rho = partial_trace(sv, [0])
print("Partial trace (rho):")
print(rho)
