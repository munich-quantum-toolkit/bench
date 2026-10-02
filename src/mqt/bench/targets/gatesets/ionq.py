# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
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
from qiskit import QuantumCircuit
from qiskit.circuit import Gate, Parameter
from qiskit.circuit.library import UGate

from ._registry import register_gateset

if TYPE_CHECKING:
    from qiskit.circuit import EquivalenceLibrary, ParameterExpression

_U_GATE = UGate(Parameter("theta"), Parameter("phi"), Parameter("lambda"))
"""Stable parameter identities for equivalence lookup."""


@register_gateset("ionq_forte")
def get_ionq_forte_gateset() -> list[str]:
    """Returns the basis gates of the IonQ Forte gateset."""
    return ["rz", "gpi", "gpi2", "rzz", "measure"]


class GPIGate(Gate):
    r"""Single-qubit GPI gate with phase in radians.

    **Circuit symbol:**

    .. parsed-literal::

             ┌───────┐
        q_0: ┤ GPI(φ)├
             └───────┘

    **Matrix Representation:**.

    .. math::

       GPI(\phi) =
            \begin{pmatrix}
                0 & e^{-i*\phi} \\
                e^{i*\phi} & 0
            \end{pmatrix}
    """

    def __init__(self, phi: ParameterExpression | float, label: str | None = None) -> None:
        """Create new GPI gate."""
        super().__init__("gpi", 1, [phi], label=label)

    def _define(self) -> None:
        """Define the GPI gate."""
        qc = QuantumCircuit(1, global_phase=np.pi / 2)
        qc.r(np.pi, self.params[0], 0)
        self.definition = qc


class GPI2Gate(Gate):
    r"""Single-qubit GPI2 gate with phase in radians.

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
                1 & -i*e^{-i*\phi} \\
                -i*e^{i*\phi} & 1
            \end{pmatrix}
    """

    def __init__(self, phi: ParameterExpression | float, label: str | None = None) -> None:
        """Create new GPI2 gate."""
        super().__init__("gpi2", 1, [phi], label=label)

    def _define(self) -> None:
        """Define the GPI2 gate."""
        qc = QuantumCircuit(1)
        qc.r(np.pi / 2, self.params[0], 0)
        self.definition = qc


def add_equivalences(sel: EquivalenceLibrary) -> None:
    """Add the exact U decomposition into IonQ gates once per library.

    Compare copies because Qiskit equality caches gate definitions.
    """
    theta, phi, lam = _U_GATE.params
    circuit = QuantumCircuit(1, global_phase=(phi + lam) / 2 - np.pi / 2)
    circuit.append(GPI2Gate(np.pi - lam), [0])
    circuit.append(GPIGate((theta + phi - lam) / 2), [0])
    circuit.append(GPI2Gate(np.pi + phi), [0])
    if circuit not in (entry.copy() for entry in sel.get_entry(_U_GATE)):
        sel.add_equivalence(_U_GATE, circuit)
