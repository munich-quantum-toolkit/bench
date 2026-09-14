# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Module for the benchmark generation and benchmark retrieval."""

from __future__ import annotations

from enum import Enum, auto
from importlib.metadata import version
from typing import TYPE_CHECKING, Literal, Unpack, assert_never, overload

import numpy as np
from qiskit import generate_preset_pass_manager
from qiskit.circuit import ClassicalRegister, QuantumCircuit, SessionEquivalenceLibrary
from qiskit.compiler import transpile
from qiskit.converters import circuit_to_dag
from qiskit.transpiler import Layout, Target

from .benchmarks import create_circuit
from .targets.gatesets import get_target_for_gateset, ionq, rigetti

if TYPE_CHECKING:  # pragma: no cover
    from .configuration_options import ConfigurationOptions


class BenchmarkLevel(Enum):
    """Enum representing different levels."""

    ALG = auto()
    INDEP = auto()
    NATIVEGATES = auto()
    MAPPED = auto()


def _get_circuit(
    benchmark: str | QuantumCircuit,
    circuit_size: int | None,
    random_parameters: bool = True,
    **kwargs: Unpack[ConfigurationOptions],
) -> QuantumCircuit:
    """Creates a raw quantum circuit based on the specified benchmark.

    This function generates a quantum circuit according to the specifications of the
    desired benchmark.

    Arguments:
        benchmark: Name of the benchmark for which the circuit is to be created.
        circuit_size: Size of the circuit to be created, required for benchmarks other than "shor".
        random_parameters: If True, assigns random parameters to the circuit's parameters if they exist.
        kwargs: Additional keyword arguments passed to the circuit creation.

    Returns:
        QuantumCircuit: Constructed quantum circuit based on the given parameters.
    """
    if isinstance(benchmark, QuantumCircuit):
        if circuit_size is not None:
            msg = "`circuit_size` must be omitted or None when `benchmark` is a QuantumCircuit."
            raise ValueError(msg)
        qc = benchmark

    else:
        if circuit_size is None:
            msg = "`circuit_size` cannot be None when `benchmark` is a str."
            raise ValueError(msg)
        qc = create_circuit(benchmark, circuit_size, **kwargs)

    if len(qc.parameters) > 0 and random_parameters:
        rng = np.random.default_rng(10)
        param_dict = {param: rng.uniform(0, 2 * np.pi) for param in qc.parameters}
        qc.assign_parameters(param_dict, inplace=True)
        assert len(qc.parameters) == 0, "All parameters should be assigned."
    return qc


def _create_mirror_circuit(
    qc_original: QuantumCircuit, *, inplace: bool = False, target: Target | None = None, optimization_level: int = 2
) -> QuantumCircuit:
    """Generates the mirror version (qc @ qc.inverse()) of a given quantum circuit.

    For circuits with an initial layout (e.g., mapped circuits), this function ensures
    that the final layout of the mirrored circuit matches the initial layout of the
    original circuit. While Qiskit's `inverse()` and `compose()` methods correctly track
    the permutation of qubits, this benchmark requires that the final qubit permutation
    is identical to the initial one, requiring the explicit layout handling herein.
    Also ensures that the mirrored circuit respects the native gate set of the target device
    if a target is provided.

    All qubits are measured at the end of the mirror circuit.

    Args:
        qc_original: The quantum circuit to mirror.
        inplace: If True, modifies the circuit in place. Otherwise, returns a new circuit.
        target: Target device for transpilation. If provided, ensures native gate set compliance.
        optimization_level: Optimization level of the transpilation.

    Returns:
        The mirrored quantum circuit.
    """
    target_qc = qc_original if inplace else qc_original.copy()

    # Remove measurements and barriers at the end of the circuit before mirroring.
    target_qc.remove_final_measurements(inplace=True)
    qc_inv = target_qc.inverse()

    # Place a barrier on all active qubits to prevent optimization passes from fully reducing the mirror circuit.
    dag = circuit_to_dag(target_qc)
    active_qubits = [qubit for qubit in target_qc.qubits if qubit not in dag.idle_wires()]
    target_qc.barrier(active_qubits)

    # Form the mirror circuit by composing the original circuit with its inverse.
    target_qc.compose(qc_inv, inplace=True)

    # Transpile to ensure the final circuit uses only native gates while preserving the initial layout.
    if target is not None:
        layout = target_qc.layout.initial_layout if target_qc.layout is not None else None
        target_qc = transpile(
            target_qc,
            target=target,
            optimization_level=optimization_level,
            layout_method=None,
            routing_method=None,
            seed_transpiler=10,
        )
        if layout is not None and target_qc.layout is not None:
            target_qc.layout.initial_layout = layout

    # Add final measurements to all active qubits
    target_qc.barrier(active_qubits)
    new_creg = ClassicalRegister(len(active_qubits), "meas")
    target_qc.add_register(new_creg)
    target_qc.measure(active_qubits, new_creg)

    # Adjust circuit name to indicate it is a mirror circuit.
    target_qc.name = f"{target_qc.name}_mirror"

    # Reset the permutation caused by routing back to the identity (all SWAPs are undone by the inverse).
    if target_qc.layout is not None:
        target_qc.layout.final_layout = Layout.generate_trivial_layout(*target_qc.qregs)

    return target_qc


