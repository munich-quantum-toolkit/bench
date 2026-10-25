# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Test targets."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from math import pi
from typing import TYPE_CHECKING

import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit.circuit import Gate, Parameter
from qiskit.circuit.library import CZGate, HGate, RXGate, RYGate, RZGate, RZZGate
from qiskit.quantum_info import Operator
from qiskit.transpiler import Target

from mqt.bench import BenchmarkLevel, get_benchmark
from mqt.bench.targets.devices import (
    _module_from_device_name,  # ruff:ignore[import-private-name]
    get_available_device_names,
    get_device,
    register_device,
)
from mqt.bench.targets.gatesets import (
    _module_from_gateset_name,  # ruff:ignore[import-private-name]
    get_available_gateset_names,
    get_gateset,
    get_target_for_gateset,
    register_gateset,
)
from mqt.bench.targets.gatesets._compilation import prepare_target  # ruff:ignore[import-private-name]
from mqt.bench.targets.gatesets.ionq import GPI2Gate, GPIGate

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


@dataclass(frozen=True)
class DeviceSpec:
    """Specification describing an expected device configuration."""

    name: str
    num_qubits: int
    single_qubit_gates: set[str] = field(default_factory=set)
    two_qubit_gates: set[str] = field(default_factory=set)
    # If *symmetric_connectivity* is *True*, require (q1, q0) whenever (q0, q1)
    symmetric_connectivity: Mapping[str, bool] = field(default_factory=dict)

    def __post_init__(self) -> None:  # pragma: no cover
        """Ensures that all declared two-qubit gates have an associated symmetry flag."""
        # Ensure symmetry flags are defined for all declared 2-qubit gates
        missing = self.two_qubit_gates.difference(self.symmetric_connectivity)
        if missing:
            object.__setattr__(
                self, "symmetric_connectivity", {**self.symmetric_connectivity, **dict.fromkeys(missing, False)}
            )


def _assert_single_qubit_gate_properties(target: Target, gate_name: str, *, vendor: str) -> None:
    if gate_name not in target.operation_names:
        pytest.fail(f"{vendor}: expected single-qubit gate '{gate_name}' not found in target.operations")

    for (qubit,) in target[gate_name]:
        props = target[gate_name][qubit,]
        assert props is not None, f"{vendor}: props for '{gate_name}' on qubit {qubit} missing"
        dur = getattr(props, "duration", None)
        if dur is not None:
            assert dur >= 0, f"{vendor}: negative duration for '{gate_name}' on qubit {qubit}"
        err = getattr(props, "error", None)
        if err is not None:
            assert 0 <= err < 1, f"{vendor}: error outside [0,1) for '{gate_name}' on qubit {qubit}"


def _assert_two_qubit_gate_properties(target: Target, gate_name: str, *, symmetric: bool, vendor: str) -> None:
    if gate_name not in target.operation_names:
        pytest.fail(f"{vendor}: expected two-qubit gate '{gate_name}' not found in target.operations")

    for (q0, q1), props in target[gate_name].items():
        assert q0 != q1, f"{vendor}: identical qubits for '{gate_name}' connection ({q0}, {q1})"
        assert props is not None, f"{vendor}: props for '{gate_name}' on ({q0}, {q1}) missing"
        dur = getattr(props, "duration", None)
        if dur is not None:
            assert dur > 0, f"{vendor}: non-positive duration for '{gate_name}' on ({q0}, {q1})"
        err = getattr(props, "error", None)
        if err is not None:
            assert 0 <= err < 1, f"{vendor}: error outside [0,1) for '{gate_name}' on ({q0}, {q1})"
        if symmetric:
            assert (
                q1,
                q0,
            ) in target[gate_name], f"{vendor}: missing symmetric connection ({q1}, {q0}) for '{gate_name}'"


def _assert_measure_properties(target: Target, *, vendor: str) -> None:
    if "measure" not in target.operation_names:
        pytest.fail(f"{vendor}: missing mandatory 'measure' operation")

    for (qubit,) in target["measure"]:
        props = target["measure"][qubit,]
        assert props is not None, f"{vendor}: measure props missing for qubit {qubit}"
        dur = getattr(props, "duration", None)
        if dur is not None:
            assert dur > 0, f"{vendor}: non-positive measure duration on qubit {qubit}"
        err = getattr(props, "error", None)
        if err is not None:
            assert 0 <= err < 1, f"{vendor}: measure error outside [0,1) on qubit {qubit}"


