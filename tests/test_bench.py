# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Tests for the benchmark generation."""

from __future__ import annotations

import datetime as dt
import functools
import io
import json
import random
import re
from enum import StrEnum
from importlib import metadata
from typing import TYPE_CHECKING, NoReturn, cast

import networkx as nx
import numpy as np
import pytest
from qiskit import QuantumCircuit, qasm2, qasm3, qpy
from qiskit.circuit import CircuitInstruction, ClassicalRegister, Clbit, ForLoopOp, IfElseOp, Parameter
from qiskit.circuit.classical import expr
from qiskit.circuit.library import CXGate, GraphStateGate, HGate, QFTGate, RXGate, RZGate, TGate, XGate, YGate, ZGate
from qiskit.compiler import transpile
from qiskit.primitives import StatevectorSampler
from qiskit.providers.basic_provider import BasicSimulator
from qiskit.quantum_info import Operator, Statevector
from qiskit.transpiler import (
    InstructionProperties,
    Layout,
    PassManager,
    Target,  # For layout handling
)
from qiskit.transpiler.exceptions import TranspilerError
from qiskit.transpiler.passes import GatesInBasis, RemoveBarriers, UnrollForLoops

if TYPE_CHECKING:  # pragma: no cover
    from collections import OrderedDict
    from collections.abc import Callable
    from pathlib import Path
    from typing import BinaryIO

    from qiskit.circuit import Gate
    from qiskit.circuit.quantumcircuitdata import QuantumCircuitData

    from mqt.bench.configuration_options import ConfigurationOptions

import mqt.bench
import mqt.bench.configuration_options
from mqt.bench.benchmark_generation import (
    BenchmarkLevel,
    RecursiveOptimizeCliffordT,
    get_benchmark,
    get_benchmark_alg,
    get_benchmark_indep,
    get_benchmark_mapped,
    get_benchmark_native_gates,
)
from mqt.bench.benchmarks import (
    create_circuit,
    get_available_benchmark_names,
    get_benchmark_catalog,
    get_benchmark_description,
    register_benchmark,
    shor,
)
from mqt.bench.output import (
    MQTBenchExporterError,
    OutputFormat,
    __qiskit_version__,
    generate_filename,
    generate_header,
    save_circuit,
    write_circuit,
)
from mqt.bench.targets.devices import get_available_device_names, get_device
from mqt.bench.targets.gatesets import (
    get_available_gateset_names,
    get_target_for_gateset,
)

SPECIAL_QUBIT_COUNTS: dict[str, int] = {
    "shor": 18,
    "hrs_cumulative_multiplier": 5,
    "bmw_quark_copula": 4,
    "cdkm_ripple_carry_adder": 4,
    "draper_qft_adder": 4,
    "full_adder": 4,
    "multiplier": 4,
    "modular_adder": 4,
    "rg_qft_multiplier": 4,
    "vbe_ripple_carry_adder": 4,
    "shors_nine_qubit_code": 17,
    "seven_qubit_steane_code": 13,
    "iqpe": 2,
    "teleportation": 3,
    "simon": 4,
    "bell": 4,
}


@pytest.mark.parametrize("benchmark_name", get_available_benchmark_names())
def test_quantumcircuit_levels(benchmark_name: str) -> None:
    """Test the creation of the algorithm level benchmarks for the benchmarks."""
    input_value = SPECIAL_QUBIT_COUNTS.get(benchmark_name, 3)

    qc = create_circuit(benchmark_name, input_value)
    assert isinstance(qc, QuantumCircuit)
    assert qc.num_qubits == input_value
    assert benchmark_name == qc.name

    res_alg = get_benchmark_alg(qc)
    assert res_alg
    assert res_alg.num_qubits == input_value

    res_indep = get_benchmark_indep(qc)
    assert res_indep
    assert res_indep.num_qubits == input_value

    if benchmark_name != "shor":
        for gateset_name in get_available_gateset_names():
            gateset = get_target_for_gateset(gateset_name, num_qubits=qc.num_qubits)
            res_native_gates = get_benchmark_native_gates(
                qc,
                None,
                gateset,
                0,
            )

            assert res_native_gates
            assert res_native_gates.num_qubits == input_value

        for device_name in get_available_device_names():
            device = get_device(device_name)
            if device.num_qubits < qc.num_qubits:
                # E.g. shors_nine_qubit_code on iqm_crystal_5
                continue
            if "reset" in qc.count_ops() and "reset" not in device.operation_names:
                # This circuit needs reset, which the target does not support.
                continue
            if "if_else" in qc.count_ops() and "if_else" not in device.operation_names:
                with pytest.raises(TranspilerError, match="control-flow construct 'if_else'"):
                    get_benchmark_mapped(qc, None, device, 0)
                continue
            res_mapped = get_benchmark_mapped(
                qc,
                None,
                device,
                0,
            )
            assert res_mapped


def test_qaoa() -> None:
    """Test that the QAOA benchmark includes measurements."""
    qc = create_circuit("qaoa", 3)
    assert qc.count_ops().get("measure", 0) == 3


@pytest.mark.parametrize(
    ("benchmark_name", "input_value", "kind"),
    [
        *[("cdkm_ripple_carry_adder", n, "half") for n in (4, 6, 8, 10)],
        *[("cdkm_ripple_carry_adder", n, "full") for n in (4, 6, 8, 10)],
        *[("cdkm_ripple_carry_adder", n, "fixed") for n in (3, 5, 7, 9)],
        *[("draper_qft_adder", n, "half") for n in (3, 5, 7, 9)],
        *[("draper_qft_adder", n, "fixed") for n in (2, 4, 6, 8)],
        *[("vbe_ripple_carry_adder", n, "half") for n in (3, 6, 9, 12)],
        *[("vbe_ripple_carry_adder", n, "full") for n in (4, 7, 10, 13)],
        *[("vbe_ripple_carry_adder", n, "fixed") for n in (2, 5, 8, 11)],
    ],
)
def test_adder_circuits(benchmark_name: str, input_value: int, kind: str) -> None:
    """Adder benchmarks: circuit qubit count matches the requested size."""
    qc = create_circuit(benchmark_name, input_value, kind)
    assert qc.num_qubits == input_value


@pytest.mark.parametrize(
    ("benchmark_name", "input_value"),
    [
        *[("full_adder", n) for n in (4, 8, 12, 16)],
        *[("modular_adder", n) for n in (2, 4, 6, 8)],
        *[("multiplier", n) for n in (4, 8, 12, 16)],
        *[("rg_qft_multiplier", n) for n in (4, 8, 12, 16)],
        *[("hrs_cumulative_multiplier", n) for n in (5, 9, 13, 17)],
    ],
)
def test_arithmetic_circuits(benchmark_name: str, input_value: int) -> None:
    """Arithmetic benchmarks without ``kind``: circuit qubit count matches the requested size."""
    qc = create_circuit(benchmark_name, input_value)
    assert qc.num_qubits == input_value


@pytest.mark.parametrize(
    ("benchmark", "size", "kind", "result_qubits", "input_qubits", "expected"),
    [
        ("full_adder", 6, None, (3, 4, 5), [0, 1, 2, 3], "101"),  # 3 + 1 + carry-in 1 = 5
        ("half_adder", 5, None, (2, 3, 4), [0, 1, 2], "100"),  # 3 + 1 = 4 (carry-out 1)
        ("modular_adder", 4, None, (2, 3), [0, 1, 2, 3], "10"),  # (3 + 3) mod 4 = 2
        ("cdkm_ripple_carry_adder", 6, "full", (3, 4, 5), [0, 1, 2, 3], "101"),  # 3 + 1 + carry-in 1 = 5
        ("cdkm_ripple_carry_adder", 6, "half", (2, 3, 4), [0, 1, 2], "100"),  # 3 + 1 = 4 (carry-out 1)
        ("cdkm_ripple_carry_adder", 5, "fixed", (2, 3), [0, 1, 2, 3], "10"),  # (3 + 3) mod 4 = 2
        ("vbe_ripple_carry_adder", 7, "full", (3, 4, 5), [0, 1, 2, 3], "101"),  # 3 + 1 + carry-in 1 = 5
        ("vbe_ripple_carry_adder", 6, "half", (2, 3, 4), [0, 1, 2], "100"),  # 3 + 1 = 4 (carry-out 1)
        ("vbe_ripple_carry_adder", 5, "fixed", (2, 3), [0, 2], "10"),  # (1 + 1) mod 4 = 2
        ("draper_qft_adder", 5, "half", (2, 3, 4), [0, 1, 2], "100"),  # 3 + 1 = 4 (carry-out 1)
        ("draper_qft_adder", 4, "fixed", (2, 3), [0, 1, 2, 3], "10"),  # (3 + 3) mod 4 = 2
        ("multiplier", 8, None, (4, 5, 6, 7), [1, 3], "0100"),  # 2 * 2 = 4
        ("rg_qft_multiplier", 8, None, (4, 5, 6, 7), [1, 3], "0100"),  # 2 * 2 = 4
        ("hrs_cumulative_multiplier", 9, None, (4, 5, 6, 7), [1, 3], "0100"),  # 2 * 2 = 4
        ("hrs_cumulative_multiplier", 9, None, (4, 5, 6, 7), [0, 1, 2, 3], "1001"),  # 3 * 3 = 9
    ],
)
@pytest.mark.parametrize("level", list(BenchmarkLevel))
def test_arithmetic_results(
    benchmark: str,
    size: int,
    kind: str | None,
    result_qubits: tuple[int, ...],
    input_qubits: list[int],
    expected: str,
    level: BenchmarkLevel,
) -> None:
    """Measure only result wires and calculate carries, modular sums, and products."""
    arithmetic = create_circuit(benchmark, size) if kind is None else create_circuit(benchmark, size, kind=kind)
    assert [(reg.name, len(reg)) for reg in arithmetic.cregs] == [("result", len(result_qubits))]
    assert [
        (arithmetic.find_bit(item.qubits[0]).index, arithmetic.find_bit(item.clbits[0]).index)
        for item in arithmetic.data
        if item.operation.name == "measure"
    ] == list(zip(result_qubits, range(len(result_qubits)), strict=True))

    qc = arithmetic.copy_empty_like()
    qc.x(input_qubits)
    qc.compose(arithmetic, inplace=True)
    target = get_target_for_gateset("ibm_heron", size)
    compiled = get_benchmark(qc, level, target=target)
    restored = qasm3.loads(qasm3.dumps(compiled))
    counts = StatevectorSampler(seed=10).run([restored], shots=16).result()[0].data["result"].get_counts()
    assert counts == {expected: 16}


def test_qft_multiplier_large_inputs() -> None:
    """The phase stage encodes 2**29 * 2**29 without inaccurate full rotations."""
    circuit = create_circuit("rg_qft_multiplier", 120)
    a, b, result = circuit.qregs
    phases = np.ones(len(result), dtype=complex)
    for instruction in circuit.data:
        if instruction.operation.name == "mcphase" and instruction.qubits[:2] == (a[-1], b[-1]):
            phases[result.index(instruction.qubits[-1])] *= Operator(instruction.operation).data[-1, -1]

    expected = np.ones(len(result), dtype=complex)
    expected[-2:] = [-1, 1j]
    np.testing.assert_allclose(phases, expected, atol=1e-12)