def _validate_opt_level(opt_level: int) -> None:
    """Validate optimization level.

    Arguments:
        opt_level: User-defined optimization level.
    """
    if not 0 <= opt_level <= 3:
        msg = f"Invalid `opt_level` '{opt_level}'. Must be in the range [0, 3]."
        raise ValueError(msg)


def _validate_compiler(compiler: str, opt_level: int) -> None:
    """Validate the compiler before creating or modifying a circuit."""
    if compiler not in {"qiskit", "mqt"}:
        msg = f"Unknown compiler '{compiler}'. Choose 'qiskit' or 'mqt'."
        raise ValueError(msg)
    _validate_opt_level(opt_level)
    if compiler == "mqt" and opt_level != 2:
        msg = "MQT Core uses its default optimization pipeline; omit opt_level or set it to 2."
        raise ValueError(msg)


def _update_qiskit_provenance(circuit: QuantumCircuit) -> None:
    """Replace an earlier compiler record when Qiskit recompiles the circuit."""
    if "mqt_bench_compiler" in circuit.metadata:
        circuit.metadata = circuit.metadata | {"mqt_bench_compiler": {"name": "qiskit", "version": version("qiskit")}}


def _get_mqt_benchmark(
    circuit: QuantumCircuit,
    target: Target | None = None,
    *,
    mapped: bool = False,
    generate_mirror_circuit: bool = False,
) -> QuantumCircuit:
    """Compile the circuit and its optional mirror without Qiskit transpilation."""
    from ._mqt_compiler import compile_circuit  # ruff:ignore[import-outside-top-level]

    compiled = compile_circuit(circuit, target, mapped=mapped)
    if generate_mirror_circuit:
        compiled = _create_mirror_circuit(compiled, inplace=True)
        if target is not None:
            compiled = compile_circuit(compiled, target, mapped=mapped)
    return compiled


@overload
def get_benchmark_alg(
    benchmark: str,
    circuit_size: int,
    *,
    generate_mirror_circuit: bool = False,
    random_parameters: bool = True,
    **kwargs: Unpack[ConfigurationOptions],
) -> QuantumCircuit: ...


@overload
def get_benchmark_alg(
    benchmark: QuantumCircuit,
    circuit_size: None = None,
    *,
    generate_mirror_circuit: bool = False,
    random_parameters: bool = True,
    **kwargs: Unpack[ConfigurationOptions],
) -> QuantumCircuit: ...


@overload
def get_benchmark_alg(
    benchmark: str | QuantumCircuit,
    circuit_size: int | None = None,
    *,
    generate_mirror_circuit: bool = False,
    random_parameters: bool = True,
    **kwargs: Unpack[ConfigurationOptions],
) -> QuantumCircuit: ...


def get_benchmark_alg(
    benchmark: str | QuantumCircuit,
    circuit_size: int | None = None,
    *,
    generate_mirror_circuit: bool = False,
    random_parameters: bool = True,
    **kwargs: Unpack[ConfigurationOptions],
) -> QuantumCircuit:
    """Return an algorithm-level benchmark circuit.

    Arguments:
        benchmark: QuantumCircuit or name of the benchmark to be generated
        circuit_size: Input for the benchmark creation, in most cases this is equal to the qubit number
        generate_mirror_circuit: If True, generates the mirror version (U @ U.inverse()) of the benchmark.
        random_parameters: If True, assigns random parameters to the circuit's parameters if they exist.
        kwargs: Additional keyword arguments passed to the circuit creation.

    Returns:
        Qiskit::QuantumCircuit representing the raw benchmark circuit without any hardware-specific compilation or mapping.
    """
    qc = _get_circuit(benchmark, circuit_size, random_parameters, **kwargs)
    if generate_mirror_circuit:
        return _create_mirror_circuit(qc, inplace=True)
    return qc


