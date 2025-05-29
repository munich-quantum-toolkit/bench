# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Module for the benchmark generation and benchmark retrieval."""

from __future__ import annotations

from enum import Enum, auto
from importlib import import_module
from typing import TYPE_CHECKING, overload

from qiskit import generate_preset_pass_manager
from qiskit.circuit import QuantumCircuit, SessionEquivalenceLibrary
from qiskit.compiler import transpile
from qiskit.transpiler import Target, TranspileLayout
from typing_extensions import assert_never

from .targets.gatesets import get_target_for_gateset, ionq, rigetti

if TYPE_CHECKING:  # pragma: no cover
    from types import ModuleType

    from qiskit.transpiler import Target


class BenchmarkLevel(Enum):
    """Enum representing different levels."""

    ALG = auto()
    INDEP = auto()
    NATIVEGATES = auto()
    MAPPED = auto()


def get_supported_benchmarks() -> list[str]:
    """Returns a list of all supported benchmarks."""
    return [
        "ae",
        "bv",
        "dj",
        "ghz",
        "graphstate",
        "grover",
        "hhl",
        "qaoa",
        "qft",
        "qftentangled",
        "qnn",
        "qpeexact",
        "qpeinexact",
        "quarkcardinality",
        "quarkcopula",
        "qwalk",
        "randomcircuit",
        "shor",
        "vqerealamprandom",
        "vqesu2random",
        "vqetwolocalrandom",
        "wstate",
    ]


def get_module_for_benchmark(benchmark_name: str) -> ModuleType:
    """Returns the module for a specific benchmark."""
    return import_module("mqt.bench.benchmarks." + benchmark_name)


def _get_circuit(
    benchmark: str | QuantumCircuit,
    circuit_size: int | None,
) -> QuantumCircuit:
    """Creates a raw quantum circuit based on the specified benchmark.

    This function generates a quantum circuit according to the specifications of the
    desired benchmark.

    Arguments:
        benchmark: Name of the benchmark for which the circuit is to be created.
        circuit_size: Size of the circuit to be created, required for benchmarks other than "shor".

    Returns:
        QuantumCircuit: Constructed quantum circuit based on the given parameters.
    """
    if isinstance(benchmark, QuantumCircuit):
        if circuit_size is not None:
            msg = "`circuit_size` must be omitted or None when `benchmark` is a QuantumCircuit."
            raise ValueError(msg)
        return benchmark

    if circuit_size is None or circuit_size <= 0:
        msg = "`circuit_size` must be a positive integer when `benchmark` is a str."
        raise ValueError(msg)

    if benchmark not in get_supported_benchmarks():
        msg = f"'{benchmark}' is not a supported benchmark. Valid names: {get_supported_benchmarks()}"
        raise ValueError(msg)

    lib = get_module_for_benchmark(benchmark)
    return lib.create_circuit(circuit_size)


