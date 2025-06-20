# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Handles the available native gatesets for Rigetti."""

from __future__ import annotations

import numpy as np
from qiskit import QuantumCircuit, QuantumRegister
from qiskit.circuit import EquivalenceLibrary, Gate, Parameter
from qiskit.circuit.library.standard_gates import RXGate, RZGate, UGate

from ._registry import register_gateset


@register_gateset("rigetti")
def get_rigetti_gateset() -> list[str]:
    """Returns the basis gates of the Rigetti gateset."""
    return ["rxpi", "rxpi2", "rxpi2dg", "rz", "iswap", "measure"]


class RXPIGate(Gate):  # type: ignore[misc]
    r"""Single-qubit RX(π) gate.

    **Circuit symbol:**
    .. parsed-literal::
             ┌─────┐
        q_0: ┤ RX(π)├
             └─────┘

    **Matrix representation:**

    .. math::

        RX(π) =
            \begin{pmatrix}
                0 & -i \\
                -i & 0
            \end{pmatrix}
    """

    def __init__(self, label: str | None = None) -> None:
        """Create RX(π) gate."""
        super().__init__("rxpi", 1, [np.pi], label=label)

    def _define(self) -> None:
        """Define RX(π) gate using standard RX."""
        q = QuantumRegister(1, "q")
        qc = QuantumCircuit(q)
        qc.rx(np.pi, 0)
        self.definition = qc


class RXPI2Gate(Gate):  # type: ignore[misc]
    r"""Single-qubit RX(π/2) gate.

    **Circuit symbol:**
    .. parsed-literal::
             ┌──────────┐
        q_0: ┤ RX(π/2)  ├
             └──────────┘

    **Matrix representation:**

    .. math::

        RX(π/2) =
            \begin{pmatrix}
                \cos(π/4) & -i \sin(π/4) \\
                -i \sin(π/4) & \cos(π/4)
            \end{pmatrix}
    """

    def __init__(self, label: str | None = None) -> None:
        """Create RX(π/2) gate."""
        super().__init__("rxpi2", 1, [np.pi / 2], label=label)

    def _define(self) -> None:
        """Define RX(π/2) gate using standard RX."""
        q = QuantumRegister(1, "q")
        qc = QuantumCircuit(q)
        qc.rx(np.pi / 2, 0)
        self.definition = qc


class RXPI2DgGate(Gate):  # type: ignore[misc]
    r"""Single-qubit RX(-π/2) gate.

    **Circuit symbol:**
    .. parsed-literal::
             ┌────────────┐
        q_0: ┤ RX(-π/2)   ├
             └────────────┘

    **Matrix representation:**

    .. math::

        RX(-π/2) =
            \begin{pmatrix}
                \cos(π/4) & i \sin(π/4) \\
                i \sin(π/4) & \cos(π/4)
            \end{pmatrix}
    """

    def __init__(self, label: str | None = None) -> None:
        """Create RX(-π/2) gate."""
        super().__init__("rxpi2dg", 1, [-np.pi / 2], label=label)

    def _define(self) -> None:
        """Define RX(-π/2) gate using standard RX."""
        q = QuantumRegister(1, "q")
        qc = QuantumCircuit(q)
        qc.rx(-np.pi / 2, 0)
        self.definition = qc


def u_gate_equivalence(sel: EquivalenceLibrary) -> None:
    """Add U(θ, φ, λ) gate equivalence to the SessionEquivalenceLibrary using RZ and RX gates."""
    theta = Parameter("θ")
    phi = Parameter("φ")
    lam = Parameter("λ")

    qr = QuantumRegister(1, "q")
    qc = QuantumCircuit(qr)

    # Decomposition: U(θ, φ, λ) = RZ(φ) RX(-π/2) RZ(θ) RX(π/2) RZ(λ)
    qc.append(RZGate(phi), [qr[0]])
    qc.append(RXPI2DgGate(), [qr[0]])
    qc.append(RZGate(theta), [qr[0]])
    qc.append(RXPI2Gate(), [qr[0]])
    qc.append(RZGate(lam), [qr[0]])

    sel.add_equivalence(UGate(theta, phi, lam), qc)


def rx_gate_equivalence(sel: EquivalenceLibrary) -> None:
    """Add RX(θ) gate equivalence using RX(±π/2) and RZ gates."""
    theta = Parameter("θ")
    qr = QuantumRegister(1, "q")
    qc = QuantumCircuit(qr)

    qc.rz(-np.pi / 2, qr[0])
    qc.append(RXPI2Gate(), [qr[0]])
    qc.rz(theta, qr[0])
    qc.append(RXPI2DgGate(), [qr[0]])
    qc.rz(np.pi / 2, qr[0])

    sel.add_equivalence(RXGate(theta), qc)


def add_equivalences(sel: EquivalenceLibrary) -> None:
    """Add Rigetti gate equivalences to the session equivalence library."""
    u_gate_equivalence(sel)
    rx_gate_equivalence(sel)
