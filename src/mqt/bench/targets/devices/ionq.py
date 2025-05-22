# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""File to create a target device from the IonQ calibration data."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np
from qiskit import QuantumRegister
from qiskit.circuit import Gate, Parameter, QuantumCircuit
from qiskit.circuit.equivalence_library import SessionEquivalenceLibrary
from qiskit.circuit.library import CU3Gate, CXGate, Measure, RXGate, RZGate, UGate, XGate
from qiskit.transpiler import InstructionProperties, Target

if TYPE_CHECKING:
    from qiskit.circuit.parameterexpression import ParameterValueType


class GPIGate(Gate):
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
        q = QuantumRegister(1, "q")
        qc = QuantumCircuit(q)
        qc.x(0)
        qc.rz(4 * phi * np.pi, 0)

        self.definition = qc

    def __array__(self, dtype: np.dtype[np.complex128] | None = None) -> np.ndarray:
        """Return a numpy array for the GPI gate."""
        top = np.exp(-1j * 2 * math.pi * self.params[0])
        bottom = np.exp(1j * 2 * math.pi * self.params[0])
        return np.array([[0, top], [bottom, 0]], dtype=dtype)


class GPI2Gate(Gate):
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
        q = QuantumRegister(1, "q")
        qc = QuantumCircuit(q)
        qc.rz(-2 * phi * np.pi, 0)
        qc.rx(np.pi / 2, 0)
        qc.rz(2 * phi * np.pi, 0)

        self.definition = qc

    def __array__(self, dtype: np.dtype[np.complex128] | None = None) -> np.ndarray:
        """Return a numpy array for the GPI2 gate."""
        top = -1j * np.exp(-1j * self.params[0] * 2 * math.pi)
        bottom = -1j * np.exp(1j * self.params[0] * 2 * math.pi)
        return 1 / np.sqrt(2) * np.array([[1, top], [bottom, 1]], dtype=dtype)


class MSGate(Gate):
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
        theta: ParameterValueType,
        label: str | None = None,
    ) -> None:
        """Create new MS gate."""
        super().__init__(
            "ms",
            2,
            [phi0, phi1, theta],
            label=label,
        )

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

    def __array__(self, dtype: np.dtype[np.complex128] | None = None) -> np.ndarray:
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


class ZZGate(Gate):
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
        q = QuantumRegister(2, "q")
        qc = QuantumCircuit(q)
        qc.cx(0, 1)
        qc.rz(2 * np.pi * theta, 1)
        qc.cx(0, 1)

        self.definition = qc

    def __array__(self, dtype: np.dtype[np.complex128] | None = None) -> np.ndarray:
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


# Below are the rules needed for Aer simulator to simulate circuits containing IonQ native gates


def gpi_gate_equivalence() -> None:
    """Add GPI gate equivalence to the SessionEquivalenceLibrary."""
    q = QuantumRegister(1, "q")
    phi_param = Parameter("phi_param")
    gpi_gate = QuantumCircuit(q)
    gpi_gate.append(XGate(), [0])
    gpi_gate.append(RZGate(4 * phi_param * np.pi), [0])
    SessionEquivalenceLibrary.add_equivalence(GPIGate(phi_param), gpi_gate)


def gpi2_gate_equivalence() -> None:
    """Add GPI2 gate equivalence to the SessionEquivalenceLibrary."""
    q = QuantumRegister(1, "q")
    phi_param = Parameter("phi_param")
    gpi2_gate = QuantumCircuit(q)
    gpi2_gate.append(RZGate(-2 * phi_param * np.pi), [0])
    gpi2_gate.append(RXGate(np.pi / 2), [0])
    gpi2_gate.append(RZGate(2 * phi_param * np.pi), [0])
    SessionEquivalenceLibrary.add_equivalence(GPI2Gate(phi_param), gpi2_gate)


def ms_gate_equivalence() -> None:
    """Add MS gate equivalence to the SessionEquivalenceLibrary."""
    q = QuantumRegister(2, "q")
    phi0_param = Parameter("phi0_param")
    phi1_param = Parameter("phi1_param")
    theta_param = Parameter("theta_param")
    alpha_param = phi0_param + phi1_param
    beta_param = phi0_param - phi1_param
    ms_gate = QuantumCircuit(q)
    ms_gate.append(CXGate(), [1, 0])
    ms_gate.x(0)
    ms_gate.append(
        CU3Gate(
            2 * theta_param * np.pi,
            2 * alpha_param * np.pi - np.pi / 2,
            np.pi / 2 - 2 * alpha_param * np.pi,
        ),
        [0, 1],
    )
    ms_gate.x(0)
    ms_gate.append(
        CU3Gate(
            2 * theta_param * np.pi,
            -2 * beta_param * np.pi - np.pi / 2,
            np.pi / 2 + 2 * beta_param * np.pi,
        ),
        [0, 1],
    )
    ms_gate.append(CXGate(), [1, 0])
    SessionEquivalenceLibrary.add_equivalence(MSGate(phi0_param, phi1_param, theta_param), ms_gate)


