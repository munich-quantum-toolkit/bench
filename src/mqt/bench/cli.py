# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Command-line interface for generating benchmarks."""

from __future__ import annotations

import argparse
import sys
from importlib import metadata
from pathlib import Path

from mqt.bench.devices.devices import get_device_by_name
from mqt.bench.devices.gatesets import get_native_gateset_by_name

from . import CompilerSettings, QiskitSettings, get_benchmark
from .benchmark_generation import generate_filename
from .output import OutputFormat, save_circuit, write_circuit


class CustomArgumentParser(argparse.ArgumentParser):
    """Custom argument parser that includes version information in the help message."""

    def format_help(self) -> str:
        """Include version information in the help message."""
        help_message = super().format_help()
        version_info = (
            f"\nMQT Bench version: {metadata.version('mqt.bench')}\nQiskit version: {metadata.version('qiskit')}\n"
        )
        return help_message + version_info


def parse_benchmark_name_and_instance(algorithm: str) -> tuple[str, str | None]:
    """Parse an algorithm name like "shor_xlarge" into a benchmark and instance name."""
    if algorithm.startswith("shor_"):
        parts = algorithm.split("_", 1)
        return parts[0], parts[1]
    return algorithm, None


def main() -> None:
    """Generate a single benchmark and output in specified format."""
    parser = CustomArgumentParser(description="Generate a single benchmark")
    parser.add_argument(
        "--level",
        type=str,
        choices=["alg", "indep", "nativegates", "mapped"],
        help='Level to generate benchmarks for ("alg", "indep", "nativegates" or "mapped").',
        required=True,
    )
    parser.add_argument(
        "--algorithm",
        type=str,
        help="Name of the benchmark (e.g., 'grover-v-chain', 'shor_xsmall').",
        required=True,
    )
    parser.add_argument(
        "--num-qubits",
        type=int,
        help="Number of qubits for the benchmark.",
        required=True,
    )
    parser.add_argument(
        "--qiskit-optimization-level",
        type=int,
        help="Qiskit compiler optimization level (0-3).",
    )
    parser.add_argument(
        "--gateset",
        type=str,
        help="Used gateset (e.g., 'iqm', 'rigetti').",
    )
    parser.add_argument(
        "--device",
        type=str,
        help="Device name for mapping stage (e.g., 'ibm_washington').",
    )
    parser.add_argument(
        "--output-format",
        type=str,
        choices=[fmt.value for fmt in OutputFormat],
        default=OutputFormat.QASM3.value,
        help=f"Output format. Possible values: {[fmt.value for fmt in OutputFormat]}.",
    )
    parser.add_argument(
        "--target-directory",
        type=str,
        default=".",
        help="Directory to save the output file (only used for 'qpy' or if --save is specified).",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="If set, save the output to a file instead of printing to stdout (e.g. for 'qpy', which is not available as text).",
    )

    args = parser.parse_args()

    # Build Qiskit settings
    qiskit_settings = QiskitSettings()
    if args.qiskit_optimization_level is not None:
        qiskit_settings = QiskitSettings(args.qiskit_optimization_level)

    # Parse algorithm and optional instance
    benchmark_name, benchmark_instance = parse_benchmark_name_and_instance(args.algorithm)

    # Generate circuit
    circuit = get_benchmark(
        benchmark_name=benchmark_name,
        benchmark_instance_name=benchmark_instance,
        level=args.level,
        circuit_size=args.num_qubits,
        compiler_settings=CompilerSettings(qiskit=qiskit_settings),
        gateset=args.gateset or "ibm_falcon",
        device_name=args.device or "ibm_washington",
    )

    try:
        fmt = OutputFormat(args.output_format)
    except ValueError:
        msg = f"Unknown output format: {args.output_format}"
        raise ValueError(msg) from None

    # For QASM outputs, serialize and print
    if fmt in (OutputFormat.QASM2, OutputFormat.QASM3) and not args.save:
        write_circuit(circuit, sys.stdout, fmt)
        return

    if args.gateset is not None:
        target = get_native_gateset_by_name(args.gateset)
    elif args.device is not None:
        target = get_device_by_name(args.device)
    else:
        target = None

    # Otherwise, save to file
    filename = generate_filename(
        benchmark_name=benchmark_name,
        level=args.level,
        num_qubits=args.num_qubits,
        target=target,
        opt_level=args.qiskit_optimization_level,
    )
    success = save_circuit(
        qc=circuit,
        filename=filename,
        output_format=fmt,
        target_directory=args.target_directory,
    )
    if not success:
        sys.exit(1)

    # Optionally, inform user of file location if saving
    if args.save or fmt == OutputFormat.QPY:
        file_ext = fmt.extension()
        path = Path(args.target_directory) / f"{filename}.{file_ext}"
        print(path)


if __name__ == "__main__":
    main()
