# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
#
# Modified by MQSC, 2025.

"""HRS Cumulative Multiplier."""

from __future__ import annotations

from qiskit.circuit import AncillaRegister, QuantumCircuit, QuantumRegister
from qiskit.synthesis import adder_ripple_c04

from ._registry import register_benchmark


@register_benchmark("hrs_cumulative_multiplier", description="Häner-Roetteler-Svore (HRS) Cumulative Multiplier")
def create_circuit(num_qubits: int) -> QuantumCircuit:
    """Create a hrs cumulative multiplier circuit.

    Arguments:
            num_qubits: Number of qubits of the returned quantum circuit, (num_qubits - 1) must be divisible by 4.

    Returns:
           QuantumCircuit: The constructed hrs cumulative multiplier circuit.


    See Also:
        :class:`qiskit.circuit.library.HRSCumulativeMultiplier`
    """
    if (num_qubits - 1) % 4 or num_qubits < 5:
        msg = "num_qubits must be an integer ≥ 5 and (num_qubits - 1) must be divisible by 4."
        raise ValueError(msg)

    num_state_qubits = num_qubits // 4
    num_result_qubits = 2 * num_state_qubits

    # define the registers
    qr_a = QuantumRegister(num_state_qubits, name="a")
    qr_b = QuantumRegister(num_state_qubits, name="b")
    qr_out = QuantumRegister(num_result_qubits, name="out")

    # prepare adder as controlled gate
    adder = adder_ripple_c04(num_state_qubits, kind="half")

    # get the number of helper qubits needed
    num_helper_qubits = adder.num_ancillas

    # add helper qubits if required
    qr_helper = AncillaRegister(num_helper_qubits, "helper") if num_helper_qubits else None

    qregs = [qr_a, qr_b, qr_out] + ([qr_helper] if qr_helper else [])

    # build multiplication circuit
    qc = QuantumCircuit(*qregs)

    for i in range(num_state_qubits):
        num_adder_qubits = num_state_qubits
        adder_for_current_step = adder
        controlled_adder = adder_for_current_step.to_gate().control(1)
        qr_list = [qr_a[i], *qr_b[:num_adder_qubits], *qr_out[i : num_state_qubits + i + 1]]
        if num_helper_qubits > 0 and qr_helper:
            qr_list.extend(qr_helper[:])
        qc.append(controlled_adder, qr_list)

    qc.measure_all()
    qc.name = "hrs_cumulative_multiplier"

    return qc
