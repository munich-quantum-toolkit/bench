# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Module for the benchmark generation and benchmark retrieval."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import TYPE_CHECKING, Literal, overload

from qiskit import generate_preset_pass_manager
from qiskit.compiler import transpile
from qiskit.transpiler import Target

from .output import (
    OutputFormat,
    save_circuit,
)
from .targets.gatesets import get_target_for_gateset

if TYPE_CHECKING:  # pragma: no cover
    from types import ModuleType

    from qiskit.circuit import QuantumCircuit
    from qiskit.transpiler import Target

from dataclasses import dataclass


@dataclass
class QiskitSettings:
    """Data class for the Qiskit compiler settings."""

    optimization_level: int = 1


@dataclass
class CompilerSettings:
    """Data class for the compiler settings."""

    qiskit: QiskitSettings | None = None


def generate_filename(
    benchmark_name: str,
    level: str,
    num_qubits: int | None,
    target: Target | None = None,
    opt_level: int | None = None,
) -> str:
    """Generate a benchmark filename based on the abstraction level and context.

    Arguments:
        benchmark_name: name of the quantum circuit
        level: abstraction level
        num_qubits: number of qubits in the benchmark circuit
        target: target device (used for 'nativegates' and 'mapped')
        opt_level: optional optimization level (used for 'nativegates' and 'mapped')

    Returns:
        A string representing a filename (excluding extension) that encodes
        all relevant metadata for reproducibility and clarity.
    """
    base = f"{benchmark_name}_{level}"
    if level in {"nativegates", "mapped"}:
        assert opt_level is not None
        assert target is not None
        # sanitize the target.description to remove any special characters etc.
        description = target.description.strip().split(" ")[0]
        return f"{base}_{description}_opt{opt_level}_{num_qubits}"

    return f"{base}_{num_qubits}"


def get_alg_level(
    qc: QuantumCircuit,
    num_qubits: int | None,
    file_precheck: bool,
    return_qc: bool = False,
    target_directory: str = "./",
    target_filename: str = "",
    output_format: OutputFormat = OutputFormat.QASM3,
) -> bool | QuantumCircuit:
    """Handles the creation of the benchmark on the algorithm level.

    Arguments:
        qc: quantum circuit which the to be created benchmark circuit is based on
        num_qubits: number of qubits
        file_precheck: flag indicating whether to check whether the file already exists before creating it (again)
        return_qc: flag if the actual circuit shall be returned
        target_directory: alternative directory to the default one to store the created circuit
        target_filename: alternative filename to the default one
        output_format: one of supported formats, as defined in `OutputFormat`

    Returns:
        if return_qc == True: quantum circuit object
        else: True/False indicating whether the function call was successful or not
    """
    if return_qc:
        return qc

    if output_format == OutputFormat.QASM2:
        msg = "'qasm2' is not supported for the algorithm level; please use e.g. 'qasm3' or 'qpy'."
        raise ValueError(msg)

    filename_alg = target_filename or generate_filename(benchmark_name=qc.name, level="alg", num_qubits=num_qubits)
    path = Path(target_directory, f"{filename_alg}.{output_format.extension()}")

    if file_precheck and path.is_file():
        return True

    return save_circuit(
        qc=qc,
        filename=filename_alg,
        level="alg",
        output_format=output_format,
        target_directory=target_directory,
    )


@overload
def get_indep_level(
    qc: QuantumCircuit,
    num_qubits: int | None,
    file_precheck: bool,
    return_qc: Literal[True],
    target_directory: str = "./",
    target_filename: str = "",
    output_format: OutputFormat = OutputFormat.QASM3,
) -> QuantumCircuit: ...


@overload
def get_indep_level(
    qc: QuantumCircuit,
    num_qubits: int | None,
    file_precheck: bool,
    return_qc: Literal[False],
    target_directory: str = "./",
    target_filename: str = "",
    output_format: OutputFormat = OutputFormat.QASM3,
) -> bool: ...


