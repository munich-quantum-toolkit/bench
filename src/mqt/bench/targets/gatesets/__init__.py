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
from typing import TYPE_CHECKING

from qiskit.circuit import Parameter
from qiskit.circuit.library.standard_gates import get_standard_gate_name_mapping
from qiskit.providers.fake_provider import GenericBackendV2

from .clifford_t import get_clifford_t_gateset, get_clifford_t_rotations_gateset
from .ibm import get_ibm_eagle_gateset, get_ibm_falcon_gateset, get_ibm_heron_gateset
from .ionq import GPI2Gate, GPIGate, MSGate, ZZGate, get_ionq_aria_gateset, get_ionq_forte_gateset
from .iqm import get_iqm_gateset
from .quantinuum import get_quantinuum_gateset
from .rigetti import RXPI2DgGate, RXPI2Gate, RXPIGate, get_rigetti_ankaa_gateset

if TYPE_CHECKING:
    from qiskit.transpiler import Target


__all__ = [
    "get_available_native_gatesets",
    "get_clifford_t_gateset",
    "get_clifford_t_rotations_gateset",
    "get_ibm_eagle_gateset",
    "get_ibm_falcon_gateset",
    "get_ibm_heron_gateset",
    "get_ionq_aria_gateset",
    "get_ionq_forte_gateset",
    "get_iqm_gateset",
    "get_quantinuum_gateset",
    "get_rigetti_ankaa_gateset",
    "get_target_for_gateset",
]


@cache
def get_available_native_gatesets() -> dict[str, list[str]]:
    """Return a list of available native gatesets."""
    return {
        "ibm_falcon": get_ibm_falcon_gateset(),
        "ibm_eagle": get_ibm_eagle_gateset(),
        "ibm_heron": get_ibm_heron_gateset(),
        "ionq_forte": get_ionq_forte_gateset(),
        "ionq_aria": get_ionq_aria_gateset(),
        "iqm": get_iqm_gateset(),
        "quantinuum": get_quantinuum_gateset(),
        "rigetti": get_rigetti_ankaa_gateset(),
        "clifford+t": get_clifford_t_gateset(),
        "clifford+t+rotations": get_clifford_t_rotations_gateset(),
    }


@cache
def get_target_for_gateset(name: str, num_qubits: int) -> Target:
    """Return the Target object for a given native gateset name."""
    try:
        gates = get_available_native_gatesets()[name]
    except KeyError:
        msg = f"Gateset '{name}' not found in available gatesets."
        raise ValueError(msg) from None

    standard_gates = []
    other_gates = []
    for gate in gates:
        if gate in get_standard_gate_name_mapping():
            standard_gates.append(gate)
        else:
            other_gates.append(gate)
    backend = GenericBackendV2(num_qubits=num_qubits, basis_gates=standard_gates)
    target = backend.target
    target.description = name

    for gate in other_gates:
        alpha = Parameter("alpha")
        beta = Parameter("beta")
        gamma = Parameter("gamma")
        if gate == "gpi":
            target.add_instruction(GPIGate(alpha))
        elif gate == "gpi2":
            target.add_instruction(GPI2Gate(alpha))
        elif gate == "ms":
            target.add_instruction(MSGate(alpha, beta, gamma))
        elif gate == "zz":
            target.add_instruction(ZZGate(alpha))
        elif gate == "rxpi":
            target.add_instruction(RXPIGate())
        elif gate == "rxpi2":
            target.add_instruction(RXPI2Gate())
        elif gate == "rxpi2dg":
            target.add_instruction(RXPI2DgGate())
        else:
            msg = f"Gate '{gate}' not found in available gatesets."
            raise ValueError(msg) from None

    return target