@overload
def get_benchmark_indep(
    benchmark: str,
    circuit_size: int,
    opt_level: int = 2,
    *,
    compiler: Literal["qiskit", "mqt"] = "qiskit",
    generate_mirror_circuit: bool = False,
    random_parameters: bool = True,
    **kwargs: Unpack[ConfigurationOptions],
) -> QuantumCircuit: ...


@overload
def get_benchmark_indep(
    benchmark: QuantumCircuit,
    circuit_size: None = None,
    opt_level: int = 2,
    *,
    compiler: Literal["qiskit", "mqt"] = "qiskit",
    generate_mirror_circuit: bool = False,
    random_parameters: bool = True,
    **kwargs: Unpack[ConfigurationOptions],
) -> QuantumCircuit: ...


@overload
def get_benchmark_indep(
    benchmark: str | QuantumCircuit,
    circuit_size: int | None = None,
    opt_level: int = 2,
    *,
    compiler: Literal["qiskit", "mqt"] = "qiskit",
    generate_mirror_circuit: bool = False,
    random_parameters: bool = True,
    **kwargs: Unpack[ConfigurationOptions],
) -> QuantumCircuit: ...


def get_benchmark_indep(
    benchmark: str | QuantumCircuit,
    circuit_size: int | None = None,
    opt_level: int = 2,
    *,
    compiler: Literal["qiskit", "mqt"] = "qiskit",
    generate_mirror_circuit: bool = False,
    random_parameters: bool = True,
    **kwargs: Unpack[ConfigurationOptions],
) -> QuantumCircuit:
    """Return a target-independent benchmark circuit.

    Arguments:
        benchmark: QuantumCircuit or name of the benchmark to be generated
        circuit_size: Input for the benchmark creation, in most cases this is equal to the qubit number
        opt_level: Qiskit optimization level. MQT Core uses its default pipeline and requires the default value 2.
        compiler: Compiler to use: "qiskit" (default) or "mqt".
        generate_mirror_circuit: If True, generates the mirror version (U @ U.inverse()) of the benchmark.
        random_parameters: If True, assigns random parameters to the circuit's parameters if they exist.
        kwargs: Additional keyword arguments passed to the circuit creation.

    Returns:
        Qiskit::QuantumCircuit expressed in a generic basis gate set, still unmapped to any physical device.
    """
    _validate_compiler(compiler, opt_level)

    circuit = _get_circuit(benchmark, circuit_size, random_parameters, **kwargs)
    if compiler == "mqt":
        return _get_mqt_benchmark(circuit, generate_mirror_circuit=generate_mirror_circuit)
    qc_processed = transpile(circuit, optimization_level=opt_level, seed_transpiler=10)
    _update_qiskit_provenance(qc_processed)
    if generate_mirror_circuit:
        return _create_mirror_circuit(qc_processed, inplace=True)
    return qc_processed


@overload
def get_benchmark_native_gates(
    benchmark: str,
    circuit_size: int,
    target: Target,
    opt_level: int = 2,
    *,
    compiler: Literal["qiskit", "mqt"] = "qiskit",
    generate_mirror_circuit: bool = False,
    random_parameters: bool = True,
    **kwargs: Unpack[ConfigurationOptions],
) -> QuantumCircuit: ...


@overload
def get_benchmark_native_gates(
    benchmark: QuantumCircuit,
    circuit_size: None,
    target: Target,
    opt_level: int = 2,
    *,
    compiler: Literal["qiskit", "mqt"] = "qiskit",
    generate_mirror_circuit: bool = False,
    random_parameters: bool = True,
    **kwargs: Unpack[ConfigurationOptions],
) -> QuantumCircuit: ...


@overload
def get_benchmark_native_gates(
    benchmark: str | QuantumCircuit,
    circuit_size: int | None,
    target: Target,
    opt_level: int = 2,
    *,
    compiler: Literal["qiskit", "mqt"] = "qiskit",
    generate_mirror_circuit: bool = False,
    random_parameters: bool = True,
    **kwargs: Unpack[ConfigurationOptions],
) -> QuantumCircuit: ...


