# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Simon's algorithm benchmark definition."""

from __future__ import annotations

from qiskit.circuit import ClassicalRegister, QuantumCircuit, QuantumRegister

from ._registry import register_benchmark


@register_benchmark("simon", description="Simon's Algorithm")
def create_circuit(num_qubits: int, hidden_string: str | None = None) -> QuantumCircuit:
    r"""Build Simon's circuit for a hidden nonzero binary string.

    The oracle implements the two-to-one function of Simon (1997, SIAM J. Comput.
    26, 1474). Inputs that differ by the hidden string give the same output.

    Args:
        num_qubits: Total width of the equal input and output registers. Must be even
            and at least 2.
        hidden_string: Binary string of length ``num_qubits // 2`` containing at least
            one ``1``. Character ``i`` belongs to input qubit ``i``. The default alternates
            ones and zeros, starting with one.

    Returns:
        A circuit that measures only the input register. Each ideal outcome :math:`y`
        satisfies :math:`y \cdot s = 0 \pmod 2` for the hidden string :math:`s`.
    """
    if num_qubits < 2 or num_qubits % 2 != 0:
        msg = "num_qubits must be an even integer ≥ 2."
        raise ValueError(msg)

    n = num_qubits // 2

    if hidden_string is None:
        hidden_string = "".join("1" if i % 2 == 0 else "0" for i in range(n))

    if len(hidden_string) != n or not set(hidden_string).issubset({"0", "1"}):
        msg = f"Invalid hidden_string '{hidden_string}'. Must be a binary string of length {n}."
        raise ValueError(msg)

    if "1" not in hidden_string:
        msg = "hidden_string must contain at least one '1'."
        raise ValueError(msg)

    inputs = QuantumRegister(n, "q")
    outputs = QuantumRegister(n, "out")
    c = ClassicalRegister(n, "c")
    qc = QuantumCircuit(inputs, outputs, c, name="simon")

    qc.h(inputs)
    qc.barrier()

    # Oracle: copy the input register and, conditioned on x_j, XOR in the hidden string.
    for i in range(n):
        qc.cx(inputs[i], outputs[i])
    j = hidden_string.index("1")
    for i, bit in enumerate(hidden_string):
        if bit == "1":
            qc.cx(inputs[j], outputs[i])
    qc.barrier()

    qc.h(inputs)
    qc.measure(inputs, c)

    return qc
