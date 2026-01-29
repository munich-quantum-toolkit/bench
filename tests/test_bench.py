# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Tests for the benchmark generation."""

from __future__ import annotations

import builtins
import functools
import io
import re
from datetime import date
from enum import Enum
from importlib import metadata
from pathlib import Path
from typing import TYPE_CHECKING, NoReturn, cast

import pytest
from qiskit import QuantumCircuit, qpy
from qiskit.circuit import IfElseOp, Parameter
from qiskit.circuit.library import CXGate, HGate, RXGate, RZGate, XGate
from qiskit.compiler import transpile
from qiskit.transpiler import (
    InstructionProperties,
    Layout,
    PassManager,
    Target,  # For layout handling
)
from qiskit.transpiler.passes import GatesInBasis, RemoveBarriers

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable

    from mqt.bench.configuration_options import ConfigurationOptions

import mqt.bench.configuration_options
from mqt.bench.benchmark_generation import (
    BenchmarkLevel,
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
            res_mapped = get_benchmark_mapped(
                qc,
                None,
                device,
                0,
            )
            assert res_mapped


@pytest.mark.parametrize(
    ("benchmark_name", "input_value", "kind"),
    [
        ("cdkm_ripple_carry_adder", 4, "half"),
        ("cdkm_ripple_carry_adder", 4, "full"),
        ("cdkm_ripple_carry_adder", 3, "fixed"),
        ("draper_qft_adder", 3, "half"),
        ("draper_qft_adder", 2, "fixed"),
        ("vbe_ripple_carry_adder", 3, "half"),
        ("vbe_ripple_carry_adder", 4, "full"),
        ("vbe_ripple_carry_adder", 2, "fixed"),
    ],
)
def test_adder_circuits(benchmark_name: str, input_value: int, kind: str) -> None:
    """Test the creation of the arithmetic circuits."""
    qc = create_circuit(benchmark_name, input_value, kind)
    assert qc.num_qubits == input_value


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
        ("shors_nine_qubit_code", 9, None, "num_qubits must be divisible by 17."),
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

    with pytest.raises(ValueError, match=r"Length of hidden_string must be num_qubits - 1."):
        create_circuit("bv", 3, hidden_string="wrong")


def test_dj_constant_oracle() -> None:
    """Test the creation of the DJ benchmark constant oracle."""
    qc = create_circuit("dj", 5, False)
    assert qc.depth() > 0


def test_graphstate_seed() -> None:
    """Test the creation of the graphstate benchmark with and without a custom seed."""
    assert get_benchmark_alg("graphstate", 5, seed=42) == get_benchmark_alg("graphstate", 5, seed=42)
    assert get_benchmark_alg("graphstate", 5, seed=0) != get_benchmark_alg("graphstate", 5, seed=42)
    # Verify that omitting the seed still produces valid circuits (no need to test inequality)
    qc_no_seed = get_benchmark_alg("graphstate", 5)
    assert qc_no_seed.num_qubits == 5
    assert qc_no_seed.name == "graphstate"


@pytest.mark.parametrize("num_qubits", [17, 34, 51, 68])
def test_shors_nine_qubit_code_circuit_structure(num_qubits: int) -> None:
    """Test that Shor's 9-qubit code circuits have the expected structure.

    For n logical qubits (num_qubits = 17n):
        - Quantum registers: n of size 9 (data), n of size 6 (bit-flip syndrome), n of size 2 (phase-flip syndrome)
        - Classical registers: n of size 6 (bit-flip), n of size 2 (phase-flip), 1 of size 17n (measurement)
        - 25n total classical bits (8n syndrome + 17n measure_all)
        - 12n conditional operations (9 bit-flip + 3 phase-flip per logical qubit)
    """
    qc = create_circuit("shors_nine_qubit_code", num_qubits)
    num_logical_qubits = num_qubits // 17

    # Check total qubits
    assert qc.num_qubits == num_qubits

    # Check total classical bits: 8 per logical qubit (syndrome) + 17 per logical qubit (measure_all)
    expected_clbits = 8 * num_logical_qubits + num_qubits
    assert qc.num_clbits == expected_clbits, f"Expected {expected_clbits} classical bits, found {qc.num_clbits}"

    # Check quantum register sizes: 9n (data) + 6n (bit-flip syndrome) + 2n (phase-flip syndrome)
    qreg_sizes = sorted(qreg.size for qreg in qc.qregs)
    expected_qreg_sizes = sorted([9] * num_logical_qubits + [6] * num_logical_qubits + [2] * num_logical_qubits)
    assert qreg_sizes == expected_qreg_sizes, f"Expected qreg sizes {expected_qreg_sizes}, found {qreg_sizes}"

    # Check classical register sizes: 6n (bit-flip) + 2n (phase-flip) + 1num_qubits (measurement)
    creg_sizes = sorted(creg.size for creg in qc.cregs)
    expected_creg_sizes = sorted([6] * num_logical_qubits + [2] * num_logical_qubits + [num_qubits])
    assert creg_sizes == expected_creg_sizes, f"Expected creg sizes {expected_creg_sizes}, found {creg_sizes}"

    # Check total if-else operations: 12 per logical qubit (9 bit-flip + 3 phase-flip)
    if_else_count = sum(1 for inst in qc.data if isinstance(inst.operation, IfElseOp))
    expected_if_else = 12 * num_logical_qubits
    assert if_else_count == expected_if_else, (
        f"Expected {expected_if_else} conditional operations, found {if_else_count}"
    )


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
            get_device("ibm_falcon_127"),
            0,
        ),
        ("ghz", BenchmarkLevel.MAPPED, 3, get_device("ibm_falcon_27"), 2),
        (
            "ghz",
            BenchmarkLevel.MAPPED,
            3,
            get_device("ionq_aria_25"),
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
            get_device("rigetti_ankaa_84"),
            1,
        )
    match = "`circuit_size` must be a positive integer when `benchmark` is a str."
    with pytest.raises(ValueError, match=match):
        get_benchmark(
            "dj",
            BenchmarkLevel.INDEP,
            -1,
            get_device("rigetti_ankaa_84"),
            1,
        )
    match = "No Shor instance for circuit_size=3. Available: 18, 42, 58, 74."
    with pytest.raises(ValueError, match=match):
        get_benchmark(
            "shor",
            BenchmarkLevel.INDEP,
            3,
            get_device("rigetti_ankaa_84"),
            1,
        )
    match = re.escape("Invalid `opt_level` '4'. Must be in the range [0, 3].")
    with pytest.raises(ValueError, match=match):
        get_benchmark(
            "qpeexact",
            BenchmarkLevel.INDEP,
            3,
            get_device("rigetti_ankaa_84"),
            4,
        )
    match = re.escape(
        "'wrong_gateset' is not a supported gateset. Known modules: ['clifford_t', 'ibm', 'ionq', 'iqm', 'quantinuum', 'rigetti']"
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
        "'wrong_device' is not a supported device. Known modules: ['ibm', 'ionq', 'iqm', 'quantinuum', 'rigetti']"
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


def test_clifford_t() -> None:
    """Test the Clifford+T gateset."""
    qc = get_benchmark(
        benchmark="qft",
        level=BenchmarkLevel.NATIVEGATES,
        circuit_size=4,
        target=get_target_for_gateset("clifford+t", 4),
        opt_level=1,
    )

    clifford_t_target = get_target_for_gateset("clifford+t", num_qubits=4)
    pm = PassManager(GatesInBasis(target=clifford_t_target))
    pm.run(qc)
    assert pm.property_set["all_gates_in_basis"]


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


def test_create_ae_circuit_with_invalid_qubit_number() -> None:
    """Testing the minimum number of qubits in the amplitude estimation circuit."""
    with pytest.raises(ValueError, match=r"Number of qubits must be at least 2 \(1 evaluation \+ 1 target\)."):
        get_benchmark("ae", BenchmarkLevel.INDEP, 1)


@pytest.mark.parametrize(
    ("level", "target", "generate_mirror_circuit", "expected"),
    [
        (BenchmarkLevel.ALG, None, False, "ghz_alg_5"),
        (BenchmarkLevel.ALG, None, True, "ghz_alg_mirror_5"),
        (BenchmarkLevel.INDEP, None, False, "ghz_indep_opt2_5"),
        (BenchmarkLevel.INDEP, None, True, "ghz_indep_mirror_opt2_5"),
        (
            BenchmarkLevel.NATIVEGATES,
            get_target_for_gateset("ibm_falcon", 5),
            False,
            "ghz_nativegates_ibm_falcon_opt2_5",
        ),
        (
            BenchmarkLevel.NATIVEGATES,
            get_target_for_gateset("ibm_falcon", 5),
            True,
            "ghz_nativegates_mirror_ibm_falcon_opt2_5",
        ),
        (
            BenchmarkLevel.MAPPED,
            get_device("ibm_falcon_127"),
            False,
            "ghz_mapped_ibm_falcon_127_opt2_5",
        ),
        (
            BenchmarkLevel.MAPPED,
            get_device("ibm_falcon_127"),
            True,
            "ghz_mapped_mirror_ibm_falcon_127_opt2_5",
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


@pytest.fixture(autouse=True)
def temp_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Ensure all files go into a temporary directory."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_generate_header_minimal(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test the generation of a minimal header."""
    monkeypatch.setattr(metadata, "version", lambda _: "9.9.9")
    hdr = generate_header(OutputFormat.QASM3, BenchmarkLevel.INDEP)
    lines = hdr.splitlines()
    # first line has today's date
    assert lines[0] == f"// Benchmark created by MQT Bench on {date.today()}"
    # contains the fixed info lines
    assert "// For more info: https://mqt-bench.app/" in hdr
    assert "// MQT Bench version: 9.9.9" in hdr
    assert f"// Qiskit version: {__qiskit_version__}" in hdr
    assert f"// Output format: {OutputFormat.QASM3.value}" in hdr
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
    """Test writing a QASM circuit."""
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)

    out = tmp_path / "test.qasm"
    write_circuit(qc, out, BenchmarkLevel.INDEP, fmt=fmt)

    text = out.read_text().splitlines()
    # header lines at top
    assert text[0].startswith("// Benchmark created by MQT Bench on")
    # QASM body present
    assert any(line.startswith("h ") for line in text), "H gate should appear"
    assert any(line.startswith("cx ") for line in text), "CX gate should appear"


def test_write_circuit_qpy(tmp_path: Path) -> None:
    """Test writing a QPY circuit with header embedded in metadata."""
    qc = QuantumCircuit(1)
    qc.x(0)
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
    assert header.startswith(f"// Benchmark created by MQT Bench on {date.today()}")
    assert "// MQT Bench version:" in header
    assert "// Output format: qpy" in header


def test_write_circuit_io_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Simulate I/O error while writing."""
    qc = QuantumCircuit(1)
    qc.h(0)

    out = tmp_path / "readonly.qasm"

    # Monkey-patch builtins.open to throw OSError on any attempt to open for writing
    def fake_open(*args: str, **kwargs: str) -> NoReturn:
        msg = "disk full"
        raise OSError(msg)

    monkeypatch.setattr(Path, "open", fake_open)
    monkeypatch.setattr(metadata, "version", lambda _: "0.1.0")

    with pytest.raises(MQTBenchExporterError) as exc:
        write_circuit(qc, out, BenchmarkLevel.INDEP, fmt=OutputFormat.QASM2)

    msg = str(exc.value)
    assert "failed to write qasm2 file" in msg.lower()
    assert "disk full" in msg.lower()

    # restore Path.open so other tests continue unharmed
    monkeypatch.setattr(Path, "open", builtins.open)


def test_write_circuit_unsupported_format(tmp_path: Path) -> None:
    """Requesting an unsupported format should raise."""

    class FakeFormat(str, Enum):
        FAKE = "fake"

    qc = QuantumCircuit(1)

    with pytest.raises(MQTBenchExporterError) as exc:
        write_circuit(qc, tmp_path / "foo.fake", BenchmarkLevel.INDEP, fmt=FakeFormat.FAKE)  # type: ignore[arg-type]

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


def test_save_circuit_write_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """save_circuit returns False when write_circuit fails."""
    qc = QuantumCircuit(1)
    qc.h(0)

    monkeypatch.setattr(
        "mqt.bench.output.write_circuit",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(MQTBenchExporterError("boom")),
    )

    ok = save_circuit(qc, "baz", BenchmarkLevel.INDEP, OutputFormat.QASM3, target_directory=str(tmp_path))
    assert ok is False


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
    target = get_device("ibm_falcon_127")
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

    target = get_device("ibm_falcon_127")
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


def test_get_benchmark_mirror_option() -> None:
    """Test the creation of mirror benchmarks, including layout verification for mapped circuits."""
    benchmark_name = "ghz"
    logical_circuit_size = 3

    levels_to_test_config = [
        (BenchmarkLevel.ALG, None, None),
        (BenchmarkLevel.INDEP, 0, None),
        (
            BenchmarkLevel.NATIVEGATES,
            1,
            get_target_for_gateset("ibm_falcon", num_qubits=logical_circuit_size),
        ),
        (
            BenchmarkLevel.MAPPED,
            1,
            get_device("ibm_falcon_27"),
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

        optimized_circuit = transpile(
            qc_mirror,
            optimization_level=2,
            basis_gates=["u", "cx"],
        )

        assert len(optimized_circuit.data) == 0, (
            f"Unitary part of mirror (U@U_inv) for level '{level_enum.name}' ({qc_mirror.num_qubits} qubits) "
            "did not optimize to an empty circuit. This means it might not represent the identity."
        )


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
