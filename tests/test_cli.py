# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Tests for the CLI."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from pytest_console_scripts import ScriptRunner
from qiskit.qasm3 import dumps
from qiskit.qasm3 import loads
from mqt.bench.benchmark_generation import generate_filename

from mqt.bench import CompilerSettings, QiskitSettings
from mqt.bench.benchmark_generation import get_benchmark
from mqt.bench.targets import get_device_by_name, get_target_for_gateset

if TYPE_CHECKING:
    from pytest_console_scripts import ScriptResult, ScriptRunner


# fmt: off
@pytest.mark.parametrize(
    ("args", "expected_output"),
    [
        ([
             "--level", "alg",
             "--algorithm", "ghz",
             "--num-qubits", "10",
         ], dumps(get_benchmark(level="alg", benchmark_name="ghz", circuit_size=10))),
        ([
             "--level", "alg",
             "--algorithm", "shor_xsmall",
             "--num-qubits", "10",
            "--output-format", "qasm2",
         ], "OPENQASM 2.0;"),  # Note: shor is non-deterministic, so just a basic sanity check
        ([
             "--level", "alg",
             "--algorithm", "ghz",
             "--num-qubits", "20",
         ], dumps(get_benchmark(level="alg", benchmark_name="ghz", circuit_size=20))),
        ([
             "--level", "indep",
             "--algorithm", "ghz",
             "--num-qubits", "20",
         ], dumps(get_benchmark(level="indep", benchmark_name="ghz", circuit_size=20))),
        ([
             "--level", "nativegates",
             "--algorithm", "ghz",
             "--num-qubits", "20",
             "--target", "ibm_falcon",
         ], dumps(get_benchmark(level="nativegates", benchmark_name="ghz", circuit_size=20, target=get_target_for_gateset("ibm_falcon", 20)))),
        ([
             "--level", "mapped",
             "--algorithm", "ghz",
             "--num-qubits", "20",
             "--qiskit-optimization-level", "2",
             "--target", "ibm_falcon_27",
         ], dumps(get_benchmark(
            level="mapped",
            benchmark_name="ghz",
            circuit_size=20,
            compiler_settings=CompilerSettings(QiskitSettings(optimization_level=2)),
            target=get_device_by_name("ibm_falcon_27"),
        ))),
        (["--help"], "usage: mqt.bench.cli"),
    ],
)
def test_cli(args: list[str], expected_output: str, script_runner: ScriptRunner) -> None:
    """Test the CLI with different arguments."""
    ret = script_runner.run(["mqt.bench.cli", *args])
    assert ret.success
    assert expected_output in ret.stdout


# fmt: off
@pytest.mark.parametrize(
    ("args", "expected_output"),
    [
        ([], "usage: mqt.bench.cli"),
        (["asd"], "usage: mqt.bench.cli"),
        (["--benchmark", "ae"], "usage: mqt.bench.cli"),
        # Note: We don't care about the actual error messages in most cases
        ([
             "--level", "alg",
             "--algorithm", "not-a-valid-benchmark",
             "--num-qubits", "20",
         ], ""),
    ],
)
def test_cli_errors(args: list[str], expected_output: str, script_runner: ScriptRunner) -> None:
    """Test the CLI with different error cases."""
    ret = script_runner.run(["mqt.bench.cli", *args])
    assert not ret.success
    assert expected_output in ret.stderr


def _run_cli(script_runner: ScriptRunner, extra_args: list[str]) -> ScriptResult:
    """Run *mqt.bench.cli* with default GHZ/ALG/5 settings plus *extra_args*."""
    cmd = ["mqt.bench.cli", "--level", "alg", "--algorithm", "ghz", "--num-qubits", "5", *extra_args]
    return script_runner.run(cmd)


@pytest.mark.parametrize("fmt", ["qasm3", "qasm2"])
def test_cli_qasm_stdout(fmt: str, script_runner: ScriptRunner) -> None:
    """QASM2/3 should stream directly to stdout when *--save* is omitted."""
    ret = _run_cli(script_runner, ["--output-format", fmt])
    assert ret.success
    assert "// MQT Bench version:" in ret.stdout  # header present
    assert "OPENQASM" in ret.stdout               # body starts with keyword
    assert not ret.stderr                   # no unexpected errors


