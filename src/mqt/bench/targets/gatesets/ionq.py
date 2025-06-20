# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2018.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

# Copyright 2024 IonQ, Inc. (www.ionq.com)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""Handles the available native gatesets for IonQ."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from qiskit import QuantumCircuit, QuantumRegister
from qiskit.circuit import EquivalenceLibrary, Gate, Parameter
from qiskit.circuit.library import CXGate, UGate

from ._registry import register_gateset

if TYPE_CHECKING:
    from qiskit.circuit.parameterexpression import ParameterValueType


@register_gateset("ionq_forte")
def get_ionq_forte_gateset() -> list[str]:
    """Returns the basis gates of the IonQ Forte gateset."""
    return ["rz", "gpi", "gpi2", "zz", "measure"]


@register_gateset("ionq_aria")
def get_ionq_aria_gateset() -> list[str]:
    """Returns the basis gates of the IonQ Aria gateset."""
    return ["rz", "gpi", "gpi2", "ms", "measure"]


class GPIGate(Gate):  # type: ignore[misc]
    r"""Single-qubit GPI gate.

    **Circuit symbol:**
    .. parsed-literal::
             ┌───────┐
        q_0: ┤ GPI(φ)├
             └───────┘
    **Matrix Representation:**.

    .. math::

       GPI(\phi) =
            \begin{pmatrix}
                0 & e^{-i*2*\pi*\phi} \\
                e^{i*2*\pi*\phi} & 0
            \end{pmatrix}
    """

    def __init__(self, phi: ParameterValueType, label: str | None = None) -> None:
        """Create new GPI gate."""
        super().__init__("gpi", 1, [phi], label=label)

    def _define(self) -> None:
        """Define the GPI gate."""
        phi = self.params[0]
        q = QuantumRegister(1, "q")
        qc = QuantumCircuit(q)
        qc.x(0)
        qc.rz(4 * phi * np.pi, 0)
        self.definition = qc


class GPI2Gate(Gate):  # type: ignore[misc]
    r"""Single-qubit GPI2 gate.

    **Circuit symbol:**
    .. parsed-literal::
             ┌───────┐
        q_0: ┤GPI2(φ)├
             └───────┘
    **Matrix Representation:**.

    .. math::

        GPI2(\phi) =
            \frac{1}{\sqrt{2}}
            \begin{pmatrix}
                1 & -i*e^{-i*2*\pi*\phi} \\
                -i*e^{i*2*\pi*\phi} & 1
            \end{pmatrix}
    """

    def __init__(self, phi: ParameterValueType, label: str | None = None) -> None:
        """Create new GPI2 gate."""
        super().__init__("gpi2", 1, [phi], label=label)

    def _define(self) -> None:
        """Define the GPI2 gate."""
        phi = self.params[0]
        q = QuantumRegister(1, "q")
        qc = QuantumCircuit(q)
        qc.rz(-2 * phi * np.pi, 0)
        qc.rx(np.pi / 2, 0)
        qc.rz(2 * phi * np.pi, 0)

        self.definition = qc


class MSGate(Gate):  # type: ignore[misc]
    r"""Entangling 2-Qubit MS gate.

    **Circuit symbol:**
    .. parsed-literal::
              _______
        q_0: ┤       ├-
             |MS(ϴ,0)|
        q_1: ┤       ├-
             └───────┘
    **Matrix representation:**.

    .. math::

       MS(\phi_0, \phi_1, \theta) =
            \begin{pmatrix}
                cos(\theta*\pi) & 0 & 0 & -i*e^{-i*2*\pi(\phi_0+\phi_1)}*sin(\theta*\pi) \\
                0 & cos(\theta*\pi) & -i*e^{i*2*\pi(\phi_0-\phi_1)}*sin(\theta*\pi) & 0 \\
                0 & -i*e^{-i*2*\pi(\phi_0-\phi_1)}*sin(\theta*\pi) & cos(\theta*\pi) & 0 \\
                -i*e^{i*2*\pi(\phi_0+\phi_1)}*sin(\theta*\pi) & 0 & 0 & cos(\theta*\pi)
            \end{pmatrix}
    """

    def __init__(
        self,
        phi0: ParameterValueType,
        phi1: ParameterValueType,
        theta: ParameterValueType | None = 0.25,
        label: str | None = None,
    ) -> None:
        """Create new MS gate."""
        super().__init__(
            "ms",
            2,
            [phi0, phi1, theta],
            label=label,
        )

    def _define(self) -> None:
        """Define the MS gate."""
        phi0 = self.params[0]
        phi1 = self.params[1]
        theta = self.params[2]
        q = QuantumRegister(2, "q")
        alpha = phi0 + phi1
        beta = phi0 - phi1

        qc = QuantumCircuit(q)
        qc.cx(q[1], q[0])
        qc.x(q[0])
        qc.cu(
            2 * theta * np.pi,
            2 * alpha * np.pi - np.pi / 2,
            np.pi / 2 - 2 * alpha * np.pi,
            0,  # gamma
            control_qubit=q[0],
            target_qubit=q[1],
        )
        qc.x(q[0])
        qc.cu(
            2 * theta * np.pi,
            -2 * beta * np.pi - np.pi / 2,
            np.pi / 2 + 2 * beta * np.pi,
            0,  # gamma
            control_qubit=q[0],
            target_qubit=q[1],
        )
        qc.cx(q[1], q[0])

        self.definition = qc


