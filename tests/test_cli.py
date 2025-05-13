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

from mqt.bench import CompilerSettings, QiskitSettings, get_benchmark

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
             "--gateset", "ibm_falcon",
         ], dumps(get_benchmark(level="nativegates", benchmark_name="ghz", circuit_size=20, gateset="ibm_falcon"))),
        ([
             "--level", "mapped",
             "--algorithm", "ghz",
             "--num-qubits", "20",
             "--qiskit-optimization-level", "2",
             "--gateset", "ibm_falcon",
             "--device", "ibm_montreal",
         ], dumps(get_benchmark(
            level="mapped",
            benchmark_name="ghz",
            circuit_size=20,
            compiler_settings=CompilerSettings(QiskitSettings(optimization_level=2)),
            gateset="ibm_falcon",
            device_name="ibm_montreal",
        ))),
        ([
             "--level", "mapped",
             "--algorithm", "ghz",
             "--num-qubits", "20",
             "--qiskit-optimization-level", "2",
             "--device", "ibm_montreal",
         ], dumps(get_benchmark(
            level="mapped",
            benchmark_name="ghz",
            circuit_size=20,
            compiler_settings=CompilerSettings(QiskitSettings(optimization_level=2)),
            device_name="ibm_montreal",
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