def _create_mirror_circuit(qc_original: QuantumCircuit, inplace: bool = False) -> QuantumCircuit:
    """Generates the mirror version (qc @ qc.inverse()) of a given quantum circuit.

    Measurements from the original circuit are preserved. For circuits with an
    initial layout (e.g., mapped circuits), this function ensures that the
    final layout of the mirrored circuit matches the initial layout of the
    original circuit. While Qiskit's `inverse()` and `compose()` methods
    handle layout transformations internally, explicit steps are taken here
    to meet this specific final layout requirement.

    Args:
        qc_original: The quantum circuit to mirror.
        inplace: If True, modifies the circuit in place. Otherwise, returns a new circuit.

    Returns:
        The mirrored quantum circuit.
    """
    target_qc = qc_original if inplace else qc_original.copy()

    # --- Layout Handling ---
    original_transpile_layout_obj = None
    original_initial_virtual_layout = None

    if hasattr(qc_original, "layout") and qc_original.layout is not None:
        original_transpile_layout_obj = qc_original.layout
        if hasattr(original_transpile_layout_obj, "initial_layout"):
            original_initial_virtual_layout = original_transpile_layout_obj.initial_layout

    # Modifying .data can strip layout.
    stored_measurements = []
    new_data_unitary_part = []

    for instruction_context in target_qc.data:
        if instruction_context.operation.name == "measure":
            stored_measurements.append(instruction_context)
        else:
            new_data_unitary_part.append(instruction_context)
    target_qc.data = new_data_unitary_part

    # If layout was stripped and an original layout existed, re-establish the initial part.
    if (
        original_transpile_layout_obj is not None
        and target_qc.layout is None
        and original_initial_virtual_layout is not None
    ):
        target_qc.layout = TranspileLayout(initial_layout=original_initial_virtual_layout)

    qc_inv = target_qc.inverse()

    target_qc.barrier()
    target_qc.compose(qc_inv, inplace=True)
    target_qc.name = f"{target_qc.name}_mirror"

    # --- Ensure Final Layout of Mirror Circuit ---
    if original_initial_virtual_layout is not None:
        if target_qc.layout is None:
            target_qc.layout = TranspileLayout(
                initial_layout=original_initial_virtual_layout, final_layout=original_initial_virtual_layout
            )
        else:
            # The TranspileLayout object exists. We assume its .initial_layout is correct.
            target_qc.layout.final_layout = original_initial_virtual_layout

    # Re-apply stored measurements
    for measure_instruction_context in stored_measurements:
        target_qc.append(measure_instruction_context)

    return target_qc


def _validate_opt_level(opt_level: int) -> None:
    """Validate optimization level.

    Arguments:
        opt_level: User-defined optimization level.
    """
    if not 0 <= opt_level <= 3:
        msg = f"Invalid `opt_level` '{opt_level}'. Must be in the range [0, 3]."
        raise ValueError(msg)


@overload
def get_benchmark_alg(
    benchmark: str,
    circuit_size: int,
    generate_mirror_circuit: bool = False,
) -> QuantumCircuit: ...


@overload
def get_benchmark_alg(
    benchmark: QuantumCircuit,
    circuit_size: None = None,
    generate_mirror_circuit: bool = False,
) -> QuantumCircuit: ...


def get_benchmark_alg(
    benchmark: str | QuantumCircuit,
    circuit_size: int | None = None,
    generate_mirror_circuit: bool = False,
) -> QuantumCircuit:
    """Return an algorithm-level benchmark circuit.

    Arguments:
            benchmark: QuantumCircuit or name of the benchmark to be generated
            circuit_size: Input for the benchmark creation, in most cases this is equal to the qubit number
            generate_mirror_circuit: If True, generates the mirror version (U @ U.inverse()) of the benchmark.

    Returns:
            Qiskit::QuantumCircuit representing the raw benchmark circuit without any hardware-specific compilation or mapping.
    """
    qc = _get_circuit(benchmark, circuit_size)
    if generate_mirror_circuit:
        return _create_mirror_circuit(qc, inplace=False)
    return qc


@overload
def get_benchmark_indep(
    benchmark: str,
    circuit_size: int,
    opt_level: int = 2,
    generate_mirror_circuit: bool = False,
) -> QuantumCircuit: ...


@overload
def get_benchmark_indep(
    benchmark: QuantumCircuit,
    circuit_size: None = None,
    opt_level: int = 2,
    generate_mirror_circuit: bool = False,
) -> QuantumCircuit: ...


def get_benchmark_indep(
    benchmark: str | QuantumCircuit,
    circuit_size: int | None = None,
    opt_level: int = 2,
    generate_mirror_circuit: bool = False,
) -> QuantumCircuit:
    """Return a target-independent benchmark circuit.

    Arguments:
            benchmark: QuantumCircuit or name of the benchmark to be generated
            circuit_size: Input for the benchmark creation, in most cases this is equal to the qubit number
            opt_level: Optimization level to be used by the transpiler.
            generate_mirror_circuit: If True, generates the mirror version (U @ U.inverse()) of the benchmark.

    Returns:
            Qiskit::QuantumCircuit expressed in a generic basis gate set, still unmapped to any physical device.
    """
    _validate_opt_level(opt_level)
    circuit = _get_circuit(benchmark, circuit_size)
    qc_processed = transpile(circuit, optimization_level=opt_level, seed_transpiler=10)
    if generate_mirror_circuit:
        return _create_mirror_circuit(qc_processed, inplace=True)
    return qc_processed


