# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Quantum Metropolis Sampling benchmark definition. Code is based on the paper Temme et al.: Quantum Metropolis Sampling (2011): https://arxiv.org/abs/0911.3635."""

from __future__ import annotations

import math

from qiskit.circuit import ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit.circuit.library import MCXGate, PauliEvolutionGate, RYGate, phase_estimation
from qiskit.quantum_info import SparsePauliOp
from qiskit.synthesis import LieTrotter

from ._registry import register_benchmark


def _heisenberg_hamiltonian(num_spins: int) -> SparsePauliOp:
    r"""Return the open Heisenberg chain :math:`-\frac{1}{2}\sum_i (X_i X_{i+1} + Y_i Y_{i+1} + Z_i Z_{i+1})` (Eq. 79)."""
    terms = [(pauli * 2, [i, i + 1], -0.5) for i in range(num_spins - 1) for pauli in "XYZ"]
    return SparsePauliOp.from_sparse_list(terms, num_qubits=num_spins)


def _phase_estimation(
    num_spins: int, num_evaluation_qubits: int, time: float, shift: float, num_trotter_steps: int
) -> QuantumCircuit:
    r"""Return the phase estimation :math:`\Phi` that writes the energy bin of an eigenstate to the pointer (Sec. 5).

    The qubits are the pointer first, then the system. The pointer holds the bin as a little-endian integer.
    """
    # Qiskit's phase estimation reads the phase phi of U = e^(2 pi i phi). With U = e^(+i (H + shift) t),
    # phi = E t / (2 pi), so the result grows with the energy E.
    # Synthesize the Trotter product into gates first. The inverse of a circuit reverses its gate order exactly.
    # The inverse of an unsynthesized PauliEvolutionGate negates the time but keeps the term order, so it does not
    # undo the Trotter product when the terms do not commute (three or more spins).
    hamiltonian = _heisenberg_hamiltonian(num_spins)
    evolution = LieTrotter(reps=num_trotter_steps).synthesize(PauliEvolutionGate(hamiltonian, time=-time))
    evolution.name = "U_H"
    # Adding the shift to H multiplies U by a phase. Phase estimation controls U, so this phase is measured.
    evolution.global_phase += shift * time

    # Qiskit's phase estimation writes the most significant bit to the first pointer qubit. Reverse the pointer
    # qubits so that pointer qubit j holds bit j.
    r = num_evaluation_qubits
    qc = QuantumCircuit(r + num_spins, name="PE")
    qc.compose(phase_estimation(r, evolution), [*reversed(range(r)), *range(r, r + num_spins)], inplace=True)
    return qc


def _estimate_and_rotate(
    phase_estimation: QuantumCircuit, num_spins: int, num_evaluation_qubits: int, beta: float, bin_width: float
) -> QuantumCircuit:
    r"""Return :math:`W \Phi`, the part of :math:`U = W \Phi C` (Fig. 1b) after the update :math:`C`.

    :math:`W` rotates the accept qubit by :math:`2 \arcsin\sqrt{f}` with :math:`f = \min(1, e^{-\beta (E_k - E_i)})`
    (Eqs. 2 and 3). It uses one multi-controlled :math:`R_y` gate for each pair of energy bins.
    """
    r = num_evaluation_qubits
    qc = QuantumCircuit(num_spins + 2 * r + 1, name="W_PE")
    system = list(range(num_spins))
    e_old = list(range(num_spins, num_spins + r))
    e_new = list(range(num_spins + r, num_spins + 2 * r))
    accept = num_spins + 2 * r

    qc.compose(phase_estimation, [*e_new, *system], inplace=True)
    for k_new in range(2**r):
        for k_old in range(2**r):
            energy_change = bin_width * (k_new - k_old)
            f = 1.0 if energy_change <= 0 else math.exp(-beta * energy_change)  # min(1, e^(-beta dE))
            angle = 2 * math.asin(math.sqrt(f))
            control_state = k_old + (k_new << r)  # little-endian over [e_old..., e_new...]
            rotation = RYGate(angle).control(2 * r, ctrl_state=control_state, annotated=False)
            qc.append(rotation, [*e_old, *e_new, accept])
    return qc