DEVICE_SPECS: Sequence[DeviceSpec] = [
    # ─────────────────────────────────────────────────────────────────── IBM ──
    DeviceSpec(
        name="ibm_heron_156",
        num_qubits=156,
        single_qubit_gates={"sx", "rz", "x", "measure"},
        two_qubit_gates={"cz"},
    ),
    # ────────────────────────────────────────────────────────────────── IonQ ──
    DeviceSpec(
        name="ionq_forte_36",
        num_qubits=36,
        single_qubit_gates={"gpi", "gpi2", "rz", "measure"},
        two_qubit_gates={"rzz"},
        symmetric_connectivity={"rzz": True},
    ),
    # ─────────────────────────────────────────────────────────────────── IQM ──
    DeviceSpec(
        name="iqm_crystal_5",
        num_qubits=5,
        single_qubit_gates={"r", "measure"},
        two_qubit_gates={"cz"},
        symmetric_connectivity={"cz": True},
    ),
    DeviceSpec(
        name="iqm_crystal_20",
        num_qubits=20,
        single_qubit_gates={"r", "measure"},
        two_qubit_gates={"cz"},
        symmetric_connectivity={"cz": True},
    ),
    DeviceSpec(
        name="iqm_crystal_54",
        num_qubits=54,
        single_qubit_gates={"r", "measure"},
        two_qubit_gates={"cz"},
        symmetric_connectivity={"cz": True},
    ),
    # ────────────────────────────────────────────────────────────── Quantinuum ──
    DeviceSpec(
        name="quantinuum_h2_56",
        num_qubits=56,
        single_qubit_gates={"rx", "ry", "rz", "measure"},
        two_qubit_gates={"rzz"},
        symmetric_connectivity={"rzz": True},
    ),
    # ─────────────────────────────────────────────────────────────── Rigetti ──
    DeviceSpec(
        name="rigetti_cepheus_108",
        num_qubits=108,
        single_qubit_gates={"rxpi", "rxpidg", "rxpi2", "rxpi2dg", "rz", "measure"},
        two_qubit_gates={"cz"},
        symmetric_connectivity={"cz": True},
    ),
]


@pytest.mark.parametrize("spec", DEVICE_SPECS, ids=[d.name for d in DEVICE_SPECS])
def test_device_spec(spec: DeviceSpec) -> None:
    """Validate *all* devices according to their :class:`DeviceSpec`."""
    target = get_device(spec.name)

    # ── Basic identity checks ───────────────────────────────────────────────
    assert isinstance(target, Target)
    assert target.description == spec.name
    assert target.num_qubits == spec.num_qubits

    # ── Single-qubit operations ──────────────────────────────────────────────
    for gate in spec.single_qubit_gates:
        _assert_single_qubit_gate_properties(target, gate, vendor=spec.name)

    # ── Two-qubit operations ────────────────────────────────────────────────
    for gate in spec.two_qubit_gates:
        _assert_two_qubit_gate_properties(
            target,
            gate,
            symmetric=spec.symmetric_connectivity.get(gate, False),
            vendor=spec.name,
        )

    # ── Measurement ─────────────────────────────────────────────────────────
    _assert_measure_properties(target, vendor=spec.name)


def test_get_unknown_device() -> None:
    """Requesting an unavailable device must raise *ValueError*."""
    unknown_name = "unknown_device"
    pattern = re.escape(
        f"'{unknown_name}' is not a supported device. Known modules: ['aqt', 'ibm', 'ionq', 'iqm', 'quantinuum', 'rigetti']"
    )

    with pytest.raises(ValueError, match=pattern):
        get_device(unknown_name)


def test_dynamic_device_registration(monkeypatch: pytest.MonkeyPatch) -> None:
    """A device registered at runtime should immediately be visible through the public helpers."""
    get_available_device_names()
    monkeypatch.setattr("mqt.bench.targets.devices._registry._REGISTRY", {})

    @register_device("dummy_device")
    def _dummy_factory() -> Target:
        return Target(num_qubits=1)

    names = get_available_device_names()
    assert "dummy_device" in names

    dev = get_device("dummy_device")
    assert isinstance(dev, Target)


