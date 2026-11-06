# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Tests for the CLI."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest
from qiskit import qasm2
from qiskit.qasm3 import dumps

from mqt.bench.benchmark_generation import BenchmarkLevel, get_benchmark
from mqt.bench.benchmarks import create_circuit
from mqt.bench.targets import get_device, get_target_for_gateset

if TYPE_CHECKING:
    from pathlib import Path

    from pytest_console_scripts import RunResult, ScriptRunner


def _generate(script_runner: ScriptRunner, level: str, algorithm: str, size: int, *options: str) -> RunResult:
    return script_runner.run([
        "mqt-bench",
        "--level",
        level,
        "--algorithm",
        algorithm,
        "--num-qubits",
        str(size),
        *options,
    ])


@pytest.mark.parametrize(
    ("extra_args", "seed", "trials"),
    [([], 10, 8), (["--compiler-seed", "17"], 17, 8), (["--mapping-trials", "3"], 10, 3)],
)
def test_mqt_cli(script_runner: ScriptRunner, tmp_path: Path, extra_args: list[str], seed: int, trials: int) -> None:
    """Keep compilation controls separate from factory options and Qiskit's opt_level."""
    result = _generate(
        script_runner,
        "nativegates",
        "graphstate",
        3,
        "--compiler",
        "mqt",
        "--target",
        "ibm_heron",
        "--seed",
        "42",
        "--benchmark-options",
        '{"degree": 2}',
        "--optimization-level",
        "1",
        "--save",
        "--target-directory",
        str(tmp_path),
        *extra_args,
    )
    assert result.success
    filename = "graphstate_nativegates_ibm_heron_mqt_3.qasm"
    assert filename in result.stdout
    exported = (tmp_path / filename).read_text()
    generation = json.loads(exported.split("// Generation options: ")[1].splitlines()[0])
    assert generation["options"] == {"seed": 42, "degree": 2}
    options = json.loads(exported.split("// Compiler options: ")[1].splitlines()[0])
    assert options["seed"] == seed
    assert options["mapping"]["trials"] == trials
    assert "// Compiler: mqt " in exported


@pytest.mark.parametrize(
    ("compiler", "level", "extra_args", "message"),
    [
        ("qiskit", "indep", ["--compiler-seed", "17"], "require --compiler mqt"),
        ("mqt", "alg", ["--mapping-trials", "2"], "require a compilation level"),
        ("mqt", "indep", ["--compiler-seed", "-1"], "--compiler-seed must be nonnegative"),
        ("mqt", "indep", ["--mapping-trials", "0"], "--mapping-trials must be positive"),
        ("mqt", "indep", ["--compiler-seed", str(2**64)], "is out of range"),
        ("mqt", "indep", ["--mapping-trials", str(2**64)], "is out of range"),
    ],
)
def test_mqt_cli_errors(
    script_runner: ScriptRunner, compiler: str, level: str, extra_args: list[str], message: str
) -> None:
    """Report invalid compiler controls as usage errors."""
    result = _generate(script_runner, level, "ghz", 3, "--compiler", compiler, *extra_args)
    assert result.returncode == 2
    assert message in result.stderr


def test_mqt_cli_compilation_failure(script_runner: ScriptRunner) -> None:
    """Report a Core synthesis failure as a CLI usage error."""
    result = _generate(script_runner, "nativegates", "qft", 4, "--compiler", "mqt", "--target", "clifford+t")
    assert result.returncode == 2
    assert "requires a single-qubit synthesis basis" in result.stderr
    assert not result.stdout


@pytest.mark.parametrize(
    ("flag", "expected"),
    [("--list-benchmarks", "qwalk: Quantum Walk"), ("--list-targets", "ibm_heron_156"), ("--help", "usage:")],
)
def test_cli_catalogue_and_help(flag: str, expected: str, script_runner: ScriptRunner) -> None:
    """Expose benchmark names, targets and version information."""
    ret = script_runner.run(["mqt-bench", flag])
    assert ret.success
    assert expected in ret.stdout
    if flag == "--help":
        assert "MQT Bench version:" in ret.stdout
        assert "Qiskit version:" in ret.stdout


@pytest.mark.parametrize("flag", ["--random-parameters", "--no-random-parameters"])
def test_cli_parameter_binding(flag: str, script_runner: ScriptRunner) -> None:
    """Forward binding options and the seed for an ansatz with symbolic parameters."""
    ret = _generate(script_runner, "indep", "vqe_real_amp", 2, "--seed", "42", flag)
    assert ret.success
    expected = get_benchmark(
        "vqe_real_amp", BenchmarkLevel.INDEP, 2, random_parameters=flag == "--random-parameters", seed=42
    )
    assert dumps(expected) in ret.stdout


def test_cli_benchmark_options(script_runner: ScriptRunner) -> None:
    """Forward JSON options to the selected benchmark."""
    ret = _generate(script_runner, "alg", "qwalk", 3, "--benchmark-options", '{"depth": 0}')
    assert ret.success
    assert dumps(create_circuit("qwalk", 3, depth=0)) in ret.stdout


