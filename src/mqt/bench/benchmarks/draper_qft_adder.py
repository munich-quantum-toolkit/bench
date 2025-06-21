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

"""Draper QFT Adder."""

from __future__ import annotations

import numpy as np
from qiskit.circuit import QuantumCircuit, QuantumRegister
from qiskit.synthesis import synth_qft_full

from ._registry import register_benchmark


@register_benchmark("draper_qft_adder", description="Draper QFT Adder")
def create_circuit(num_qubits: int, kind: str = "fixed") -> QuantumCircuit:
    """Create a draper QFT adder circuit.

    Arguments:
            num_qubits: Number of qubits of the returned quantum circuit
            kind: The kind of adder, can be ``"half"`` for a half adder or
               ``"fixed"`` for a fixed-sized adder. A half adder contains a carry-out to represent
               the most-significant bit, but the fixed-sized adder doesn't and hence performs
               addition modulo ``2 ** num_state_qubits``.

    Returns:
           QuantumCircuit: The constructed draper QFT adder circuit.

    See Also:
        :class:`qiskit.circuit.library.DraperQFTAdder`
    """
    if kind == "half":
        if num_qubits % 2 == 0 or num_qubits < 3:
            msg = "num_qubits must be an odd integer ≥ 3."
            raise ValueError(msg)
        num_state_qubits = (num_qubits - 1) // 2
    elif kind == "fixed":
        if num_qubits % 2 or num_qubits < 2:
            msg = "num_qubits must be an even integer ≥ 2."
            raise ValueError(msg)
        num_state_qubits = num_qubits // 2
    else:
        msg = "kind must be 'half' or 'fixed'."
        raise ValueError(msg)

    qr_a = QuantumRegister(num_state_qubits, name="a")
    qr_b = QuantumRegister(num_state_qubits, name="b")
    qr_z = QuantumRegister(1, name="cout")
    qc = QuantumCircuit(qr_a, qr_b)

    if kind == "half":
        qc.add_register(qr_z)
        qr_sum = qr_b[:] + qr_z[:]
        num_qubits_qft = num_state_qubits + 1
    else:
        qr_sum = qr_b[:]
        num_qubits_qft = num_state_qubits

    # build QFT adder circuit
    qft_circ = synth_qft_full(num_qubits_qft, do_swaps=False)
    qft_gate = qft_circ.to_gate()
    inv_qft_gate = qft_gate.inverse()
    qc.append(qft_gate, qr_sum)

    for j in range(num_state_qubits):
        for k in range(num_state_qubits - j):
            lam = np.pi / (2**k)
            qc.cp(lam, qr_a[j], qr_b[j + k])

    if kind == "half":
        for j in range(num_state_qubits):
            lam = np.pi / (2 ** (j + 1))
            qc.cp(lam, qr_a[num_state_qubits - j - 1], qr_z[0])

    qc.append(inv_qft_gate, qr_sum)

    qc.measure_all()
    qc.name = "draper_qft_adder"

    return qc