def get_indep_level(
    qc: QuantumCircuit,
    num_qubits: int | None,
    file_precheck: bool,
    return_qc: bool = False,
    target_directory: str = "./",
    target_filename: str = "",
    output_format: OutputFormat = OutputFormat.QASM3,
) -> bool | QuantumCircuit:
    """Handles the creation of the benchmark on the target-independent level.

    Arguments:
        qc: quantum circuit which the to be created benchmark circuit is based on
        num_qubits: number of qubits
        file_precheck: flag indicating whether to check whether the file already exists before creating it (again)
        return_qc: flag if the actual circuit shall be returned
        target_directory: alternative directory to the default one to store the created circuit
        target_filename: alternative filename to the default one
        output_format: one of supported formats, as defined in `OutputFormat`

    Returns:
        if return_qc == True: quantum circuit object
        else: True/False indicating whether the function call was successful or not
    """
    filename_indep = target_filename or generate_filename(benchmark_name=qc.name, level="indep", num_qubits=num_qubits)
    path = Path(target_directory, f"{filename_indep}.{output_format.extension()}")

    if file_precheck and path.is_file():
        return True

    if return_qc:
        return qc

    return save_circuit(
        qc=qc,
        filename=filename_indep,
        level="indep",
        output_format=output_format,
        target_directory=target_directory,
    )


@overload
def get_native_gates_level(
    qc: QuantumCircuit,
    target: Target,
    num_qubits: int | None,
    opt_level: int,
    file_precheck: bool,
    return_qc: Literal[True],
    target_directory: str = "./",
    target_filename: str = "",
    output_format: OutputFormat = OutputFormat.QASM3,
) -> QuantumCircuit: ...


@overload
def get_native_gates_level(
    qc: QuantumCircuit,
    target: Target,
    num_qubits: int | None,
    opt_level: int,
    file_precheck: bool,
    return_qc: Literal[False],
    target_directory: str = "./",
    target_filename: str = "",
    output_format: OutputFormat = OutputFormat.QASM3,
) -> bool: ...


def get_native_gates_level(
    qc: QuantumCircuit,
    target: Target,
    num_qubits: int | None,
    opt_level: int,
    file_precheck: bool,
    return_qc: bool = False,
    target_directory: str = "./",
    target_filename: str = "",
    output_format: OutputFormat = OutputFormat.QASM3,
) -> bool | QuantumCircuit:
    """Handles the creation of the benchmark on the target-dependent native gates level.

    Arguments:
        qc: quantum circuit which the to be created benchmark circuit is based on
        target: defines the gate set
        num_qubits: number of qubits
        opt_level: optimization level
        file_precheck: flag indicating whether to check whether the file already exists before creating it (again)
        return_qc: flag if the actual circuit shall be returned
        target_directory: alternative directory to the default one to store the created circuit
        target_filename: alternative filename to the default one
        output_format: one of supported formats, as defined in `OutputFormat`

    Returns:
        if return_qc == True: quantum circuit object
        else: True/False indicating whether the function call was successful or not
    """
    filename_native = target_filename or generate_filename(
        benchmark_name=qc.name,
        level="native",
        num_qubits=num_qubits,
        target=target,
        opt_level=opt_level,
    )
    path = Path(target_directory, f"{filename_native}.{output_format.extension()}")

    if file_precheck and path.is_file():
        return True

    if target.description == "clifford+t":
        from qiskit.transpiler import PassManager  # noqa: PLC0415
        from qiskit.transpiler.passes.synthesis import SolovayKitaev  # noqa: PLC0415

        # Transpile the circuit to single- and two-qubit gates including rotations
        clifford_t_rotations = get_target_for_gateset("clifford+t+rotations", num_qubits=num_qubits)
        compiled_for_sk = transpile(
            qc,
            target=clifford_t_rotations,
            optimization_level=opt_level,
            seed_transpiler=10,
        )
        # Synthesize the rotations to Clifford+T gates
        # Measurements are removed and added back after the synthesis to avoid errors in the Solovay-Kitaev pass
        pm = PassManager(SolovayKitaev())
        qc = pm.run(compiled_for_sk.remove_final_measurements(inplace=False))
        qc.measure_all()

    pm = generate_preset_pass_manager(optimization_level=opt_level, target=target, seed_transpiler=10)
    pm.layout = None
    pm.routing = None
    pm.scheduling = None

    compiled = pm.run(qc)

    if return_qc:
        return compiled

    return save_circuit(
        qc=compiled,
        filename=filename_native,
        level="nativegates",
        output_format=output_format,
        target=target,
        target_directory=target_directory,
    )


