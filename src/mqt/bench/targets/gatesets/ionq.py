# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Handles the available native gatesets for IonQ."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np
from qiskit import QuantumCircuit, QuantumRegister
from qiskit.circuit import Gate, Parameter, SessionEquivalenceLibrary
from qiskit.circuit.library import CXGate, UGate

if TYPE_CHECKING:
    from numpy._typing import NDArray
    from qiskit.circuit.parameterexpression import ParameterValueType


def get_ionq_gateset() -> list[str]:
    """Returns the basis gates of the IonQ gateset."""
    return ["rx", "ry", "rz", "rxx"]


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

    def __array__(self, dtype: np.dtype[np.complex128] | None = None) -> NDArray[np.complex128]:  # noqa: PLW3201
        """Return a numpy array for the GPI gate."""
        top = np.exp(-1j * 2 * math.pi * self.params[0])
        bottom = np.exp(1j * 2 * math.pi * self.params[0])
        return np.array([[0, top], [bottom, 0]], dtype=dtype)


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

    def __array__(self, dtype: np.dtype[np.complex128] | None = None) -> NDArray[np.complex128]:  # noqa: PLW3201
        """Return a numpy array for the GPI2 gate."""
        top = -1j * np.exp(-1j * self.params[0] * 2 * math.pi)
        bottom = -1j * np.exp(1j * self.params[0] * 2 * math.pi)
        return 1 / np.sqrt(2) * np.array([[1, top], [bottom, 1]], dtype=dtype)


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

    def __array__(self, dtype: np.dtype[np.complex128] | None = None) -> NDArray[np.complex128]:  # noqa: PLW3201
        """Return a numpy array for the MS gate."""
        phi0 = self.params[0]
        phi1 = self.params[1]
        theta = self.params[2]
        diag = np.cos(math.pi * theta)
        sin = np.sin(math.pi * theta)

        return np.array(
            [
                [diag, 0, 0, sin * -1j * np.exp(-1j * 2 * math.pi * (phi0 + phi1))],
                [0, diag, sin * -1j * np.exp(1j * 2 * math.pi * (phi0 - phi1)), 0],
                [0, sin * -1j * np.exp(-1j * 2 * math.pi * (phi0 - phi1)), diag, 0],
                [sin * -1j * np.exp(1j * 2 * math.pi * (phi0 + phi1)), 0, 0, diag],
            ],
            dtype=dtype,
        )


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
        qc.cx(0, 1)
        qc.rz(2 * np.pi * theta, 1)
        qc.cx(0, 1)

        self.definition = qc

    def __array__(self, dtype: np.dtype[np.complex128] | None = None) -> NDArray[np.complex128]:  # noqa: PLW3201
        """Return a numpy array for the ZZ gate."""
        itheta2 = 1j * float(self.params[0]) * math.pi
        return np.array(
            [
                [np.exp(-itheta2), 0, 0, 0],
                [0, np.exp(itheta2), 0, 0],
                [0, 0, np.exp(itheta2), 0],
                [0, 0, 0, np.exp(-itheta2)],
            ],
            dtype=dtype,
        )


def u_gate_equivalence() -> None:
    """Add U gate equivalence to the SessionEquivalenceLibrary."""
    q = QuantumRegister(1, "q")
    theta_param = Parameter("theta_param")
    phi_param = Parameter("phi_param")
    lambda_param = Parameter("lambda_param")
    u_gate = QuantumCircuit(q)
    # this sequence can be compacted if virtual-z gates will be introduced
    u_gate.append(GPI2Gate(0.5 - lambda_param / (2 * np.pi)), [0])
    u_gate.append(
        GPIGate(theta_param / (4 * np.pi) + phi_param / (4 * np.pi) - lambda_param / (4 * np.pi)),
        [0],
    )
    u_gate.append(GPI2Gate(0.5 + phi_param / (2 * np.pi)), [0])
    SessionEquivalenceLibrary.add_equivalence(UGate(theta_param, phi_param, lambda_param), u_gate)


def cx_via_ms_equivalence() -> None:
    """Add CX gate equivalence to the SessionEquivalenceLibrary for both native two-qubit gates."""
    q = QuantumRegister(2, "q")
    cx_gate = QuantumCircuit(q)
    cx_gate.append(GPI2Gate(1 / 4), [0])
    cx_gate.append(MSGate(0, 0, 0.25), [0, 1])
    cx_gate.append(GPI2Gate(1 / 2), [0])
    cx_gate.append(GPI2Gate(1 / 2), [1])
    cx_gate.append(GPI2Gate(-1 / 4), [0])
    SessionEquivalenceLibrary.add_equivalence(CXGate(), cx_gate)


def cx_via_zz_equivalence() -> None:
    """Add equivalence CX ≡ H-ZZ(pi/4)-H."""
    q = QuantumRegister(2, "q")
    cx_equiv = QuantumCircuit(q)
    cx_equiv.h(1)
    cx_equiv.append(ZZGate(0.25), [0, 1])  # pi/4
    cx_equiv.h(1)

    SessionEquivalenceLibrary.add_equivalence(CXGate(), cx_equiv)


def add_ionq_equivalences() -> None:
    """Add IonQ gate equivalences to the SessionEquivalenceLibrary."""
    u_gate_equivalence()
    cx_via_ms_equivalence()
    cx_via_zz_equivalence()
