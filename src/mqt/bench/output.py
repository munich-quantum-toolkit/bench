# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Output functions for the MQT Bench module."""

from __future__ import annotations

import datetime as dt
import json
import sys
from enum import StrEnum
from importlib import metadata
from io import TextIOBase
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, overload

from qiskit.qasm2 import dump as dump2
from qiskit.qasm3 import dump as dump3
from qiskit.qpy import dump as dump_qpy
from qiskit.version import __version__ as __qiskit_version__

from .benchmark_generation import BenchmarkLevel

if TYPE_CHECKING:  # pragma: no cover
    from typing import BinaryIO

    from qiskit.circuit import QuantumCircuit
    from qiskit.transpiler import Target


class OutputFormat(StrEnum):
    """Enumeration of supported output formats for circuit export."""

    QASM2 = "qasm2"
    QASM3 = "qasm3"
    QPY = "qpy"

    def extension(self) -> str:
        """Return the canonical filename extension for this format."""
        return "qasm" if self in (OutputFormat.QASM2, OutputFormat.QASM3) else self.value


class MQTBenchExporterError(Exception):
    """Custom exception for errors arising during MQT Bench exporting operations."""


def _attach_metadata(qc: QuantumCircuit, header: str) -> QuantumCircuit:
    """Copy the circuit and add the MQT Bench header to its metadata."""
    clone = qc.copy()
    clone.metadata = (clone.metadata or {}) | {"mqt_bench": header}
    return clone


def generate_header(
    fmt: OutputFormat,
    level: BenchmarkLevel,
    target: Target | None = None,
    *,
    generation_options: dict | None = None,
) -> str:
    """Generate a standardized header for MQT Bench outputs.

    Arguments:
        fmt: The chosen output format enum member
        level: The level of the circuit (e.g., "nativegates", "mapped")
        target: The transpilation target, if any.
        generation_options: Available generation and compilation settings.

    Returns:
        A string containing the formatted header.
    """
    try:
        version = metadata.version("mqt.bench")
    except Exception as exc:
        msg = (
            "The Python package `mqt.bench` is not installed in the current "
            "environment. Install it with\n\n"
            "    pip install mqt.bench\n\n"
            f"and try again. (Original error: {exc})"
        )
        raise MQTBenchExporterError(msg) from exc

    lines: list[str] = []
    lines.extend((
        f"// Benchmark created by MQT Bench on {dt.datetime.now(tz=dt.UTC).date()}",
        "// SPDX-License-Identifier: MIT",
        "// For more info: https://mqt-bench.app/",
        f"// MQT Bench version: {version}",
        f"// Qiskit version: {__qiskit_version__}",
        f"// Output format: {fmt.value}",
        f"// Level: {level.name.lower()}",
    ))

    if generation_options:
        lines.append(f"// Generation options: {json.dumps(generation_options, sort_keys=True)}")

    if level in {BenchmarkLevel.NATIVEGATES, BenchmarkLevel.MAPPED}:
        assert target is not None, "Target must be provided for nativegates or mapped level."
        lines.extend((
            f"// Target: {target.description}",
            f"// Used gateset: {list(target.operation_names)}",
        ))
        if level == BenchmarkLevel.MAPPED:
            c_map = target.build_coupling_map()
            edges = [list(edge) for edge in c_map.get_edges()] if c_map else "all-to-all"
            lines.append(f"// Coupling map: {edges}")

    return "\n".join(lines) + "\n\n"


def _write_file_atomically(
    qc: QuantumCircuit, destination: Path, level: BenchmarkLevel, fmt: OutputFormat, target: Target | None
) -> None:
    """Serialize beside the destination, then replace it after a successful write."""
    with TemporaryDirectory(dir=destination.parent) as directory:
        temporary = Path(directory) / destination.name
        with temporary.open("wb") if fmt is OutputFormat.QPY else temporary.open("w", encoding="utf-8") as stream:
            write_circuit(qc, stream, level, fmt, target)
        if destination.exists():
            temporary.chmod(destination.stat().st_mode)
        temporary.replace(destination)


@overload
def write_circuit(
    qc: QuantumCircuit,
    destination: Path,
    level: BenchmarkLevel,
    fmt: OutputFormat = OutputFormat.QASM3,
    target: Target | None = None,
) -> None:  # pragma: no cover - typing overload only
    ...


@overload
def write_circuit(
    qc: QuantumCircuit,
    destination: TextIOBase | BinaryIO,
    level: BenchmarkLevel,
    fmt: OutputFormat = OutputFormat.QASM3,
    target: Target | None = None,
) -> None:  # pragma: no cover - typing overload only
    ...


