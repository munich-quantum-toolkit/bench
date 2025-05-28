# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Test targets."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import pytest
from qiskit.transpiler import Target

from mqt.bench.targets.devices import device_registry, get_available_device_names, get_available_devices, get_device
from mqt.bench.targets.gatesets import (
    gateset_registry,
    get_available_gateset_names,
    get_available_native_gatesets,
    get_gateset,
)

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
        assert err is not None, f"{vendor}: error rate for '{gate_name}' on qubit {qubit} missing"
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
        assert err is not None, f"{vendor}: error rate for '{gate_name}' on ({q0}, {q1}) missing"
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
        assert err is not None, f"{vendor}: error rate for qubit {qubit} missing"
        assert 0 <= err < 1, f"{vendor}: measure error outside [0,1) on qubit {qubit}"


DEVICE_SPECS: Sequence[DeviceSpec] = [
    # ─────────────────────────────────────────────────────────────────── IBM ──
    DeviceSpec(
        name="ibm_falcon_27",
        num_qubits=27,
        single_qubit_gates={"sx", "rz", "x", "measure"},
        two_qubit_gates={"cx"},
    ),
    DeviceSpec(
        name="ibm_falcon_127",
        num_qubits=127,
        single_qubit_gates={"sx", "rz", "x", "measure"},
        two_qubit_gates={"cx"},
    ),
    DeviceSpec(
        name="ibm_eagle_127",
        num_qubits=127,
        single_qubit_gates={"sx", "rz", "x", "measure"},
        two_qubit_gates={"ecr"},
    ),
    DeviceSpec(
        name="ibm_heron_133",
        num_qubits=133,
        single_qubit_gates={"sx", "rz", "x", "measure"},
        two_qubit_gates={"cz"},
    ),
    DeviceSpec(
        name="ibm_heron_156",
        num_qubits=156,
        single_qubit_gates={"sx", "rz", "x", "measure"},
        two_qubit_gates={"cz"},
    ),
    # ────────────────────────────────────────────────────────────────── IonQ ──
    DeviceSpec(
        name="ionq_aria_25",
        num_qubits=25,
        single_qubit_gates={"gpi", "gpi2", "measure"},
        two_qubit_gates={"ms"},
        symmetric_connectivity={"ms": True},
    ),
    DeviceSpec(
        name="ionq_forte_36",
        num_qubits=36,
        single_qubit_gates={"gpi", "gpi2", "measure"},
        two_qubit_gates={"zz"},
        symmetric_connectivity={"zz": True},
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
    ),
    DeviceSpec(
        name="iqm_crystal_54",
        num_qubits=54,
        single_qubit_gates={"r", "measure"},
        two_qubit_gates={"cz"},
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
        name="rigetti_ankaa_84",
        num_qubits=84,
        single_qubit_gates={"rxpi", "rxpi2", "rxpi2dg", "rz", "measure"},
        two_qubit_gates={"iswap"},
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
    available = get_available_device_names()
    pattern = rf"Unknown device '{unknown_name}'. Available devices: {re.escape(str(available))}"

    with pytest.raises(ValueError, match=pattern):
        get_device(unknown_name)


class _DummyTarget(Target):
    """Very small Target subclass for tests."""

    def __init__(self) -> None:
        super().__init__(num_qubits=1)


def test_dynamic_device_registration(monkeypatch: pytest.MonkeyPatch) -> None:
    """A device registered at runtime should immediately be visible through the public helpers."""
    monkeypatch.setattr(device_registry, "_REGISTRY", {}, raising=False)
    get_available_device_names.cache_clear()
    get_available_devices.cache_clear()

    @device_registry.register("dummy_device")
    def _dummy_factory() -> Target:
        return _DummyTarget()

    names = get_available_device_names()
    assert "dummy_device" in names

    dev = get_device("dummy_device")
    assert isinstance(dev, _DummyTarget)

    devs = get_available_devices()
    assert isinstance(devs["dummy_device"], _DummyTarget)


def test_dynamic_gateset_registration(monkeypatch: pytest.MonkeyPatch) -> None:
    """A gateset registered at runtime should immediately be visible through the public helpers."""
    monkeypatch.setattr(gateset_registry, "_REGISTRY", {}, raising=False)
    get_available_gateset_names.cache_clear()
    get_available_native_gatesets.cache_clear()

    @gateset_registry.register("dummy_gateset")
    def _dummy_factory() -> list[str]:
        return ["dummy_gate"]

    names = get_available_gateset_names()
    assert "dummy_gateset" in names

    gateset = get_gateset("dummy_gateset")
    assert gateset == ["dummy_gate"]

    gatesets = get_available_native_gatesets()
    assert gatesets["dummy_gateset"] == gateset


def test_duplicate_device_registration(monkeypatch: pytest.MonkeyPatch) -> None:
    """Registering the same name twice must raise ValueError."""
    monkeypatch.setattr(device_registry, "_REGISTRY", {}, raising=False)

    @device_registry.register("dup_device")
    def _factory1() -> Target:
        return _DummyTarget()

    # second registration with same name should fail
    with pytest.raises(ValueError, match="already registered"):

        @device_registry.register("dup_device")
        def _factory2() -> Target:
            return _DummyTarget()


def test_duplicate_gateset_registration(monkeypatch: pytest.MonkeyPatch) -> None:
    """Registering the same name twice must raise ValueError."""
    monkeypatch.setattr(gateset_registry, "_REGISTRY", {}, raising=False)

    @gateset_registry.register("dup_device")
    def _factory1() -> list[str]:
        return ["dummy_gate"]

    # second registration with same name should fail
    with pytest.raises(ValueError, match="already registered"):

        @gateset_registry.register("dup_device")
        def _factory2() -> list[str]:
            return ["dummy_gate"]
