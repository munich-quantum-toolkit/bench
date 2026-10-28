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
import json
import sys
from importlib import metadata
from io import TextIOBase
from pathlib import Path

from qiskit.exceptions import QiskitError

from mqt.bench.benchmarks import get_available_benchmark_names, get_benchmark_catalog
from mqt.bench.targets.devices import get_available_device_names, get_device
from mqt.bench.targets.gatesets import get_available_gateset_names, get_target_for_gateset

from .benchmark_generation import BenchmarkLevel, get_benchmark
from .output import MQTBenchExporterError, OutputFormat, generate_filename, save_circuit, write_circuit


def _benchmark_options(text: str) -> dict[str, object]:
    """Read a JSON object of options for the selected benchmark factory."""
    try:
        options = json.loads(text)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
    if not isinstance(options, dict):
        msg = "Benchmark options must be a JSON object."
        raise argparse.ArgumentTypeError(msg)
    return options


def main() -> None:
    """Generate a single benchmark and output in specified format."""
    parser = argparse.ArgumentParser(
        description="Generate a single benchmark",
        epilog=f"MQT Bench version: {metadata.version('mqt.bench')}\nQiskit version: {metadata.version('qiskit')}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--level",
        type=str,
        choices=["alg", "indep", "nativegates", "mapped"],
        help='Level to generate benchmarks for ("alg", "indep", "nativegates" or "mapped").',
    )
    parser.add_argument(
        "--algorithm",
        type=str,
        help="Name of the benchmark (e.g., 'grover', 'shor').",
        choices=get_available_benchmark_names(),
    )
    parser.add_argument(
        "--num-qubits",
        type=int,
        help="Number of qubits for the benchmark.",
    )
    parser.add_argument(
        "--compiler", choices=["qiskit", "mqt"], default="qiskit", help="Compiler to use (default: qiskit)."
    )
    parser.add_argument("--compiler-seed", type=int, help="MQT Core compilation seed (default: 10).")
    parser.add_argument("--mapping-trials", type=int, help="Number of MQT Core mapping trials (default: 4).")
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
        help=("Gate set name for nativegates (e.g., 'ibm_heron') or device name for mapped (e.g., 'ibm_heron_156')."),
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
    parser.add_argument(
        "--mirror",
        action="store_true",
        help="If set, generate the mirror version of the benchmark (circuit @ circuit.inverse()).",
    )

    catalogue = parser.add_mutually_exclusive_group()
    catalogue.add_argument("--list-benchmarks", action="store_true", help="List benchmarks and descriptions.")
    catalogue.add_argument("--list-targets", action="store_true", help="List native gate sets and mapped devices.")
    parser.add_argument("--seed", type=int, help="Seed for benchmark construction and random parameter values.")
    parser.add_argument(
        "--benchmark-options",
        type=_benchmark_options,
        default={},
        metavar="JSON",
        help='Benchmark-specific options as a JSON object, e.g. {"depth": 5, "for_loop": true}.',
    )

    args = parser.parse_args()

    if args.list_benchmarks:
        for name, description in sorted(get_benchmark_catalog().items()):
            print(f"{name}: {description}")
        return
    if args.list_targets:
        print("Gate sets:", *get_available_gateset_names(), sep="\n")
        print("Devices:", *get_available_device_names(), sep="\n")
        return

    missing = [
        f"--{name.replace('_', '-')}" for name in ("level", "algorithm", "num_qubits") if getattr(args, name) is None
    ]
    if missing:
        parser.error(f"the following arguments are required: {', '.join(missing)}")
    level = BenchmarkLevel[args.level.upper()]
    if level in (BenchmarkLevel.NATIVEGATES, BenchmarkLevel.MAPPED) and not args.target:
        parser.error(f"--target is required when --level is '{args.level}'.")

    if args.compiler == "mqt" and level != BenchmarkLevel.ALG and args.optimization_level != 2:
        parser.error("--compiler mqt requires --optimization-level 2.")

    compiler_options = None
    if args.compiler_seed is not None or args.mapping_trials is not None:
        if args.compiler != "mqt":
            parser.error("--compiler-seed and --mapping-trials require --compiler mqt.")
        if level == BenchmarkLevel.ALG:
            parser.error("--compiler-seed and --mapping-trials require a compilation level.")
        if args.compiler_seed is not None and args.compiler_seed < 0:
            parser.error("--compiler-seed must be nonnegative.")
        if args.mapping_trials is not None and args.mapping_trials < 1:
            parser.error("--mapping-trials must be positive.")
        from ._mqt_compiler import CompilationOptions, MappingOptions  # ruff:ignore[import-outside-top-level]

        compiler_options = CompilationOptions(
            seed=args.compiler_seed if args.compiler_seed is not None else 10,
            mapping=MappingOptions(trials=args.mapping_trials if args.mapping_trials is not None else 4),
        )

    options = dict(args.benchmark_options)
    if args.seed is not None:
        if "seed" in options:
            parser.error("Specify the seed only once.")
        options["seed"] = args.seed
    target = None
    try:
        if level in (BenchmarkLevel.NATIVEGATES, BenchmarkLevel.MAPPED):
            target = (
                get_device(args.target)
                if level == BenchmarkLevel.MAPPED
                else get_target_for_gateset(args.target, num_qubits=args.num_qubits)
            )
        circuit = get_benchmark(
            benchmark=args.algorithm,
            level=level,
            circuit_size=args.num_qubits,
            target=target,
            opt_level=args.optimization_level,
            compiler=args.compiler,
            compiler_options=compiler_options,
            generate_mirror_circuit=args.mirror,
            random_parameters=args.random_parameters,
            **options,
        )
    except (ValueError, TypeError, KeyError, QiskitError) as exc:
        parser.error(str(exc))

    fmt = OutputFormat(args.output_format)

    # For QASM outputs, serialize and print
    if fmt in (OutputFormat.QASM2, OutputFormat.QASM3) and not args.save:
        assert isinstance(sys.stdout, TextIOBase)
        try:
            write_circuit(circuit, sys.stdout, level, fmt, target)
        except MQTBenchExporterError as exc:
            print(exc, file=sys.stderr)
            sys.exit(1)
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