def write_circuit(
    qc: QuantumCircuit,
    destination: Path | TextIOBase | BinaryIO,
    level: BenchmarkLevel,
    fmt: OutputFormat = OutputFormat.QASM3,
    target: Target | None = None,
) -> None:
    """Write the given quantum circuit to disk in the specified format, preceded by an MQT Bench header.

    Arguments:
        qc: The QuantumCircuit to export
        destination: Destination file path or stream (including extension)
        level: The level of the circuit (e.g., BenchmarkLevel.MAPPED)
        fmt: Desired output format
        target: The target circuit to be transpiled, if any.

    Raises:
        MQTBenchExporterError: On unsupported format or I/O errors.
    """
    if isinstance(destination, Path):
        try:
            _write_file_atomically(qc, destination, level, fmt, target)
        except Exception as exc:
            msg = f"Failed to write {fmt.value.upper()} file to {destination}. (Original error: {exc})"
            raise MQTBenchExporterError(msg) from exc
        return

    generation = (qc.metadata or {}).get("mqt_bench_generation")
    header = generate_header(
        fmt, level, target, generation_options=generation if isinstance(generation, dict) else None
    )

    compiler_info = (qc.metadata or {}).get("mqt_bench_compiler")
    if compiler_info is not None:
        header += f"// Compiler: {compiler_info['name']} {compiler_info['version']}\n\n"

    if fmt in (OutputFormat.QASM2, OutputFormat.QASM3):
        if not isinstance(destination, TextIOBase):
            msg = "QASM output requires a *text* stream."
            raise MQTBenchExporterError(msg)
        try:
            destination.write(header)
            (dump2 if fmt is OutputFormat.QASM2 else dump3)(qc, destination)
        except Exception as exc:  # pragma: no cover - unforeseen I/O
            msg = f"Failed to write QASM stream. (Original error: {exc})"
            raise MQTBenchExporterError(msg) from exc
        return

    if fmt is OutputFormat.QPY:
        if isinstance(destination, TextIOBase):
            msg = "QPY output requires a *binary* stream."
            raise MQTBenchExporterError(msg)
        try:
            dump_qpy(_attach_metadata(qc, header), destination)
        except Exception as exc:
            msg = f"Failed to write QPY stream. (Original error: {exc})"
            raise MQTBenchExporterError(msg) from exc
        return

    msg = f"Unsupported output format {fmt}. Supported formats are {[m.value for m in OutputFormat]}."
    raise MQTBenchExporterError(msg)


def save_circuit(
    qc: QuantumCircuit,
    filename: str,
    level: BenchmarkLevel,
    output_format: OutputFormat = OutputFormat.QASM3,
    target: Target | None = None,
    target_directory: str = "",
) -> bool:
    """Public API to save a quantum circuit in various formats with MQT Bench header.

    Arguments:
        qc: Circuit to export
        filename: Base filename without extension
        level: Level of the circuit (e.g., BenchmarkLevel.MAPPED)
        output_format: One of the supported format values, as defined in `OutputFormat`
        target: Target circuit to be transpiled, if any
        target_directory: Directory to place the output file

    Returns:
        True on success, False otherwise.
    """
    path = Path(target_directory) / f"{filename}.{output_format.extension()}"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        write_circuit(qc, path, level, output_format, target)
    except (MQTBenchExporterError, OSError) as e:
        print(e, file=sys.stderr)
        return False

    return True


def generate_filename(
    benchmark_name: str,
    level: BenchmarkLevel,
    num_qubits: int | None,
    target: Target | None = None,
    opt_level: int | None = None,
    generate_mirror_circuit: bool = False,
    *,
    compiler: str = "qiskit",
) -> str:
    """Generate a benchmark filename based on the abstraction level and context.

    Arguments:
        benchmark_name: name of the quantum circuit
        level: abstraction level
        num_qubits: number of qubits in the benchmark circuit
        target: target device (e.g., BenchmarkLevel.MAPPED)
        opt_level: optional optimization level (used for 'nativegates' and 'mapped')
        generate_mirror_circuit: whether this is a mirror circuit
        compiler: Compiler name. MQT filenames omit the Qiskit optimization level.

    Returns:
        A filename without an extension, containing the benchmark name, level,
        size, and compilation settings. Factory options are stored in the circuit
        metadata and export header.
    """
    base = f"{benchmark_name}_{level.name.lower()}{'_mirror' if generate_mirror_circuit else ''}"

    if compiler not in {"qiskit", "mqt"}:
        msg = f"Unknown compiler '{compiler}'. Choose 'qiskit' or 'mqt'."
        raise ValueError(msg)
    if compiler == "mqt" and level != BenchmarkLevel.ALG:
        if level in {BenchmarkLevel.NATIVEGATES, BenchmarkLevel.MAPPED}:
            assert target is not None, "target is required for native or mapped filenames."
            base += f"_{target.description.strip().split(' ')[0]}"
        return f"{base}_mqt_{num_qubits}"

    if level == BenchmarkLevel.INDEP:
        assert opt_level is not None, "opt_level is required for 'indep' level filenames."
        return f"{base}_opt{opt_level}_{num_qubits}"

    if level in {BenchmarkLevel.NATIVEGATES, BenchmarkLevel.MAPPED}:
        assert opt_level is not None, f"opt_level is required for '{level.name.lower()}' level filenames."
        assert target is not None, f"target is required for '{level.name.lower()}' level filenames."
        # sanitize the target.description to remove any special characters etc.
        description = target.description.strip().split(" ")[0]
        return f"{base}_{description}_opt{opt_level}_{num_qubits}"

    return f"{base}_{num_qubits}"
