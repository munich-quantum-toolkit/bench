# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Module for the benchmark generation and benchmark retrieval."""

from __future__ import annotations

import json
from copy import deepcopy
from enum import Enum, auto
from typing import TYPE_CHECKING, Unpack, assert_never, overload

import numpy as np
from qiskit import generate_preset_pass_manager
from qiskit.circuit import CircuitError, ClassicalRegister, Gate, QuantumCircuit, SessionEquivalenceLibrary
from qiskit.compiler import transpile
from qiskit.transpiler import Layout, Target
from qiskit.transpiler.passes import OptimizeCliffordT, RemoveFinalMeasurements

from .benchmarks import create_circuit
from .targets.gatesets import get_target_for_gateset
from .targets.gatesets._compilation import prepare_target
from .targets.gatesets.ibm import configure_fractional_angles

if TYPE_CHECKING:  # pragma: no cover
    from qiskit.dagcircuit import DAGCircuit
    from qiskit.transpiler import PassManager, StagedPassManager

    from .configuration_options import ConfigurationOptions


class BenchmarkLevel(Enum):
    """Enum representing different levels."""

    ALG = auto()
    INDEP = auto()
    NATIVEGATES = auto()
    MAPPED = auto()


class RecursiveOptimizeCliffordT(OptimizeCliffordT):
    """Also optimize control-flow blocks, which Qiskit's pass skips."""

    def run(self, dag: DAGCircuit) -> DAGCircuit:
        """Optimize each control-flow block and then the enclosing circuit."""
        for node in dag.control_flow_op_nodes():
            operation = node.op
            dag.substitute_node(node, operation.replace_blocks([self(block) for block in operation.blocks]))
        return super().run(dag)


def _get_circuit(
    benchmark: str | QuantumCircuit,
    circuit_size: int | None,
    random_parameters: bool = True,
    **kwargs: Unpack[ConfigurationOptions],
) -> tuple[QuantumCircuit, dict]:
    """Create a raw circuit and collect its generation settings.

    Arguments:
        benchmark: Name of the benchmark for which the circuit is to be created.
        circuit_size: Size of the circuit to be created, required when the benchmark is a name.
        random_parameters: If True, assigns random parameters to the circuit's parameters if they exist.
        kwargs: Additional keyword arguments passed to the circuit creation.

    Returns:
        The circuit and its generation settings.
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

    previous = (qc.metadata or {}).get("mqt_bench_generation", {})
    generation = deepcopy(previous) if isinstance(previous, dict) else {}
    generation.setdefault("benchmark", benchmark if isinstance(benchmark, str) else qc.name)
    generation.setdefault("circuit_size", circuit_size if circuit_size is not None else qc.num_qubits)
    generation.setdefault("random_parameters", random_parameters)
    options = dict(generation.get("options", {}))
    if isinstance(benchmark, str):
        for name, value in kwargs.items():
            try:
                options[name] = json.loads(json.dumps(value, allow_nan=False))
            except (TypeError, ValueError):
                continue
    generation["options"] = options

    if qc.parameters and random_parameters:
        seed = kwargs.get("seed", 10)
        rng = np.random.default_rng(seed)
        param_dict = {param: rng.uniform(0, 2 * np.pi) for param in qc.parameters}
        if qc is benchmark:
            qc = qc.copy()
        qc.assign_parameters(param_dict, inplace=True)
        generation["random_parameters"] = True
        generation["parameter_seed"] = seed
    return qc, generation


def _record_generation(
    qc: QuantumCircuit,
    level: BenchmarkLevel,
    generation: dict,
    *,
    target: Target | None = None,
    opt_level: int | None = None,
    mirror: bool = False,
) -> None:
    """Attach the compilation settings to the circuit's generation record."""
    generation.update({
        "level": level.name.lower(),
        "opt_level": opt_level,
        "target": target.description if target is not None else None,
        "mirror": mirror or generation.get("mirror", False),
    })
    qc.metadata = (qc.metadata or {}) | {"mqt_bench_generation": generation}


