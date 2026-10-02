# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Fixed RX pulses and arbitrary RZ rotations for Rigetti targets."""

from __future__ import annotations

from math import pi
from typing import TYPE_CHECKING

from qiskit import QuantumCircuit
from qiskit.circuit import Gate, Parameter
from qiskit.circuit.library import UGate

from ._registry import register_gateset

if TYPE_CHECKING:
    from qiskit.circuit import EquivalenceLibrary

_U_GATE = UGate(Parameter("theta"), Parameter("phi"), Parameter("lambda"))
"""Stable parameter identities for equivalence lookup."""


@register_gateset("rigetti")
def get_rigetti_gateset() -> list[str]:
    """Return the RX/RZ/CZ basis used by Cepheus."""
    return ["rxpi", "rxpidg", "rxpi2", "rxpi2dg", "rz", "cz", "measure"]


def add_equivalences(sel: EquivalenceLibrary) -> None:
    """Register U decomposition with fixed RX target aliases once per library.

    Compare copies because Qiskit equality caches pulse definitions.
    """
    theta, phi, lam = _U_GATE.params
    pulses = []
    for name, angle in (("rxpi2", pi / 2), ("rxpi2dg", -pi / 2)):
        pulse = Gate(name, 1, [angle])
        pulse.definition = QuantumCircuit(1)
        pulse.definition.rx(angle, 0)
        pulses.append(pulse)
    circuit = QuantumCircuit(1, global_phase=(phi + lam) / 2)
    circuit.rz(lam, 0)
    circuit.append(pulses[0], [0])
    circuit.rz(theta, 0)
    circuit.append(pulses[1], [0])
    circuit.rz(phi, 0)
    if circuit not in (entry.copy() for entry in sel.get_entry(_U_GATE)):
        sel.add_equivalence(_U_GATE, circuit)
