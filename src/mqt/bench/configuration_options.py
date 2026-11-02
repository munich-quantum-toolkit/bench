# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Configuration options for the MQT Bench library."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from collections.abc import Iterable

    from qiskit.circuit import Gate, QuantumCircuit

__all__ = ["ConfigurationOptions"]


class ConfigurationOptions(TypedDict, total=False):
    """Configuration options for benchmark generation.

    All fields are optional. Each factory accepts only its documented options.
    The shared seed also controls random parameter values and is passed to
    factories that accept it.
    """

    seed: int | None
    """Random seed for parameter values and factories that accept a seed (None for random behavior)."""

    hidden_string: str | None
    balanced: bool
    dynamic: bool
    message: str | None
    kind: str
    degree: int
    depth: int
    for_loop: bool
    probability: float
    exact: bool
    rotation_threshold: float
    num_rounds: int
    b_max: float
    reps: int
    repetitions: int
    entanglement: str
    rotation_blocks: str | Gate | Iterable[str | Gate]
    entanglement_blocks: str | Gate | Iterable[str | Gate]
    state_preparation: QuantumCircuit | None
    coin_state_preparation: QuantumCircuit | None
    num_evaluation_qubits: int
    beta: float
    num_steps: int
    num_trotter_steps: int
