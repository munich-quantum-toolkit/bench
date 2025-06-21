# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Shor benchmark definition."""
# Code is based on Qiskit, therefore we have to add the following information:
# This code is part of Qiskit.
#
# (C) Copyright IBM 2019, 2022.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from numpy.typing import NDArray
import math
from typing import cast

import numpy as np
from qiskit.circuit import Instruction, ParameterVector, QuantumCircuit, QuantumRegister
from qiskit.circuit.library import QFTGate
from qiskit.synthesis import synth_qft_full

from ._registry import register_benchmark

_SIZE_TO_PARAMS = {
    18: (15, 4),  # "small"
    42: (821, 4),  # "medium"
    58: (11777, 4),  # "large"
    74: (201209, 4),  # "xlarge"
}


@register_benchmark("shor", description="Shor's Algorithm")
def create_circuit(circuit_size: int) -> QuantumCircuit:
    """Construct Shor's circuit based on total qubit count.

    Arguments:
        circuit_size: one of 18, 42, 58, 74.

    Raises:
        ValueError: if the size is not available.

    Returns:
        QuantumCircuit implementing Shor's algorithm for the chosen size.
    """
    try:
        n, a = _SIZE_TO_PARAMS[circuit_size]
    except KeyError as exc:
        valid = ", ".join(map(str, sorted(_SIZE_TO_PARAMS)))
        msg = f"No Shor instance for circuit_size={circuit_size}. Available: {valid}."
        raise ValueError(msg) from exc

    return create_circuit_from_num_and_coprime(n, a)


def create_circuit_from_num_and_coprime(num_to_be_factorized: int, a: int = 2) -> QuantumCircuit:
    """Returns a quantum circuit implementing the Shor's algorithm.

    Arguments:
        num_to_be_factorized: number which shall be factorized
        a: any integer that satisfies 1 < a < num_to_be_factorized and gcd(a, num_to_be_factorized) = 1
    """
    qc = Shor().construct_circuit(num_to_be_factorized, a)
    qc.measure_all()
    qc.name = "shor"

    return qc


def get_instance(choice: str) -> list[int]:
    """Returns the number to be factorized and the integer a for the Shor's algorithm."""
    instances = {
        "xsmall": [9, 4],  # 18 qubits
        "small": [15, 4],  # 18 qubits
        "medium": [821, 4],  # 42 qubits
        "large": [11777, 4],  # 58 qubits
        "xlarge": [201209, 4],  # 74 qubits
    }
    return instances[choice]