def test_arithmetic_mirror_measurements() -> None:
    """Mirror benchmarks still measure all active qubits to check the identity."""
    qc = get_benchmark("full_adder", BenchmarkLevel.ALG, 6, generate_mirror_circuit=True)
    assert qc.num_clbits == 6
    result = StatevectorSampler(seed=10).run([qc], shots=16).result()[0]
    assert result.data["meas"].get_counts() == {"000000": 16}


def test_mirror_with_unused_classical_registers() -> None:
    """Keep unused registers and measure only active qubits into a new register."""
    circuit = QuantumCircuit(2)
    circuit.add_register(ClassicalRegister(2, "meas"), ClassicalRegister(1, "meas_"))
    circuit.h(1)
    mirror = get_benchmark_alg(circuit, generate_mirror_circuit=True)
    assert mirror.cregs[:-1] == circuit.cregs
    measurements = [item for item in mirror.data if item.operation.name == "measure"]
    assert [(item.qubits, item.clbits) for item in measurements] == [((mirror.qubits[1],), (mirror.cregs[-1][0],))]
    mirror.remove_final_measurements()
    assert Operator(mirror).equiv(Operator(np.eye(4)))


@pytest.mark.parametrize(
    ("benchmark_name", "input_value", "kind", "msg"),
    [
        ("cdkm_ripple_carry_adder", 5, "half", "num_qubits must be an even integer ≥ 4."),
        ("cdkm_ripple_carry_adder", 3, "full", "num_qubits must be an even integer ≥ 4."),
        ("cdkm_ripple_carry_adder", 4, "fixed", "num_qubits must be an odd integer ≥ 3."),
        ("cdkm_ripple_carry_adder", 4, "unknown_adder", "kind must be 'full', 'half', or 'fixed'."),
        ("draper_qft_adder", 4, "half", "num_qubits must be an odd integer ≥ 3."),
        ("draper_qft_adder", 3, "fixed", "num_qubits must be an even integer ≥ 2."),
        ("draper_qft_adder", 3, "unknown_adder", "kind must be 'half' or 'fixed'."),
        ("full_adder", 5, None, "num_qubits must be an even integer ≥ 4."),
        ("half_adder", 4, None, "num_qubits must be an odd integer ≥ 3."),
        (
            "hrs_cumulative_multiplier",
            6,
            None,
            re.escape("num_qubits must be an integer ≥ 5 and (num_qubits - 1) must be divisible by 4."),
        ),
        ("modular_adder", 3, None, "num_qubits must be an even integer ≥ 2"),
        ("multiplier", 3, None, "num_qubits must be an integer ≥ 4 and divisible by 4."),
        ("rg_qft_multiplier", 5, None, "num_qubits must be an integer ≥ 4 and divisible by 4."),
        ("vbe_ripple_carry_adder", 4, "half", "num_qubits must be an integer ≥ 3 and divisible by 3."),
        (
            "vbe_ripple_carry_adder",
            3,
            "full",
            re.escape("num_qubits must be an integer ≥ 4 and (num_qubits - 1) must be divisible by 3."),
        ),
        (
            "vbe_ripple_carry_adder",
            4,
            "fixed",
            re.escape("num_qubits must be an integer ≥ 2 and (num_qubits + 1) must be divisible by 3."),
        ),
        ("vbe_ripple_carry_adder", 3, "unknown_adder", "kind must be 'full', 'half', or 'fixed'."),
        ("hhl", 2, None, "Number of qubits must be at least 3 for HHL."),
        ("grover", 1, None, "num_qubits must be at least 2 for Grover's algorithm."),
        ("qwalk", 1, None, "num_qubits must be at least 2 for quantum walks."),
        ("qpeinexact", 1, None, "num_qubits must be at least 2 for inexact QPE."),
        ("bv", 1, None, "num_qubits must be at least 2 for Bernstein-Vazirani."),
        ("dj", 1, None, "num_qubits must be at least 2 for Deutsch-Jozsa."),
        ("qpeexact", 1, None, "Number of qubits must be at least 2 for QPE exact."),
        ("iqpe", 1, None, "Number of qubits must be at least 2 for IQPE."),
        ("bmw_quark_copula", 3, None, "num_qubits must be a positive multiple of 2."),
        ("ae", 1, None, r"Number of qubits must be at least 2 \(1 evaluation \+ 1 target\)."),
        ("shors_nine_qubit_code", 9, None, "num_qubits must be a positive multiple of 17."),
        ("seven_qubit_steane_code", 9, None, "num_qubits must be a positive multiple of 13."),
        ("teleportation", 1, None, "num_qubits must be a positive multiple of 3."),
        ("superdense_coding", 1, None, "num_qubits must be at least 2."),
        ("simon", 1, None, "num_qubits must be an even integer ≥ 2."),
        ("bell", 1, None, "num_qubits must be a positive multiple of 2."),
    ],
)
def test_wrong_circuit_size(benchmark_name: str, input_value: int, kind: str | None, msg: str) -> None:
    """Test the creation of the arithmetic circuits with faulty input values."""
    if kind:
        with pytest.raises(ValueError, match=msg):
            create_circuit(benchmark_name, input_value, kind=kind)
    else:
        with pytest.raises(ValueError, match=msg):
            create_circuit(benchmark_name, input_value)


@pytest.mark.parametrize("num_qubits", [2, 3, 4])
def test_superdense_coding(num_qubits: int) -> None:
    """Test the creation and correctness of the scalable superdense coding benchmark."""
    sampler = StatevectorSampler()

    # Test with default message (all ones)
    qc_default = create_circuit("superdense_coding", num_qubits)
    assert qc_default.num_qubits == num_qubits
    assert qc_default.num_clbits == num_qubits
    assert "superdense_coding" in qc_default.name

    res_default = sampler.run([qc_default], shots=10).result()
    assert res_default[0].data["c"].get_counts() == {"1" * num_qubits: 10}

    # Test through pipeline
    res_alg = get_benchmark_alg("superdense_coding", num_qubits)
    assert res_alg.num_qubits == num_qubits


@pytest.mark.parametrize("message", ["00", "01", "10", "11"])
def test_superdense_coding_2qubits_all_messages(message: str) -> None:
    """Test 2-qubit canonical superdense coding over all four 2-bit messages."""
    sampler = StatevectorSampler()
    qc = create_circuit("superdense_coding", 2, message=message)
    result = sampler.run([qc], shots=10).result()
    assert result[0].data["c"].get_counts() == {message: 10}


@pytest.mark.parametrize("message", ["000", "001", "010", "011", "100", "101", "110", "111"])
def test_superdense_coding_3qubits_all_messages(message: str) -> None:
    """Test 3-qubit scalable superdense coding over all eight 3-bit messages."""
    sampler = StatevectorSampler()
    qc = create_circuit("superdense_coding", 3, message=message)
    result = sampler.run([qc], shots=10).result()
    assert result[0].data["c"].get_counts() == {message: 10}


def test_superdense_coding_invalid_inputs() -> None:
    """Test invalid message and qubit count inputs."""
    with pytest.raises(ValueError, match="num_qubits must be at least 2"):
        create_circuit("superdense_coding", 1)

    with pytest.raises(ValueError, match="Invalid message"):
        create_circuit("superdense_coding", 2, message="010")

    with pytest.raises(ValueError, match="Invalid message"):
        create_circuit("superdense_coding", 3, message="abc")


@pytest.mark.parametrize(
    ("num_qubits", "message"),
    [
        (2, "01"),
        (2, "10"),
        (3, "010"),
        (3, "101"),
        (4, "0110"),
        (4, "1001"),
    ],
)
def test_superdense_coding_indep_compilation(num_qubits: int, message: str) -> None:
    """Test target-independent compilation retains 2*(n-1) CX gates and preserves output."""
    sampler = StatevectorSampler()
    qc = create_circuit("superdense_coding", num_qubits, message=message)
    qc_indep = get_benchmark_indep(qc)

    ops = qc_indep.count_ops()
    assert ops.get("cx", 0) == 2 * (num_qubits - 1)

    result = sampler.run([qc_indep], shots=10).result()
    assert result[0].data["c"].get_counts() == {message: 10}


@pytest.mark.parametrize(
    ("num_qubits", "hidden_string"),
    [(2, "1"), (4, "01"), (4, "11"), (6, "101"), (6, "010"), (8, "1010"), (8, "0001")],
)
def test_simon_output_distribution(num_qubits: int, hidden_string: str) -> None:
    """Test that the measured distribution is uniform over all y with y.s = 0 (mod 2) and zero elsewhere."""
    n = num_qubits // 2
    qc = create_circuit("simon", num_qubits, hidden_string=hidden_string)
    assert qc.num_qubits == num_qubits
    assert qc.num_clbits == n
    assert qc.name == "simon"

    # probabilities()[k] is the probability of the input register reading k, with qubit q_i as bit i of k.
    assert [
        (qc.find_bit(item.qubits[0]).index, qc.find_bit(item.clbits[0]).index)
        for item in qc
        if item.operation.name == "measure"
    ] == list(zip(range(n), range(n), strict=True))
    qc.remove_final_measurements()
    probabilities = Statevector(qc).probabilities(qargs=list(range(n)))
    expected = np.zeros(2**n)
    for k in range(2**n):
        dot_product = sum(((k >> i) & 1) * int(hidden_string[i]) for i in range(n)) % 2
        if dot_product == 0:
            expected[k] = 1 / 2 ** (n - 1)
    np.testing.assert_allclose(probabilities, expected, atol=1e-9)


@pytest.mark.parametrize(
    ("hidden_string", "msg"),
    [
        ("0", "hidden_string must contain at least one '1'"),
        ("00", "hidden_string must contain at least one '1'"),
        ("1", "Invalid hidden_string"),
        ("101", "Invalid hidden_string"),
        ("1a", "Invalid hidden_string"),
    ],
)
def test_simon_invalid_hidden_string(hidden_string: str, msg: str) -> None:
    """Test that invalid hidden strings are rejected."""
    num_qubits = 2 if hidden_string == "0" else 4
    with pytest.raises(ValueError, match=msg):
        create_circuit("simon", num_qubits, hidden_string=hidden_string)


def test_bv() -> None:
    """Test the creation of the BV benchmark."""
    qc = create_circuit("bv", 3)
    assert qc.depth() > 0
    assert qc.num_qubits == 3
    assert "bv" in qc.name

    qc = create_circuit("bv", 3, dynamic=True)
    assert qc.depth() > 0
    assert qc.num_qubits == 3
    assert "bv" in qc.name

    assert get_benchmark_alg("bv", 2, dynamic=True, generate_mirror_circuit=True).num_qubits == 2

    with pytest.raises(ValueError, match=r"hidden_string must be a binary string of length num_qubits - 1."):
        create_circuit("bv", 3, hidden_string="wrong")


@pytest.mark.parametrize(
    ("benchmark", "size", "kwargs", "message"),
    [
        ("bv", 3, {"hidden_string": "x0"}, "binary string"),
        ("qwalk", 3, {"depth": -1}, "nonnegative"),
        ("graphstate", 3, {"degree": 1}, "must be even"),
        ("bmw_quark_cardinality", 3, {"depth": -1}, "nonnegative"),
        ("bmw_quark_copula", 4, {"depth": -1}, "nonnegative"),
        ("qaoa", 3, {"repetitions": -1}, "nonnegative"),
        ("ae", 3, {"probability": -0.1}, "between 0 and 1"),
        ("ae", 3, {"probability": float("nan")}, "between 0 and 1"),
    ],
)
def test_invalid_benchmark_options(benchmark: str, size: int, kwargs: dict, message: str) -> None:
    """Reject invalid problem parameters before constructing the circuit."""
    with pytest.raises(ValueError, match=message):
        create_circuit(benchmark, size, **kwargs)