@overload
def get_mapped_level(
    qc: QuantumCircuit,
    num_qubits: int | None,
    device: Target,
    opt_level: int,
    file_precheck: bool,
    return_qc: Literal[True],
    target_directory: str = "./",
    target_filename: str = "",
    output_format: OutputFormat = OutputFormat.QASM3,
) -> QuantumCircuit: ...


@overload
def get_mapped_level(
    qc: QuantumCircuit,
    num_qubits: int | None,
    device: Target,
    opt_level: int,
    file_precheck: bool,
    return_qc: Literal[False],
    target_directory: str = "./",
    target_filename: str = "",
    output_format: OutputFormat = OutputFormat.QASM3,
) -> bool: ...


def get_mapped_level(
    qc: QuantumCircuit,
    num_qubits: int | None,
    device: Target,
    opt_level: int,
    file_precheck: bool,
    return_qc: bool = False,
    target_directory: str = "./",
    target_filename: str = "",
    output_format: OutputFormat = OutputFormat.QASM3,
) -> bool | QuantumCircuit:
    """Handles the creation of the benchmark on the target-dependent mapped level.

    Arguments:
        qc: quantum circuit which the to be created benchmark circuit is based on
        num_qubits: number of qubits
        device: target device
        opt_level: optimization level
        file_precheck: flag indicating whether to check whether the file already exists before creating it (again)
        return_qc: flag if the actual circuit shall be returned
        target_directory: alternative directory to the default one to store the created circuit
        target_filename: alternative filename to the default one
        output_format: one of supported formats, as defined in `OutputFormat`

    Returns:
        if return_qc == True: quantum circuit object
        else: True/False indicating whether the function call was successful or not
    """
    filename_mapped = target_filename or generate_filename(
        benchmark_name=qc.name, level="mapped", num_qubits=num_qubits, target=device, opt_level=opt_level
    )
    path = Path(target_directory, f"{filename_mapped}.{output_format.extension()}")

    if file_precheck and path.is_file():
        return True

    compiled = transpile(
        qc,
        target=device,
        optimization_level=opt_level,
        seed_transpiler=10,
    )

    if return_qc:
        return compiled

    return save_circuit(
        qc=compiled,
        filename=filename_mapped,
        level="mapped",
        output_format=output_format,
        target=device,
        target_directory=target_directory,
    )