def _create_mirror_circuit(
    qc_original: QuantumCircuit, *, inplace: bool = False, pass_manager: PassManager | None = None
) -> QuantumCircuit:
    """Generates the mirror version (qc @ qc.inverse()) of a given quantum circuit.

    For circuits with an initial layout (e.g., mapped circuits), this function ensures
    that the final layout of the mirrored circuit matches the initial layout of the
    original circuit. While Qiskit's `inverse()` and `compose()` methods correctly track
    the permutation of qubits, this benchmark requires that the final qubit permutation
    is identical to the initial one, requiring the explicit layout handling herein.
    Also ensures that the mirrored circuit respects the native gate set of the target device
    if a pass manager is provided.

    All qubits are measured at the end of the mirror circuit.

    Args:
        qc_original: The quantum circuit to mirror.
        inplace: If True, modifies the circuit in place. Otherwise, returns a new circuit.
        pass_manager: Compiler pipeline to reuse for the mirror.

    Returns:
        The mirrored quantum circuit.

    Raises:
        ValueError: If the circuit cannot be inverted after removing final measurements.
    """
    # Check inversion before modifying the input circuit.
    try:
        qc_inv = RemoveFinalMeasurements()(qc_original).inverse()
    except CircuitError as exc:
        msg = (
            "Cannot mirror this circuit: after removing final measurements, it contains operations "
            "without a supported inverse (such as mid-circuit measurements, resets, or control flow). "
            "Set generate_mirror_circuit=False."
        )
        raise ValueError(msg) from exc

    target_qc = qc_original if inplace else qc_original.copy()
    target_qc.remove_final_measurements(inplace=True)

    # Place a barrier on all active qubits to prevent optimization passes from fully reducing the mirror circuit.
    dag = target_qc.to_dag()
    idle_qubits = set(dag.idle_wires())
    active_qubits = [index for index, qubit in enumerate(target_qc.qubits) if qubit not in idle_qubits]
    target_qc.barrier(active_qubits)

    # Form the mirror circuit by composing the original circuit with its inverse.
    target_qc.compose(qc_inv, inplace=True)

    # Transpile to ensure the final circuit uses only native gates while preserving the initial layout.
    if pass_manager is not None:
        layout = deepcopy(target_qc.layout)
        target_qc = pass_manager.run(target_qc)
        if target_qc.layout is not None:
            final_indices = target_qc.layout.final_index_layout()
            active_qubits = [final_indices[index] for index in active_qubits]
        if layout is not None and target_qc.layout is not None:
            target_qc._layout = layout  # ruff:ignore[private-member-access]

    # Add final measurements to all active qubits
    target_qc.barrier(active_qubits)
    name = "meas"
    existing_names = {register.name for register in target_qc.cregs}
    while name in existing_names:
        name += "_"
    new_creg = ClassicalRegister(len(active_qubits), name)
    target_qc.add_register(new_creg)
    target_qc.measure(active_qubits, new_creg)

    # Adjust circuit name to indicate it is a mirror circuit.
    target_qc.name = f"{target_qc.name}_mirror"

    # Reset the permutation caused by routing back to the identity (all SWAPs are undone by the inverse).
    if target_qc.layout is not None:
        target_qc.layout.final_layout = Layout.generate_trivial_layout(*target_qc.qregs)

    return target_qc


def _get_qiskit_pass_manager(
    target: Target, opt_level: int, *, native_num_qubits: int | None = None
) -> StagedPassManager:
    """Build the native or mapped pipeline, including final gate lowering."""
    target, lowering = prepare_target(target, native_num_qubits=native_num_qubits)
    pm = generate_preset_pass_manager(
        optimization_level=opt_level,
        target=target,
        seed_transpiler=10,
        routing_method="none" if native_num_qubits is not None else None,
    )
    pm.post_scheduling = lowering
    configure_fractional_angles(pm, target)
    return pm


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
    qc, generation = _get_circuit(benchmark, circuit_size, random_parameters, **kwargs)
    if qc is benchmark:
        qc = qc.copy()
    _record_generation(qc, BenchmarkLevel.ALG, generation, mirror=generate_mirror_circuit)
    if generate_mirror_circuit:
        return _create_mirror_circuit(qc, inplace=True)
    return qc


