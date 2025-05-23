# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Handles the available native gatesets for Rigetti."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from qiskit import QuantumCircuit, QuantumRegister
from qiskit.circuit import Gate, Parameter, SessionEquivalenceLibrary
from qiskit.circuit.library import CXGate, RXGate, iSwapGate
from qiskit.circuit.library.standard_gates import RZGate, UGate

if TYPE_CHECKING:
    from numpy._typing import NDArray


def get_rigetti_gateset() -> list[str]:
    """Returns the basis gates of the Rigetti gateset."""
    add_rigetti_equivalences()
    return ["rx_pi", "rx_pi_by_2", "rx_pi_by_minus_2", "rz", "iswap", "measure"]


class RXPiGate(Gate):  # type: ignore[misc]
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
        super().__init__("rx_pi", 1, [np.pi], label=label)

    def _define(self) -> None:
        """Define RX(π) gate using standard RX."""
        q = QuantumRegister(1, "q")
        qc = QuantumCircuit(q)
        qc.rx(np.pi, 0)
        self.definition = qc

    def __array__(self, dtype: np.dtype[np.complex128] | None = None) -> NDArray[np.complex128]:  # noqa: PLW3201
        """Return matrix representation of RX(π)."""
        return RXGate(np.pi).__array__(dtype=dtype)


class RXPiOver2Gate(Gate):  # type: ignore[misc]
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
        super().__init__("rx_pi_2", 1, [np.pi / 2], label=label)

    def _define(self) -> None:
        """Define RX(π/2) gate using standard RX."""
        q = QuantumRegister(1, "q")
        qc = QuantumCircuit(q)
        qc.rx(np.pi / 2, 0)
        self.definition = qc

    def __array__(self, dtype: np.dtype[np.complex128] | None = None) -> NDArray[np.complex128]:  # noqa: PLW3201
        """Return matrix representation of RX(π/2)."""
        return RXGate(np.pi / 2).__array__(dtype=dtype)


class RXMinusPiOver2Gate(Gate):  # type: ignore[misc]
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
        super().__init__("rx_minus_pi_2", 1, [-np.pi / 2], label=label)

    def _define(self) -> None:
        """Define RX(-π/2) gate using standard RX."""
        q = QuantumRegister(1, "q")
        qc = QuantumCircuit(q)
        qc.rx(-np.pi / 2, 0)
        self.definition = qc

    def __array__(self, dtype: np.dtype[np.complex128] | None = None) -> NDArray[np.complex128]:  # noqa: PLW3201
        """Return matrix representation of RX(-π/2)."""
        return RXGate(-np.pi / 2).__array__(dtype=dtype)


def u_gate_equivalence() -> None:
    """Add U(θ, φ, λ) gate equivalence to the SessionEquivalenceLibrary using RZ and RX gates."""
    theta = Parameter("θ")
    phi = Parameter("φ")
    lam = Parameter("λ")

    qr = QuantumRegister(1, "q")
    qc = QuantumCircuit(qr)

    # Decomposition: U(θ, φ, λ) = RZ(φ) RX(-π/2) RZ(θ) RX(π/2) RZ(λ)
    qc.append(RZGate(phi), [qr[0]])
    qc.append(RXMinusPiOver2Gate(), [qr[0]])
    qc.append(RZGate(theta), [qr[0]])
    qc.append(RXPiOver2Gate(), [qr[0]])
    qc.append(RZGate(lam), [qr[0]])

    SessionEquivalenceLibrary.add_equivalence(UGate(theta, phi, lam), qc)


def cx_gate_equivalence() -> None:
    """Add CX gate equivalence using iSWAP and single-qubit RX/RZ gates."""
    qr = QuantumRegister(2, "q")
    qc = QuantumCircuit(qr)

    # (I ⊗ H) ≈ RZ(pi) RX(pi/2) RZ(pi)
    qc.rz(np.pi, qr[1])
    qc.append(RXPiOver2Gate(), [qr[1]])
    qc.rz(np.pi, qr[1])

    # First iSWAP
    qc.append(iSwapGate(), [qr[0], qr[1]])

    # (S† ⊗ H) ≈ RZ(-pi/2) on control, RZ(pi) RX(pi/2) RZ(pi) on target
    qc.rz(-np.pi / 2, qr[0])
    qc.rz(np.pi, qr[1])
    qc.append(RXPiOver2Gate(), [qr[1]])
    qc.rz(np.pi, qr[1])

    # Second iSWAP
    qc.append(iSwapGate(), [qr[0], qr[1]])

    # Final (I ⊗ S) ≈ RZ(pi/2)
    qc.rz(np.pi / 2, qr[1])

    # Register equivalence
    SessionEquivalenceLibrary.add_equivalence(CXGate(), qc)


def add_rigetti_equivalences() -> None:
    """Add Rigetti gate equivalences to the session equivalence library."""
    u_gate_equivalence()
    cx_gate_equivalence()


add_rigetti_equivalences()