def get_benchmark_native_gates(
    benchmark: str | QuantumCircuit,
    circuit_size: int | None,
    target: Target,
    opt_level: int = 2,
    *,
    compiler: Literal["qiskit", "mqt"] = "qiskit",
    generate_mirror_circuit: bool = False,
    random_parameters: bool = True,
    **kwargs: Unpack[ConfigurationOptions],
) -> QuantumCircuit:
    """Return a benchmark compiled to the target's native gate set.

    Arguments:
        benchmark: QuantumCircuit or name of the benchmark to be generated
        circuit_size: Input for the benchmark creation, in most cases this is equal to the qubit number
        target: `~qiskit.transpiler.target.Target` for the benchmark generation
        opt_level: Qiskit optimization level. MQT Core uses its default pipeline and requires the default value 2.
        compiler: Compiler to use: "qiskit" (default) or "mqt".
        generate_mirror_circuit: If True, generates the mirror version (U @ U.inverse()) of the benchmark.
        random_parameters: If True, assigns random parameters to the circuit's parameters if they exist.
        kwargs: Additional keyword arguments passed to the circuit creation.

    Returns:
        Qiskit::QuantumCircuit whose operations are restricted to ``target``'s native gate set but are **not** yet qubit-mapped to a concrete device connectivity.
    """
    _validate_compiler(compiler, opt_level)

    circuit = _get_circuit(benchmark, circuit_size, random_parameters, **kwargs)

    if compiler == "mqt":
        return _get_mqt_benchmark(circuit, target, generate_mirror_circuit=generate_mirror_circuit)
    if target.description == "clifford+t":
        from qiskit.transpiler import PassManager  # ruff:ignore[import-outside-top-level]
        from qiskit.transpiler.passes.synthesis import SolovayKitaev  # ruff:ignore[import-outside-top-level]

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
        circuit = pm.run(compiled_for_sk.remove_final_measurements(inplace=False))  # ty: ignore[invalid-argument-type]
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
    _update_qiskit_provenance(compiled_circuit)
    if generate_mirror_circuit:
        return _create_mirror_circuit(compiled_circuit, inplace=True, target=target, optimization_level=opt_level)
    return compiled_circuit


@overload
def get_benchmark_mapped(
    benchmark: str,
    circuit_size: int,
    target: Target,
    opt_level: int = 2,
    *,
    compiler: Literal["qiskit", "mqt"] = "qiskit",
    generate_mirror_circuit: bool = False,
    random_parameters: bool = True,
    **kwargs: Unpack[ConfigurationOptions],
) -> QuantumCircuit: ...


@overload
def get_benchmark_mapped(
    benchmark: QuantumCircuit,
    circuit_size: None,
    target: Target,
    opt_level: int = 2,
    *,
    compiler: Literal["qiskit", "mqt"] = "qiskit",
    generate_mirror_circuit: bool = False,
    random_parameters: bool = True,
    **kwargs: Unpack[ConfigurationOptions],
) -> QuantumCircuit: ...


@overload
def get_benchmark_mapped(
    benchmark: str | QuantumCircuit,
    circuit_size: int | None,
    target: Target,
    opt_level: int = 2,
    *,
    compiler: Literal["qiskit", "mqt"] = "qiskit",
    generate_mirror_circuit: bool = False,
    random_parameters: bool = True,
    **kwargs: Unpack[ConfigurationOptions],
) -> QuantumCircuit: ...


def get_benchmark_mapped(
    benchmark: str | QuantumCircuit,
    circuit_size: int | None,
    target: Target,
    opt_level: int = 2,
    *,
    compiler: Literal["qiskit", "mqt"] = "qiskit",
    generate_mirror_circuit: bool = False,
    random_parameters: bool = True,
    **kwargs: Unpack[ConfigurationOptions],
) -> QuantumCircuit:
    """Return a benchmark fully compiled and qubit-mapped to a device.

    Arguments:
        benchmark: QuantumCircuit or name of the benchmark to be generated
        circuit_size: Input for the benchmark creation, in most cases this is equal to the qubit number
        target: `~qiskit.transpiler.target.Target` for the benchmark generation
        opt_level: Qiskit optimization level. MQT Core uses its default pipeline and requires the default value 2.
        compiler: Compiler to use: "qiskit" (default) or "mqt".
        generate_mirror_circuit: If True, generates the mirror version (U @ U.inverse()) of the benchmark.
        random_parameters: If True, assigns random parameters to the circuit's parameters if they exist.
        kwargs: Additional keyword arguments passed to the circuit creation.

    Returns:
        Qiskit::QuantumCircuit that has been decomposed and routed onto the connectivity described by ``target``.
    """
    _validate_compiler(compiler, opt_level)

    circuit = _get_circuit(benchmark, circuit_size, random_parameters, **kwargs)
    if compiler == "mqt":
        return _get_mqt_benchmark(circuit, target, mapped=True, generate_mirror_circuit=generate_mirror_circuit)

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
    _update_qiskit_provenance(mapped_circuit)
    if generate_mirror_circuit:
        return _create_mirror_circuit(mapped_circuit, inplace=True, target=target, optimization_level=opt_level)
    return mapped_circuit


