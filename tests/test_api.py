# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Test the public API for level-specific benchmark retrieval in MQT Bench."""

from __future__ import annotations

import pytest

from mqt.bench.api import (
    get_alg_benchmark,
    get_indep_benchmark,
    get_mapped_benchmark,
    get_native_gates_benchmark,
)
from mqt.bench.benchmark_generation import (
    CompilerSettings,
    QiskitSettings,
    get_benchmark,
)
from mqt.bench.targets.devices import get_device_by_name
from mqt.bench.targets.gatesets import get_target_for_gateset


@pytest.mark.parametrize(("benchmark", "size"), [("qft", 4), ("bv", 6)])
def test_alg_parity(benchmark: str, size: int) -> None:
    """Test parity of algorithm-level benchmarks."""
    qc_wrapper = get_alg_benchmark(benchmark, size)
    qc_ref = get_benchmark(benchmark, "alg", size)
    assert qc_wrapper == qc_ref


@pytest.mark.parametrize(("benchmark", "size"), [("qft", 4)])
def test_indep_parity(benchmark: str, size: int) -> None:
    """Test parity of target-independent benchmarks."""
    qc_wrapper = get_indep_benchmark(benchmark, size)
    qc_ref = get_benchmark(benchmark, "indep", size)
    assert qc_wrapper == qc_ref


@pytest.mark.parametrize(("benchmark", "size", "opt"), [("qft", 4, 1), ("grover", 3, 2)])
def test_native_gate_parity(benchmark: str, size: int, opt: int) -> None:
    """Test parity of native gate-level benchmarks."""
    target = get_target_for_gateset("ionq", num_qubits=size)
    qc_wrapper = get_native_gates_benchmark(
        benchmark,
        circuit_size=size,
        target=target,
        opt_level=opt,
    )
    qc_ref = get_benchmark(
        benchmark,
        "nativegates",
        size,
        compiler_settings=CompilerSettings(QiskitSettings(opt)),
        target=target,
    )
    assert qc_wrapper.num_qubits == qc_ref.num_qubits
    assert qc_wrapper == qc_ref


@pytest.mark.parametrize(("benchmark", "size", "opt"), [("qft", 4, 1)])
def test_mapped_parity(benchmark: str, size: int, opt: int) -> None:
    """Test parity of mapped benchmarks."""
    target = get_device_by_name("ibm_falcon_127")
    qc_wrapper = get_mapped_benchmark(
        benchmark,
        circuit_size=size,
        target=target,
        opt_level=opt,
    )
    qc_ref = get_benchmark(
        benchmark,
        "mapped",
        size,
        compiler_settings=CompilerSettings(QiskitSettings(opt)),
        target=target,
    )
    assert qc_wrapper.num_qubits == qc_ref.num_qubits
    assert qc_wrapper == qc_ref


def test_keyword_only_enforcement() -> None:
    """Supplying a keyword-only argument positionally must raise *TypeError*."""
    with pytest.raises(TypeError):
        # benchmark_instance_name is keyword-only (after the "*" marker)
        get_alg_benchmark("qft", 4, "15_4")  # type: ignore[arg-type]

    bogus_target = get_target_for_gateset("clifford+t", num_qubits=2)
    with pytest.raises(TypeError):
        # target is keyword-only for native-gates wrapper
        get_native_gates_benchmark("qft", 3, bogus_target)  # type: ignore[arg-type]
