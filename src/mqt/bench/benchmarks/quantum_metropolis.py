# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Quantum Metropolis Sampling benchmark definition. Code is based on the paper Temme et al.,: Quantum Metropolis Sampling (2011): https://arxiv.org/abs/0911.3635."""

from __future__ import annotations

import numpy as np
from qiskit.circuit import ClassicalRegister, QuantumCircuit, QuantumRegister

from ._registry import register_benchmark


@register_benchmark("quantum_metropolis", description="Quantum Metropolis Sampling")
def create_circuit(
    num_spin_sites: int, beta: float, num_estimation_qubits: int = 3, num_steps: int = 1, *, for_loop: bool = False
) -> QuantumCircuit:
    r"""Returns a quantum circuit implementing a Quantum Metropolis Sampling step loop.

    The circuit is based on Temme et al. (2011), "Quantum Metropolis Sampling" (https://arxiv.org/abs/0911.3635).
    It allocates four distinct quantum registers: a system register for spin configurations, two energy
    estimation registers for tracking energy updates, and a single-qubit coin register for acceptance sampling.
    Mid-circuit measurement logs the selection result of each step into a dedicated classical register.

    Arguments:
        num_spin_sites: Number of system qubits representing physical state spaces (spins). Must be at least 1.
        beta: The inverse temperature parameter (1/kT) of the thermal environment. Must be positive.
        num_estimation_qubits: Bit precision count for the energy readout registers. Must be at least 1.
        num_steps: Total number of sequential Markov Chain Monte Carlo transition attempts. Must be at least 1.
        for_loop: Whether to wrap repeated steps in a structured ForLoopOp.

    Returns:
        The constructed Quantum Metropolis circuit framework.
    """
    if num_spin_sites < 1:
        msg = "num_spin_sites must be at least 1."
        raise ValueError(msg)

    if not np.isfinite(beta) or beta <= 0:
        msg = "beta must be positive and finite."
        raise ValueError(msg)

    if num_estimation_qubits < 1:
        msg = "num_estimation_qubits must be at least 1."
        raise ValueError(msg)

    if num_steps < 1:
        msg = "num_steps must be at least 1."
        raise ValueError(msg)

    # 1. Register Allocation following Temme et al. layout
    state_q = QuantumRegister(num_spin_sites, "state")
    e1_q = QuantumRegister(num_estimation_qubits, "e1")
    e2_q = QuantumRegister(num_estimation_qubits, "e2")
    coin_q = QuantumRegister(1, "coin")
    c = ClassicalRegister(num_steps, "accept_bits")

    # 2. Main circuit container initialization
    return QuantumCircuit(state_q, e1_q, e2_q, coin_q, c, name="quantum_metropolis")

    # [NEXT STEP WILL ADD IN-LOOP GATES HERE]
