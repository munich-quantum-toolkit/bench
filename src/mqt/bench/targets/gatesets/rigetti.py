# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Fixed-angle RX gates and arbitrary RZ rotations for Rigetti targets."""

from __future__ import annotations

from copy import deepcopy
from math import pi

from qiskit import QuantumCircuit
from qiskit.circuit import EquivalenceLibrary, Gate
from qiskit.circuit.equivalence_library import StandardEquivalenceLibrary
from qiskit.circuit.library import SXdgGate, SXGate, XGate
from qiskit.transpiler import PassManager, Target
from qiskit.transpiler.passes import BasisTranslator

from ._registry import register_gateset


@register_gateset("rigetti")
def get_rigetti_gateset() -> list[str]:
    """Return the RX/RZ/CZ basis used by Cepheus."""
    return ["rxpi", "rxpidg", "rxpi2", "rxpi2dg", "rz", "cz", "measure"]


def prepare_target(target: Target, *, native: bool) -> tuple[Target, PassManager]:
    """Use standard X gates for Qiskit synthesis, then lower to native RX gates.

    The input is a Rigetti RX/RZ/CZ target with all four fixed RX angles.
    The local equivalences preserve full phase without changing Qiskit's
    session library. Native compilation ignores physical placement.
    """
    compilation_target = Target(
        num_qubits=target.num_qubits,
        description=target.description,
        dt=target.dt,
        granularity=target.granularity,
        min_length=target.min_length,
        pulse_alignment=target.pulse_alignment,
        acquire_alignment=target.acquire_alignment,
        qubit_properties=target.qubit_properties,
        concurrent_measurements=target.concurrent_measurements,
    )
    standard_gates = {"rxpi": (XGate(), pi), "rxpi2": (SXGate(), pi / 2), "rxpi2dg": (SXdgGate(), -pi / 2)}
    library = EquivalenceLibrary(base=StandardEquivalenceLibrary)
    for name in target.operation_names:
        if name == "rxpidg":
            # X lowers to RX(pi); the native target retains both signs.
            continue
        operation = target.operation_from_name(name)
        properties = None if native or isinstance(operation, type) else deepcopy(target[name])
        if name not in standard_gates:
            compilation_target.add_instruction(operation, properties, name=name)
            continue
        standard_gate, angle = standard_gates[name]
        compilation_target.add_instruction(standard_gate, properties)
        gate = Gate(name, 1, [angle])
        gate.definition = QuantumCircuit(1)
        gate.definition.rx(angle, 0)
        rule = QuantumCircuit(1, global_phase=angle / 2)
        rule.append(gate, [0])
        library.add_equivalence(standard_gate, rule)
    lowering = PassManager(BasisTranslator(library, list(target.operation_names), target=None if native else target))
    return compilation_target, lowering
