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

"""RG QFT Multiplier."""

from __future__ import annotations

import numpy as np
from qiskit.circuit import QuantumCircuit, QuantumRegister
from qiskit.synthesis import synth_qft_full

from ._registry import register_benchmark


@register_benchmark("rg_qft_multiplier", description="Ruiz-Garcia (RG) QFT Multiplier")
def create_circuit(num_qubits: int) -> QuantumCircuit:
    """Create a rg qft multiplier circuit.

    Arguments:
            num_qubits: Number of qubits of the returned quantum circuit, must be divisible by 4.

    Returns:
           QuantumCircuit: The constructed rg qft multiplier circuit.

    See Also:
        :class:`qiskit.circuit.library.RGQFTMultiplier`
    """
    if num_qubits % 4 or num_qubits < 4:
        msg = "num_qubits must be an integer ≥ 4 and divisible by 4."
        raise ValueError(msg)

    num_state_qubits = num_qubits // 4
    num_result_qubits = 2 * num_state_qubits

    # define the registers
    qr_a = QuantumRegister(num_state_qubits, name="a")
    qr_b = QuantumRegister(num_state_qubits, name="b")
    qr_out = QuantumRegister(num_result_qubits, name="out")
    qc = QuantumCircuit(qr_a, qr_b, qr_out)

    qft_circ = synth_qft_full(num_result_qubits, do_swaps=False)
    qft_gate = qft_circ.to_gate()
    inv_qft_gate = qft_gate.inverse()
    qc.append(qft_gate, qr_out)

    for j in range(1, num_state_qubits + 1):
        for i in range(1, num_state_qubits + 1):
            for k in range(1, num_result_qubits + 1):
                lam = (2 * np.pi) / (2 ** (i + j + k - 2 * num_state_qubits))
                qc.mcp(
                    lam,
                    [qr_a[num_state_qubits - j], qr_b[num_state_qubits - i]],
                    qr_out[k - 1],
                )

    qc.append(inv_qft_gate, qr_out)

    qc.measure_all()
    qc.name = "rg_qft_multiplier"

    return qc
