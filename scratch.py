# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

from qiskit import QuantumCircuit
from qiskit.quantum_info import partial_trace
from qiskit_aer import AerSimulator

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
