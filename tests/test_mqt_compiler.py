# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Tests for compilation with the optional MQT Core dependency."""

from __future__ import annotations

import io
import subprocess
import sys
import textwrap
from typing import TYPE_CHECKING, cast

import numpy as np
import pytest
from qiskit import QuantumCircuit, qpy
from qiskit.circuit import Parameter
from qiskit.circuit.library import CXGate, HGate, PermutationGate, RZGate, SXGate, XGate
from qiskit.quantum_info import Operator, Statevector
from qiskit.transpiler import Target

from mqt.bench import (
    BenchmarkLevel,
    get_benchmark,
    get_benchmark_indep,
    get_benchmark_mapped,
    get_benchmark_native_gates,
)
from mqt.bench.output import MQTBenchExporterError, OutputFormat, generate_filename, save_circuit, write_circuit
from mqt.bench.targets import get_device, get_target_for_gateset

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Literal

    from pytest_console_scripts import ScriptRunner

core = pytest.importorskip("mqt.core.mlir")


@pytest.mark.parametrize("fmt", [OutputFormat.QIR, OutputFormat.LLVM, OutputFormat.QIR_BITCODE])
@pytest.mark.parametrize("profile", ["base", "adaptive"])
def test_qir_export(fmt: OutputFormat, profile: Literal["base", "adaptive"], tmp_path: Path) -> None:
    """Text and bitcode preserve classical measurement order through streams and files."""
    from mqt.core.qdmi import ProgramFormat  # ruff:ignore[import-outside-top-level]
    from mqt.core.qdmi.driver import open_device  # ruff:ignore[import-outside-top-level]

    circuit = QuantumCircuit(2, 2, metadata={"user": 42})
    circuit.x(0)
    circuit.measure([0, 1], [1, 0])
    original = circuit.copy()
    binary = fmt is OutputFormat.QIR_BITCODE
    stream = io.BytesIO() if binary else io.StringIO()
    write_circuit(circuit, stream, BenchmarkLevel.ALG, fmt, qir_profile=profile)
    assert circuit == original
    assert circuit.metadata == original.metadata
    assert save_circuit(circuit, "qir", BenchmarkLevel.ALG, fmt, target_directory=str(tmp_path), qir_profile=profile)
    path = tmp_path / ("qir.bc" if binary else "qir.ll")
    data = path.read_bytes() if binary else path.read_text()
    assert data == stream.getvalue()
    if isinstance(data, str):
        assert data.startswith("; Benchmark created by MQT Bench")
        assert "; QIR exporter: MQT Core " in data
        assert f'"qir_profiles"="{profile}_profile"' in data
    else:
        assert data.startswith(b"BC\xc0\xde")

    device = open_device("mqt.ddsim.default")
    program_format = getattr(ProgramFormat, f"QIR_{profile.upper()}_{'MODULE' if binary else 'STRING'}")
    job = device.submit_job(data, program_format, 8)
    assert job.wait()
    assert job.get_counts() == {"10": 8}


def test_qir_feedback_and_export_errors(tmp_path: Path) -> None:
    """Adaptive export handles feedback; failed lowering leaves an existing file intact."""
    from mqt.core.qdmi import ProgramFormat  # ruff:ignore[import-outside-top-level]
    from mqt.core.qdmi.driver import open_device  # ruff:ignore[import-outside-top-level]

    circuit = QuantumCircuit(2, 2)
    circuit.x(0)
    circuit.measure(0, 0)
    with circuit.if_test((circuit.clbits[0], True)):
        circuit.x(1)
    circuit.measure(1, 1)
    stream = io.StringIO()
    write_circuit(circuit, stream, BenchmarkLevel.ALG, OutputFormat.QIR, qir_profile="adaptive")
    device = open_device("mqt.ddsim.default")
    job = device.submit_job(stream.getvalue(), ProgramFormat.QIR_ADAPTIVE_STRING, 8)
    assert job.wait()
    assert job.get_counts() == {"11": 8}

    path = tmp_path / "existing.ll"
    path.write_text("existing output")
    with pytest.raises(MQTBenchExporterError, match="Unknown QIR profile"):
        write_circuit(
            circuit,
            path,
            BenchmarkLevel.ALG,
            OutputFormat.QIR,
            qir_profile=cast('Literal["base", "adaptive"]', "invalid"),
        )
    with pytest.raises(MQTBenchExporterError, match="base profile"):
        write_circuit(circuit, path, BenchmarkLevel.ALG, OutputFormat.QIR)
    assert path.read_text() == "existing output"
    circuit.rx(Parameter("theta"), 0)
    with pytest.raises(MQTBenchExporterError, match="requires bound parameters"):
        write_circuit(circuit, path, BenchmarkLevel.ALG, OutputFormat.QIR, qir_profile="adaptive")
    assert path.read_text() == "existing output"