def test_dynamic_gateset_registration(monkeypatch: pytest.MonkeyPatch) -> None:
    """A gateset registered at runtime should immediately be visible through the public helpers."""
    get_available_gateset_names()
    monkeypatch.setattr("mqt.bench.targets.gatesets._registry._REGISTRY", {})

    @register_gateset("dummy_gateset")
    def _dummy_factory() -> list[str]:
        return ["dummy_gate"]

    names = get_available_gateset_names()
    assert "dummy_gateset" in names

    gateset = get_gateset("dummy_gateset")
    assert gateset == ["dummy_gate"]

    with pytest.raises(ValueError, match=re.escape("Gate 'dummy_gate' not found in available custom gates.")):
        get_target_for_gateset("dummy_gateset", 2)


def test_duplicate_device_registration(monkeypatch: pytest.MonkeyPatch) -> None:
    """Registering the same name twice must raise ValueError."""
    get_available_device_names()
    monkeypatch.setattr("mqt.bench.targets.devices._registry._REGISTRY", {})

    @register_device("dup_device")
    def _factory1() -> Target:
        return Target(num_qubits=1)

    # second registration with same name should fail
    with pytest.raises(ValueError, match="already registered"):

        @register_device("dup_device")
        def _factory2() -> Target:
            return Target(num_qubits=1)


def test_duplicate_gateset_registration(monkeypatch: pytest.MonkeyPatch) -> None:
    """Registering the same name twice must raise ValueError."""
    get_available_gateset_names()
    monkeypatch.setattr("mqt.bench.targets.gatesets._registry._REGISTRY", {})

    @register_gateset("dup_device")
    def _factory1() -> list[str]:
        return ["dummy_gate"]

    # second registration with same name should fail
    with pytest.raises(ValueError, match="already registered"):

        @register_gateset("dup_device")
        def _factory2() -> list[str]:
            return ["dummy_gate"]


def test_get_device_immutability() -> None:
    """Changes to a device retrieved by get_device should not affect the device in the registry. Same for device names."""
    device = get_device("ionq_forte_36")
    device.description = "dummy_description"
    assert device.description == "dummy_description"

    device2 = get_device("ionq_forte_36")
    assert device2.description == "ionq_forte_36"

    device_names = get_available_device_names()
    device_names.append("dummy_devicename")

    device_names2 = get_available_device_names()
    assert "dummy_devicename" not in device_names2


def test_get_gateset_immutability() -> None:
    """Changes to a gateset retrieved by get_gateset should not affect the gateset in the registry. Sames for gateset names."""
    gateset = get_gateset("ibm_heron")
    gateset.append("dummy_gate")
    assert "dummy_gate" in gateset

    gateset2 = get_gateset("ibm_heron")
    assert "dummy_gate" not in gateset2

    gateset_names = get_available_gateset_names()
    assert "dummy_gatesetname" not in gateset_names
    gateset_names.append("dummy_gatesetname")

    gateset_names2 = get_available_gateset_names()
    assert "dummy_gatesetname" not in gateset_names2


@pytest.mark.parametrize("gateset_name", get_available_gateset_names())
def test_gateset_target_has_no_hardware_constraints(gateset_name: str) -> None:
    """Native gate sets apply globally without simulated hardware calibration."""
    target = get_target_for_gateset(gateset_name, 3)

    assert target.num_qubits == 3
    assert target.description == gateset_name
    assert target.build_coupling_map() is None
    assert all(properties == {None: None} for properties in target.values())


@pytest.mark.parametrize(
    ("gateset_name", "module_name"),
    [
        ("rigetti", "rigetti"),
        ("ionq_forte", "ionq"),
        ("clifford+t", "clifford_t"),
        ("clifford+t+rotations", "clifford_t"),
    ],
)
def test_module_from_gateset_name(gateset_name: str, module_name: str) -> None:
    """Test module name extraction from gateset name."""
    assert _module_from_gateset_name(gateset_name) == module_name


@pytest.mark.parametrize(
    ("device_name", "module_name"), [("rigetti_cepheus_108", "rigetti"), ("ionq_forte_36", "ionq")]
)
def test_module_from_device_name(device_name: str, module_name: str) -> None:
    """Test module name extraction from device name."""
    assert _module_from_device_name(device_name) == module_name