class ZZGate(Gate):  # type: ignore[misc]
    r"""Two-qubit ZZ-rotation gate.

    **Circuit Symbol:**
    .. parsed-literal::
        q_0: ───■────
                │zz(θ)
        q_1: ───■────
    **Matrix Representation:**.

    .. math::

        ZZ(\theta) =
            \begin{pmatrix}
                e^{-i \theta*\pi} & 0 & 0 & 0 \\
                0 & e^{i \theta*\pi} & 0 & 0 \\
                0 & 0 & e^{i \theta*\pi} & 0 \\
                0 & 0 & 0 & e^{-i \theta\*\pi}
            \end{pmatrix}
    """

    def __init__(self, theta: ParameterValueType, label: str | None = None) -> None:
        """Create new ZZ gate."""
        super().__init__("zz", 2, [theta], label=label)

    def _define(self) -> None:
        """Define the ZZ gate."""
        theta = self.params[0]
        q = QuantumRegister(2, "q")
        qc = QuantumCircuit(q)
        qc.rzz(2 * np.pi * theta, 0, 1)

        self.definition = qc


def u_gate_equivalence(sel: EquivalenceLibrary) -> None:
    """Add U gate equivalence to the SessionEquivalenceLibrary."""
    q = QuantumRegister(1, "q")
    theta_param = Parameter("theta_param")
    phi_param = Parameter("phi_param")
    lambda_param = Parameter("lambda_param")
    u_gate = QuantumCircuit(q)
    u_gate.append(GPI2Gate(0.5 - lambda_param / (2 * np.pi)), [0])
    u_gate.append(
        GPIGate(theta_param / (4 * np.pi) + phi_param / (4 * np.pi) - lambda_param / (4 * np.pi)),
        [0],
    )
    u_gate.append(GPI2Gate(0.5 + phi_param / (2 * np.pi)), [0])
    sel.add_equivalence(UGate(theta_param, phi_param, lambda_param), u_gate)


def cx_via_ms_equivalence(sel: EquivalenceLibrary) -> None:
    """Add CX gate equivalence to the SessionEquivalenceLibrary for both native two-qubit gates."""
    q = QuantumRegister(2, "q")
    cx_gate = QuantumCircuit(q)
    cx_gate.append(GPI2Gate(1 / 4), [0])
    cx_gate.append(MSGate(0, 0, 0.25), [0, 1])
    cx_gate.append(GPI2Gate(1 / 2), [0])
    cx_gate.append(GPI2Gate(1 / 2), [1])
    cx_gate.append(GPI2Gate(-1 / 4), [0])
    sel.add_equivalence(CXGate(), cx_gate)


def cx_via_zz_equivalence(sel: EquivalenceLibrary) -> None:
    """Add equivalence CX ≡ H-ZZ(pi/4)-H."""
    q = QuantumRegister(2, "q")
    cx_equiv = QuantumCircuit(q)
    cx_equiv.h(1)
    cx_equiv.append(ZZGate(0.25), [0, 1])  # pi/4
    cx_equiv.h(1)

    sel.add_equivalence(CXGate(), cx_equiv)


def add_equivalences(sel: EquivalenceLibrary) -> None:
    """Add IonQ gate equivalences to the SessionEquivalenceLibrary."""
    u_gate_equivalence(sel)
    cx_via_ms_equivalence(sel)
    cx_via_zz_equivalence(sel)