@pytest.mark.parametrize("fmt", [OutputFormat.QIR, OutputFormat.LLVM, OutputFormat.QIR_BITCODE])
def test_qir_stream_mode(fmt: OutputFormat) -> None:
    """Reject text/bitcode stream mismatches before writing output."""
    stream = io.StringIO() if fmt is OutputFormat.QIR_BITCODE else io.BytesIO()
    with pytest.raises(MQTBenchExporterError, match="requires a"):
        write_circuit(QuantumCircuit(1), stream, BenchmarkLevel.ALG, fmt)
    assert not stream.getvalue()


@pytest.mark.parametrize("fmt", ["qir", "llvm", "qir-bitcode"])
@pytest.mark.parametrize("save", [False, True])
def test_qir_cli(fmt: str, save: bool, script_runner: ScriptRunner, tmp_path: Path) -> None:
    """The CLI prints LLVM text or writes text/bitcode with the requested profile."""
    result = script_runner.run([
        "mqt-bench",
        "--algorithm",
        "ghz_dynamic",
        "--num-qubits",
        "3",
        "--level",
        "indep",
        "--compiler",
        "mqt",
        "--output-format",
        fmt,
        "--qir-profile",
        "adaptive",
        "--target-directory",
        str(tmp_path),
        *(["--save"] if save else []),
    ])
    assert result.success
    if fmt == "qir-bitcode":
        path = tmp_path / "ghz_dynamic_indep_mqt_3.bc"
        assert path.read_bytes().startswith(b"BC\xc0\xde")
        assert result.stdout.strip() == str(path)
    else:
        if save:
            path = tmp_path / "ghz_dynamic_indep_mqt_3.ll"
            text = path.read_text()
            assert result.stdout.strip() == str(path)
        else:
            text = result.stdout
            assert not list(tmp_path.glob("*.ll"))
        assert text.startswith("; Benchmark created by MQT Bench")
        assert "; Compiler: mqt " in text
        assert '"qir_profiles"="adaptive_profile"' in text


def _measurement_probabilities(circuit: QuantumCircuit) -> dict[str, float]:
    """Compute classical outputs independently of Core for terminal measurements."""
    unitary = circuit.copy()
    unitary.remove_final_measurements(inplace=True)
    state = Statevector.from_instruction(unitary)
    probabilities: dict[str, float] = {}
    for basis, probability in enumerate(state.probabilities()):
        if probability < 1e-10:
            continue
        bits = ["0"] * circuit.num_clbits
        for item in circuit.data:
            if item.operation.name == "measure":
                qubit = circuit.find_bit(item.qubits[0]).index
                bit = circuit.find_bit(item.clbits[0]).index
                bits[bit] = str((basis >> qubit) & 1)
        outcome = "".join(reversed(bits))
        probabilities[outcome] = probabilities.get(outcome, 0.0) + float(probability)
    return probabilities


