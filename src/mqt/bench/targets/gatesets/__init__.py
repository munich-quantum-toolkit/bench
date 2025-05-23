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

from qiskit.providers.fake_provider import GenericBackendV2

from .clifford_t import get_clifford_t_gateset, get_clifford_t_rotations_gateset
from .ibm import get_ibm_falcon_gateset, get_ibm_eagle_gateset, get_ibm_heron_gateset
from .iqm import get_iqm_gateset
from .ionq import get_ionq_gateset
from .quantinuum import get_quantinuum_gateset
from .rigetti import get_rigetti_gateset

if TYPE_CHECKING:
    from qiskit.transpiler import Target


@cache
def get_available_native_gatesets() -> dict[str, list[str]]:
    """Return a list of available native gatesets."""
    return {
        "ibm_falcon": get_ibm_falcon_gateset(),
        "ibm_eagle": get_ibm_eagle_gateset(),
        "ibm_heron": get_ibm_heron_gateset(),
        "ionq": get_ionq_gateset(),
        "iqm": get_iqm_gateset(),
        "quantinuum": get_quantinuum_gateset(),
        "rigetti": get_rigetti_gateset(),
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

    backend = GenericBackendV2(num_qubits=num_qubits, basis_gates=gates)
    target = backend.target
    target.description = name
    return target