@overload
def get_benchmark(
    benchmark: str,
    level: BenchmarkLevel,
    circuit_size: int,
    target: Target | None = None,
    opt_level: int = 2,
    *,
    compiler: Literal["qiskit", "mqt"] = "qiskit",
    generate_mirror_circuit: bool = False,
    random_parameters: bool = True,
    **kwargs: Unpack[ConfigurationOptions],
) -> QuantumCircuit: ...


@overload
def get_benchmark(
    benchmark: QuantumCircuit,
    level: BenchmarkLevel,
    circuit_size: None,
    target: Target | None = None,
    opt_level: int = 2,
    *,
    compiler: Literal["qiskit", "mqt"] = "qiskit",
    generate_mirror_circuit: bool = False,
    random_parameters: bool = True,
    **kwargs: Unpack[ConfigurationOptions],
) -> QuantumCircuit: ...


@overload
def get_benchmark(
    benchmark: str | QuantumCircuit,
    level: BenchmarkLevel,
    circuit_size: int | None = None,
    target: Target | None = None,
    opt_level: int = 2,
    *,
    compiler: Literal["qiskit", "mqt"] = "qiskit",
    generate_mirror_circuit: bool = False,
    random_parameters: bool = True,
    **kwargs: Unpack[ConfigurationOptions],
) -> QuantumCircuit: ...


def get_benchmark(
    benchmark: str | QuantumCircuit,
    level: BenchmarkLevel,
    circuit_size: int | None = None,
    target: Target | None = None,
    opt_level: int = 2,
    *,
    compiler: Literal["qiskit", "mqt"] = "qiskit",
    generate_mirror_circuit: bool = False,
    random_parameters: bool = True,
    **kwargs: Unpack[ConfigurationOptions],
) -> QuantumCircuit:
    """Returns one benchmark as a qiskit.QuantumCircuit object.

    Arguments:
        benchmark: QuantumCircuit or name of the benchmark to be generated
        level: Choice of level
        circuit_size: Input for the benchmark creation, in most cases this is equal to the qubit number
        target: `~qiskit.transpiler.target.Target` for the benchmark generation
                (only used for "nativegates" and "mapped" level)
        opt_level: Qiskit optimization level. MQT Core uses its default pipeline and requires the default value 2.
        compiler: Compiler to use: "qiskit" (default) or "mqt".
        generate_mirror_circuit: If True, generates the mirror version (U @ U.inverse()) of the benchmark.
        random_parameters: If True, assigns random parameters to the circuit's parameters if they exist.
        kwargs: Additional keyword arguments passed to the circuit creation.

    Returns:
        Qiskit::QuantumCircuit object representing the benchmark with the selected options
    """
    _validate_compiler(compiler, opt_level if level is not BenchmarkLevel.ALG else 2)
    if level is BenchmarkLevel.ALG:
        return get_benchmark_alg(
            benchmark=benchmark,
            circuit_size=circuit_size,
            generate_mirror_circuit=generate_mirror_circuit,
            random_parameters=random_parameters,
            **kwargs,
        )

    if level is BenchmarkLevel.INDEP:
        return get_benchmark_indep(
            benchmark=benchmark,
            circuit_size=circuit_size,
            opt_level=opt_level,
            compiler=compiler,
            generate_mirror_circuit=generate_mirror_circuit,
            random_parameters=random_parameters,
            **kwargs,
        )

    if level is BenchmarkLevel.NATIVEGATES:
        if target is None:
            msg = "Target must be provided for 'nativegates' level."
            raise ValueError(msg)
        return get_benchmark_native_gates(
            benchmark=benchmark,
            circuit_size=circuit_size,
            target=target,
            opt_level=opt_level,
            compiler=compiler,
            generate_mirror_circuit=generate_mirror_circuit,
            random_parameters=random_parameters,
            **kwargs,
        )

    if level is BenchmarkLevel.MAPPED:
        if target is None:
            msg = "Target must be provided for 'mapped' level."
            raise ValueError(msg)
        return get_benchmark_mapped(
            benchmark=benchmark,
            circuit_size=circuit_size,
            target=target,
            opt_level=opt_level,
            compiler=compiler,
            generate_mirror_circuit=generate_mirror_circuit,
            random_parameters=random_parameters,
            **kwargs,
        )

    assert_never(level)