@pytest.mark.parametrize(
    "gateset", ["ibm_falcon", "ibm_eagle", "ibm_heron", "iqm", "quantinuum", "clifford+t+rotations"]
)
def test_native_equivalence(gateset: str) -> None:
    """Native compilation preserves the unitary, width, name, and user metadata."""
    circuit = QuantumCircuit(3, name="native_test", metadata={"user": 42})
    circuit.h(0)
    circuit.ry(0.37, 1)
    circuit.cx(0, 2)
    circuit.cp(0.23, 1, 2)
    circuit.global_phase = 0.17
    original = circuit.copy()
    target = get_target_for_gateset(gateset, 8)
    result = get_benchmark_native_gates(circuit, None, target, compiler="mqt")
    assert circuit == original
    assert result.num_qubits == circuit.num_qubits
    assert result.name == circuit.name
    assert result.metadata["user"] == 42
    assert result.metadata["mqt_bench_compiler"]["name"] == "mqt"
    assert Operator(result).equiv(Operator(circuit))
    assert set(result.count_ops()) <= set(target.operation_names)


def test_symbolic_independent_circuit() -> None:
    """Free parameters survive Core optimization and remain bindable by identity."""
    parameter = Parameter("theta")
    circuit = QuantumCircuit(2)
    circuit.ry(parameter, 0)
    circuit.cx(0, 1)
    result = get_benchmark_indep(circuit, compiler="mqt", random_parameters=False)
    assert result.parameters == circuit.parameters
    for value in [0.0, 0.7, np.pi]:
        assert Operator(result.assign_parameters({parameter: value})).equiv(
            Operator(circuit.assign_parameters({parameter: value}))
        )


def test_mapped_measurement_order() -> None:
    """Routing preserves classical results and respects directed physical gates."""
    target = Target(num_qubits=4)
    for instruction in [XGate(), SXGate(), RZGate(Parameter("theta"))]:
        target.add_instruction(instruction)
    target.add_instruction(CXGate(), {(1, 0): None, (1, 2): None, (3, 2): None})
    from qiskit.circuit import Measure  # ruff:ignore[import-outside-top-level]

    target.add_instruction(Measure())
    circuit = QuantumCircuit(3, 3)
    circuit.x(0)
    circuit.h(1)
    circuit.cx(0, 2)
    circuit.measure([0, 1, 2], [2, 0, 1])
    result = get_benchmark_mapped(circuit, None, target, compiler="mqt")
    assert result.num_qubits == target.num_qubits
    assert result.layout is None
    assert _measurement_probabilities(result) == pytest.approx(_measurement_probabilities(circuit))
    for item in result.data:
        if item.operation.name == "cx":
            sites = tuple(result.find_bit(qubit).index for qubit in item.qubits)
            assert target.instruction_supported(operation_name="cx", qargs=sites)


@pytest.mark.parametrize("level", [BenchmarkLevel.INDEP, BenchmarkLevel.NATIVEGATES, BenchmarkLevel.MAPPED])
def test_mirror_without_qiskit_transpilation(level: BenchmarkLevel, monkeypatch: pytest.MonkeyPatch) -> None:
    """A Core mirror keeps both halves and returns only the all-zero outcome."""

    def reject_transpile(*args: object, **kwargs: object) -> None:
        pytest.fail("The MQT compiler must not call the Qiskit transpiler.")

    target = get_device("iqm_crystal_5") if level == BenchmarkLevel.MAPPED else get_target_for_gateset("ibm_falcon", 3)
    monkeypatch.setattr("mqt.bench.benchmark_generation.transpile", reject_transpile)
    monkeypatch.setattr("mqt.bench.benchmark_generation.generate_preset_pass_manager", reject_transpile)
    result = get_benchmark("ghz", level, 3, target=target, compiler="mqt", generate_mirror_circuit=True)
    assert result.name == "ghz_mirror"
    assert result.count_ops().get("barrier", 0) >= 1
    assert result.count_ops().get("cx", 0) + result.count_ops().get("cz", 0) >= 4
    assert _measurement_probabilities(result) == pytest.approx({"0" * result.num_clbits: 1.0})