@pytest.mark.parametrize(
    ("args", "expected_output"),
    [
        ([], "usage:"),
        (
            ["--level", "not-a-valid-level", "--algorithm", "ae", "--num-qubits", "20"],
            "invalid choice: 'not-a-valid-level' ",
        ),
        (
            ["--level", "alg", "--algorithm", "not-a-valid-benchmark", "--num-qubits", "20"],
            "invalid choice: 'not-a-valid-benchmark'",
        ),
        (
            ["--level", "nativegates", "--algorithm", "ghz", "--num-qubits", "20"],
            "--target is required when --level is 'nativegates'",
        ),
        (
            ["--level", "mapped", "--algorithm", "ghz", "--num-qubits", "20"],
            "--target is required when --level is 'mapped'",
        ),
        (
            ["--level", "mapped", "--algorithm", "ghz", "--num-qubits", "3", "--target", "unknown"],
            "not a supported device",
        ),
        (["--level", "alg", "--algorithm", "bv", "--num-qubits", "0"], "must be a positive integer"),
        (["--level", "alg", "--algorithm", "graphstate", "--num-qubits", "2"], "degree must satisfy"),
        (
            [
                "--level",
                "alg",
                "--algorithm",
                "bmw_quark_cardinality",
                "--num-qubits",
                "3",
                "--benchmark-options",
                '{"depth": -1}',
            ],
            "depth must be nonnegative",
        ),
        (["--benchmark-options", "{"], "--benchmark-options:"),
        (["--benchmark-options", "[]"], "must be a JSON object"),
        (
            ["--level", "alg", "--algorithm", "ghz", "--num-qubits", "3", "--benchmark-options", '{"unknown": 1}'],
            "unexpected keyword argument",
        ),
        (
            [
                "--level",
                "alg",
                "--algorithm",
                "ghz",
                "--num-qubits",
                "3",
                "--seed",
                "42",
                "--benchmark-options",
                '{"seed": 43}',
            ],
            "Specify the seed only once",
        ),
    ],
)
def test_cli_errors(args: list[str], expected_output: str, script_runner: ScriptRunner) -> None:
    """Test the CLI with different error cases."""
    ret = script_runner.run(["mqt-bench", *args])
    assert ret.returncode == 2
    assert expected_output in ret.stderr
    assert "Traceback" not in ret.stderr
    assert not ret.stdout


@pytest.mark.parametrize(
    ("algorithm", "size", "fmt"), [("ghz", 5, "qasm3"), ("shor", 18, "qasm2"), ("iqpe", 5, "qasm2")]
)
def test_cli_qasm_stdout(algorithm: str, size: int, fmt: str, script_runner: ScriptRunner) -> None:
    """Stream the chosen QASM format and report unsupported exports on stderr."""
    ret = _generate(script_runner, "alg", algorithm, size, "--output-format", fmt)
    if algorithm == "iqpe":
        assert ret.returncode == 1
        assert "Failed to write QASM stream" in ret.stderr
        assert "Traceback" not in ret.stderr
        return
    assert ret.success
    assert "// MQT Bench version:" in ret.stdout
    assert ("OPENQASM 3.0;" if fmt == "qasm3" else "OPENQASM 2.0;") in ret.stdout
    if algorithm == "ghz":
        assert dumps(create_circuit("ghz", size)) in ret.stdout
    assert not ret.stderr


def test_cli_qpy_save(tmp_path: Path, script_runner: ScriptRunner) -> None:
    """QPY always writes a file, even without --save."""
    directory = tmp_path / "new" / "circuits"
    ret = _generate(script_runner, "alg", "ghz", 5, "--output-format", "qpy", "--target-directory", str(directory))
    assert ret.success
    path = directory / "ghz_alg_5.qpy"
    assert ret.stdout.strip() == str(path)
    assert path.is_file()


@pytest.mark.parametrize(
    ("level", "target_name", "mirror"),
    [
        (BenchmarkLevel.NATIVEGATES, "ibm_heron", False),
        (BenchmarkLevel.MAPPED, "ibm_heron_156", False),
        (BenchmarkLevel.MAPPED, "ibm_heron_156", True),
    ],
)
def test_cli_targeted_save(
    level: BenchmarkLevel, target_name: str, *, mirror: bool, tmp_path: Path, script_runner: ScriptRunner
) -> None:
    """The saved filename and circuit reflect the target, optimization level and mirror flag."""
    level_name = level.name.lower()
    ret = _generate(
        script_runner,
        level_name,
        "ghz",
        5,
        "--output-format",
        "qasm2",
        "--optimization-level",
        "1",
        "--target",
        target_name,
        "--target-directory",
        str(tmp_path),
        "--save",
        *(["--mirror"] if mirror else []),
    )
    assert ret.success
    path = tmp_path / f"ghz_{level_name}{'_mirror' if mirror else ''}_{target_name}_opt1_5.qasm"
    assert ret.stdout.strip() == str(path)
    target = get_device(target_name) if level == BenchmarkLevel.MAPPED else get_target_for_gateset(target_name, 5)
    expected = get_benchmark("ghz", level, 5, target, 1, generate_mirror_circuit=mirror)
    assert qasm2.dumps(expected) in path.read_text(encoding="utf-8")


def test_cli_save_error(tmp_path: Path, script_runner: ScriptRunner) -> None:
    """A failed save returns a nonzero exit code and reports the export error."""
    target_dir = tmp_path / "occupied"
    target_dir.write_text("existing file")
    ret = _generate(script_runner, "alg", "ghz", 5, "--output-format", "qpy", "--target-directory", str(target_dir))
    assert ret.returncode == 1
    assert target_dir.name in ret.stderr
    assert "Traceback" not in ret.stderr
    assert not ret.stdout
    assert target_dir.read_text() == "existing file"


def test_cli_invalid_qir_profile(script_runner: ScriptRunner) -> None:
    """Reject an unknown QIR profile during argument parsing."""
    ret = _generate(script_runner, "alg", "ghz", 5, "--qir-profile", "invalid")
    assert ret.returncode == 2
    assert "invalid choice" in ret.stderr
