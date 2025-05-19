# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Handles the available native gatesets."""

from __future__ import annotations

from functools import cache

from qiskit.circuit import Instruction, Measure, Parameter
from qiskit.circuit.library import (
    Barrier,
    CPhaseGate,
    CXGate,
    CYGate,
    CZGate,
    DCXGate,
    ECRGate,
    HGate,
    IGate,
    RXGate,
    RXXGate,
    RYGate,
    RZGate,
    RZZGate,
    SdgGate,
    SGate,
    SwapGate,
    SXdgGate,
    SXGate,
    TdgGate,
    TGate,
    U3Gate,
    XGate,
    XXPlusYYGate,
    YGate,
    ZGate,
    iSwapGate,
)
from qiskit.transpiler import Target


def get_clifford_t_gateset() -> list[Instruction]:
    """Returns the native gateset for the Clifford+T target."""
    return [
        IGate(),
        XGate(),
        YGate(),
        ZGate(),
        HGate(),
        SGate(),
        SdgGate(),
        TGate(),
        TdgGate(),
        SXGate(),
        SXdgGate(),
        CXGate(),
        CYGate(),
        CZGate(),
        SwapGate(),
        iSwapGate(),
        DCXGate(),
        ECRGate(),
        Measure(),
    ]


@cache
def get_available_native_gatesets() -> dict[str, list[Instruction]]:
    """Return a list of available native gatesets."""
    return {
        "ibm_falcon": get_ibm_falcon_gateset(),
        "ibm_heron_r1": get_ibm_heron_r1_gateset(),
        "ionq": get_ionq_gateset(),
        "iqm": get_iqm_gateset(),
        "quantinuum": get_quantinuum_gateset(),
        "rigetti": get_rigetti_gateset(),
        "clifford+t": get_clifford_t_gateset(),
    }


@cache
def get_native_gateset_by_name(name: str, num_qubits: int = 20) -> Target:
    """Return the Target object for a given native gateset name."""
    gatesets = get_available_native_gatesets()
    try:
        gates = gatesets[name]

    except KeyError:
        msg = f"Gateset '{name}' not found in available gatesets."
        raise ValueError(msg) from None

    target = Target(num_qubits=num_qubits, description=name)

    for gate in gates:
        target.add_instruction(gate)
    target.add_instruction(Barrier(num_qubits))
    return target


def get_ibm_falcon_gateset() -> list[Instruction]:
    """Returns the basis gates of the ibm falcon gateset."""
    alpha = Parameter("alpha")
    return [SXGate(), RZGate(alpha), CXGate(), Measure()]


def get_ibm_heron_r1_gateset() -> list[Instruction]:
    """Returns the basis gates of the ibm heron r1 gateset."""
    alpha = Parameter("alpha")
    return [SXGate(), RZGate(alpha), CZGate(), XGate(), Measure()]


def get_ionq_gateset() -> list[Instruction]:
    """Returns the basis gates of the ionq gateset."""
    alpha = Parameter("alpha")
    beta = Parameter("beta")
    gamma = Parameter("gamma")
    delta = Parameter("delta")
    return [RXGate(alpha), RZGate(beta), RXXGate(delta), RYGate(gamma), Measure()]


def get_iqm_gateset() -> list[Instruction]:
    """Returns the basis gates of the iqm gateset."""
    alpha = Parameter("alpha")
    beta = Parameter("beta")
    gamma = Parameter("gamma")
    return [U3Gate(alpha, beta, gamma), CZGate(), Measure()]


def get_quantinuum_gateset() -> list[Instruction]:
    """Returns the basis gates of the quantinuum gateset."""
    alpha = Parameter("alpha")
    beta = Parameter("beta")
    gamma = Parameter("gamma")
    delta = Parameter("delta")
    return [RZZGate(delta), RZGate(alpha), RYGate(beta), RXGate(gamma), Measure()]


def get_rigetti_gateset() -> list[Instruction]:
    """Returns the basis gates of the rigetti gateset."""
    alpha = Parameter("alpha")
    beta = Parameter("beta")
    gamma = Parameter("gamma")
    delta = Parameter("delta")
    return [RXGate(alpha), RZGate(beta), CZGate(), CPhaseGate(gamma), XXPlusYYGate(delta), Measure()]