def test_cli_qpy_save(tmp_path: Path, script_runner: ScriptRunner) -> None:
    """When *--save* is given, QPY file is persisted and path is echoed."""
    target_dir = str(tmp_path)
    ret = _run_cli(
        script_runner,
        [
            "--output-format",
            "qpy",
            "--save",
            "--target-directory",
            target_dir,
        ],
    )
    assert ret.success

    expected_path = Path(target_dir) / "ghz_alg_5.qpy"
    # CLI prints the path on a single line - ensure correctness
    assert str(expected_path) in ret.stdout.strip().splitlines()[-1]
    assert expected_path.is_file()

def test_cli_mirror_circuit_stdout(script_runner: ScriptRunner) -> None:
    """Test the CLI with --generate-mirror-circuit flag to stdout."""
    args = [
        "--level", "alg",
        "--algorithm", "ghz",
        "--num-qubits", "3",
        "--generate-mirror-circuit",
        "--output-format", "qasm3",
    ]
    ret = script_runner.run(["mqt.bench.cli", *args])
    assert ret.success

    expected_qc = get_benchmark(
        level="alg",
        benchmark_name="ghz",
        circuit_size=3,
        generate_mirror_circuit=True
    )
    qasm_body_from_cli = "\n".join(ret.stdout.splitlines()[4:]) 
    cli_qc = loads(qasm_body_from_cli)

    assert cli_qc.num_qubits == expected_qc.num_qubits
    assert cli_qc.count_ops().get("barrier", 0) >= 1 
    original_qc = get_benchmark(level="alg", benchmark_name="ghz", circuit_size=3, generate_mirror_circuit=False)
    num_ops_original_unitary = len(original_qc.remove_final_measurements(inplace=False).data)
    
    cli_ops_count = 0
    for instruction in cli_qc.data:
        if instruction.operation.name not in ["barrier", "measure"]:
            cli_ops_count += 1
    assert cli_ops_count == 2 * num_ops_original_unitary
    assert cli_qc.count_ops().get("measure", 0) == expected_qc.num_qubits

def test_cli_mirror_circuit_save_file(tmp_path: Path, script_runner: ScriptRunner) -> None:
    """Test saving a mirrored circuit from CLI to a file."""
    target_dir = str(tmp_path)
    algorithm_name = "ghz"
    num_q = 3
    level_str = "alg"

    args = [
        "--level", level_str,
        "--algorithm", algorithm_name,
        "--num-qubits", str(num_q),
        "--generate-mirror-circuit",
        "--save", 
        "--target-directory", target_dir,
        "--output-format", "qasm3"
    ]
    ret = script_runner.run(["mqt.bench.cli", *args])
    assert ret.success

    expected_circuit_name_in_cli = f"{algorithm_name}_mirrored"
    expected_filename_base = generate_filename(
        benchmark_name=expected_circuit_name_in_cli,
        level=level_str,
        num_qubits=num_q
    )
    expected_file_path = tmp_path / f"{expected_filename_base}.qasm"

    assert expected_file_path.is_file(), f"Expected file {expected_file_path} not found. Found: {[p.name for p in tmp_path.iterdir()]}"
    
    expected_qc = get_benchmark(
        level=level_str,
        benchmark_name=algorithm_name,
        circuit_size=num_q,
        generate_mirror_circuit=True
    )
    
    saved_content = expected_file_path.read_text()
    qasm_body_from_file = "\n".join(saved_content.splitlines()[4:])
    
    file_qc = loads(qasm_body_from_file)

    assert file_qc.num_qubits == expected_qc.num_qubits
    assert file_qc.count_ops().get("barrier", 0) >= 1
    original_qc = get_benchmark(level=level_str, benchmark_name=algorithm_name, circuit_size=num_q, generate_mirror_circuit=False)
    num_ops_original_unitary = len(original_qc.remove_final_measurements(inplace=False).data)
    file_ops_count = 0
    for instruction in file_qc.data:
        if instruction.operation.name not in ["barrier", "measure"]:
            file_ops_count += 1
    assert file_ops_count == 2 * num_ops_original_unitary
    assert file_qc.count_ops().get("measure", 0) == expected_qc.num_qubits

def test_cli_help_includes_mirror_flag(script_runner: ScriptRunner) -> None:
    """Test that --help includes the new --generate-mirror-circuit flag."""
    ret = script_runner.run(["mqt.bench.cli", "--help"])
    assert ret.success
    assert "--generate-mirror-circuit" in ret.stdout
