# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Compile native gate aliases through standard Qiskit gates."""

from __future__ import annotations

from copy import deepcopy
from math import pi

from qiskit import QuantumCircuit
from qiskit.circuit import EquivalenceLibrary, Gate
from qiskit.circuit.equivalence_library import StandardEquivalenceLibrary
from qiskit.circuit.library import RXGate, SXdgGate, SXGate, XGate
from qiskit.transpiler import PassManager, Target
from qiskit.transpiler.passes import BasisTranslator

from .ionq import GPI2Gate, GPIGate


def prepare_target(target: Target, *, native: bool) -> tuple[Target, PassManager | None]:
    """Optimize standard gates, then lower to IonQ or Rigetti native names.

    Local equivalences preserve global phase without changing Qiskit's session
    library. Native compilation ignores physical placement.
    """
    candidates = {
        "gpi": (GPIGate, XGate(), 0.0, 0.0),
        "gpi2": (GPI2Gate, SXGate(), 0.0, pi / 4),
        "rxpi": (RXGate, XGate(), pi, pi / 2),
        "rxpidg": (RXGate, XGate(), -pi, -pi / 2),
        "rxpi2": (RXGate, SXGate(), pi / 2, pi / 4),
        "rxpi2dg": (RXGate, SXdgGate(), -pi / 2, -pi / 4),
    }
    standard_gates = {}
    for name, (gate_type, standard_gate, angle, phase) in candidates.items():
        if name not in target.operation_names or standard_gate.name in target.operation_names:
            continue
        operation = target.operation_from_name(name)
        if type(operation) is not gate_type:
            continue
        if gate_type is RXGate and operation.params != [angle]:
            continue
        if target.instruction_supported(operation_name=name, parameters=[angle]):
            standard_gates[name] = (standard_gate, angle, phase)
    if not standard_gates:
        return target, None

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
    library = EquivalenceLibrary(base=StandardEquivalenceLibrary)
    for name in target.operation_names:
        operation = target.operation_from_name(name)
        properties = None if native or isinstance(operation, type) else deepcopy(target[name])
        if name not in standard_gates:
            compilation_target.add_instruction(operation, properties, name=name)
            continue
        standard_gate, angle, phase = standard_gates[name]
        if standard_gate.name in compilation_target.operation_names:
            continue
        compilation_target.add_instruction(standard_gate, properties)
        if name in {"gpi", "gpi2"}:
            gate = GPIGate(angle) if name == "gpi" else GPI2Gate(angle)
        else:
            gate = Gate(name, 1, [angle])
            gate.definition = QuantumCircuit(1)
            gate.definition.rx(angle, 0)
        rule = QuantumCircuit(1, global_phase=phase)
        rule.append(gate, [0])
        library.add_equivalence(standard_gate, rule)
    lowering = PassManager(BasisTranslator(library, list(target.operation_names), target=None if native else target))
    return compilation_target, lowering