@overload
def get_benchmark_native_gates(
    benchmark: str,
    circuit_size: int,
    target: Target,
    opt_level: int = 2,
    generate_mirror_circuit: bool = False,
) -> QuantumCircuit: ...


@overload
def get_benchmark_native_gates(
    benchmark: QuantumCircuit,
    circuit_size: None,
    target: Target,
    opt_level: int = 2,
    generate_mirror_circuit: bool = False,
) -> QuantumCircuit: ...


def get_benchmark_native_gates(
    benchmark: str | QuantumCircuit,
    circuit_size: int | None,
    target: Target,
    opt_level: int = 2,
    generate_mirror_circuit: bool = False,
) -> QuantumCircuit:
    """Return a benchmark compiled to the target's native gate set.

    Arguments:
            benchmark: QuantumCircuit or name of the benchmark to be generated
            circuit_size: Input for the benchmark creation, in most cases this is equal to the qubit number
            target: `~qiskit.transpiler.target.Target` for the benchmark generation
            opt_level: Optimization level to be used by the transpiler.
            generate_mirror_circuit: If True, generates the mirror version (U @ U.inverse()) of the benchmark.

    Returns:
            Qiskit::QuantumCircuit whose operations are restricted to ``target``'s native gate set but are **not** yet qubit-mapped to a concrete device connectivity.
    """
    _validate_opt_level(opt_level)

    circuit = _get_circuit(benchmark, circuit_size)

    if target.description == "clifford+t":
        from qiskit.transpiler import PassManager  # noqa: PLC0415
        from qiskit.transpiler.passes.synthesis import SolovayKitaev  # noqa: PLC0415

        # Transpile the circuit to single- and two-qubit gates including rotations
        clifford_t_rotations = get_target_for_gateset("clifford+t+rotations", num_qubits=circuit.num_qubits)
        compiled_for_sk = transpile(
            circuit,
            target=clifford_t_rotations,
            optimization_level=opt_level,
            seed_transpiler=10,
        )
        # Synthesize the rotations to Clifford+T gates
        # Measurements are removed and added back after the synthesis to avoid errors in the Solovay-Kitaev pass
        pm = PassManager(SolovayKitaev())
        circuit = pm.run(compiled_for_sk.remove_final_measurements(inplace=False))
        circuit.measure_all()

    if "rigetti" in target.description:
        rigetti.add_equivalences(SessionEquivalenceLibrary)
    elif "ionq" in target.description:
        ionq.add_equivalences(SessionEquivalenceLibrary)
    pm = generate_preset_pass_manager(optimization_level=opt_level, target=target, seed_transpiler=10)
    pm.layout = None
    pm.routing = None
    pm.scheduling = None

    compiled_circuit = pm.run(circuit)
    if generate_mirror_circuit:
        return _create_mirror_circuit(compiled_circuit, inplace=True)
    return compiled_circuit


@overload
def get_benchmark_mapped(
    benchmark: str,
    circuit_size: int,
    target: Target,
    opt_level: int = 2,
    generate_mirror_circuit: bool = False,
) -> QuantumCircuit: ...


@overload
def get_benchmark_mapped(
    benchmark: QuantumCircuit,
    circuit_size: None,
    target: Target,
    opt_level: int = 2,
    generate_mirror_circuit: bool = False,
) -> QuantumCircuit: ...