@pytest.mark.parametrize("gateset", ["ionq_forte", "rigetti"])
@pytest.mark.parametrize("opt_level", [0, 1, 2, 3])
@pytest.mark.parametrize("level", [BenchmarkLevel.NATIVEGATES, BenchmarkLevel.MAPPED])
@pytest.mark.parametrize("symbolic", [False, True])
def test_native_compilation_semantics(gateset: str, opt_level: int, level: BenchmarkLevel, *, symbolic: bool) -> None:
    """Each hardware family preserves the complete matrix and target constraints."""
    theta = Parameter("theta")
    circuit = QuantumCircuit(2)
    circuit.rx(theta if symbolic else 0.31, 0)
    circuit.h(1)
    circuit.u(0.43, -0.25, theta if symbolic else 0.16, 1)
    circuit.cx(0, 1)
    circuit.rz(-0.7, 0)
    target = get_target_for_gateset(gateset, 2)
    result = get_benchmark(circuit, level, target=target, opt_level=opt_level, random_parameters=False)
    for instruction in result.data:
        assert target.instruction_supported(
            instruction.operation.name,
            qargs=tuple(result.find_bit(q).index for q in instruction.qubits),
            parameters=instruction.operation.params,
        )
    if symbolic:
        circuit = circuit.assign_parameters({theta: 0.37})
        result = result.assign_parameters({theta: 0.37})
    np.testing.assert_allclose(Operator.from_circuit(result).data, Operator(circuit).data, atol=1e-12)


def test_native_compilation_preserves_session_equivalences() -> None:
    """Compile arbitrary U/RX gates without adding global equivalence rules."""
    from qiskit.circuit.equivalence_library import SessionEquivalenceLibrary  # ruff:ignore[import-outside-top-level]
    from qiskit.circuit.library import UGate  # ruff:ignore[import-outside-top-level]

    theta, phi, lam = (Parameter(name) for name in ("theta", "phi", "lambda"))
    gates = [UGate(theta, phi, lam), RXGate(theta)]
    before = [SessionEquivalenceLibrary.get_entry(gate) for gate in gates]
    circuit = QuantumCircuit(1)
    circuit.u(0.43, -0.25, 0.16, 0)
    circuit.rx(0.37, 0)
    for gateset in ("ionq_forte", "rigetti"):
        get_benchmark(circuit, BenchmarkLevel.NATIVEGATES, target=get_target_for_gateset(gateset, 1))
    assert [SessionEquivalenceLibrary.get_entry(gate) for gate in gates] == before


@pytest.mark.parametrize(("gate_type", "angle", "phase"), [(GPIGate, pi, pi / 2), (GPI2Gate, pi / 2, 0)])
def test_ionq_radian_definition(gate_type: type[GPIGate | GPI2Gate], angle: float, phase: float) -> None:
    """Gate phases use radians and retain the GPI gate's global phase."""
    phi = Parameter("phi")
    circuit = QuantumCircuit(1)
    circuit.append(gate_type(phi), [0])
    reference = QuantumCircuit(1, global_phase=phase)
    reference.r(angle, 0.37, 0)
    np.testing.assert_allclose(
        Operator(circuit.assign_parameters({phi: 0.37})).data, Operator(reference).data, atol=1e-12
    )


def test_rigetti_fixed_rx_aliases() -> None:
    """All four fixed gates are standard RX capabilities with distinct names."""
    for target in (
        get_target_for_gateset("rigetti", 2),
        get_device("rigetti_cepheus_108"),
    ):
        for name, angle in (("rxpi", pi), ("rxpidg", -pi), ("rxpi2", pi / 2), ("rxpi2dg", -pi / 2)):
            operation = target.operation_from_name(name)
            assert isinstance(operation, RXGate)
            assert operation.params == [angle]
            assert target.instruction_supported(name, (0,), parameters=[angle])
            assert not target.instruction_supported(name, (0,), parameters=[0.123])


def test_cepheus_architecture() -> None:
    """Cepheus includes all 108 qubits and the full grid's bidirectional couplings."""
    target = get_device("rigetti_cepheus_108")
    assert target.num_qubits == 108
    assert set(target["measure"]) == {(q,) for q in range(108)}
    edges = set(target["cz"])
    assert len(edges) == 390
    assert {edge for edge in edges if 8 in edge} == {(7, 8), (8, 7), (8, 17), (17, 8)}
    assert (0, 9) in edges
    assert (98, 107) in edges
    assert (8, 9) not in edges
    assert all((j, i) in edges for i, j in edges)