@pytest.mark.parametrize(
    ("benchmark_name", "num_qubits", "expected_iterations"),
    [("grover", 4, 2), ("qwalk", 4, 3), ("qwalk", 2, 3)],
)
def test_for_loop_option(benchmark_name: str, num_qubits: int, expected_iterations: int) -> None:
    """Test the optional structured loop implementations."""
    assert "for_loop" not in create_circuit(benchmark_name, num_qubits).count_ops()
    circuit = create_circuit(benchmark_name, num_qubits, for_loop=True)
    assert circuit.count_ops()["for_loop"] == 1
    loop = next(instruction.operation for instruction in circuit.data if isinstance(instruction.operation, ForLoopOp))
    assert loop.params[0] == range(expected_iterations)


@pytest.mark.parametrize("exact", [True, False])
def test_iqpe(exact: bool) -> None:
    """Iterative and ordinary QPE estimate the same phase in the same bit order."""
    qc = create_circuit("iqpe", 4, exact=exact)
    reference = create_circuit("qpeexact" if exact else "qpeinexact", 4)
    reference.remove_final_measurements()
    expected = Statevector(reference).probabilities(qargs=[0, 1, 2])
    counts = np.zeros(8)
    for seed in range(256):
        counts[int(_run_with_control_flow(qc, seed=seed), 2)] += 1
    np.testing.assert_allclose(counts / 256, expected, atol=0.08)
    assert qc.num_qubits == 2


@pytest.mark.parametrize("benchmark", ["qpeexact", "qpeinexact", "iqpe"])
def test_phase_estimation_preserves_random_state(benchmark: str) -> None:
    """Constructing a benchmark must leave the application's random stream alone."""
    before = random.getstate()
    create_circuit(benchmark, 4)
    assert random.getstate() == before


@pytest.mark.parametrize("num_qubits", [3, 5])
@pytest.mark.parametrize("level", [BenchmarkLevel.ALG, BenchmarkLevel.INDEP])
@pytest.mark.parametrize("fmt", [OutputFormat.QASM2, OutputFormat.QASM3])
def test_hhl_solution(num_qubits: int, level: BenchmarkLevel, fmt: OutputFormat) -> None:
    """HHL preserves the successful solution and measurement wiring through QASM export."""
    qc = get_benchmark("hhl", level, num_qubits)
    stream = io.StringIO()
    write_circuit(qc, stream, level, fmt)
    qc = (
        qasm2.loads(stream.getvalue(), custom_instructions=qasm2.LEGACY_CUSTOM_INSTRUCTIONS)
        if fmt is OutputFormat.QASM2
        else qasm3.loads(stream.getvalue())
    )
    assert [
        (qc.find_bit(item.qubits[0]).index, qc.find_bit(item.clbits[0]).index)
        for item in qc
        if item.operation.name == "measure"
    ] == [(0, 0), (num_qubits - 1, 1)]
    qc.remove_final_measurements()
    state = Statevector(qc)
    successful = state.data[2 ** (num_qubits - 1) :]
    assert np.linalg.norm(successful) > 0
    successful = Statevector(successful / np.linalg.norm(successful))
    expected = np.zeros(2 ** (num_qubits - 1))
    expected[:2] = np.linalg.solve([[1, 1], [1, 3]], [0, 1])
    assert successful.equiv(Statevector(expected / np.linalg.norm(expected)))


@pytest.mark.parametrize("width", [1, 2, 3])
def test_fixed_vbe_arithmetic(width: int) -> None:
    """Check every fixed-width sum, relative phase, and helper uncomputation."""
    qc = create_circuit("vbe_ripple_carry_adder", 3 * width - 1, kind="fixed")
    qc.remove_final_measurements()
    rng = np.random.default_rng(10)
    initial = np.zeros(2**qc.num_qubits, dtype=complex)
    initial[: 4**width] = rng.normal(size=4**width) + 1j * rng.normal(size=4**width)
    initial /= np.linalg.norm(initial)
    expected = np.zeros_like(initial)
    mask = (1 << width) - 1
    for value in range(4**width):
        a, b = value & mask, value >> width
        expected[a | (((a + b) & mask) << width)] = initial[value]
    assert Statevector(initial).evolve(qc).equiv(Statevector(expected))


def test_teleportation() -> None:
    """Test the creation of the teleportation benchmark."""
    qc = create_circuit("teleportation", 3)
    assert qc.num_qubits == 3
    assert qc.num_clbits == 3  # 2 mid-circuit bits + 1 final measurement bit
    assert "teleportation" in qc.name
    assert qc.count_ops()["if_else"] == 2

    # Multi-block: 2 corrections and 3 classical bits per block
    qc6 = create_circuit("teleportation", 6)
    assert qc6.num_qubits == 6
    assert qc6.num_clbits == 6
    assert qc6.count_ops()["if_else"] == 4

    # Test through pipeline
    res = get_benchmark_alg("teleportation", 3)
    assert res.num_qubits == 3


def test_teleportation_state_preparation() -> None:
    """The state preparation is applied to the source qubit of every block."""
    prep = QuantumCircuit(1, name="prep")
    prep.h(0)

    qc = get_benchmark_alg("teleportation", 6, state_preparation=prep)
    prep_qubits = [qc.find_bit(inst.qubits[0]).index for inst in qc.data if inst.operation.name == "prep"]
    assert prep_qubits == [0, 3]
    assert "state_preparation" not in qc.metadata["mqt_bench_generation"]["options"]

    with pytest.raises(ValueError, match=r"state_preparation must be a 1-qubit circuit\."):
        create_circuit("teleportation", 3, state_preparation=QuantumCircuit(2))


def test_teleportation_state_preparation_rejects_classical_bits() -> None:
    """State preparation must not contain classical bits."""
    prep = QuantumCircuit(1, 1)

    with pytest.raises(ValueError, match="classical bits"):
        create_circuit("teleportation", 3, state_preparation=prep)


def _run_with_control_flow(qc: QuantumCircuit, *, seed: int) -> str:
    """Sample a circuit with bit, register, and parity conditions.

    Qiskit's statevector sampler does not support control flow. Execute these
    small circuits instruction by instruction to test their classical feedback.
    """
    rng = np.random.default_rng(seed)
    bit_index = {bit: i for i, bit in enumerate(qc.clbits)}
    clbits = [0] * qc.num_clbits
    state = Statevector.from_label("0" * qc.num_qubits)
    state.seed(rng)

    def value(item: Clbit | ClassicalRegister | expr.Expr) -> bool | int:
        if isinstance(item, expr.Value):
            return item.value
        if isinstance(item, expr.Var):
            return value(item.var)
        if isinstance(item, ClassicalRegister):
            return sum(clbits[bit_index[bit]] << i for i, bit in enumerate(item))
        if isinstance(item, expr.Binary):
            left, right = value(item.left), value(item.right)
            if item.op == expr.Binary.Op.EQUAL:
                return left == right
            assert item.op == expr.Binary.Op.BIT_XOR
            return left ^ right
        assert isinstance(item, Clbit)
        return clbits[bit_index[item]]

    def run_block(instructions: QuantumCircuitData, qubit_map: dict, state: Statevector) -> Statevector:
        for instruction in instructions:
            op = instruction.operation
            qubits = [qubit_map[q] for q in instruction.qubits]
            if op.name == "measure":
                outcome, state = state.measure(qubits)
                clbits[bit_index[instruction.clbits[0]]] = int(outcome)
            elif isinstance(op, IfElseOp):
                condition = op.condition
                passed = value(condition[0]) == condition[1] if isinstance(condition, tuple) else value(condition)
                if passed:
                    block = op.blocks[0]
                    inner_map = dict(zip(block.qubits, qubits, strict=True))
                    state = run_block(block.data, inner_map, state)
            else:
                state = state.evolve(op, qubits)
        return state

    state = run_block(qc.data, {q: i for i, q in enumerate(qc.qubits)}, state)
    final_bits = [clbits[bit_index[bit]] for bit in qc.cregs[-1]]
    return "".join(str(bit) for bit in reversed(final_bits))