def get_benchmark_mapped(
    benchmark: str | QuantumCircuit,
    circuit_size: int | None,
    target: Target,
    opt_level: int = 2,
    generate_mirror_circuit: bool = False,
) -> QuantumCircuit:
    """Return a benchmark fully compiled and qubit-mapped to a device.

    Arguments:
            benchmark: QuantumCircuit or name of the benchmark to be generated
            circuit_size: Input for the benchmark creation, in most cases this is equal to the qubit number
            target: `~qiskit.transpiler.target.Target` for the benchmark generation
            opt_level: Optimization level to be used by the transpiler.
            generate_mirror_circuit: If True, generates the mirror version (U @ U.inverse()) of the benchmark.

    Returns:
            Qiskit::QuantumCircuit that has been decomposed and routed onto the connectivity described by ``target``.
    """
    _validate_opt_level(opt_level)

    circuit = _get_circuit(benchmark, circuit_size)

    if "rigetti" in target.description:
        rigetti.add_equivalences(SessionEquivalenceLibrary)
    elif "ionq" in target.description:
        ionq.add_equivalences(SessionEquivalenceLibrary)

    mapped_circuit = transpile(
        circuit,
        target=target,
        optimization_level=opt_level,
        seed_transpiler=10,
    )
    if generate_mirror_circuit:
        return _create_mirror_circuit(mapped_circuit, inplace=True)
    return mapped_circuit


@overload
def get_benchmark(
    benchmark: str,
    level: BenchmarkLevel,
    circuit_size: int,
    target: Target | None = None,
    opt_level: int = 2,
    generate_mirror_circuit: bool = False,
) -> QuantumCircuit: ...


@overload
def get_benchmark(
    benchmark: QuantumCircuit,
    level: BenchmarkLevel,
    circuit_size: None,
    target: Target | None = None,
    opt_level: int = 2,
    generate_mirror_circuit: bool = False,
) -> QuantumCircuit: ...


def get_benchmark(
    benchmark: str | QuantumCircuit,
    level: BenchmarkLevel,
    circuit_size: int | None = None,
    target: Target | None = None,
    opt_level: int = 2,
    generate_mirror_circuit: bool = False,
) -> QuantumCircuit:
    """Returns one benchmark as a qiskit.QuantumCircuit object.

    Arguments:
        benchmark: QuantumCircuit or name of the benchmark to be generated
        level: Choice of level (BenchmarkLevel Enum)
        circuit_size: Input for the benchmark creation, in most cases this is equal to the qubit number
        target: `~qiskit.transpiler.target.Target` for the benchmark generation
                (only used for "nativegates" and "mapped" level)
        opt_level: Optimization level to be used by the transpiler.
        generate_mirror_circuit: If True, generates the mirror version (U @ U.inverse()) of the benchmark.

    Returns:
        Qiskit::QuantumCircuit object representing the benchmark with the selected options
    """
    qc_processed: QuantumCircuit

    if level is BenchmarkLevel.ALG:
        qc_processed = get_benchmark_alg(
            benchmark,
            circuit_size=circuit_size,
            generate_mirror_circuit=generate_mirror_circuit,
        )
    elif level is BenchmarkLevel.INDEP:
        qc_processed = get_benchmark_indep(
            benchmark,
            circuit_size,
            opt_level,
            generate_mirror_circuit=generate_mirror_circuit,
        )
    elif level is BenchmarkLevel.NATIVEGATES:
        if target is None:
            msg = "Target must be provided for 'nativegates' level."
            raise ValueError(msg)
        qc_processed = get_benchmark_native_gates(
            benchmark,
            circuit_size,
            target,
            opt_level,
            generate_mirror_circuit=generate_mirror_circuit,
        )
    elif level is BenchmarkLevel.MAPPED:
        if target is None:
            msg = "Target must be provided for 'mapped' level."
            raise ValueError(msg)
        qc_processed = get_benchmark_mapped(
            benchmark,
            circuit_size,
            target,
            opt_level,
            generate_mirror_circuit=generate_mirror_circuit,
        )
    else:
        assert_never(level)

    return qc_processed