@register_benchmark("quantum_metropolis", description="Quantum Metropolis Sampling")
def create_circuit(
    num_qubits: int,
    num_evaluation_qubits: int = 1,
    beta: float = 1.0,
    num_steps: int = 1,
    num_trotter_steps: int = 1,
) -> QuantumCircuit:
    r"""Returns a dynamic quantum circuit implementing Quantum Metropolis Sampling.

    The circuit follows Temme et al. (2011), "Quantum Metropolis Sampling" (https://arxiv.org/abs/0911.3635),
    Sec. 3 and Figs. 1 to 3, for the open Heisenberg chain of Eq. 79. The qubits form the four registers of
    Step 0: ``num_qubits - 2 * num_evaluation_qubits - 1`` system spins, the energy register :math:`|E_i\rangle`,
    the phase estimation pointer :math:`|E_k\rangle`, and the accept qubit. The energy register and the pointer
    have ``num_evaluation_qubits`` qubits each. With ``num_qubits = 5`` and one evaluation qubit, the circuit is
    the five-qubit experiment of Sec. 8.

    Each Metropolis step:

    0. Measure the reset accept qubit in the :math:`X` basis twice. The two random bits select the update
       :math:`C \in \{X, Z\}` on the first or second spin (Sec. 8, Step 2). Pauli updates are Hermitian, so the
       update measure is symmetric, as detailed balance requires (Eq. 31).
    1. Apply phase estimation, copy the result into the energy register, undo the phase estimation, and measure
       the energy register (Fig. 1a). This step prepares an eigenstate with known energy :math:`E_i`.
    2. Apply :math:`U = W \Phi C` (Fig. 1b) and measure the accept qubit.
    3. Accept: measure the pointer to read :math:`E_k` and undo the phase estimation.
       Reject: apply :math:`U^\dagger`, then repeat the binary measurements :math:`P` (Fig. 1c) and
       :math:`Q = U^\dagger (|s\rangle\langle s|) U` until :math:`P` returns the energy :math:`E_i` (Fig. 2).
    4. Reset the energy register, the pointer, and the accept qubit (Step 4).

    The classical register ``energy`` holds the energy bin of the current state: :math:`E_i` during a step,
    :math:`E_k` after an accepted update, and the sampled energy after a final step 1 at the end.

    The measurement in step 1 leaves the energy register in a known basis state. The measurement :math:`P`
    therefore uses the first qubit of the energy register as a flag and prepares :math:`|E_i\rangle` again from
    the classical result (Sec. 8 notes that the circuit can condition on this classical result).

    Bin ``k`` of an ``r``-qubit register has the energy :math:`4 (n - 1) k / 2^r` for ``n`` spins. Rounding the energies to
    ``r`` bits gives an error of order :math:`\beta 2^{-r}` (Sec. 4).

    Arguments:
        num_qubits: Total number of qubits, that is, system spins + ``2 * num_evaluation_qubits`` + 1.
            The chain needs at least two spins.
        num_evaluation_qubits: Bits of precision ``r`` of the energy register and the pointer. Must be at least 1.
            The Metropolis gate :math:`W` uses :math:`4^r` multi-controlled rotations.
        beta: Inverse temperature. Must be non-negative and finite.
        num_steps: Number of Metropolis steps. Must be at least 1.
        num_trotter_steps: Number of Lie-Trotter steps for the shortest time evolution in the phase estimation.
            The evolution is exact for two spins. For more spins, the error decreases as ``1 / num_trotter_steps``.

    Returns:
        The constructed Quantum Metropolis Sampling circuit.
    """
    if num_evaluation_qubits < 1:
        msg = "num_evaluation_qubits must be at least 1."
        raise ValueError(msg)
    num_spins = num_qubits - 2 * num_evaluation_qubits - 1
    if num_spins < 2:
        msg = "num_qubits must be at least 2 * num_evaluation_qubits + 3."
        raise ValueError(msg)
    if not math.isfinite(beta) or beta < 0:
        msg = "beta must be non-negative and finite."
        raise ValueError(msg)
    if num_steps < 1:
        msg = "num_steps must be at least 1."
        raise ValueError(msg)
    if num_trotter_steps < 1:
        msg = "num_trotter_steps must be at least 1."
        raise ValueError(msg)

    r = num_evaluation_qubits

    # Each neighboring pair has energy -1/2 (triplet) or 3/2 (singlet). Phase estimation needs energies >= 0
    # (Sec. 5), so add 1/2 per pair: each pair then contributes 0 or 2.
    num_pairs = num_spins - 1
    shift = 0.5 * num_pairs
    max_energy = 2.0 * num_pairs
    # Phase estimation reads the phase E * time / (2 pi), which must stay below 1 (Sec. 5). With this time, the
    # phase of max_energy is 1/2. For two spins, time = pi / 2 and the evolution is SWAP (Eq. 80).
    time = math.pi / max_energy
    # The pointer covers energies 0 to 2 * max_energy in 2**r bins, so bin k has energy k * bin_width.
    bin_width = math.ldexp(2 * max_energy, -r)

    system = QuantumRegister(num_spins, "system")
    e_old = QuantumRegister(r, "energy_register")
    e_new = QuantumRegister(r, "pointer")
    accept = QuantumRegister(1, "accept")
    c_update = ClassicalRegister(2, "update")
    c_energy = ClassicalRegister(r, "energy")
    c_accept = ClassicalRegister(1, "accepted")
    c_p = ClassicalRegister(1, "p_outcome")
    qc = QuantumCircuit(system, e_old, e_new, accept, c_update, c_energy, c_accept, c_p, name="quantum_metropolis")

    phase_estimation = _phase_estimation(num_spins, r, time, shift, num_trotter_steps)
    estimate_and_rotate = _estimate_and_rotate(phase_estimation, num_spins, r, beta, bin_width)
    pe_qubits = [*e_new, *system]
    u_qubits = [*system, *e_old, *e_new, *accept]
    flag = e_old[0]

    def apply_update() -> None:
        """Apply the update C selected by the two random bits: bit 0 picks the spin, bit 1 picks X or Z."""
        for value, (spin, pauli) in enumerate([(0, "x"), (1, "x"), (0, "z"), (1, "z")]):
            with qc.if_test((c_update, value)):
                getattr(qc, pauli)(system[spin])

    def apply_u() -> None:
        apply_update()
        qc.compose(estimate_and_rotate, u_qubits, inplace=True)

    def apply_u_inverse() -> None:
        qc.compose(estimate_and_rotate.inverse(), u_qubits, inplace=True)
        apply_update()  # Pauli updates are their own inverse

    def read_energy(target: ClassicalRegister) -> None:
        """Step 1 (Fig. 1a): project onto an eigenstate and measure its energy bin."""
        qc.compose(phase_estimation, pe_qubits, inplace=True)
        qc.cx(e_new, e_old)
        qc.compose(phase_estimation.inverse(), pe_qubits, inplace=True)
        qc.measure(e_old, target)

    def measure_p() -> None:
        """Measurement P (Fig. 1c): check whether the current energy bin equals E_i."""
        qc.reset(e_old)  # the classical register holds E_i, so the energy register is free for the flag
        qc.compose(phase_estimation, pe_qubits, inplace=True)
        for j in range(r):  # the pointer is all ones exactly when its bin equals E_i
            with qc.if_test((c_energy[j], 0)):
                qc.x(e_new[j])
        qc.append(MCXGate(r), [*e_new, flag])
        qc.measure(flag, c_p[0])
        qc.append(MCXGate(r), [*e_new, flag])  # return the flag to |0> for both outcomes
        for j in range(r):
            with qc.if_test((c_energy[j], 0)):
                qc.x(e_new[j])
        qc.compose(phase_estimation.inverse(), pe_qubits, inplace=True)
        for j in range(r):  # prepare |E_i> again for W
            with qc.if_test((c_energy[j], 1)):
                qc.x(e_old[j])

    def measure_q() -> None:
        """Measurement Q = U^dagger (|s><s|) U on the accept qubit (Sec. 3, Step 4)."""
        apply_u()
        qc.measure(accept[0], c_p[0])  # the outcome of Q is not used; the next P overwrites this bit
        apply_u_inverse()

    for _ in range(num_steps):
        # Step 0: draw the update with the reset accept qubit.
        for bit in c_update:
            qc.h(accept[0])
            qc.measure(accept[0], bit)
            qc.reset(accept[0])

        # Step 1: eigenstate with known energy E_i.
        read_energy(c_energy)

        # Step 2: propose C, estimate E_k, and rotate the accept qubit with W.
        apply_u()
        qc.measure(accept[0], c_accept[0])

        # Step 3: accept, or reject with the repeat-until-success loop of Fig. 2.
        with qc.if_test((c_accept[0], 1)) as else_:
            qc.measure(e_new, c_energy)
            qc.compose(phase_estimation.inverse(), pe_qubits, inplace=True)
        with else_:
            apply_u_inverse()
            measure_p()
            with qc.while_loop((c_p[0], 0)):
                measure_q()
                measure_p()

        # Step 4: reset the ancilla registers for the next step.
        qc.reset([*e_old, *e_new, *accept])

    read_energy(c_energy)
    return qc