def test_forte_virtual_z() -> None:
    """Forte supports arbitrary virtual Z rotations in the compiler model."""
    target = get_device("ionq_forte_36")
    assert target.instruction_supported("rz", (0,), parameters=[0.123])
    assert target["rz"][0,].duration == 0
    assert target["rz"][0,].error == 0
    assert "rz" in get_gateset("ionq_forte")


@pytest.mark.parametrize("gateset", ["rigetti", "ionq_forte"])
@pytest.mark.parametrize("angle", [pi / 2, -pi / 2, pi, -pi])
def test_fixed_rotation_uses_one_native_gate(gateset: str, angle: float) -> None:
    """Quarter and half turns need only one native gate besides virtual Z."""
    circuit = QuantumCircuit(2)
    circuit.rx(angle, 0)
    target = get_target_for_gateset(gateset, 2)
    result = get_benchmark(circuit, BenchmarkLevel.NATIVEGATES, target=target)
    assert sum(count for name, count in result.count_ops().items() if name != "rz") == 1
    np.testing.assert_allclose(Operator(result).data, Operator(circuit).data, atol=1e-12)


@pytest.mark.parametrize("gateset", ["rigetti", "ionq_forte"])
@pytest.mark.parametrize("level", [BenchmarkLevel.NATIVEGATES, BenchmarkLevel.MAPPED])
def test_native_output_can_be_controlled_and_recompiled(gateset: str, level: BenchmarkLevel) -> None:
    """Native definitions stay reusable outside their original target."""
    from qiskit import transpile  # ruff:ignore[import-outside-top-level]

    theta = Parameter("theta")
    circuit = QuantumCircuit(2)
    circuit.rx(theta, 0)
    circuit.h(1)
    circuit.cx(0, 1)
    target = get_target_for_gateset(gateset, 2)
    target.description = "custom target"
    result = get_benchmark(circuit, level, target=target, random_parameters=False)
    for value in [-0.37, 0.29]:
        bound = result.assign_parameters({theta: value})
        expected = Operator(bound).data
        recompiled = transpile(bound, basis_gates=["rz", "sx", "x", "cx"])
        np.testing.assert_allclose(Operator.from_circuit(recompiled).data, expected, atol=1e-12)
        np.testing.assert_allclose(
            Operator(bound.to_gate().control()).data,
            Operator(Operator(bound).to_instruction().control()).data,
            atol=1e-12,
        )


@pytest.mark.parametrize(
    ("name", "operation"),
    [
        ("rxpi2", RXGate(0.37)),
        ("rxpi2", RYGate(pi / 2)),
        ("gpi2", HGate()),
        ("gpi2", GPI2Gate(0.37)),
    ],
)
def test_native_gate_names_do_not_override_capabilities(name: str, operation: Gate) -> None:
    """A familiar alias must not change the declared gate or allowed angles."""
    target = Target(num_qubits=2)
    target.add_instruction(RZGate(Parameter("theta")))
    target.add_instruction(CZGate())
    target.add_instruction(operation, name=name)
    prepared, lowering = prepare_target(target, native_num_qubits=2)
    assert prepared.operation_from_name(name) == operation
    assert lowering is None


@pytest.mark.parametrize("level", [BenchmarkLevel.NATIVEGATES, BenchmarkLevel.MAPPED])
@pytest.mark.parametrize("gateset", ["ionq_forte", "rigetti"])
def test_native_aliases_keep_bounded_entanglers(level: BenchmarkLevel, gateset: str) -> None:
    """Lowering aliases retains angle constraints on other native operations."""
    from qiskit.circuit.library import RZZGate  # ruff:ignore[import-outside-top-level]

    original = get_target_for_gateset(gateset, 2)
    target = Target(num_qubits=2)
    for name in original.operation_names:
        operation = original.operation_from_name(name)
        if operation.num_qubits == 1:
            target.add_instruction(operation, name=name)
    target.add_instruction(RZZGate(Parameter("theta")), angle_bounds=[(0, pi / 2)])
    circuit = QuantumCircuit(2)
    circuit.rzz(0.37, 0, 1)
    result = get_benchmark(circuit, level, target=target)
    assert all(
        target.instruction_supported(item.operation.name, parameters=item.operation.params) for item in result.data
    )
    assert target.gate_has_angle_bounds("rzz")
    np.testing.assert_allclose(Operator.from_circuit(result).data, Operator(circuit).data, atol=1e-12)