class Shor:
    """Shor's algorithm implementation."""

    @staticmethod
    def _get_angles(a: int, n: int) -> NDArray[np.float64]:
        """Calculates the array of angles to be used in the addition in Fourier Space."""
        bits_little_endian = (f"{a:b}".zfill(n))[::-1]

        angles = np.zeros(n)
        for i in range(n):
            for j in range(i + 1):
                k = i - j
                if bits_little_endian[j] == "1":
                    angles[i] += pow(2, -k)

        return cast("NDArray[np.float64]", angles * np.pi)

    @staticmethod
    def _phi_add_gate(angles: NDArray[np.float64] | ParameterVector) -> QuantumCircuit:
        """Gate that performs addition by a in Fourier Space."""
        circuit = QuantumCircuit(len(angles), name="phi_add_a")
        for i, angle in enumerate(angles):
            circuit.p(angle, i)
        return circuit

    def _double_controlled_phi_add_mod_n(
        self,
        angles: NDArray[np.float64] | ParameterVector,
        c_phi_add_n: QuantumCircuit,
        iphi_add_n: QuantumCircuit,
        qft: QuantumCircuit,
        iqft: QuantumCircuit,
    ) -> QuantumCircuit:
        """Creates a circuit which implements double-controlled modular addition by a."""
        ctrl_qreg = QuantumRegister(2, "ctrl")
        b_qreg = QuantumRegister(len(angles), "b")
        flag_qreg = QuantumRegister(1, "flag")

        circuit = QuantumCircuit(ctrl_qreg, b_qreg, flag_qreg, name="ccphi_add_a_mod_N")

        cc_phi_add_a = self._phi_add_gate(angles).control(2)
        cc_iphi_add_a = cc_phi_add_a.inverse()

        circuit.compose(cc_phi_add_a, [*ctrl_qreg, *b_qreg], inplace=True)

        circuit.compose(iphi_add_n, b_qreg, inplace=True)

        circuit.compose(iqft, b_qreg, inplace=True)
        circuit.cx(b_qreg[-1], flag_qreg[0])
        circuit.compose(qft, b_qreg, inplace=True)

        circuit.compose(c_phi_add_n, [*flag_qreg, *b_qreg], inplace=True)

        circuit.compose(cc_iphi_add_a, [*ctrl_qreg, *b_qreg], inplace=True)

        circuit.compose(iqft, b_qreg, inplace=True)
        circuit.x(b_qreg[-1])
        circuit.cx(b_qreg[-1], flag_qreg[0])
        circuit.x(b_qreg[-1])
        circuit.compose(qft, b_qreg, inplace=True)

        return circuit.compose(cc_phi_add_a, [*ctrl_qreg, *b_qreg])

    def _controlled_multiple_mod_n(
        self,
        num_bits_necessary: int,
        to_be_factored_number: int,
        a: int,
        c_phi_add_n: QuantumCircuit,
        iphi_add_n: QuantumCircuit,
        qft: QuantumCircuit,
        iqft: QuantumCircuit,
    ) -> QuantumCircuit:
        """Implements modular multiplication by a as an instruction."""
        ctrl_qreg = QuantumRegister(1, "ctrl")
        x_qreg = QuantumRegister(num_bits_necessary, "x")
        b_qreg = QuantumRegister(num_bits_necessary + 1, "b")
        flag_qreg = QuantumRegister(1, "flag")

        circuit = QuantumCircuit(ctrl_qreg, x_qreg, b_qreg, flag_qreg, name="cmult_a_mod_N")

        angle_params = ParameterVector("angles", length=num_bits_necessary + 1)
        modulo_adder = self._double_controlled_phi_add_mod_n(angle_params, c_phi_add_n, iphi_add_n, qft, iqft)

        def append_adder(adder: QuantumCircuit, constant: int, idx: int) -> None:
            partial_constant = (pow(2, idx, to_be_factored_number) * constant) % to_be_factored_number
            angles = self._get_angles(partial_constant, num_bits_necessary + 1)
            bound = adder.assign_parameters({angle_params: angles})
            circuit.append(bound, [*ctrl_qreg, x_qreg[idx], *b_qreg, *flag_qreg])

        circuit.compose(qft, b_qreg, inplace=True)

        # perform controlled addition by a on the aux register in Fourier space
        for i in range(num_bits_necessary):
            append_adder(modulo_adder, a, i)

        circuit.compose(iqft, b_qreg, inplace=True)

        # perform controlled subtraction by a in Fourier space on both the aux and down register
        for i in range(num_bits_necessary):
            circuit.cswap(ctrl_qreg, x_qreg[i], b_qreg[i])

        circuit.compose(qft, b_qreg, inplace=True)

        a_inv = pow(a, -1, mod=to_be_factored_number)

        modulo_adder_inv = modulo_adder.inverse()
        for i in reversed(range(num_bits_necessary)):
            append_adder(modulo_adder_inv, a_inv, i)

        return circuit.compose(iqft, b_qreg)

    def _power_mod_n(self, num_bits_necessary: int, to_be_factored_number: int, a: int) -> Instruction:
        """Implements modular exponentiation a^x as an instruction."""
        up_qreg = QuantumRegister(2 * num_bits_necessary, name="up")
        down_qreg = QuantumRegister(num_bits_necessary, name="down")
        aux_qreg = QuantumRegister(num_bits_necessary + 2, name="aux")

        circuit = QuantumCircuit(up_qreg, down_qreg, aux_qreg, name=f"{a}^x mod {to_be_factored_number}")

        qft = synth_qft_full(num_bits_necessary + 1, do_swaps=False)
        iqft = qft.inverse()

        # Create gates to perform addition/subtraction by N in Fourier Space
        phi_add_n = self._phi_add_gate(self._get_angles(to_be_factored_number, num_bits_necessary + 1))
        iphi_add_n = phi_add_n.inverse()
        c_phi_add_n = phi_add_n.control(1)

        # Apply the multiplication gates as showed in
        # the report in order to create the exponentiation
        for i in range(2 * num_bits_necessary):
            partial_a = pow(a, pow(2, i), to_be_factored_number)
            modulo_multiplier = self._controlled_multiple_mod_n(
                num_bits_necessary, to_be_factored_number, partial_a, c_phi_add_n, iphi_add_n, qft, iqft
            )
            circuit.compose(modulo_multiplier, [up_qreg[i], *down_qreg, *aux_qreg], inplace=True)

        return circuit

    @staticmethod
    def _validate_input(to_be_factored_number: int, a: int) -> None:
        """Check parameters of the algorithm.

        Arguments:
            to_be_factored_number: The odd integer to be factored, has a min. value of 3.
            a: Any integer that satisfies 1 < a < N and gcd(a, N) = 1.

        Raises:
            ValueError: Invalid input

        """
        if a < 2:
            msg = f"{'a'} must have value >= {2}, was {a}"
            raise ValueError(msg)

        if to_be_factored_number < 3 or to_be_factored_number % 2 == 0:
            msg = f"The input needs to be an odd integer greater than 3, was {to_be_factored_number}."
            raise ValueError(msg)

        if a >= to_be_factored_number or math.gcd(a, to_be_factored_number) != 1:
            msg = (
                f"The integer a needs to satisfy a < N and gcd(a, N) = 1, was a = {a} and N = {to_be_factored_number}."
            )
            raise ValueError(msg)

    def construct_circuit(self, to_be_factored_number: int, a: int = 2) -> QuantumCircuit:
        """Construct quantum part of the algorithm.

        Arguments:
            to_be_factored_number: The odd integer to be factored, has a min. value of 3.
            a: Any integer that satisfies 1 < a < N and gcd(a, N) = 1.

        Returns:
            Quantum circuit.

        """
        self._validate_input(to_be_factored_number, a)

        # Get n value used in Shor's algorithm, to know how many qubits are used
        num_bits_necessary = to_be_factored_number.bit_length()

        # quantum register where the sequential QFT is performed
        up_qreg = QuantumRegister(2 * num_bits_necessary, name="up")
        # quantum register where the multiplications are made
        down_qreg = QuantumRegister(num_bits_necessary, name="down")
        # auxiliary quantum register used in addition and multiplication
        aux_qreg = QuantumRegister(num_bits_necessary + 2, name="aux")

        # Create Quantum Circuit
        circuit = QuantumCircuit(up_qreg, down_qreg, aux_qreg, name=f"Shor(N={to_be_factored_number}, a={a})")

        # Create maximal superposition in top register
        circuit.h(up_qreg)

        # Initialize down register to 1
        circuit.x(down_qreg[0])

        # Apply modulo exponentiation
        modulo_power = self._power_mod_n(num_bits_necessary, to_be_factored_number, a)
        circuit.compose(modulo_power.decompose(reps=4), circuit.qubits, inplace=True)

        # Apply inverse QFT
        iqft = QFTGate(len(up_qreg)).inverse()
        return circuit.compose(iqft, up_qreg)