def zz_gate_equivalence() -> None:
    """Add ZZ gate equivalence to the SessionEquivalenceLibrary."""
    q = QuantumRegister(2, "q")
    theta_param = Parameter("theta_param")
    zz_circuit = QuantumCircuit(q)
    zz_circuit.cx(0, 1)
    zz_circuit.rz(2 * np.pi * theta_param, 1)
    zz_circuit.cx(0, 1)
    SessionEquivalenceLibrary.add_equivalence(ZZGate(theta_param), zz_circuit)


def add_equivalences() -> None:
    """Add IonQ gate equivalences to the SessionEquivalenceLibrary."""
    u_gate_equivalence()
    cx_via_ms_equivalence()
    cx_via_zz_equivalence()
    gpi_gate_equivalence()
    gpi2_gate_equivalence()
    ms_gate_equivalence()
    zz_gate_equivalence()


add_equivalences()


def get_ionq_target(device_name: str) -> Target:
    """Get the target device for a given IonQ device name."""
    if device_name == "ionq_aria_1":
        return get_ionq_aria_1_target()
    if device_name == "ionq_forte_1":
        return get_ionq_forte_1_target()
    msg = f"Unknown IonQ device: '{device_name}'"
    raise ValueError(msg)


def get_ionq_aria_1_target() -> Target:
    """Get the target device for IonQ Aria 1."""
    num_qubits = 25
    return _build_ionq_target(
        num_qubits=num_qubits,
        description="ionq_aria_1",
        entangling_gate="MS",
        oneq_duration=135e-6,
        twoq_duration=600e-6,
        readout_duration=300e-6,
        oneq_fidelity=0.9998,
        twoq_fidelity=0.98720,
        spam_fidelity=0.99370,
    )


def get_ionq_forte_1_target() -> Target:
    """Get the target device for IonQ Forte 1."""
    num_qubits = 36
    return _build_ionq_target(
        num_qubits=num_qubits,
        description="ionq_forte_1",
        entangling_gate="ZZ",
        oneq_duration=130e-6,
        twoq_duration=970e-6,
        readout_duration=150e-6,
        oneq_fidelity=0.9998,
        twoq_fidelity=0.9932,
        spam_fidelity=0.9959,
    )


def _build_ionq_target(
    *,
    num_qubits: int,
    description: str,
    entangling_gate: str,
    oneq_duration: float,
    twoq_duration: float,
    readout_duration: float,
    oneq_fidelity: float,
    twoq_fidelity: float,
    spam_fidelity: float,
) -> Target:
    """Construct a hardcoded IonQ target using mean values."""
    target = Target(num_qubits=num_qubits, description=description)

    theta = Parameter("theta")
    phi = Parameter("phi")

    # === Add single-qubit gates ===
    singleq_props = {
        (q,): InstructionProperties(duration=oneq_duration, error=1 - oneq_fidelity) for q in range(num_qubits)
    }
    measure_props = {
        (q,): InstructionProperties(duration=readout_duration, error=1 - spam_fidelity) for q in range(num_qubits)
    }

    target.add_instruction(GPIGate(theta), singleq_props)
    target.add_instruction(GPI2Gate(phi), singleq_props)
    target.add_instruction(Measure(), measure_props)

    # === Add two-qubit gates ===
    connectivity = [(i, j) for i in range(num_qubits) for j in range(num_qubits) if i != j]
    twoq_props = {
        (q1, q2): InstructionProperties(duration=twoq_duration, error=1 - twoq_fidelity) for q1, q2 in connectivity
    }

    if entangling_gate == "MS":
        alpha = Parameter("alpha")
        beta = Parameter("beta")
        gamma = Parameter("gamma")
        target.add_instruction(MSGate(alpha, beta, gamma), twoq_props)
    elif entangling_gate == "ZZ":
        alpha = Parameter("alpha")
        target.add_instruction(ZZGate(alpha), twoq_props)
    else:
        msg = f"Unknown entangling gate: '{entangling_gate}'."
        raise ValueError(msg)
    return target