def test_native_target_legacy_angle_bounds() -> None:
    """Accept bounded targets with the Qiskit 2.2-2.5 serialization schema."""

    class LegacyTarget(Target):
        def __getstate__(self) -> dict:
            state = super().__getstate__()
            base = state["base"]
            if "angle_bounds" not in base:
                base["angle_bounds"] = {
                    name: entry["angle_bounds"]
                    for name, entry in base["gate_map"].items()
                    if self.gate_has_angle_bounds(name)
                }
            return state

    from qiskit.circuit.library import RZZGate  # ruff:ignore[import-outside-top-level]

    target = LegacyTarget(num_qubits=2)
    target.add_instruction(RZGate(Parameter("z")))
    target.add_instruction(RXGate(pi / 2), name="rxpi2")
    target.add_instruction(RZZGate(Parameter("zz")), angle_bounds=[(0, pi / 2)])
    circuit = QuantumCircuit(2)
    circuit.rzz(0.37, 0, 1)
    result = get_benchmark(circuit, BenchmarkLevel.NATIVEGATES, target=target)
    assert all(
        target.instruction_supported(item.operation.name, parameters=item.operation.params) for item in result.data
    )
    np.testing.assert_allclose(Operator.from_circuit(result).data, Operator(circuit).data, atol=1e-12)


@pytest.mark.parametrize("opt_level", [0, 1, 2, 3])
@pytest.mark.parametrize("level", [BenchmarkLevel.NATIVEGATES, BenchmarkLevel.MAPPED])
@pytest.mark.parametrize("angle", [-1e8, -2 * pi, -pi, -pi / 2, -0.37, 0.0, 0.37, pi / 2, 2.4, pi, 2 * pi, 1e8])
def test_fractional_heron_qiskit(level: BenchmarkLevel, angle: float, opt_level: int) -> None:
    """Fractional targets keep native RZZ angles within the hardware interval."""
    target = get_target_for_gateset("ibm_heron_fractional", 2)
    circuit = QuantumCircuit(2)
    circuit.rzz(angle, 0, 1)
    result = get_benchmark(circuit, level, target=target, random_parameters=False, opt_level=opt_level)
    assert all(
        target.instruction_supported(item.operation.name, parameters=item.operation.params) for item in result.data
    )
    np.testing.assert_allclose(Operator(result).data, Operator(circuit).data, atol=1e-12, rtol=0)
    assert result.count_ops().get("rzz", 0) <= 1


@pytest.mark.parametrize("level", [BenchmarkLevel.NATIVEGATES, BenchmarkLevel.MAPPED])
@pytest.mark.parametrize("gateset", ["ionq_forte", "rigetti"])
@pytest.mark.parametrize("angle", [-0.37, 2.4])
def test_native_aliases_preserve_angle_bounds(level: BenchmarkLevel, gateset: str, angle: float) -> None:
    """Native alias lowering retains bounds on other target gates."""
    target = get_target_for_gateset(gateset, 2)
    # Use a bounded entangler with the gate set's native single-qubit aliases.
    bounded = Target(num_qubits=2)
    for name in target.operation_names:
        operation = target.operation_from_name(name)
        if operation.num_qubits == 1:
            bounded.add_instruction(operation, name=name)
    bounded.add_instruction(RZZGate(Parameter("zz")), angle_bounds=[(0, pi / 2)])
    circuit = QuantumCircuit(2)
    circuit.rzz(angle, 0, 1)
    result = get_benchmark(circuit, level, target=bounded, random_parameters=False)
    assert all(
        bounded.instruction_supported(item.operation.name, parameters=item.operation.params) for item in result.data
    )
    assert all(
        bounded.supported_angle_bound("rzz", item.operation.params)
        for item in result.data
        if item.operation.name == "rzz"
    )
    np.testing.assert_allclose(Operator.from_circuit(result).data, Operator(circuit).data, atol=1e-12)