@overload
def get_benchmark_indep(
    benchmark: str,
    circuit_size: int,
    opt_level: int = 2,
    *,
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
    generate_mirror_circuit: bool = False,
    random_parameters: bool = True,
    **kwargs: Unpack[ConfigurationOptions],
) -> QuantumCircuit: ...


def get_benchmark_indep(
    benchmark: str | QuantumCircuit,
    circuit_size: int | None = None,
    opt_level: int = 2,
    *,
    generate_mirror_circuit: bool = False,
    random_parameters: bool = True,
    **kwargs: Unpack[ConfigurationOptions],
) -> QuantumCircuit:
    """Return a target-independent benchmark circuit.

    Arguments:
        benchmark: QuantumCircuit or name of the benchmark to be generated
        circuit_size: Input for the benchmark creation, in most cases this is equal to the qubit number
        opt_level: Optimization level to be used by the transpiler.
        generate_mirror_circuit: If True, generates the mirror version (U @ U.inverse()) of the benchmark.
        random_parameters: If True, assigns random parameters to the circuit's parameters if they exist.
        kwargs: Additional keyword arguments passed to the circuit creation.

    Returns:
        Qiskit::QuantumCircuit expressed in a generic basis gate set, still unmapped to any physical device.
    """
    _validate_opt_level(opt_level)

    circuit, generation = _get_circuit(benchmark, circuit_size, random_parameters, **kwargs)
    qc_processed = transpile(circuit, optimization_level=opt_level, seed_transpiler=10, routing_method="none")
    _record_generation(
        qc_processed, BenchmarkLevel.INDEP, generation, opt_level=opt_level, mirror=generate_mirror_circuit
    )
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
    generate_mirror_circuit: bool = False,
    random_parameters: bool = True,
    **kwargs: Unpack[ConfigurationOptions],
) -> QuantumCircuit:
    """Return a benchmark compiled to the target's native gate set.

    Arguments:
        benchmark: QuantumCircuit or name of the benchmark to be generated
        circuit_size: Input for the benchmark creation, in most cases this is equal to the qubit number
        target: `~qiskit.transpiler.target.Target` for the benchmark generation
        opt_level: Optimization level to be used by the transpiler.
        generate_mirror_circuit: If True, generates the mirror version (U @ U.inverse()) of the benchmark.
        random_parameters: If True, assigns random parameters to the circuit's parameters if they exist.
        kwargs: Additional keyword arguments passed to the circuit creation.

    Returns:
        Qiskit::QuantumCircuit whose operations are restricted to ``target``'s native gate set but are **not** yet qubit-mapped to a concrete device connectivity.
    """
    _validate_opt_level(opt_level)

    circuit, generation = _get_circuit(benchmark, circuit_size, random_parameters, **kwargs)

    if {"h", "t"} <= target.operation_names <= get_target_for_gateset("clifford+t", circuit.num_qubits).operation_names:
        from qiskit.transpiler import PassManager  # ruff:ignore[import-outside-top-level]
        from qiskit.transpiler.passes import (  # ruff:ignore[import-outside-top-level]
            BasisTranslator,
            HighLevelSynthesis,
            SynthesizeRZRotations,
        )

        target, _ = prepare_target(target, native_num_qubits=circuit.num_qubits)
        # Compile to Clifford+T and rotation gates
        clifford_t_rotations = get_target_for_gateset("clifford+t+rotations", num_qubits=circuit.num_qubits)
        pm = generate_preset_pass_manager(
            target=clifford_t_rotations,
            optimization_level=opt_level,
            seed_transpiler=10,
            # Keep permutations in the circuit so QASM export does not depend on layout metadata.
            routing_method="none",
        )
        mirror_pm = PassManager(HighLevelSynthesis(target=target, equivalence_library=SessionEquivalenceLibrary))
        if opt_level:
            basis_gates = [
                name for name in sorted(target.operation_names) if isinstance(target.operation_from_name(name), Gate)
            ]
            mirror_pm.append(RecursiveOptimizeCliffordT(basis_gates=basis_gates))
        mirror_pm.append(BasisTranslator(SessionEquivalenceLibrary, sorted(target.operation_names), target))

        class RecursiveSynthesizeRZRotations(SynthesizeRZRotations):
            """Also synthesize rotations in control-flow blocks, which Qiskit's pass skips."""

            def run(self, dag: DAGCircuit) -> DAGCircuit:
                for node in dag.control_flow_op_nodes():
                    op = node.op
                    dag.substitute_node(node, op.replace_blocks([self(block) for block in op.blocks]))
                return super().run(dag)

        synthesis_pm = PassManager([
            BasisTranslator(SessionEquivalenceLibrary, sorted(clifford_t_rotations.operation_names - {"rx", "ry"})),
            RecursiveSynthesizeRZRotations(),
        ])
        pm.post_optimization = synthesis_pm + mirror_pm
    else:
        pm = _get_qiskit_pass_manager(target, opt_level, native_num_qubits=circuit.num_qubits)
        mirror_pm = pm

    compiled_circuit = pm.run(circuit)
    _record_generation(
        compiled_circuit,
        BenchmarkLevel.NATIVEGATES,
        generation,
        target=target,
        opt_level=opt_level,
        mirror=generate_mirror_circuit,
    )
    if generate_mirror_circuit:
        return _create_mirror_circuit(compiled_circuit, inplace=True, pass_manager=mirror_pm)
    return compiled_circuit


