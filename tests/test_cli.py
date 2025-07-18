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

from mqt.bench.benchmark_generation import BenchmarkLevel, get_benchmark
from mqt.bench.targets import get_device, get_target_for_gateset

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
         ], dumps(get_benchmark(level=BenchmarkLevel.ALG, benchmark="ghz", circuit_size=10))),
        ([
             "--level", "alg",
             "--algorithm", "shor",
             "--num-qubits", "18",
            "--output-format", "qasm2",
         ], "OPENQASM 2.0;"),  # Note: shor is non-deterministic, so just a basic sanity check
        ([
             "--level", "alg",
             "--algorithm", "ghz",
             "--num-qubits", "20",
             "--random-parameters"
         ], dumps(get_benchmark(level=BenchmarkLevel.ALG, benchmark="ghz", circuit_size=20, random_parameters=True))),
        ([
             "--level", "indep",
             "--algorithm", "ghz",
             "--num-qubits", "20",
             "--optimization-level", "2",
             "--no-random-parameters"
         ], dumps(get_benchmark(level=BenchmarkLevel.INDEP, benchmark="ghz", circuit_size=20, opt_level=2, random_parameters=False))),
        ([
             "--level", "nativegates",
             "--algorithm", "ghz",
             "--num-qubits", "20",
            "--optimization-level", "2",
             "--target", "ibm_falcon",
         ], dumps(get_benchmark(level=BenchmarkLevel.NATIVEGATES, benchmark="ghz", circuit_size=20, target=get_target_for_gateset("ibm_falcon", 20), opt_level=2))),
        ([
             "--level", "mapped",
             "--algorithm", "ghz",
             "--num-qubits", "20",
             "--optimization-level", "2",
             "--target", "ibm_falcon_27",
         ], dumps(get_benchmark(
            level=BenchmarkLevel.MAPPED,
            benchmark="ghz",
            circuit_size=20,
            opt_level=2,
            target=get_device("ibm_falcon_27"),
        ))),
                ([
            "--level", "alg",
            "--algorithm", "ghz",
            "--num-qubits", "3",
            "--mirror",
        ], dumps(get_benchmark(level=BenchmarkLevel.ALG, benchmark="ghz", circuit_size=3, generate_mirror_circuit=True))),

        ([
            "--level", "mapped",
            "--algorithm", "ghz",
            "--num-qubits", "3",
            "--optimization-level", "0",
            "--target", "ibm_falcon_27",
            "--mirror",
        ], dumps(get_benchmark(
            level=BenchmarkLevel.MAPPED,
            benchmark="ghz",
            circuit_size=3,
            opt_level=0,
            target=get_device("ibm_falcon_27"),
            generate_mirror_circuit=True,
        ))),
        (["--help"], "usage: mqt-bench"),
    ],
)
def test_cli(args: list[str], expected_output: str, script_runner: ScriptRunner) -> None:
    """Test the CLI with different arguments."""
    ret = script_runner.run(["mqt-bench", *args])
    assert ret.success
    assert expected_output in ret.stdout


# fmt: off
@pytest.mark.parametrize(
    ("args", "expected_output"),
    [
        ([], "usage: mqt-bench"),
        (["asd"], "usage: mqt-bench"),
        (["--benchmark", "ae"], "usage: mqt-bench"),
        # Note: We don't care about the actual error messages in most cases
        ([
             "--level", "not-a-valid-level",
             "--algorithm", "ae",
             "--num-qubits", "20",
         ], "invalid choice: 'not-a-valid-level' "),
        ([
             "--level", "alg",
             "--algorithm", "not-a-valid-benchmark",
             "--num-qubits", "20",
         ], ""),
    ],
)
def test_cli_errors(args: list[str], expected_output: str, script_runner: ScriptRunner) -> None:
    """Test the CLI with different error cases."""
    ret = script_runner.run(["mqt-bench", *args])
    assert not ret.success
    assert expected_output in ret.stderr


def _run_cli(script_runner: ScriptRunner, extra_args: list[str]) -> ScriptResult:
    """Run *mqt-bench* with default GHZ/ALG/5 settings plus *extra_args*."""
    cmd = ["mqt-bench", "--level", "alg", "--algorithm", "ghz", "--num-qubits", "5", *extra_args]
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


def test_cli_nativegates_qasm2_save(tmp_path: Path, script_runner: ScriptRunner) -> None:
    """QASM2 file should be saved for nativegates level when --save is specified."""
    target_dir = str(tmp_path)
    ret = script_runner.run(
        [
            "mqt-bench",
            "--level", "nativegates",
            "--algorithm", "ghz",
            "--num-qubits", "5",
            "--target", "ibm_falcon",
            "--optimization-level", "1",
            "--output-format", "qasm2",
            "--save",
            "--target-directory", target_dir,
        ]
    )
    assert ret.success
    expected_path = Path(target_dir) / "ghz_nativegates_ibm_falcon_opt1_5.qasm"
    assert str(expected_path) in ret.stdout.strip().splitlines()[-1]
    assert expected_path.is_file()


def test_cli_mapped_qasm2_save(tmp_path: Path, script_runner: ScriptRunner) -> None:
    """QASM2 file should be saved for mapped level when --save is specified."""
    target_dir = str(tmp_path)
    ret = script_runner.run(
        [
            "mqt-bench",
            "--level", "mapped",
            "--algorithm", "ghz",
            "--num-qubits", "5",
            "--target", "ibm_falcon_27",
            "--optimization-level", "1",
            "--output-format", "qasm2",
            "--save",
            "--target-directory", target_dir,
        ]
    )
    assert ret.success
    expected_path = Path(target_dir) / "ghz_mapped_ibm_falcon_27_opt1_5.qasm"
    assert str(expected_path) in ret.stdout.strip().splitlines()[-1]
    assert expected_path.is_file()