def test_fractional_heron_device() -> None:
    """Fractional gates share the Heron sites and couplings."""
    target = get_device("ibm_heron_156_fractional")
    assert target.num_qubits == 156
    assert target.qargs_for_operation_name("rx") == target.qargs_for_operation_name("sx")
    assert target.qargs_for_operation_name("rzz") == target.qargs_for_operation_name("cz")
    assert target.instruction_supported("rzz", (0, 1), parameters=[np.pi / 2])
    assert not target.instruction_supported("rzz", (0, 1), parameters=[-0.37])


@pytest.mark.parametrize("level", [BenchmarkLevel.NATIVEGATES, BenchmarkLevel.MAPPED])
def test_fractional_wrapping_respects_narrower_bounds(level: BenchmarkLevel) -> None:
    """Heron wrapping must not override a caller's narrower RZZ interval."""
    from qiskit.circuit.library import SXGate, XGate  # ruff:ignore[import-outside-top-level]

    target = Target(num_qubits=2)
    target.add_instruction(XGate())
    target.add_instruction(SXGate())
    target.add_instruction(RZGate(Parameter("z")))
    target.add_instruction(RZZGate(Parameter("zz")), angle_bounds=[(0, pi / 4)])
    circuit = QuantumCircuit(2)
    circuit.rzz(0.1, 0, 1)
    result = get_benchmark(circuit, level, target=target)
    assert all(
        target.instruction_supported(item.operation.name, parameters=item.operation.params) for item in result.data
    )
    np.testing.assert_allclose(Operator.from_circuit(result).data, Operator(circuit).data, atol=1e-12)


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("standard", [False, True])
@pytest.mark.parametrize("level", [BenchmarkLevel.NATIVEGATES, BenchmarkLevel.MAPPED])
def test_aliases_keep_physical_sites_for_mapping(level: BenchmarkLevel, *, reverse: bool, standard: bool) -> None:
    """Equivalent RX aliases retain each physical site's native capability."""
    target = Target(num_qubits=2)
    aliases = [("rxpi", pi, 0), ("rxpidg", -pi, 1)]
    for name, angle, qubit in reversed(aliases) if reverse else aliases:
        if standard and name == "rxpi":
            from qiskit.circuit.library import XGate  # ruff:ignore[import-outside-top-level]

            target.add_instruction(XGate(), {(qubit,): None})
        else:
            target.add_instruction(RXGate(angle), {(qubit,): None}, name=name)
    target.add_instruction(RZGate(Parameter("theta")))
    circuit = QuantumCircuit(2)
    circuit.x(0)
    circuit.x(1)
    result = get_benchmark(circuit, level, target=target)
    for item in result.data:
        assert target.instruction_supported(
            item.operation.name,
            tuple(result.find_bit(qubit).index for qubit in item.qubits) if level is BenchmarkLevel.MAPPED else None,
            parameters=item.operation.params,
        )
    np.testing.assert_allclose(Operator.from_circuit(result).data, Operator(circuit).data, atol=1e-12)


def test_aqt_target() -> None:
    """IBEX exposes all ordered RXX pairs and virtual RZ gates."""
    target = get_device("aqt_ibex_12")
    assert target.num_qubits == 12
    assert set(target.operation_names) == {"r", "rz", "rxx", "measure"}
    assert len(target["rxx"]) == 12 * 11
    assert all(props.duration == 0 and props.error == 0 for props in target["rz"].values())
    for level, model in [
        (BenchmarkLevel.NATIVEGATES, get_target_for_gateset("aqt", 3)),
        (BenchmarkLevel.MAPPED, target),
    ]:
        circuit = get_benchmark("ghz", level, 3, target=model)
        assert set(circuit.count_ops()) <= set(model.operation_names) | {"barrier"}


def test_nighthawk() -> None:
    """Nighthawk has 218 bidirectional grid edges and a CZ basis."""
    target = get_device("ibm_nighthawk_120")
    assert target.num_qubits == 120
    assert get_gateset("ibm_nighthawk") == get_gateset("ibm_heron")
    edges = set(target["cz"])
    expected = {(q, q + 1) for q in range(120) if q % 10 != 9}
    expected |= {(q, q + 10) for q in range(110)}
    expected |= {(b, a) for a, b in list(expected)}
    assert edges == expected
    circuit = get_benchmark("ghz", BenchmarkLevel.MAPPED, 3, target=target)
    assert circuit.num_qubits == 120
    for item in circuit.data:
        if item.operation.num_qubits == 2:
            assert tuple(circuit.find_bit(q).index for q in item.qubits) in edges