def get_benchmark(
    benchmark_name: str,
    level: str | int,
    circuit_size: int | None = None,
    benchmark_instance_name: str | None = None,
    compiler_settings: CompilerSettings | None = None,
    target: Target | None = None,
    **kwargs: str,
) -> QuantumCircuit:
    """Returns one benchmark as a qiskit.QuantumCircuit object.

    Arguments:
        benchmark_name: name of the to be generated benchmark
        level: Choice of level, either as a string ("alg", "indep", "nativegates" or "mapped") or as a number between 0-3 where 0 corresponds to "alg" level and 3 to "mapped" level
        circuit_size: Input for the benchmark creation, in most cases this is equal to the qubit number
        benchmark_instance_name: Input selection for some benchmarks, namely "shor"
        compiler_settings: Data class containing the respective compiler settings for the specified compiler (e.g., optimization level for Qiskit)
        target: Qiskit's Target for the benchmark generation (only used for "nativegates" and "mapped" level)
        kwargs: Additional arguments for the benchmark generation

    Returns:
        Qiskit::QuantumCircuit object representing the benchmark with the selected options
    """
    if benchmark_name not in get_supported_benchmarks():
        msg = f"Selected benchmark is not supported. Valid benchmarks are {get_supported_benchmarks()}."
        raise ValueError(msg)

    if level not in get_supported_levels():
        msg = f"Selected level must be in {get_supported_levels()}."
        raise ValueError(msg)

    if benchmark_name != "shor" and not (isinstance(circuit_size, int) and circuit_size > 0):
        msg = "circuit_size must be None or int for this benchmark."
        raise ValueError(msg)

    if benchmark_name == "shor" and not isinstance(benchmark_instance_name, str):
        msg = "benchmark_instance_name must be defined for this benchmark."
        raise ValueError(msg)

    lib = get_module_for_benchmark(
        benchmark_name.split("-")[0]
    )  # split is used to filter the ancillary mode for grover and qwalk

    if "grover" in benchmark_name or "qwalk" in benchmark_name:
        if "noancilla" in benchmark_name:
            anc_mode = "noancilla"
        elif "v-chain" in benchmark_name:
            anc_mode = "v-chain"
        else:
            msg = "Either `noancilla` or `v-chain` must be specified for ancillary mode of Grover and QWalk benchmarks."
            raise ValueError(msg)

        qc = lib.create_circuit(circuit_size, ancillary_mode=anc_mode)

    elif benchmark_name == "shor":
        to_be_factored_number, a_value = lib.get_instance(benchmark_instance_name)
        qc = lib.create_circuit(to_be_factored_number, a_value)

    else:
        qc = lib.create_circuit(circuit_size)

    if level in ("alg", 0):
        return qc

    if compiler_settings is None:
        compiler_settings = CompilerSettings(QiskitSettings())
    elif not isinstance(compiler_settings, CompilerSettings):
        msg = "compiler_settings must be of type CompilerSettings or None."  # type: ignore[unreachable]
        raise ValueError(msg)

    independent_level = 1
    if level in ("indep", independent_level):
        return get_indep_level(qc, circuit_size, False, True)

    native_gates_level = 2
    if level in ("nativegates", native_gates_level):
        assert compiler_settings.qiskit is not None
        opt_level = compiler_settings.qiskit.optimization_level
        return get_native_gates_level(qc, target, circuit_size, opt_level, False, True)

    mapped_level = 3
    if level in ("mapped", mapped_level):
        assert compiler_settings.qiskit is not None
        opt_level = compiler_settings.qiskit.optimization_level
        assert isinstance(opt_level, int)
        return get_mapped_level(
            qc,
            circuit_size,
            target,
            opt_level,
            False,
            True,
        )

    msg = f"Invalid level specified. Must be in {get_supported_levels()}."
    raise ValueError(msg)


def get_supported_benchmarks() -> list[str]:
    """Returns a list of all supported benchmarks."""
    return [
        "ae",
        "bv",
        "dj",
        "grover-noancilla",
        "grover-v-chain",
        "ghz",
        "graphstate",
        "qaoa",
        "qft",
        "qftentangled",
        "qnn",
        "qpeexact",
        "qpeinexact",
        "qwalk-noancilla",
        "qwalk-v-chain",
        "randomcircuit",
        "vqerealamprandom",
        "vqesu2random",
        "vqetwolocalrandom",
        "wstate",
        "shor",
    ]


def get_supported_levels() -> list[str | int]:
    """Returns a list of all supported benchmark levels."""
    return ["alg", "indep", "nativegates", "mapped", 0, 1, 2, 3]


def get_module_for_benchmark(benchmark_name: str) -> ModuleType:
    """Returns the module for a specific benchmark."""
    return import_module("mqt.bench.benchmarks." + benchmark_name)
