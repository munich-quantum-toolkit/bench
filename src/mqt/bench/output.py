# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Output functions for the MQT Bench module."""

from __future__ import annotations

from datetime import date
from enum import Enum
from importlib import metadata
from io import TextIOBase
from pathlib import Path
from typing import TYPE_CHECKING, TextIO, overload

from qiskit import __version__ as __qiskit_version__
from qiskit.qasm2 import dump as dump2
from qiskit.qasm3 import dump as dump3
from qiskit.qpy import dump as dump_qpy

from .benchmark_generation import BenchmarkLevel

if TYPE_CHECKING:  # pragma: no cover
    from typing import BinaryIO

    from qiskit.circuit import QuantumCircuit
    from qiskit.transpiler import Target


class OutputFormat(str, Enum):
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
    """Return *a shallow copy* whose ``metadata`` carries the MQT-Bench header."""
    clone = qc.copy()
    clone.metadata = (clone.metadata or {}) | {"mqt_bench": header}
    return clone


def generate_header(
    fmt: OutputFormat,
    level: BenchmarkLevel,
    target: Target | None = None,
) -> str:
    """Generate a standardized header for MQT Bench outputs.

    Arguments:
        fmt: The chosen output format enum member
        level: The level of the circuit (e.g., "nativegates", "mapped")
        target: The transpilation target, if any.

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
        raise MQTBenchExporterError(msg) from None

    lines: list[str] = []
    lines.extend((
        f"// Benchmark created by MQT Bench on {date.today()}",
        "// For more info: https://www.cda.cit.tum.de/mqtbench/",
        f"// MQT Bench version: {version}",
        f"// Qiskit version: {__qiskit_version__}",
        f"// Output format: {fmt.value}",
    ))

    if level in {BenchmarkLevel.NATIVEGATES, BenchmarkLevel.MAPPED}:
        assert target is not None, "Target must be provided for nativegates or mapped level."
        lines.extend((
            f"// Level: {level.name.lower()}",
            f"// Target: {target.description}",
            f"// Used gateset: {list(target.operation_names)}",
        ))
        if level == BenchmarkLevel.MAPPED:
            c_map = target.build_coupling_map()
            lines.append(f"// Coupling map: {c_map or 'all-to-all'}")

    return "\n".join(lines) + "\n\n"


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
    destination: TextIO | BinaryIO,
    level: BenchmarkLevel,
    fmt: OutputFormat = OutputFormat.QASM3,
    target: Target | None = None,
) -> None:  # pragma: no cover - typing overload only
    ...


def write_circuit(
    qc: QuantumCircuit,
    destination: Path | TextIO | BinaryIO,
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
    header = generate_header(fmt, level, target)

    if not isinstance(destination, Path):
        is_text = isinstance(destination, TextIOBase)

        if fmt in (OutputFormat.QASM2, OutputFormat.QASM3):
            if not is_text:
                msg = "QASM output requires a *text* stream."
                raise MQTBenchExporterError(msg)
            try:
                assert isinstance(destination, TextIOBase)
                destination.write(header)
                (dump2 if fmt is OutputFormat.QASM2 else dump3)(qc, destination)
            except Exception as exc:  # pragma: no cover - unforeseen I/O
                msg = f"Failed to write QASM stream. (Original error: {exc})"
                raise MQTBenchExporterError(msg) from None
            return

        if fmt is OutputFormat.QPY:
            if is_text:
                msg = "QPY output requires a *binary* stream."
                raise MQTBenchExporterError(msg)
            try:
                dump_qpy(_attach_metadata(qc, header), destination)
            except Exception as exc:
                msg = f"Failed to write QPY stream. (Original error: {exc})"
                raise MQTBenchExporterError(msg) from None
            return

        msg = f"Unsupported output format {fmt}. Supported formats are {[m.value for m in OutputFormat]}."
        raise MQTBenchExporterError(msg)

    if fmt in (OutputFormat.QASM2, OutputFormat.QASM3):
        try:
            with destination.open("w", encoding="utf-8") as f:
                f.write(header)
                (dump2 if fmt is OutputFormat.QASM2 else dump3)(qc, f)
        except Exception as exc:
            msg = f"Failed to write {fmt.value.upper()} file to {destination}. (Original error: {exc})"
            raise MQTBenchExporterError(msg) from None

    elif fmt is OutputFormat.QPY:
        try:
            with destination.open("wb") as f:
                dump_qpy(_attach_metadata(qc, header), f)
        except Exception as exc:
            msg = f"Failed to write QPY file to {destination}. (Original error: {exc})"
            raise MQTBenchExporterError(msg) from None

    else:
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
        write_circuit(qc, path, level, output_format, target)
    except MQTBenchExporterError as e:
        print(e)
        return False

    return True


def generate_filename(
    benchmark_name: str,
    level: BenchmarkLevel,
    num_qubits: int | None,
    target: Target | None = None,
    opt_level: int | None = None,
    generate_mirror_circuit: bool = False,
) -> str:
    """Generate a benchmark filename based on the abstraction level and context.

    Arguments:
        benchmark_name: name of the quantum circuit
        level: abstraction level
        num_qubits: number of qubits in the benchmark circuit
        target: target device (e.g., BenchmarkLevel.MAPPED)
        opt_level: optional optimization level (used for 'nativegates' and 'mapped')
        generate_mirror_circuit: whether this is a mirror circuit

    Returns:
        A string representing a filename (excluding extension) that encodes
        all relevant metadata for reproducibility and clarity.
    """
    base = f"{benchmark_name}_{level.name.lower()}{'_mirror' if generate_mirror_circuit else ''}"

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