@pytest.mark.parametrize(
    "benchmark",
    ["ghz", "qft", "grover", "qwalk", "dynamic_qft", "ghz_dynamic", "modular_adder", "hrs_cumulative_multiplier"],
)
@pytest.mark.parametrize("level", [BenchmarkLevel.INDEP, BenchmarkLevel.NATIVEGATES, BenchmarkLevel.MAPPED])
def test_benchmark_levels(benchmark: str, level: BenchmarkLevel) -> None:
    """Static and structured Bench circuits pass through every Core compilation level."""
    target = get_device("iqm_crystal_5") if level == BenchmarkLevel.MAPPED else get_target_for_gateset("ibm_falcon", 3)
    circuit = get_benchmark(
        benchmark,
        BenchmarkLevel.ALG,
        {"modular_adder": 4, "hrs_cumulative_multiplier": 5}.get(benchmark, 3),
        **({"for_loop": True} if benchmark in {"grover", "qwalk"} else {}),
    )
    result = get_benchmark(circuit, level, target=target, compiler="mqt")
    assert isinstance(result, QuantumCircuit)
    assert result.name == benchmark
    assert result.count_ops().get("measure", 0) > 0
    if benchmark == "dynamic_qft":
        assert result.count_ops().get("if_else", 0) > 0


@pytest.mark.parametrize("gateset", ["ionq_aria", "ionq_forte", "rigetti"])
def test_custom_targets_rejected(gateset: str) -> None:
    """Unsupported target gates produce an error instead of a Qiskit fallback."""
    with pytest.raises(ValueError, match="does not support target instruction"):
        get_benchmark_native_gates("ghz", 3, get_target_for_gateset(gateset, 3), compiler="mqt")


def test_fixed_parameter_target_rejected() -> None:
    """Core must not broaden a fixed-angle gate into an arbitrary rotation."""
    target = Target(num_qubits=1)
    target.add_instruction(RZGate(np.pi / 4))
    with pytest.raises(ValueError, match="requires unrestricted parameters"):
        get_benchmark_native_gates("ghz", 1, target, compiler="mqt")


def test_disconnected_target_rejected() -> None:
    """An empty coupling graph must not be treated as all-to-all connectivity."""
    target = Target(num_qubits=2)
    target.add_instruction(HGate())
    target.add_instruction(CXGate(), {})
    with pytest.raises(RuntimeError, match="Target compilation failed"):
        get_benchmark_mapped("ghz", 2, target, compiler="mqt")


def test_target_capacity() -> None:
    """Mapped compilation rejects circuits that do not fit on the device."""
    with pytest.raises(ValueError, match="at least as many qubits"):
        get_benchmark_mapped("ghz", 6, get_device("iqm_crystal_5"), compiler="mqt")


def test_compiler_provenance() -> None:
    """Text and binary exports identify Core and keep user metadata."""
    result = get_benchmark_indep("ghz", 3, compiler="mqt")
    text = io.StringIO()
    write_circuit(result, text, BenchmarkLevel.INDEP)
    assert "// Compiler: mqt " in text.getvalue()
    binary = io.BytesIO()
    write_circuit(result, binary, BenchmarkLevel.INDEP, OutputFormat.QPY)
    binary.seek(0)
    restored = qpy.load(binary)[0]
    assert restored.metadata["mqt_bench_compiler"] == result.metadata["mqt_bench_compiler"]
    assert generate_filename("ghz", BenchmarkLevel.INDEP, 3, compiler="mqt") == "ghz_indep_mqt_3"


def test_mqt_cli(script_runner: ScriptRunner, tmp_path: Path) -> None:
    """The compiler option works with the default optimization setting and saves a distinct file."""
    result = script_runner.run([
        "mqt-bench",
        "--compiler",
        "mqt",
        "--level",
        "nativegates",
        "--algorithm",
        "ghz",
        "--num-qubits",
        "3",
        "--target",
        "ibm_falcon",
        "--save",
        "--target-directory",
        str(tmp_path),
    ])
    assert result.success
    assert "ghz_nativegates_ibm_falcon_mqt_3.qasm" in result.stdout


