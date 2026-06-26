"""Grover benchmark definition."""

from __future__ import annotations

import numpy as np
from qiskit.circuit import AncillaRegister, QuantumCircuit, QuantumRegister
from qiskit.circuit.library import grover_operator

from ._reference import MetricApplicability, ObjectiveSpec, ReferenceSpec, SparseReference
from ._registry import register_benchmark, register_reference


@register_benchmark("grover", description="Grover's Algorithm")
def create_circuit(num_qubits: int) -> QuantumCircuit:
    """Returns a quantum circuit implementing Grover's algorithm.

    Arguments:
        num_qubits: number of qubits of the returned quantum circuit
    """
    num_qubits = num_qubits - 1  # -1 because of the flag qubit
    q = QuantumRegister(num_qubits, "q")
    flag = AncillaRegister(1, "flag")

    state_preparation = QuantumCircuit(q, flag)
    state_preparation.h(q)
    state_preparation.x(flag)

    oracle = QuantumCircuit(q, flag)
    oracle.mcp(np.pi, q, flag)

    operator = grover_operator(oracle)
    iterations = int(np.pi / 4 * np.sqrt(2**num_qubits))

    num_qubits = operator.num_qubits - 1  # -1 because last qubit is "flag" qubit and already taken care of

    # num_qubits may differ now depending on the mcx_mode
    q2 = QuantumRegister(num_qubits, "q")
    qc = QuantumCircuit(q2, flag, name="grover")
    qc.compose(state_preparation, inplace=True)

    qc.compose(operator.power(iterations), inplace=True)
    qc.measure_all()
    qc.name = qc.name

    return qc


@register_reference("grover")
def create_reference(num_qubits: int) -> ReferenceSpec:
    """Reference spec for the Grover circuit.

    The oracle ``mcp(π, q, flag)`` marks the all-ones state on the search
    register (all ``num_qubits - 1`` computational qubits set to |1⟩).
    After the optimal number of Grover iterations the marked state is
    amplified to approximate success probability P_success.

    The ``measured_qubits`` field lists only the *search-register* qubit
    indices (0..n_search-1).  The flag and any ancillas added by
    ``grover_operator`` are not included because they carry no search
    information.

    Arguments:
        num_qubits: total qubits passed to :func:`create_circuit` (search
            register = ``num_qubits - 1`` qubits).
    """
    n_search = num_qubits - 1
    n_states = 2**n_search
    iterations = int(np.pi / 4 * np.sqrt(n_states))
    theta = np.arcsin(1.0 / np.sqrt(n_states))
    p_success = float(np.sin((2 * iterations + 1) * theta) ** 2)

    # Marked state on the search register: all-ones.
    # In Qiskit's big-endian counts string this is "1" * n_search.
    marked_state = "1" * n_search

    return ReferenceSpec(
        circuit="grover",
        n_qubits=num_qubits,
        measured_qubits=list(range(n_search)),
        bit_order="qiskit-little-endian",
        reference=SparseReference(entries={marked_state: p_success}),
        objective=ObjectiveSpec(type="marked_states", value=[marked_state]),
        metrics={
            "hellinger_fidelity": MetricApplicability(applicable=True),
            "tvd": MetricApplicability(applicable=True),
            "success_probability": MetricApplicability(applicable=True, ideal=p_success),
            "linear_xeb": MetricApplicability(applicable=False),
        },
    )
