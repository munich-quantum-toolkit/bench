# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
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
from io import TextIOBase
from pathlib import Path

from mqt.bench.targets.devices import get_device
from mqt.bench.targets.gatesets import get_target_for_gateset

from .benchmark_generation import BenchmarkLevel, get_benchmark
from .output import OutputFormat, generate_filename, save_circuit, write_circuit


class CustomArgumentParser(argparse.ArgumentParser):
    """Custom argument parser that includes version information in the help message."""

    def format_help(self) -> str:
        """Include version information in the help message."""
        help_message = super().format_help()
        version_info = (
            f"\nMQT Bench version: {metadata.version('mqt.bench')}\nQiskit version: {metadata.version('qiskit')}\n"
        )
        return help_message + version_info


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
        help="Name of the benchmark (e.g., 'grover', 'shor').",
        required=True,
    )
    parser.add_argument(
        "--num-qubits",
        type=int,
        help="Number of qubits for the benchmark.",
        required=True,
    )
    parser.add_argument(
        "--compiler", choices=["qiskit", "mqt"], default="qiskit", help="Compiler to use (default: qiskit)."
    )
    parser.add_argument(
        "--optimization-level",
        type=int,
        choices=range(4),
        default=2,
        help="Qiskit optimization level (0-3, default: 2). The MQT compiler requires the default value 2.",
    )
    parser.add_argument(
        "--target",
        type=str,
        help="Target name for native gates and mapped level (e.g., 'ibm_falcon' or 'ibm_washington').",
    )
    parser.add_argument(
        "--random-parameters",
        dest="random_parameters",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Whether to assign random parameters to parametric circuits (default: True). Use --no-random-parameters to disable.",
    )
    parser.add_argument(
        "--output-format",
        type=str,
        choices=[fmt.value for fmt in OutputFormat],
        default=OutputFormat.QASM3.value,
        help=f"Output format. Possible values: {[fmt.value for fmt in OutputFormat]}.",
    )
    parser.add_argument(
        "--qir-profile",
        choices=["base", "adaptive"],
        default="base",
        help="Profile for QIR/LLVM output (default: base). Use adaptive for measurement feedback.",
    )
    parser.add_argument(
        "--target-directory",
        type=str,
        default=".",
        help="Directory to save the output file (used for binary formats or if --save is specified).",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="If set, save the output to a file instead of printing to stdout (e.g. for 'qpy', which is not available as text).",
    )
    parser.add_argument(
        "--mirror",
        action="store_true",
        help="If set, generate the mirror version of the benchmark (circuit @ circuit.inverse()).",
    )

    args = parser.parse_args()

    if args.level == "alg":
        level = BenchmarkLevel.ALG
    elif args.level == "indep":
        level = BenchmarkLevel.INDEP
    elif args.level == "nativegates":
        level = BenchmarkLevel.NATIVEGATES
    else:
        level = BenchmarkLevel.MAPPED

    if level == BenchmarkLevel.NATIVEGATES:
        target = get_target_for_gateset(args.target, num_qubits=args.num_qubits)
    elif level == BenchmarkLevel.MAPPED:
        target = get_device(args.target)
    else:
        target = None

    # Generate circuit
    circuit = get_benchmark(
        benchmark=args.algorithm,
        level=level,
        circuit_size=args.num_qubits,
        target=target,
        opt_level=args.optimization_level,
        compiler=args.compiler,
        generate_mirror_circuit=args.mirror,
        random_parameters=args.random_parameters,
    )

    try:
        fmt = OutputFormat(args.output_format)
    except ValueError:
        msg = f"Unknown output format: {args.output_format}"
        raise ValueError(msg) from None

    # Text formats stream to stdout unless saving is requested.
    if fmt not in (OutputFormat.QPY, OutputFormat.QIR_BITCODE) and not args.save:
        assert isinstance(sys.stdout, TextIOBase)
        write_circuit(circuit, sys.stdout, level, fmt, target, qir_profile=args.qir_profile)
        return

    # Otherwise, save to file
    filename = generate_filename(
        benchmark_name=args.algorithm,
        level=level,
        num_qubits=args.num_qubits,
        target=target,
        opt_level=args.optimization_level,
        compiler=args.compiler,
        generate_mirror_circuit=args.mirror,
    )
    success = save_circuit(
        qc=circuit,
        filename=filename,
        level=level,
        output_format=fmt,
        target=target,
        target_directory=args.target_directory,
        qir_profile=args.qir_profile,
    )
    if not success:
        sys.exit(1)

    # Optionally, inform user of file location if saving
    if args.save or fmt in (OutputFormat.QPY, OutputFormat.QIR_BITCODE):
        file_ext = fmt.extension()
        path = Path(args.target_directory) / f"{filename}.{file_ext}"
        print(path)


if __name__ == "__main__":
    main()
