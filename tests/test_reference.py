# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Tests for the reference-spec framework (issue #924)."""

from __future__ import annotations

import json
import math
import random
from fractions import Fraction

import numpy as np
import pytest

from mqt.bench.benchmarks import (
    NoneReference,
    ReferenceSpec,
    SimulateReference,
    SparseReference,
    UniformReference,
    get_reference_spec,
    has_reference,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _prob_sum(spec: ReferenceSpec) -> float:
    """Return the sum of probabilities stored in a SparseReference."""
    assert isinstance(spec.reference, SparseReference)
    return sum(spec.reference.entries.values())


# ---------------------------------------------------------------------------
# Framework-level tests
# ---------------------------------------------------------------------------


def test_has_reference_known() -> None:
    """has_reference returns True for benchmarks that have a create_reference."""
    for name in ("ghz", "wstate", "bv", "dj", "grover", "qpeexact", "randomcircuit"):
        assert has_reference(name), f"Expected has_reference('{name}') to be True"


def test_has_reference_unknown() -> None:
    """has_reference returns False for benchmarks that exist but lack a create_reference."""
    assert not has_reference("qaoa")
    assert not has_reference("vqe_su2")


def test_has_reference_nonexistent_benchmark() -> None:
    """has_reference returns False (not raises) for a name that is not a benchmark at all."""
    assert not has_reference("not_a_real_benchmark_name")


def test_get_reference_spec_raises_for_no_reference() -> None:
    """get_reference_spec raises ValueError for benchmarks without a spec."""
    with pytest.raises(ValueError, match="No reference spec registered"):
        get_reference_spec("qaoa", 4)


def test_get_reference_spec_raises_for_invalid_size() -> None:
    """get_reference_spec raises ValueError when circuit_size <= 0."""
    with pytest.raises(ValueError, match="circuit_size"):
        get_reference_spec("ghz", 0)


def test_reference_spec_to_dict_is_json_serialisable() -> None:
    """ReferenceSpec.to_dict() must round-trip through JSON without error."""
    for name, size in [("ghz", 4), ("wstate", 3), ("bv", 5), ("dj", 4), ("randomcircuit", 5)]:
        spec = get_reference_spec(name, size)
        d = spec.to_dict()
        serialised = json.dumps(d)
        recovered = json.loads(serialised)
        assert recovered["circuit"] == name
        assert recovered["n_qubits"] == size


# ---------------------------------------------------------------------------
# GHZ reference
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("n", [2, 3, 5, 8])
def test_ghz_reference_structure(n: int) -> None:
    """GHZ reference is a sparse 50/50 distribution over all-zeros and all-ones."""
    spec = get_reference_spec("ghz", n)
    assert spec.circuit == "ghz"
    assert spec.n_qubits == n
    assert spec.measured_qubits == list(range(n))
    assert isinstance(spec.reference, SparseReference)
    assert spec.reference.normalized is True
    assert set(spec.reference.entries.keys()) == {"0" * n, "1" * n}
    assert abs(_prob_sum(spec) - 1.0) < 1e-12
    for p in spec.reference.entries.values():
        assert abs(p - 0.5) < 1e-12


def test_ghz_reference_no_objective() -> None:
    """GHZ has no semantic answer — objective should be None."""
    spec = get_reference_spec("ghz", 3)
    assert spec.objective is None


# ---------------------------------------------------------------------------
# W state reference
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("n", [2, 3, 5, 8])
def test_wstate_reference_structure(n: int) -> None:
    """W-state reference is a uniform distribution over weight-1 bitstrings."""
    spec = get_reference_spec("wstate", n)
    assert spec.circuit == "wstate"
    assert spec.n_qubits == n
    assert isinstance(spec.reference, UniformReference)
    assert spec.reference.predicate == "hamming_weight == 1"
    assert spec.reference.size == n


def test_wstate_reference_probability() -> None:
    """P(x) = 1/n for any weight-1 bitstring."""
    n = 5
    spec = get_reference_spec("wstate", n)
    assert isinstance(spec.reference, UniformReference)
    p = 1.0 / spec.reference.size
    assert abs(p - 1.0 / n) < 1e-12


def test_wstate_reference_success_metric() -> None:
    """W-state success_probability metric should have ideal value 1."""
    spec = get_reference_spec("wstate", 4)
    assert "success_probability" in spec.metrics
    ideal = spec.metrics["success_probability"].ideal
    assert ideal is not None
    assert math.isclose(ideal, 1.0)


# ---------------------------------------------------------------------------
# Bernstein-Vazirani reference
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("n", [3, 5, 7])
def test_bv_reference_structure(n: int) -> None:
    """BV reference is a single-entry sparse distribution with probability 1."""
    spec = get_reference_spec("bv", n)
    assert spec.circuit == "bv"
    assert spec.n_qubits == n
    assert isinstance(spec.reference, SparseReference)
    assert len(spec.reference.entries) == 1
    assert abs(_prob_sum(spec) - 1.0) < 1e-12


@pytest.mark.parametrize("n", [3, 5, 7])
def test_bv_reference_default_hidden_string(n: int) -> None:
    """Default hidden string is alternating 0/1 of length n-1; Qiskit string is its reverse."""
    expected_hidden = "".join(str(i % 2) for i in range(n - 1))
    spec = get_reference_spec("bv", n)
    assert spec.objective is not None
    assert spec.objective.type == "hidden_string"
    assert spec.objective.value == expected_hidden
    assert isinstance(spec.reference, SparseReference)
    (qiskit_string,) = spec.reference.entries.keys()
    assert qiskit_string == expected_hidden[::-1]


def test_bv_reference_custom_hidden_string() -> None:
    """Custom hidden strings are handled correctly; Qiskit string is reversed."""
    spec = get_reference_spec("bv", 4, hidden_string="110")
    assert spec.objective is not None
    assert spec.objective.value == "110"
    assert isinstance(spec.reference, SparseReference)
    (qiskit_string,) = spec.reference.entries.keys()
    assert qiskit_string == "011"


# ---------------------------------------------------------------------------
# Deutsch-Jozsa reference
# ---------------------------------------------------------------------------


def test_dj_balanced_reference() -> None:
    """Balanced DJ: single non-zero measurement string derived from fixed seed."""
    n_total = 4
    n_input = n_total - 1

    spec = get_reference_spec("dj", n_total, balanced=True)
    assert isinstance(spec.reference, SparseReference)
    assert len(spec.reference.entries) == 1
    assert abs(_prob_sum(spec) - 1.0) < 1e-12

    rng = np.random.default_rng(10)
    b_str = "".join(str(int(rng.integers(0, 2))) for _ in range(n_input))
    expected_qiskit = b_str[::-1]

    (measured,) = spec.reference.entries.keys()
    assert measured == expected_qiskit, f"Expected '{expected_qiskit}', got '{measured}'"

    assert spec.objective is not None
    assert spec.objective.value == "balanced"


def test_dj_constant_reference() -> None:
    """Constant DJ: measurement is always the all-zeros string."""
    n_total = 4
    n_input = n_total - 1

    spec = get_reference_spec("dj", n_total, balanced=False)
    assert isinstance(spec.reference, SparseReference)
    (measured,) = spec.reference.entries.keys()
    assert measured == "0" * n_input
    assert spec.objective is not None
    assert spec.objective.value == "constant"


def test_dj_balanced_measured_qubits_exclude_ancilla() -> None:
    """The flag ancilla is not included in measured_qubits."""
    n_total = 5
    spec = get_reference_spec("dj", n_total, balanced=True)
    assert spec.measured_qubits == list(range(n_total - 1))


# ---------------------------------------------------------------------------
# Grover reference
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("n", [3, 5, 7])
def test_grover_reference_structure(n: int) -> None:
    """Grover reference is a single-entry sparse distribution for the marked state."""
    spec = get_reference_spec("grover", n)
    assert spec.circuit == "grover"
    assert spec.n_qubits == n
    assert isinstance(spec.reference, SparseReference)
    assert len(spec.reference.entries) == 1


@pytest.mark.parametrize("n", [3, 5, 7])
def test_grover_marked_state_is_all_ones(n: int) -> None:
    """Grover oracle marks the all-ones state on the search register."""
    spec = get_reference_spec("grover", n)
    n_search = n - 1
    assert isinstance(spec.reference, SparseReference)
    (marked,) = spec.reference.entries.keys()
    assert marked == "1" * n_search
    assert spec.objective is not None
    assert spec.objective.type == "marked_states"
    assert spec.objective.value == ["1" * n_search]


@pytest.mark.parametrize("n", [3, 5, 7])
def test_grover_success_probability_in_range(n: int) -> None:
    """Grover success probability must be in (0, 1]."""
    spec = get_reference_spec("grover", n)
    assert isinstance(spec.reference, SparseReference)
    (p,) = spec.reference.entries.values()
    assert 0.0 < p <= 1.0


@pytest.mark.parametrize("n", [3, 5, 7])
def test_grover_measured_qubits_exclude_flag(n: int) -> None:
    """Only the search-register qubits (0..n_search-1) are listed in measured_qubits."""
    spec = get_reference_spec("grover", n)
    assert spec.measured_qubits == list(range(n - 1))


# ---------------------------------------------------------------------------
# QPE-exact reference
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("n", [2, 3, 5])
def test_qpeexact_reference_structure(n: int) -> None:
    """QPE-exact reference is a single-entry sparse distribution with probability 1."""
    spec = get_reference_spec("qpeexact", n)
    assert spec.circuit == "qpeexact"
    assert spec.n_qubits == n
    assert isinstance(spec.reference, SparseReference)
    assert len(spec.reference.entries) == 1
    (p,) = spec.reference.entries.values()
    assert abs(p - 1.0) < 1e-12


@pytest.mark.parametrize("n", [2, 3, 5])
def test_qpeexact_reference_bitstring_matches_seed(n: int) -> None:
    """The output bitstring must match theta derived from random.seed(10)."""
    n_est = n - 1

    random.seed(10)
    theta = 0
    while theta == 0:
        theta = random.getrandbits(n_est)

    lam = Fraction(0, 1)
    for i in range(n_est):
        if theta & (1 << (n_est - i - 1)):
            lam += Fraction(1, (1 << i))

    expected_string = format(theta, f"0{n_est}b")

    spec = get_reference_spec("qpeexact", n)
    assert isinstance(spec.reference, SparseReference)
    (measured,) = spec.reference.entries.keys()
    assert measured == expected_string

    assert spec.objective is not None
    assert spec.objective.type == "phase"
    assert abs(spec.objective.value - float(lam)) < 1e-12


def test_qpeexact_reference_raises_for_one_qubit() -> None:
    """QPE-exact requires at least 2 qubits; fewer should raise."""
    with pytest.raises(ValueError, match="at least 2"):
        get_reference_spec("qpeexact", 1)


# ---------------------------------------------------------------------------
# Random circuit reference
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("n", [3, 5])
def test_randomcircuit_reference_kind(n: int) -> None:
    """Random circuit reference has kind=simulate and no objective."""
    spec = get_reference_spec("randomcircuit", n)
    assert spec.circuit == "randomcircuit"
    assert isinstance(spec.reference, SimulateReference)
    assert spec.reference.max_qubits >= n
    assert spec.objective is None


# ---------------------------------------------------------------------------
# to_dict contract
# ---------------------------------------------------------------------------


def test_to_dict_sparse() -> None:
    """SparseReference serialises with kind=sparse and an entries dict."""
    spec = get_reference_spec("ghz", 2)
    d = spec.to_dict()
    assert d["reference"]["kind"] == "sparse"
    assert "00" in d["reference"]["entries"]
    assert "11" in d["reference"]["entries"]


def test_to_dict_uniform() -> None:
    """UniformReference serialises with kind=uniform and a size field."""
    spec = get_reference_spec("wstate", 3)
    d = spec.to_dict()
    assert d["reference"]["kind"] == "uniform"
    assert d["reference"]["size"] == 3


def test_to_dict_simulate() -> None:
    """SimulateReference serialises with kind=simulate."""
    spec = get_reference_spec("randomcircuit", 4)
    d = spec.to_dict()
    assert d["reference"]["kind"] == "simulate"


def test_to_dict_none_reference() -> None:
    """NoneReference serialises correctly with and without a reason string."""
    ref = NoneReference(reason="no compact form")
    assert ref.to_dict() == {"kind": "none", "reason": "no compact form"}

    ref_no_reason = NoneReference()
    assert ref_no_reason.to_dict() == {"kind": "none"}


def test_to_dict_metrics_present() -> None:
    """Metrics appear in the dict when the spec defines them."""
    spec = get_reference_spec("bv", 5)
    d = spec.to_dict()
    assert "metrics" in d
    assert d["metrics"]["success_probability"]["applicable"] is True
    assert math.isclose(d["metrics"]["success_probability"]["ideal"], 1.0)