@overload
def get_benchmark_mapped(
    benchmark: str,
    circuit_size: int,
    target: Target,
    opt_level: int = 2,
    *,
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
    generate_mirror_circuit: bool = False,
    random_parameters: bool = True,
    **kwargs: Unpack[ConfigurationOptions],
) -> QuantumCircuit:
    """Return a benchmark fully compiled and qubit-mapped to a device.

    Arguments:
        benchmark: QuantumCircuit or name of the benchmark to be generated
        circuit_size: Input for the benchmark creation, in most cases this is equal to the qubit number
        target: `~qiskit.transpiler.target.Target` for the benchmark generation
        opt_level: Optimization level to be used by the transpiler.
        generate_mirror_circuit: If True, generates the mirror version (U @ U.inverse()) of the benchmark.
        random_parameters: If True, assigns random parameters to the circuit's parameters if they exist.
        kwargs: Additional keyword arguments passed to the circuit creation.

    Returns:
        Qiskit::QuantumCircuit that has been decomposed and routed onto the connectivity described by ``target``.
    """
    _validate_opt_level(opt_level)

    circuit, generation = _get_circuit(benchmark, circuit_size, random_parameters, **kwargs)

    pm = _get_qiskit_pass_manager(target, opt_level)
    mapped_circuit = pm.run(circuit)
    _record_generation(
        mapped_circuit,
        BenchmarkLevel.MAPPED,
        generation,
        target=target,
        opt_level=opt_level,
        mirror=generate_mirror_circuit,
    )
    if generate_mirror_circuit:
        return _create_mirror_circuit(mapped_circuit, inplace=True, pass_manager=pm)
    return mapped_circuit


@overload
def get_benchmark(
    benchmark: str,
    level: BenchmarkLevel,
    circuit_size: int,
    target: Target | None = None,
    opt_level: int = 2,
    *,
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
        opt_level: Optimization level to be used by the transpiler.
        generate_mirror_circuit: If True, generates the mirror version (U @ U.inverse()) of the benchmark.
        random_parameters: If True, assigns random parameters to the circuit's parameters if they exist.
        kwargs: Additional keyword arguments passed to the circuit creation.

    Returns:
        Qiskit::QuantumCircuit object representing the benchmark with the selected options
    """
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
            generate_mirror_circuit=generate_mirror_circuit,
            random_parameters=random_parameters,
            **kwargs,
        )

    assert_never(level)
