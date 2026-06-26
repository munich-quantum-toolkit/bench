"""Deutsch Josza benchmark definition. Code is based on https://qiskit.org/textbook/ch-algorithms/deutsch-jozsa.html."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from qiskit.circuit import QuantumCircuit

from ._reference import MetricApplicability, ObjectiveSpec, ReferenceSpec, SparseReference
from ._registry import register_benchmark, register_reference

if TYPE_CHECKING:
    from qiskit.circuit.gate import Gate


def dj_oracle(case: str, n: int) -> Gate:
    """Returns a quantum circuit implementing the Deutsch-Josza oracle."""
    # plus one output qubit
    oracle_qc = QuantumCircuit(n + 1)
    rng = np.random.default_rng(10)

    if case == "balanced":
        b_str = ""
        for _ in range(n):
            b = rng.integers(0, 2)
            b_str = b_str + str(b)

        for qubit in range(len(b_str)):
            if b_str[qubit] == "1":
                oracle_qc.x(qubit)

        for qubit in range(n):
            oracle_qc.cx(qubit, n)

        for qubit in range(len(b_str)):
            if b_str[qubit] == "1":
                oracle_qc.x(qubit)

    if case == "constant":
        output = rng.integers(2)
        if output == 1:
            oracle_qc.x(n)

    oracle_gate = oracle_qc.to_gate()
    oracle_gate.name = "Oracle"  # To show when we display the circuit
    return oracle_gate


def dj_algorithm(oracle: Gate, n: int) -> QuantumCircuit:
    """Returns a quantum circuit implementing the Deutsch-Josza algorithm."""
    dj_circuit = QuantumCircuit(n + 1, n)

    dj_circuit.x(n)
    dj_circuit.h(n)

    for qubit in range(n):
        dj_circuit.h(qubit)

    dj_circuit.append(oracle, range(n + 1))

    for qubit in range(n):
        dj_circuit.h(qubit)

    dj_circuit.barrier()
    for i in range(n):
        dj_circuit.measure(i, i)

    return dj_circuit


@register_benchmark("dj", description="Deutsch-Jozsa")
def create_circuit(num_qubits: int, balanced: bool = True) -> QuantumCircuit:
    """Returns a quantum circuit implementing the Deutsch-Josza algorithm.

    Arguments:
        num_qubits: number of qubits of the returned quantum circuit
        balanced: True for a balanced and False for a constant oracle
    """
    oracle_mode = "balanced" if balanced else "constant"
    num_qubits = num_qubits - 1  # because of ancilla qubit
    oracle_gate = dj_oracle(oracle_mode, num_qubits)
    qc = dj_algorithm(oracle_gate, num_qubits)
    qc.name = "dj"

    return qc


@register_reference("dj")
def create_reference(num_qubits: int, balanced: bool = True) -> ReferenceSpec:
    """Reference spec for the Deutsch-Jozsa circuit.

    DJ is deterministic: the measurement reveals whether the oracle is
    balanced (any non-zero string is measured with probability 1) or
    constant (all-zeros string is measured with probability 1).

    For the balanced oracle the exact output bitstring is determined by the
    fixed random seed (``np.random.default_rng(10)``) used in
    :func:`create_circuit`, so we can compute it here without running the
    circuit.

    Qiskit bit-string convention: classical bit *i* maps to qubit *i*, and
    the output string is big-endian over classical bits, so the b_str
    produced by the oracle appears reversed in the counts dict.

    Arguments:
        num_qubits: total qubits including the ancilla (same as :func:`create_circuit`).
        balanced: ``True`` for a balanced oracle, ``False`` for constant.
    """
    n = num_qubits - 1  # input qubits (ancilla excluded)

    if balanced:
        # Reproduce the same RNG sequence used in dj_oracle to get b_str
        rng = np.random.default_rng(10)
        b_str = "".join(str(int(rng.integers(0, 2))) for _ in range(n))
        # Qiskit string: c[n-1]...c[0] = b_str[n-1]...b_str[0] = reversed
        qiskit_string = b_str[::-1]
        kind_value = "balanced"
    else:
        # Constant oracle: input qubits remain |0...0⟩ after H◦H = I
        qiskit_string = "0" * n
        kind_value = "constant"

    return ReferenceSpec(
        circuit="dj",
        n_qubits=num_qubits,
        measured_qubits=list(range(n)),
        bit_order="qiskit-little-endian",
        reference=SparseReference(entries={qiskit_string: 1.0}),
        objective=ObjectiveSpec(type="balanced_or_constant", value=kind_value),
        metrics={
            "hellinger_fidelity": MetricApplicability(applicable=True, ideal=1.0),
            "tvd": MetricApplicability(applicable=True, ideal=0.0),
            "success_probability": MetricApplicability(applicable=True, ideal=1.0),
            "linear_xeb": MetricApplicability(applicable=False),
        },
    )