@pytest.mark.parametrize("num_qubits", [3, 6, 9])
def test_teleportation_correctness(num_qubits: int) -> None:
    """Teleporting |1⟩ must always yield 1 on every destination qubit."""
    prep = QuantumCircuit(1)
    prep.x(0)

    qc = create_circuit("teleportation", num_qubits, state_preparation=prep)
    outcomes = {_run_with_control_flow(qc, seed=seed) for seed in range(20)}
    assert outcomes == {"1" * (num_qubits // 3)}


def _success_rates(qc: QuantumCircuit, shots: int = 500) -> list[float]:
    """Run the circuit on the BasicSimulator and return, for every round k, the fraction of shots with c[k] = 1."""
    backend = BasicSimulator()
    unrolled = PassManager(UnrollForLoops()).run(qc)
    counts = backend.run(transpile(unrolled, backend), shots=shots, seed_simulator=42).result().get_counts()
    return [sum(c for bits, c in counts.items() if bits[-1 - k] == "1") / shots for k in range(qc.num_clbits)]


def _expected_success_rates(num_qubits: int, num_rounds: int, b_max: float) -> list[float]:
    """Return sin^2((2 m_k + 1) theta_a) for the schedule m = 0, 1, 2, 4, ... with a = sin^2(theta_a) from Eq. (23)."""
    num_state_qubits = num_qubits - 1
    a = sum(np.sin((x + 0.5) * b_max / 2**num_state_qubits) ** 2 for x in range(2**num_state_qubits))
    theta_a = np.arcsin(np.sqrt(a / 2**num_state_qubits))
    schedule = [0] + [2**k for k in range(num_rounds)]
    return [float(np.sin((2 * m + 1) * theta_a) ** 2) for m in schedule]


@pytest.mark.parametrize(
    ("num_qubits", "b_max", "for_loop"),
    [(1, np.pi / 4, False), (2, np.pi / 4, True), (3, np.pi / 4, False), (2, 1.0, True)],
)
def test_mlqae_simulated_output(num_qubits: int, b_max: float, for_loop: bool) -> None:
    """Test that simulating the circuit gives round k a success rate of sin^2((2 m_k + 1) theta_a)."""
    num_rounds = 3
    qc = create_circuit("mlqae", num_qubits, num_rounds=num_rounds, b_max=b_max, for_loop=for_loop)

    expected = _expected_success_rates(num_qubits, num_rounds, b_max)

    assert _success_rates(qc) == pytest.approx(expected, abs=0.1)


@pytest.mark.parametrize(("num_qubits", "num_rounds"), [(1, 1), (2, 2), (3, 3), (5, 4)])
def test_mlqae_circuit_structure(num_qubits: int, num_rounds: int) -> None:
    """Verify the structure of the ML-QAE circuit for various qubit and round counts."""
    qc = create_circuit("mlqae", num_qubits, num_rounds)

    assert qc.num_qubits == num_qubits
    assert qc.num_clbits == num_rounds + 1
    assert "mlqae" in qc.name

    measured_clbits = [qc.find_bit(inst.clbits[0]).index for inst in qc.data if inst.operation.name == "measure"]
    assert measured_clbits == list(range(num_rounds + 1))

    reset_qubits = [qc.find_bit(inst.qubits[0]).index for inst in qc.data if inst.operation.name == "reset"]
    for q_idx in range(num_qubits):
        assert reset_qubits.count(q_idx) == num_rounds

    ops: OrderedDict[str, int] = qc.count_ops()
    assert ops.get("measure", 0) == num_rounds + 1
    assert ops.get("reset", 0) == num_rounds * num_qubits


def test_mlqae_for_loop() -> None:
    """Verify the structured for-loop version is constructed."""
    qc = create_circuit("mlqae", 3, num_rounds=3, for_loop=True)

    assert qc.num_qubits == 3
    assert qc.num_clbits == 4
    assert qc.count_ops().get("for_loop", 0) == 3


def test_mlqae_invalid_parameters() -> None:
    """Test the creation of the ML-QAE benchmark with faulty input values."""
    with pytest.raises(ValueError, match=r"num_rounds must be at least 1."):
        create_circuit("mlqae", 3, num_rounds=0)

    with pytest.raises(ValueError, match=r"b_max must be positive and finite."):
        create_circuit("mlqae", 3, b_max=0.0)

    with pytest.raises(ValueError, match=r"b_max must be positive and finite."):
        create_circuit("mlqae", 3, b_max=float("inf"))

    with pytest.raises(ValueError, match=r"b_max must be positive and finite."):
        create_circuit("mlqae", 3, b_max=float("nan"))


def test_teleportation_preserves_phase() -> None:
    """Teleporting |+⟩ must yield 0 when Bob measures in the X basis."""
    prep = QuantumCircuit(1)
    prep.h(0)

    qc = create_circuit("teleportation", 3, state_preparation=prep)
    final_measurement = qc.data.pop()
    qc.h(2)
    qc.append(final_measurement.operation, final_measurement.qubits, final_measurement.clbits)

    outcomes = {_run_with_control_flow(qc, seed=seed) for seed in range(20)}
    assert outcomes == {"0"}


def test_dj_constant_oracle() -> None:
    """The public balanced=False option produces the constant-oracle result."""
    qc = get_benchmark_alg("dj", 5, balanced=False)
    qc.remove_final_measurements()
    assert Statevector(qc).probabilities([0, 1, 2, 3])[0] == pytest.approx(1)


@pytest.mark.parametrize(("num_qubits", "degree", "seed"), [(1, 0, 42), (6, 2, 0), (6, 3, 42)])
def test_graphstate_seeded_operator(num_qubits: int, degree: int, seed: int) -> None:
    """Direct graph-state construction preserves the seeded adjacency-matrix operator."""
    graph = nx.random_regular_graph(degree, num_qubits, seed=seed)
    expected = GraphStateGate(nx.to_numpy_array(graph))
    circuit = get_benchmark_alg("graphstate", num_qubits, degree=degree, seed=seed)

    assert circuit.count_ops().get("cz", 0) == num_qubits * degree // 2
    assert circuit.count_ops()["measure"] == num_qubits
    circuit.remove_final_measurements()
    assert Operator(circuit).equiv(Operator(expected))


@pytest.mark.parametrize("benchmark", ["graphstate", "randomcircuit", "vqe_real_amp"])
def test_benchmark_seed(benchmark: str) -> None:
    """The seed controls both random construction and parameter binding."""
    seeded = get_benchmark_alg(benchmark, 5, seed=42)
    assert seeded == get_benchmark_alg(benchmark, 5, seed=42)
    assert seeded != get_benchmark_alg(benchmark, 5, seed=0)
    assert seeded.metadata["mqt_bench_generation"]["options"]["seed"] == 42
    qc_no_seed = get_benchmark_alg(benchmark, 5)
    assert qc_no_seed.num_qubits == 5
    assert qc_no_seed.name == benchmark


@pytest.mark.parametrize("bound", [False, True])
def test_generation_options_survive_recompilation(bound: bool) -> None:
    """Retain the construction seed and record only parameter binding that occurs."""
    circuit = get_benchmark_alg("qaoa", 4, seed=1, random_parameters=bound)
    target = get_target_for_gateset("ibm_heron", 4)
    compiled = get_benchmark_native_gates(circuit, None, target, seed=2, repetitions=3)
    generation = compiled.metadata["mqt_bench_generation"]
    assert generation["options"] == {"seed": 1}
    assert generation["parameter_seed"] == (1 if bound else 2)
    assert generation["random_parameters"] is True
    expected = circuit.copy()
    expected.remove_final_measurements()
    if not bound:
        expected.assign_parameters(
            np.random.default_rng(2).uniform(0, 2 * np.pi, len(expected.parameters)), inplace=True
        )
    compiled.remove_final_measurements()
    assert Operator(compiled).equiv(Operator(expected))


@pytest.mark.parametrize("num_qubits", [1, 2, 5, 6])
def test_dynamic_ghz(num_qubits: int) -> None:
    """All classical branches preserve the coherent GHZ state."""
    qc = create_circuit("ghz_dynamic", num_qubits)
    qc.remove_final_measurements()
    if num_qubits > 1:
        qc.cx(0, range(1, num_qubits))
    qc.h(0)
    qc.measure_all()
    assert {_run_with_control_flow(qc, seed=seed) for seed in range(16)} == {"0" * num_qubits}


@pytest.mark.parametrize(("num_qubits", "number"), [(1, 1), (3, 3), (4, 5)])
def test_dynamic_qft(num_qubits: int, number: int) -> None:
    """Semiclassical QFT reads Fourier-basis inputs in ordinary QFT bit order."""
    qc = QuantumCircuit(num_qubits)
    qc.x([i for i in range(num_qubits) if number & (1 << i)])
    qc.append(QFTGate(num_qubits).inverse(), range(num_qubits))
    qc.compose(create_circuit("dynamic_qft", num_qubits), inplace=True)
    assert _run_with_control_flow(qc, seed=10) == format(number, f"0{num_qubits}b")


@pytest.mark.parametrize(
    ("benchmark", "width"),
    [
        ("seven_qubit_steane_code", 13),
        ("shors_nine_qubit_code", 17),
    ],
)
@pytest.mark.parametrize(("error", "qubit"), [(XGate(), 0), (ZGate(), 0), (YGate(), -1)])
def test_error_correction(benchmark: str, width: int, error: Gate, qubit: int) -> None:
    """Recover a state with relative phase after bit, phase, and combined errors."""
    code = create_circuit(benchmark, width)
    encoded = next(i for i, item in enumerate(code.data) if item.operation.name == "barrier")
    code.data.insert(encoded, CircuitInstruction(error, [code.qregs[0][qubit]], []))
    qc = code.copy_empty_like()
    qc.h(0)
    qc.s(0)
    qc.compose(code, inplace=True)
    qc.remove_final_measurements()
    qc.sdg(0)
    qc.h(0)
    result = ClassicalRegister(1, "check")
    qc.add_register(result)
    qc.measure(0, result)
    assert _run_with_control_flow(qc, seed=10) == "0"
    multiple = create_circuit(benchmark, 2 * width)
    assert multiple.num_qubits == 2 * width
    assert len({reg.name for reg in multiple.cregs}) == len(multiple.cregs)


@pytest.mark.parametrize(
    (
        "benchmark_name",
        "level",
        "circuit_size",
        "target",
        "opt_level",
    ),
    [
        # Algorithm-level tests
        ("dj", BenchmarkLevel.ALG, 3, None, None),
        ("wstate", BenchmarkLevel.ALG, 3, None, None),
        ("hhl", BenchmarkLevel.ALG, 3, None, None),
        ("shor", BenchmarkLevel.ALG, 18, None, None),
        ("grover", BenchmarkLevel.ALG, 3, None, None),
        ("qwalk", BenchmarkLevel.ALG, 3, None, None),
        # Independent level tests
        ("ghz", BenchmarkLevel.INDEP, 3, None, 2),
        ("graphstate", BenchmarkLevel.INDEP, 3, None, 2),
        # Native gates level tests
        (
            "dj",
            BenchmarkLevel.NATIVEGATES,
            2,
            get_target_for_gateset("ionq_forte", num_qubits=5),
            0,
        ),
        ("qft", BenchmarkLevel.NATIVEGATES, 3, get_target_for_gateset("rigetti", 5), 2),
        # Mapped level tests
        (
            "ghz",
            BenchmarkLevel.MAPPED,
            3,
            get_device("ibm_heron_156"),
            0,
        ),
        ("ghz", BenchmarkLevel.MAPPED, 3, get_device("ibm_heron_156"), 2),
        (
            "ghz",
            BenchmarkLevel.MAPPED,
            3,
            get_device("ionq_forte_36"),
            0,
        ),
    ],
)
def test_get_benchmark(
    benchmark_name: str,
    level: BenchmarkLevel,
    circuit_size: int | None,
    target: Target | None,
    opt_level: int | None,
) -> None:
    """Test the creation of the benchmarks using the get_benchmark method."""
    qc = get_benchmark(
        benchmark=benchmark_name,
        level=level,
        circuit_size=circuit_size,
        target=target,
        opt_level=opt_level if opt_level is not None else 2,
    )
    assert qc.depth() > 0
    generation = qc.metadata["mqt_bench_generation"]
    assert generation["benchmark"] == benchmark_name
    assert generation["circuit_size"] == circuit_size
    assert generation["level"] == level.name.lower()
    assert generation["target"] == (target.description if target is not None else None)
    if target:
        assert isinstance(qc, QuantumCircuit)
        for qc_instruction in qc.data:
            instruction = qc_instruction.operation
            gate_type = instruction.name
            assert gate_type in target.operation_names or gate_type == "barrier"


def test_get_benchmark_alg_with_quantum_circuit() -> None:
    """Test get_benchmark method with QuantumCircuit as input for algorithm level benchmarks."""
    qc = create_circuit("ae", 3)
    assert qc.name == "ae"
    qc_bench = get_benchmark(qc, BenchmarkLevel.ALG)

    assert qc == qc_bench
    assert not qc.metadata


def test_get_benchmark_faulty_parameters() -> None:
    """Test the get_benchmark method with faulty parameters."""
    match = re.escape(
        f"'wrong_name' is not a supported benchmark. Available benchmarks: {get_available_benchmark_names()}"
    )
    with pytest.raises(ValueError, match=match):
        get_benchmark("wrong_name", BenchmarkLevel.INDEP, 6)
    match = "`circuit_size` cannot be None when `benchmark` is a str."
    with pytest.raises(ValueError, match=match):
        get_benchmark(
            "dj",
            BenchmarkLevel.INDEP,
            None,
            get_device("rigetti_cepheus_108"),
            1,
        )
    match = "`circuit_size` must be a positive integer when `benchmark` is a str."
    with pytest.raises(ValueError, match=match):
        get_benchmark(
            "dj",
            BenchmarkLevel.INDEP,
            -1,
            get_device("rigetti_cepheus_108"),
            1,
        )
    match = "No Shor instance for circuit_size=3. Available: 18, 42, 58, 74."
    with pytest.raises(ValueError, match=match):
        get_benchmark(
            "shor",
            BenchmarkLevel.INDEP,
            3,
            get_device("rigetti_cepheus_108"),
            1,
        )
    match = re.escape("Invalid `opt_level` '4'. Must be in the range [0, 3].")
    with pytest.raises(ValueError, match=match):
        get_benchmark(
            "qpeexact",
            BenchmarkLevel.INDEP,
            3,
            get_device("rigetti_cepheus_108"),
            4,
        )
    match = re.escape(
        "'wrong_gateset' is not a supported gateset. Known modules: ['aqt', 'clifford_t', 'ibm', 'ionq', 'iqm', 'quantinuum', 'rigetti']"
    )
    with pytest.raises(ValueError, match=match):
        get_benchmark(
            "qpeexact",
            BenchmarkLevel.NATIVEGATES,
            3,
            get_target_for_gateset("wrong_gateset", 3),
            1,
        )
    match = re.escape(
        "'wrong_device' is not a supported device. Known modules: ['aqt', 'ibm', 'ionq', 'iqm', 'quantinuum', 'rigetti']"
    )
    with pytest.raises(ValueError, match=match):
        get_benchmark(
            "qpeexact",
            BenchmarkLevel.MAPPED,
            3,
            get_device("wrong_device"),
            1,
        )

    match = "Target must be provided for 'nativegates' level."
    with pytest.raises(ValueError, match=match):
        get_benchmark(benchmark="ghz", level=BenchmarkLevel.NATIVEGATES, circuit_size=3, target=None, opt_level=0)

    match = "Target must be provided for 'mapped' level."
    with pytest.raises(ValueError, match=match):
        get_benchmark(benchmark="ghz", level=BenchmarkLevel.MAPPED, circuit_size=3, target=None, opt_level=0)


@pytest.mark.parametrize(
    "getter",
    [
        get_benchmark_alg,
        get_benchmark_indep,
        functools.partial(get_benchmark_native_gates, target=get_target_for_gateset("ionq_forte", 3)),
        functools.partial(get_benchmark_mapped, target=get_device("ionq_forte_36")),
        functools.partial(get_benchmark, level=BenchmarkLevel.ALG),
        functools.partial(get_benchmark, level=BenchmarkLevel.INDEP),
        functools.partial(
            get_benchmark, level=BenchmarkLevel.NATIVEGATES, target=get_target_for_gateset("ionq_forte", 3)
        ),
        functools.partial(get_benchmark, level=BenchmarkLevel.MAPPED, target=get_device("ionq_forte_36")),
    ],
)
def test_invalid_circuit_size_combinations(getter: Callable[..., QuantumCircuit]) -> None:
    """All get_benchmark_* helpers must reject the two illegal argument combos."""
    qc = create_circuit("ae", 3)

    # QuantumCircuit plus a circuit_size
    with pytest.raises(
        ValueError,
        match=r"`circuit_size` must be omitted or None when `benchmark` is a QuantumCircuit",
    ):
        getter(qc, circuit_size=1)

    # str with a bad/absent circuit_size
    with pytest.raises(
        ValueError,
        match=r"`circuit_size` must be a positive integer when `benchmark` is a str",
    ):
        getter("ae", circuit_size=-1)

    with pytest.raises(
        ValueError,
        match=r"`circuit_size` cannot be None when `benchmark` is a str",
    ):
        getter("ae", circuit_size=None)


@pytest.mark.parametrize("opt_level", [0, 1, 2, 3])
def test_clifford_t(opt_level: int) -> None:
    """Renaming a Clifford+T target must preserve its synthesis pipeline."""
    target = get_target_for_gateset("clifford+t", 4)
    target.description = "User-defined Clifford+T target"
    qc = get_benchmark(
        benchmark="qft",
        level=BenchmarkLevel.NATIVEGATES,
        circuit_size=4,
        target=target,
        opt_level=opt_level,
    )

    clifford_t_target = get_target_for_gateset("clifford+t", num_qubits=4)
    pm = PassManager(GatesInBasis(target=clifford_t_target))
    pm.run(qc)
    assert pm.property_set["all_gates_in_basis"]


@pytest.mark.parametrize("opt_level", [0, 1, 2, 3])
@pytest.mark.parametrize("mirror", [False, True])
def test_clifford_t_rotations(opt_level: int, mirror: bool) -> None:
    """Approximate rotations about every axis while retaining the Clifford+T basis."""
    qc = QuantumCircuit(2)
    qc.rx(0.3, 0)
    qc.ry(-0.7, 1)
    qc.cx(0, 1)
    qc.rz(0.2, 1)
    qc.rzz(0.3, 0, 1)
    qc.swap(0, 1)
    target = get_target_for_gateset("clifford+t", 2)

    compiled = get_benchmark_native_gates(qc, None, target, opt_level, generate_mirror_circuit=mirror)

    pm = PassManager(GatesInBasis(target=target))
    pm.run(compiled)
    assert pm.property_set["all_gates_in_basis"]
    compiled.remove_final_measurements()
    expected = Operator(np.eye(4)) if mirror else Operator(qc)
    assert Operator.from_circuit(compiled).equiv(expected, atol=1e-8 if mirror else 1e-4)


@pytest.mark.parametrize("opt_level", [0, 1, 2, 3])
@pytest.mark.parametrize("gate_name", ["iswap", "dcx"])
def test_clifford_t_mirror_inverse_gates(opt_level: int, gate_name: str) -> None:
    """Lower inverses of native Clifford gates back to the target basis."""
    circuit = QuantumCircuit(2)
    getattr(circuit, gate_name)(0, 1)
    target = get_target_for_gateset("clifford+t", 2)

    compiled = get_benchmark_native_gates(circuit, None, target, opt_level, generate_mirror_circuit=True)

    pm = PassManager(GatesInBasis(target=target))
    pm.run(compiled)
    assert pm.property_set["all_gates_in_basis"]
    compiled.remove_final_measurements()
    assert Operator(compiled).equiv(Operator(np.eye(4)))


@pytest.mark.parametrize("opt_level", [0, 1, 2, 3])
def test_clifford_t_rotations_in_loop(opt_level: int) -> None:
    """Synthesize rotations inside structured loops without unrolling the loop."""
    qc = QuantumCircuit(1)
    with qc.for_loop(range(2)):
        qc.rx(0.3, 0)
    target = get_target_for_gateset("clifford+t", 1)

    compiled = get_benchmark_native_gates(qc, None, target, opt_level)

    assert any(isinstance(inst.operation, ForLoopOp) for inst in compiled.data)
    pm = PassManager(GatesInBasis(target=target))
    pm.run(compiled)
    assert pm.property_set["all_gates_in_basis"]
    expected = QuantumCircuit(1)
    expected.rx(0.6, 0)
    assert Operator.from_circuit(UnrollForLoops()(compiled)).equiv(Operator(expected), atol=1e-4)


@pytest.mark.parametrize("loop_depth", [0, 1, 2])
@pytest.mark.parametrize(("gates", "t_count"), [("t t", 0), ("s h t t t", 1)])
def test_clifford_t_post_synthesis_optimization(loop_depth: int, gates: str, t_count: int) -> None:
    """Reduce T counts without changing the unitary, including inside nested loops."""
    circuit = QuantumCircuit(1)
    for gate in gates.split():
        getattr(circuit, gate)(0)
    for _ in range(loop_depth):
        body = circuit
        circuit = QuantumCircuit(1)
        circuit.append(ForLoopOp(range(2), None, body), circuit.qubits)
    original = circuit.copy()
    optimized = RecursiveOptimizeCliffordT(basis_gates=["h", "t", "tdg", "s", "sdg", "x", "y", "z"])(circuit)

    assert circuit == original
    counts = optimized.to_dag().count_ops(recurse=True)
    assert counts.get("t", 0) + counts.get("tdg", 0) == t_count
    np.testing.assert_allclose(
        Operator(UnrollForLoops()(optimized)).data, Operator(UnrollForLoops()(original)).data, atol=1e-12
    )


@pytest.mark.parametrize("mirror", [False, True])
def test_clifford_t_optimization_preserves_target_basis(mirror: bool) -> None:
    """Translate optimized loops and mirrors back to a basis without S or Sdg."""
    circuit = QuantumCircuit(1)
    circuit.t(0)
    circuit.t(0)
    if not mirror:
        body = circuit
        circuit = QuantumCircuit(1)
        circuit.append(ForLoopOp(range(2), None, body), circuit.qubits)
    native_target = get_target_for_gateset("clifford+t", 1)
    target = Target(description="clifford+t", num_qubits=1)
    for name in ("h", "t", "for_loop", "measure"):
        target.add_instruction(native_target.operation_from_name(name), name=name)

    optimized = get_benchmark_native_gates(circuit, None, target, 2, generate_mirror_circuit=mirror)

    pm = PassManager(GatesInBasis(target=target))
    pm.run(optimized)
    assert pm.property_set["all_gates_in_basis"]
    if not mirror:
        assert isinstance(optimized.data[0].operation, ForLoopOp)
    optimized.remove_final_measurements()
    expected = Operator(np.eye(2)) if mirror else Operator(UnrollForLoops()(circuit))
    assert Operator(UnrollForLoops()(optimized)).equiv(expected)


@pytest.mark.parametrize("opt_level", [0, 1, 2, 3])
@pytest.mark.parametrize("measurement_case", ["none", "final", "repeated"])
def test_clifford_t_preserves_measurements(opt_level: int, measurement_case: str) -> None:
    """Preserve classical registers and measurement destinations during synthesis."""
    qc = QuantumCircuit(2)
    qc.x(1)
    if measurement_case != "none":
        qc.add_register(ClassicalRegister(1, "first"), ClassicalRegister(2, "last"))
        if measurement_case == "repeated":
            qc.measure(1, 0)
            qc.reset(1)
            qc.x(1)
            qc.measure(1, 2)
        else:
            qc.measure([0, 1], [2, 0])

    compiled = get_benchmark_native_gates(qc, None, get_target_for_gateset("clifford+t", 2), opt_level)

    assert compiled.layout is None
    assert compiled.cregs == qc.cregs
    assert compiled.clbits == qc.clbits
    assert sorted(
        compiled.find_bit(inst.clbits[0]).index for inst in compiled.data if inst.operation.name == "measure"
    ) == ([] if measurement_case == "none" else [0, 2])
    if measurement_case == "none":
        assert Operator(compiled).equiv(Operator(qc))
    else:
        expected_result = "10 1" if measurement_case == "repeated" else "00 1"
        assert BasicSimulator().run(compiled, shots=16).result().get_counts() == {expected_result: 16}


@pytest.mark.parametrize(
    ("level", "gateset", "opt_level"),
    [
        *[(BenchmarkLevel.NATIVEGATES, "clifford+t", opt) for opt in range(4)],
        (BenchmarkLevel.NATIVEGATES, "ibm_heron", 2),
        (BenchmarkLevel.INDEP, None, 2),
    ],
)
@pytest.mark.parametrize("mirror", [False, True])
@pytest.mark.parametrize("fmt", [OutputFormat.QASM2, OutputFormat.QASM3])
def test_unmapped_compilation_preserves_permutations(
    level: BenchmarkLevel, gateset: str | None, opt_level: int, mirror: bool, fmt: OutputFormat
) -> None:
    """Preserve logical SWAPs through compilation, mirrors, and QASM export."""
    qc = QuantumCircuit(4)
    qc.h(0)
    qc.t(1)
    qc.cx(1, 2)
    qc.swap(0, 1)
    qc.swap(1, 2)
    target = get_target_for_gateset(gateset, 4) if gateset is not None else None

    compiled = get_benchmark(qc, level, target=target, opt_level=opt_level, generate_mirror_circuit=mirror)

    expected = Operator(np.eye(16)) if mirror else Operator(qc)
    if mirror:
        assert {
            compiled.find_bit(inst.qubits[0]).index for inst in compiled.data if inst.operation.name == "measure"
        } == {0, 1, 2}
    compiled.remove_final_measurements()
    assert Operator.from_circuit(compiled).equiv(expected)
    assert Operator(compiled).equiv(expected)

    stream = io.StringIO()
    write_circuit(compiled, stream, level, fmt, target)
    restored = (
        qasm2.loads(stream.getvalue(), custom_instructions=qasm2.LEGACY_CUSTOM_INSTRUCTIONS)
        if fmt is OutputFormat.QASM2
        else qasm3.loads(stream.getvalue())
    )
    assert Operator(restored).equiv(expected)


def test_benchmark_helper_shor() -> None:
    """Testing the Shor benchmarks."""
    shor_instances = ["xsmall", "small", "medium", "large", "xlarge"]
    for elem in shor_instances:
        res_shor = shor.get_instance(elem)
        assert res_shor


def test_validate_input() -> None:
    """Test the _validate_input() method for various edge cases."""
    # Case 1: to_be_factored_number (N) < 3.
    with pytest.raises(ValueError, match=r"The input needs to be an odd integer greater than 3, was 2"):
        shor.create_circuit_from_num_and_coprime(2, 2)

    # Case 2: a < 2.
    with pytest.raises(ValueError, match=r"a must have value >= 2, was 1"):
        shor.create_circuit_from_num_and_coprime(15, 1)

    # Case 3: N is even (and thus not odd).
    with pytest.raises(ValueError, match=r"The input needs to be an odd integer greater than 3, was 4."):
        shor.create_circuit_from_num_and_coprime(4, 3)

    # Case 4: a >= N.
    with pytest.raises(
        ValueError, match=r"The integer a needs to satisfy a < N and gcd\(a, N\) = 1, was a = 15 and N = 15."
    ):
        shor.create_circuit_from_num_and_coprime(15, 15)

    # Case 5: gcd(a, N) != 1 (for example, N=15 and a=6, since gcd(15,6)=3).
    with pytest.raises(
        ValueError, match=r"The integer a needs to satisfy a < N and gcd\(a, N\) = 1, was a = 6 and N = 15."
    ):
        shor.create_circuit_from_num_and_coprime(15, 6)

    # Case 6: Valid input (should not raise any exception).
    try:
        shor.create_circuit_from_num_and_coprime(15, 2)
    except ValueError as e:
        pytest.fail(f"Unexpected ValueError raised for valid input: {e}")


@pytest.mark.parametrize(
    ("level", "target", "generate_mirror_circuit", "expected"),
    [
        (BenchmarkLevel.ALG, None, False, "ghz_alg_5"),
        (BenchmarkLevel.ALG, None, True, "ghz_alg_mirror_5"),
        (BenchmarkLevel.INDEP, None, False, "ghz_indep_opt2_5"),
        (BenchmarkLevel.INDEP, None, True, "ghz_indep_mirror_opt2_5"),
        *[
            (BenchmarkLevel.NATIVEGATES, Target(num_qubits=5, description=description), False, expected)
            for description, expected in [
                (None, "ghz_nativegates_custom_target_opt2_5"),
                ("   ", "ghz_nativegates_custom_target_opt2_5"),
                (r"Custom/native\target", "ghz_nativegates_Custom_native_target_opt2_5"),
                ("clifford+t", "ghz_nativegates_clifford+t_opt2_5"),
            ]
        ],
        (
            BenchmarkLevel.NATIVEGATES,
            get_target_for_gateset("ibm_heron", 5),
            False,
            "ghz_nativegates_ibm_heron_opt2_5",
        ),
        (
            BenchmarkLevel.NATIVEGATES,
            get_target_for_gateset("ibm_heron", 5),
            True,
            "ghz_nativegates_mirror_ibm_heron_opt2_5",
        ),
        (
            BenchmarkLevel.MAPPED,
            get_device("ibm_heron_156"),
            False,
            "ghz_mapped_ibm_heron_156_opt2_5",
        ),
        (
            BenchmarkLevel.MAPPED,
            get_device("ibm_heron_156"),
            True,
            "ghz_mapped_mirror_ibm_heron_156_opt2_5",
        ),
    ],
)
def test_generate_filename(
    level: BenchmarkLevel,
    target: Target | None,
    generate_mirror_circuit: bool,
    expected: str,
) -> None:
    """Test the generation of a filename."""
    filename = generate_filename(
        benchmark_name="ghz",
        level=level,
        num_qubits=5,
        target=target,
        opt_level=2,
        generate_mirror_circuit=generate_mirror_circuit,
    )
    assert filename == expected


def test_generate_header_minimal(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test the generation of a minimal header."""
    monkeypatch.setattr(metadata, "version", lambda _: "9.9.9")
    hdr = generate_header(OutputFormat.QASM3, BenchmarkLevel.INDEP)
    lines = hdr.splitlines()
    # first line has today's date
    assert lines[0] == f"// Benchmark created by MQT Bench on {dt.datetime.now(tz=dt.UTC).date()}"
    assert "// SPDX-License-Identifier: MIT" in lines
    # contains the fixed info lines
    assert "// For more info: https://mqt-bench.app/" in hdr
    assert "// MQT Bench version: 9.9.9" in hdr
    assert f"// Qiskit version: {__qiskit_version__}" in hdr
    assert f"// Output format: {OutputFormat.QASM3.value}" in hdr
    assert "// Level: indep" in hdr
    # no gateset or mapping lines when omitted
    assert "// Used gateset:" not in hdr
    assert "// Coupling map:" not in hdr


def test_generate_header_with_options(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test the generation of a header with options."""
    monkeypatch.setattr(metadata, "version", lambda _: "0.1.0")
    gates = ["h", "x", "cx"]
    cmap = [[0, 1], [1, 2]]
    target = Target(num_qubits=3)

    # === Single-qubit gates ===
    # Define all-qubit props (or use None if not needed)
    x_props = {(q,): None for q in range(3)}
    h_props = {(q,): None for q in range(3)}

    target.add_instruction(HGate(), h_props)
    target.add_instruction(XGate(), x_props)

    # === Two-qubit CX gate on limited connectivity
    cx_props = {
        (0, 1): InstructionProperties(),
        (1, 2): InstructionProperties(),
    }
    target.add_instruction(CXGate(), cx_props)
    hdr = generate_header(OutputFormat.QASM2, level=BenchmarkLevel.MAPPED, target=target)

    assert f"// Used gateset: {gates}" in hdr
    assert f"// Coupling map: {cmap}" in hdr


def test_generate_header_pkg_not_installed(monkeypatch: pytest.MonkeyPatch) -> None:
    """metadata.version raises PackageNotFoundError."""
    monkeypatch.setattr(
        metadata,
        "version",
        lambda _pkg: (_ for _ in ()).throw(MQTBenchExporterError("boom")),
    )
    with pytest.raises(MQTBenchExporterError) as exc:
        generate_header(OutputFormat.QASM2, BenchmarkLevel.INDEP)

    msg = str(exc.value)
    assert "not installed" in msg.lower()
    assert "mqt.bench" in msg


@pytest.mark.parametrize("fmt", [OutputFormat.QASM2, OutputFormat.QASM3])
def test_write_circuit_qasm(tmp_path: Path, fmt: OutputFormat) -> None:
    """Export multiline target descriptions and preserve existing file permissions."""
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    target = get_target_for_gateset("clifford+t+rotations", 2)
    target.description = "Custom target\nCalibration from Monday\r\nRevision 2"

    out = tmp_path / "test.qasm"
    out.write_text("previous circuit")
    out.chmod(0o640)
    mode = out.stat().st_mode
    write_circuit(qc, out, BenchmarkLevel.NATIVEGATES, fmt=fmt, target=target)
    assert out.stat().st_mode == mode

    text = out.read_text().splitlines()
    # header lines at top
    assert text[0].startswith("// Benchmark created by MQT Bench on")
    assert "// SPDX-License-Identifier: MIT" in text
    # QASM body present
    assert any(line.startswith("h ") for line in text), "H gate should appear"
    assert any(line.startswith("cx ") for line in text), "CX gate should appear"
    restored = (qasm2 if fmt is OutputFormat.QASM2 else qasm3).loads(out.read_text())
    assert Operator(restored).equiv(Operator(qc))


def test_write_circuit_qpy(tmp_path: Path) -> None:
    """Test writing a QPY circuit with header embedded in metadata."""
    qc = get_benchmark_indep("graphstate", 4, seed=42)
    out = tmp_path / "test.qpy"
    write_circuit(qc, out, BenchmarkLevel.INDEP, fmt=OutputFormat.QPY)

    data = out.read_bytes()
    assert data.startswith(b"QISKIT"), "QPY file must start with the QISKIT magic"

    with out.open("rb") as fd:
        loaded = list(qpy.load(fd))
    assert len(loaded) == 1
    circ = loaded[0]
    assert isinstance(circ, QuantumCircuit)

    header = circ.metadata["mqt_bench"]
    assert header.startswith(f"// Benchmark created by MQT Bench on {dt.datetime.now(tz=dt.UTC).date()}")
    assert "// MQT Bench version:" in header
    assert "// SPDX-License-Identifier: MIT" in header.splitlines()
    assert "// Output format: qpy" in header
    generation = circ.metadata["mqt_bench_generation"]
    assert generation == qc.metadata["mqt_bench_generation"]
    assert generation["options"] == {"seed": 42}
    assert generation["opt_level"] == 2
    assert json.loads(header.split("// Generation options: ")[1].splitlines()[0]) == generation


@pytest.mark.parametrize("fmt", [OutputFormat.QASM2, OutputFormat.QPY])
def test_write_circuit_io_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fmt: OutputFormat) -> None:
    """A failed export leaves the previous file intact and removes temporary files."""
    qc = QuantumCircuit(1)
    qc.h(0)

    out = tmp_path / f"existing.{fmt.extension()}"
    out.write_text("previous circuit")

    def fail_after_writing(_qc: QuantumCircuit, stream: io.TextIOBase | BinaryIO) -> NoReturn:
        if isinstance(stream, io.TextIOBase):
            stream.write("partial circuit")
        else:
            stream.write(b"partial circuit")
        msg = "disk full"
        raise OSError(msg)

    monkeypatch.setattr(
        "mqt.bench.output.dump2" if fmt is OutputFormat.QASM2 else "mqt.bench.output.dump_qpy", fail_after_writing
    )

    with pytest.raises(MQTBenchExporterError) as exc:
        write_circuit(qc, out, BenchmarkLevel.INDEP, fmt=fmt)

    msg = str(exc.value)
    assert f"failed to write {fmt.value} file" in msg.lower()
    assert "disk full" in msg.lower()

    assert out.read_text() == "previous circuit"
    assert list(tmp_path.iterdir()) == [out]


def test_write_circuit_unsupported_format(tmp_path: Path) -> None:
    """Requesting an unsupported format should raise."""

    class FakeFormat(StrEnum):
        FAKE = "fake"

    qc = QuantumCircuit(1)

    with pytest.raises(MQTBenchExporterError) as exc:
        write_circuit(qc, tmp_path / "foo.fake", BenchmarkLevel.INDEP, fmt=FakeFormat.FAKE)  # ty: ignore[no-matching-overload]

    msg = str(exc.value)
    assert "unsupported output format" in msg.lower()
    assert "fake" in msg.lower()


def test_save_circuit_success(tmp_path: Path) -> None:
    """Happy-path save."""
    qc = QuantumCircuit(1)
    qc.h(0)

    assert save_circuit(qc, "foo", BenchmarkLevel.INDEP, OutputFormat.QASM2, target_directory=str(tmp_path))
    assert (tmp_path / "foo.qasm").exists()

    assert save_circuit(qc, "bar", BenchmarkLevel.INDEP, OutputFormat.QPY, target_directory=str(tmp_path))
    assert (tmp_path / "bar.qpy").exists()


def test_save_circuit_write_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """save_circuit returns False when write_circuit fails."""
    qc = QuantumCircuit(1)
    qc.h(0)

    monkeypatch.setattr(
        "mqt.bench.output.write_circuit",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(MQTBenchExporterError("boom")),
    )

    ok = save_circuit(qc, "baz", BenchmarkLevel.INDEP, OutputFormat.QASM3, target_directory=str(tmp_path))
    assert ok is False
    captured = capsys.readouterr()
    assert not captured.out
    assert "boom" in captured.err


@pytest.mark.parametrize("fmt", [OutputFormat.QASM2, OutputFormat.QASM3])
def test_write_circuit_qasm_to_text_stream(fmt: OutputFormat) -> None:
    """Test writing a QASM circuit to a text stream."""
    qc = QuantumCircuit(2)
    qc.cx(0, 1)

    buf = io.StringIO()
    write_circuit(qc, buf, BenchmarkLevel.INDEP, fmt=fmt)

    text = buf.getvalue().splitlines()
    assert text[0].startswith("// Benchmark created by MQT Bench on")
    assert any("cx" in line for line in text)


def test_write_circuit_qpy_to_binary_stream() -> None:
    """Test writing a QPY circuit to a binary stream."""
    qc = QuantumCircuit(1)
    qc.x(0)

    buf = io.BytesIO()
    write_circuit(qc, buf, BenchmarkLevel.INDEP, fmt=OutputFormat.QPY)

    buf.seek(0)
    magic = buf.read(6)
    assert magic == b"QISKIT"


def test_stream_mode_mismatch_raises() -> None:
    """Test that stream mode mismatch raises an error."""
    qc = QuantumCircuit(1)

    # Binary stream + QASM → error
    with pytest.raises(MQTBenchExporterError):
        write_circuit(qc, io.BytesIO(), BenchmarkLevel.INDEP, fmt=OutputFormat.QASM3)

    # Text stream + QPY → error
    with pytest.raises(MQTBenchExporterError):
        write_circuit(qc, io.StringIO(), BenchmarkLevel.INDEP, fmt=OutputFormat.QPY)


def test_custom_target() -> None:
    """Test the compilation with an external target that is not part of the pre-defined ones."""
    target = Target(num_qubits=3, description="custom_target")
    alpha = Parameter("alpha")
    beta = Parameter("beta")

    single_qubit_props = InstructionProperties(duration=1e-3, error=1e-4)
    properties = {
        (0,): single_qubit_props,
        (1,): single_qubit_props,
        (2,): single_qubit_props,
    }
    target.add_instruction(RXGate(alpha), properties=properties)
    target.add_instruction(RZGate(beta), properties=properties)

    two_qubit_props = InstructionProperties(duration=1e-2, error=1e-3)
    cx_props = {
        (0, 1): two_qubit_props,
        (1, 2): two_qubit_props,
    }
    target.add_instruction(CXGate(), properties=cx_props)

    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)

    for opt_level in [0, 1, 2, 3]:
        qc_native_gates = get_benchmark_native_gates(qc, None, target, opt_level)
        assert qc_native_gates.depth() > 0
        assert qc_native_gates.layout is None

    qc_mapped = get_benchmark_mapped(qc, None, target, 0)
    assert qc_mapped.depth() > 0
    assert qc_mapped.layout is not None


@pytest.mark.parametrize("opt_level", [0, 1, 2, 3])
@pytest.mark.parametrize("mirror", [False, True])
@pytest.mark.parametrize("description", ["custom_target", "clifford+t"])
@pytest.mark.parametrize("num_qubits", [2, 5])
def test_native_gates_ignore_hardware(opt_level: int, mirror: bool, description: str, num_qubits: int) -> None:
    """Ignore device capacity and gate placement during native compilation."""
    target = Target(num_qubits=num_qubits, description=description)
    target.add_instruction(HGate(), {(0,): None})
    target.add_instruction(TGate(), {(0,): None})
    target.add_instruction(XGate(), {(q,): None for q in range(num_qubits)})
    target.add_instruction(CXGate(), {(0, 1): None})

    qc = QuantumCircuit(3)
    qc.h(2)
    qc.cx(2, 0)
    qc.x(1)
    compiled = get_benchmark_native_gates(qc, None, target, opt_level, generate_mirror_circuit=mirror)

    assert compiled.num_qubits == qc.num_qubits
    assert compiled.layout is None
    expected = Operator(np.eye(8)) if mirror else Operator(qc)
    compiled.remove_final_measurements()
    assert Operator(compiled).equiv(expected)
    assert target.num_qubits == num_qubits
    assert set(target["cx"]) == {(0, 1)}


@pytest.mark.parametrize("gateset_name", ["clifford+t", "ibm_heron"])
@pytest.mark.parametrize("jump", ["break_loop", "continue_loop"])
@pytest.mark.parametrize("opt_level", [0, 1, 2, 3])
@pytest.mark.parametrize("conditional", [False, True])
def test_native_gates_preserve_loop_jumps(gateset_name: str, jump: str, opt_level: int, conditional: bool) -> None:
    """Compile loop exits using Qiskit's instruction names."""
    qc = QuantumCircuit(2, 1)
    with qc.for_loop(range(2)):
        qc.x(0)
        if conditional:
            with qc.if_test((qc.clbits[0], 0)):
                getattr(qc, jump)()
        else:
            getattr(qc, jump)()
        qc.x(1)

    compiled = get_benchmark_native_gates(qc, None, get_target_for_gateset(gateset_name, 2), opt_level)

    assert compiled.layout is None
    loop = compiled.data[0].operation
    assert isinstance(loop, ForLoopOp)
    assert loop.blocks[0].to_dag().count_ops(recurse=True)[jump] == 1


@pytest.mark.parametrize(("benchmark", "size"), [("qft", 4), ("bv", 6)])
def test_alg_parity(benchmark: str, size: int) -> None:
    """Test parity of algorithm-level benchmarks."""
    qc_wrapper = get_benchmark_alg(benchmark, size)
    qc_ref = get_benchmark(benchmark, BenchmarkLevel.ALG, size)
    assert qc_wrapper == qc_ref


@pytest.mark.parametrize(("benchmark", "size"), [("qft", 4)])
def test_indep_parity(benchmark: str, size: int) -> None:
    """Test parity of target-independent benchmarks."""
    qc_wrapper = get_benchmark_indep(benchmark, size)
    qc_ref = get_benchmark(benchmark, BenchmarkLevel.INDEP, size)
    assert qc_wrapper == qc_ref


@pytest.mark.parametrize(("benchmark", "size", "opt_level"), [("qft", 4, 1), ("grover", 3, 2)])
def test_native_gate_parity(benchmark: str, size: int, opt_level: int) -> None:
    """Test parity of native gate-level benchmarks."""
    target = get_target_for_gateset("ionq_forte", num_qubits=size)
    qc_wrapper = get_benchmark_native_gates(
        benchmark,
        size,
        target,
        opt_level,
    )
    qc_ref = get_benchmark(
        benchmark,
        BenchmarkLevel.NATIVEGATES,
        size,
        target,
        opt_level,
    )
    assert qc_wrapper == qc_ref


@pytest.mark.parametrize(("benchmark", "size", "opt_level"), [("qft", 4, 1)])
def test_mapped_parity(benchmark: str, size: int, opt_level: int) -> None:
    """Test parity of mapped benchmarks."""
    target = get_device("ibm_heron_156")
    qc_wrapper = get_benchmark_mapped(
        benchmark,
        size,
        target,
        opt_level,
    )
    qc_ref = get_benchmark(
        benchmark,
        BenchmarkLevel.MAPPED,
        size,
        target,
        opt_level,
    )
    assert qc_wrapper == qc_ref


@pytest.mark.parametrize(("benchmark", "size", "opt_level"), [("qft", 4, 4), ("ae", 3, -1)])
def test_validate_opt_level(benchmark: str, size: int, opt_level: int) -> None:
    """Test opt_level validation."""
    match = re.escape(f"Invalid `opt_level` '{opt_level}'. Must be in the range [0, 3].")
    with pytest.raises(ValueError, match=match):
        get_benchmark_indep(
            benchmark,
            circuit_size=size,
            opt_level=opt_level,
        )

    target = get_device("ibm_heron_156")
    with pytest.raises(ValueError, match=match):
        get_benchmark_native_gates(
            benchmark,
            circuit_size=size,
            target=target,
            opt_level=opt_level,
        )
    with pytest.raises(ValueError, match=match):
        get_benchmark_mapped(
            benchmark,
            circuit_size=size,
            target=target,
            opt_level=opt_level,
        )
    with pytest.raises(ValueError, match=match):
        get_benchmark(
            benchmark,
            level=BenchmarkLevel.INDEP,
            circuit_size=size,
            target=target,
            opt_level=opt_level,
        )


def test_assert_never_runtime() -> None:
    """Test that assert_never raises an error at runtime."""
    bad_level = cast("BenchmarkLevel", object())

    with pytest.raises(AssertionError):
        # get_benchmark will fall through the if-chain and hit assert_never
        get_benchmark("qft", level=bad_level, circuit_size=3)


@pytest.mark.parametrize(("benchmark_name", "logical_circuit_size"), [("ghz", 3), ("qwalk", 2)])
def test_get_benchmark_mirror_option(benchmark_name: str, logical_circuit_size: int) -> None:
    """Test the creation of mirror benchmarks, including layout verification for mapped circuits."""
    levels_to_test_config = [
        (BenchmarkLevel.ALG, None, None),
        (BenchmarkLevel.INDEP, 0, None),
        (
            BenchmarkLevel.NATIVEGATES,
            1,
            get_target_for_gateset("ibm_heron", num_qubits=logical_circuit_size),
        ),
        (
            BenchmarkLevel.MAPPED,
            1,
            get_device("ibm_heron_156"),
        ),
    ]

    for level_enum, comp_opt_level, target_obj in levels_to_test_config:
        qc_base = get_benchmark(
            benchmark=benchmark_name,
            level=level_enum,
            circuit_size=logical_circuit_size,
            opt_level=comp_opt_level if comp_opt_level is not None else 2,
            target=target_obj,
            generate_mirror_circuit=False,
        )

        # Get the mirror circuit
        qc_mirror = get_benchmark(
            benchmark=benchmark_name,
            level=level_enum,
            circuit_size=logical_circuit_size,
            opt_level=comp_opt_level if comp_opt_level is not None else 2,
            target=target_obj,
            generate_mirror_circuit=True,
        )

        assert qc_mirror.name == f"{qc_base.name}_mirror"

        assert qc_mirror.num_qubits == qc_base.num_qubits

        # Ensure the mirror circuit contains only native gates for the given target.
        pm = PassManager(GatesInBasis(target=target_obj))
        pm.run(qc_mirror)
        assert pm.property_set["all_gates_in_basis"]

        # at least each logical qubit should be measured
        assert sum(inst.operation.name == "measure" for inst in qc_mirror.data) >= logical_circuit_size

        # at least one barrier should be present in the middle of the circuit and one before the measurements at the end
        assert sum(1 for inst in qc_mirror.data if inst.operation.name == "barrier") >= 2, (
            f"Mirror circuit for level '{level_enum.name}' should contain at least 2 barriers."
        )

        # --- Layout Verification ---
        if level_enum == BenchmarkLevel.MAPPED:
            assert target_obj is not None, f"Target for {benchmark_name} is None."
            assert qc_base.layout is not None, f"Base mapped circuit for {benchmark_name} lacks a layout."
            assert qc_mirror.layout is not None, f"Mirror of mapped circuit for {benchmark_name} lacks a layout."

            assert qc_mirror.layout.initial_layout == qc_base.layout.initial_layout, (
                f"Mirror circuit's initial_layout ({qc_mirror.layout.initial_layout}) "
                f"differs from base circuit's initial_layout ({qc_base.layout.initial_layout})."
            )

            assert qc_mirror.layout.final_layout == Layout.generate_trivial_layout(*qc_mirror.qregs), (
                f"Mirror circuit's final_layout ({qc_mirror.layout.final_layout}) "
                f"should be a trivial layout for the mirror circuit, but it is not."
            )

            # if the circuit to be mapped has fewer qubits than the target, not every qubit should be measured
            if qc_base.num_qubits < target_obj.num_qubits:
                measured_qubits = {inst.qubits[0].index for inst in qc_mirror.data if inst.operation.name == "measure"}
                assert len(measured_qubits) < target_obj.num_qubits, (
                    f"Mirror circuit for level '{level_enum.name}' should not measure all qubits of the target "
                    f"({target_obj.num_qubits}), but measures {len(measured_qubits)}."
                )

        # --- Verification of U @ U_inv being Identity ---
        qc_mirror.remove_final_measurements(inplace=True)
        qc_mirror = RemoveBarriers()(qc_mirror)

        active_qubits = [q for q in qc_mirror.qubits if q not in qc_mirror.to_dag().idle_wires()]
        compact = QuantumCircuit(len(active_qubits), global_phase=qc_mirror.global_phase)
        for instruction in qc_mirror.data:
            compact.append(instruction.operation, [active_qubits.index(q) for q in instruction.qubits])
        np.testing.assert_allclose(Operator(compact).data, np.eye(2 ** len(active_qubits)), atol=1e-12)


@pytest.mark.parametrize("level", list(BenchmarkLevel))
def test_mirror_provenance_survives_recompilation(level: BenchmarkLevel) -> None:
    """Compiling an existing mirror keeps its generation record and export header."""
    circuit = get_benchmark_alg("ghz", 3, generate_mirror_circuit=True)
    original = circuit.copy()
    target = get_device("iqm_crystal_5")

    compiled = get_benchmark(circuit, level, target=target)

    assert circuit.metadata == original.metadata
    assert compiled.metadata["mqt_bench_generation"]["mirror"] is True
    stream = io.StringIO()
    write_circuit(compiled, stream, level, target=target)
    generation = json.loads(stream.getvalue().split("// Generation options: ")[1].splitlines()[0])
    assert generation["mirror"] is True
    assert generation["level"] == level.name.lower()
    compiled.remove_final_measurements()
    assert Statevector(compiled).probabilities()[0] == pytest.approx(1)


@pytest.mark.parametrize("level", list(BenchmarkLevel))
def test_dynamic_ghz_mirror_rejected(level: BenchmarkLevel) -> None:
    """Every level rejects a dynamic GHZ mirror without changing the input circuit."""
    circuit = get_benchmark_alg("ghz_dynamic", 5)
    original = circuit.copy()
    target = get_target_for_gateset("ibm_heron", num_qubits=5)
    with pytest.raises(ValueError, match=r"Cannot mirror this circuit.*generate_mirror_circuit=False"):
        get_benchmark(circuit, level, target=target, generate_mirror_circuit=True)
    assert circuit == original


def test_mapped_mirror_preserves_complete_layout() -> None:
    """Mirror layout metadata keeps the original logical qubits and ancillas."""
    source = QuantumCircuit(3)
    source.h(2)
    source.cx(2, 1)
    source.cx(1, 0)
    original = source.copy()
    target = get_device("iqm_crystal_5")
    base = get_benchmark_mapped(source, None, target)
    mirror = get_benchmark_mapped(source, None, target, generate_mirror_circuit=True)
    assert source == original
    assert base.layout is not None
    assert mirror.layout is not None
    assert mirror.layout.final_index_layout() == base.layout.initial_index_layout(filter_ancillas=True)
    mirror.remove_final_measurements(inplace=True)
    np.testing.assert_allclose(Operator.from_circuit(mirror).data, np.eye(2**mirror.num_qubits), atol=1e-12)


def test_dynamic_benchmark_registration() -> None:
    """A benchmark registered at runtime should immediately be visible through the public helpers."""

    @register_benchmark("dummy_benchmark", description="Dummy benchmark")
    def _dummy_factory(num_qubits: int) -> QuantumCircuit:
        return QuantumCircuit(num_qubits, name="dummy_benchmark")

    names = get_available_benchmark_names()
    assert "dummy_benchmark" in names
    assert get_benchmark_catalog()["dummy_benchmark"] == "Dummy benchmark"
    assert get_benchmark_description("dummy_benchmark") == "Dummy benchmark"

    benchmark = create_circuit("dummy_benchmark", 3)
    assert benchmark.name == "dummy_benchmark"
    assert benchmark.num_qubits == 3

    benchmark = create_circuit("dummy_benchmark", 2)
    assert benchmark.name == "dummy_benchmark"
    assert benchmark.num_qubits == 2

    with pytest.raises(
        ValueError,
        match=re.escape(
            f"'nonexistent_benchmark' is not a supported benchmark. Available benchmarks: {get_available_benchmark_names()}"
        ),
    ):
        create_circuit("nonexistent_benchmark", 3)


def test_duplicate_benchmark_registration() -> None:
    """Registering the same name twice must raise ValueError."""
    benchmark_name = "dup_benchmark"

    @register_benchmark(benchmark_name)
    def _dummy_factory1(num_qubits: int) -> QuantumCircuit:
        return QuantumCircuit(num_qubits, name=benchmark_name)

    # second registration with same name should fail
    with pytest.raises(ValueError, match="already registered"):

        @register_benchmark(benchmark_name)
        def _dummy_factory2(num_qubits: int) -> QuantumCircuit:
            return QuantumCircuit(num_qubits, name=benchmark_name)


def test_catalogue_and_names_match() -> None:
    """Every entry returned by benchmark_catalogue must appear in benchmark_names and vice-versa."""
    names = set(get_available_benchmark_names())
    cat = get_benchmark_catalog()

    assert set(cat) == names, "Name → description mapping is out of sync with benchmark_names()"

    # all descriptions are strings (may be empty)
    assert all(isinstance(desc, str) for desc in cat.values())

    for name in names:
        assert get_benchmark_description(name) == cat[name]


@pytest.mark.parametrize(
    ("benchmark"),
    ["qaoa", "qnn", "bmw_quark_cardinality", "bmw_quark_copula", "vqe_real_amp", "vqe_su2", "vqe_two_local"],
)
def test_benchmarks_with_parameters(benchmark: str) -> None:
    """Test that benchmarks with parameters can be created."""
    circuit_size = 4
    qc = get_benchmark(benchmark, level=BenchmarkLevel.ALG, circuit_size=circuit_size, random_parameters=False)
    assert len(qc.parameters) > 0, f"Benchmark {benchmark} should have parameters on the algorithm level."

    res_indep = get_benchmark(benchmark, level=BenchmarkLevel.INDEP, circuit_size=circuit_size, random_parameters=False)
    assert len(res_indep.parameters) > 0, f"Benchmark {benchmark} should have parameters on the independent level."

    for gateset_name in get_available_gateset_names():
        if gateset_name == "clifford+t":
            continue
        gateset = get_target_for_gateset(gateset_name, num_qubits=qc.num_qubits)
        res_native_gates = get_benchmark_native_gates(qc, None, gateset, 0, random_parameters=False)
        assert len(res_native_gates.parameters) > 0, (
            f"Benchmark {benchmark} should have parameters on the native gates level."
        )

        assert res_native_gates
        assert res_native_gates.num_qubits == circuit_size

    for device_name in get_available_device_names():
        device = get_device(device_name)
        res_mapped = get_benchmark_mapped(qc, None, device, 0, random_parameters=False)
        assert res_mapped
        assert len(res_mapped.parameters) > 0, f"Benchmark {benchmark} should have parameters on the mapped level."


def test_configuration_options() -> None:
    """Test ConfigurationOptions TypedDict structure and usage."""
    assert "ConfigurationOptions" in mqt.bench.configuration_options.__all__

    # Test valid configurations
    valid_config: ConfigurationOptions = {"seed": 42}
    assert valid_config["seed"] == 42

    # Test with None seed
    config_with_none: ConfigurationOptions = {"seed": None}
    assert config_with_none["seed"] is None

    # Test empty dict (all fields are optional due to total=False)
    empty_config: ConfigurationOptions = {}
    assert len(empty_config) == 0


def test_version() -> None:
    """Test that the package version is accessible."""
    assert isinstance(mqt.bench.__version__, str)
    assert isinstance(mqt.bench.__version_tuple__, tuple)


@pytest.mark.parametrize("level", list(BenchmarkLevel))
@pytest.mark.parametrize("mirror", [False, True])
@pytest.mark.parametrize("parameterized", [False, True])
def test_get_benchmark_does_not_modify_input_circuit(level: BenchmarkLevel, mirror: bool, parameterized: bool) -> None:
    """Passing a circuit to `get_benchmark` must leave that circuit untouched."""
    theta = Parameter("theta")
    circuit = QuantumCircuit(2)
    circuit.h(0)
    circuit.rx(theta if parameterized else 0.5, 1)
    circuit.cx(0, 1)
    circuit.measure_all()
    circuit.metadata = {
        "user": {"label": "input"},
        "mqt_bench_generation": {"options": {"rotation_blocks": ["ry"]}},
    }
    original = circuit.copy()

    target = None
    if level == BenchmarkLevel.NATIVEGATES:
        target = get_target_for_gateset("ibm_heron", 2)
    elif level == BenchmarkLevel.MAPPED:
        target = get_device("ibm_heron_156")
    result = get_benchmark(circuit, level, target=target, generate_mirror_circuit=mirror)

    assert circuit == original
    assert set(circuit.parameters) == set(original.parameters)
    assert circuit.metadata == original.metadata
    assert result.metadata["user"] == circuit.metadata["user"]
    assert result.metadata["mqt_bench_generation"]["mirror"] is mirror
    result.metadata["mqt_bench_generation"]["options"]["rotation_blocks"].append("rz")
    assert circuit.metadata == original.metadata