@pytest.mark.parametrize("level", [BenchmarkLevel.INDEP, BenchmarkLevel.NATIVEGATES, BenchmarkLevel.MAPPED])
def test_qiskit_recompilation_provenance(level: BenchmarkLevel) -> None:
    """Recompiling with Qiskit must not retain Core as the last compiler."""
    circuit = get_benchmark_indep("ghz", 3, compiler="mqt")
    target = get_target_for_gateset("ibm_falcon", 3)
    result = get_benchmark(circuit, level, target=target)
    assert result.metadata["mqt_bench_compiler"]["name"] == "qiskit"
    assert circuit.metadata["mqt_bench_compiler"]["name"] == "mqt"


@pytest.mark.parametrize("level", [BenchmarkLevel.INDEP, BenchmarkLevel.NATIVEGATES, BenchmarkLevel.MAPPED])
def test_classical_feed_forward(level: BenchmarkLevel) -> None:
    """Classical destinations and a conditional gate retain their meaning after compilation."""
    circuit = QuantumCircuit(3, 3)
    circuit.x(0)
    circuit.measure(0, 2)
    with circuit.if_test((circuit.clbits[2], True)):
        circuit.x(2)
    circuit.measure([1, 2], [1, 0])
    target = get_device("iqm_crystal_5")
    result = get_benchmark(circuit, level, target=target, compiler="mqt")
    assert core.QCProgram.from_qiskit(result).to_qco().sample(shots=16, seed=42) == {"101": 16}


@pytest.mark.parametrize("level", [BenchmarkLevel.INDEP, BenchmarkLevel.NATIVEGATES, BenchmarkLevel.MAPPED])
def test_amplitude_estimation_import(level: BenchmarkLevel) -> None:
    """Import array-valued permutation parameters without aborting the Python process."""
    script = textwrap.dedent(f"""\
        from mqt.bench import BenchmarkLevel, get_benchmark, get_benchmark_alg
        from mqt.bench.targets import get_device
        from qiskit.quantum_info import Statevector
        from qiskit import QuantumCircuit

        original = get_benchmark_alg("ae", 3)
        result = get_benchmark(original, BenchmarkLevel.{level.name}, target=get_device("iqm_crystal_5"), compiler="mqt")
        assert result.name == original.name
        # Compare classical probabilities after accounting for physical output wires.
        def probabilities(circuit):
            unitary = circuit.copy()
            unitary.remove_final_measurements(inplace=True)
            output = {{}}
            for basis, probability in enumerate(Statevector.from_instruction(unitary).probabilities()):
                bits = ["0"] * circuit.num_clbits
                for item in circuit.data:
                    if item.operation.name == "measure":
                        q = circuit.find_bit(item.qubits[0]).index
                        c = circuit.find_bit(item.clbits[0]).index
                        bits[c] = str((basis >> q) & 1)
                key = "".join(reversed(bits))
                output[key] = output.get(key, 0.0) + probability
            return output
        reference = probabilities(original)
        actual = probabilities(result)
        assert all(abs(actual.get(key, 0) - value) < 1e-8 for key, value in reference.items())
    """)
    result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, timeout=30, check=False)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("controlled", [False, True])
def test_nested_permutation(controlled: bool) -> None:
    """Normalize permutations inside reusable and controlled custom gate definitions."""
    block = QuantumCircuit(3)
    block.append(PermutationGate([2, 0, 1]), range(3))
    gate = block.to_gate()
    if controlled:
        gate = gate.control(1, annotated=True)
    circuit = QuantumCircuit(gate.num_qubits)
    circuit.append(gate, range(gate.num_qubits))
    result = get_benchmark_indep(circuit, compiler="mqt")
    assert Operator(result).equiv(Operator(circuit))
