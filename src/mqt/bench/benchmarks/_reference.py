"""Reference specification types for noise-free benchmark outputs.

Each benchmark can optionally expose a ``create_reference`` function (registered
via :func:`register_reference`) that returns a :class:`ReferenceSpec` describing
the ideal, noise-free output distribution in a compact, evaluable form.

The spec is deliberately *poly-size* even for exponentially large Hilbert spaces:
it stores a *description* of the distribution (sparse table, uniform predicate,
analytic form, or semantic objective) rather than a dense state vector.

Calling :func:`~mqt.bench.benchmarks.get_reference_spec` returns the spec as a
:class:`ReferenceSpec` object; call :meth:`ReferenceSpec.to_dict` to get a
plain ``dict`` that serialises cleanly to JSON.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SparseReference:
    """Explicit probability table for circuits with a small support.

    Suitable for: GHZ, BV, DJ, QPE, Grover (few high-probability states).
    """

    entries: dict[str, float]
    normalized: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {"kind": "sparse", "normalized": self.normalized, "entries": self.entries}


@dataclass
class UniformReference:
    """Uniform distribution over a predicate-defined support.

    Stores only the predicate string and support size, so P(x) = 1/size
    whenever the predicate holds and 0 otherwise.  Evaluable in O(1) per
    bitstring without enumerating the full support.

    Suitable for: W state (``hamming_weight == 1``), random Clifford states, etc.
    """

    predicate: str
    size: int

    def to_dict(self) -> dict[str, Any]:
        return {"kind": "uniform", "predicate": self.predicate, "size": self.size}


@dataclass
class SimulateReference:
    """Reference to be obtained by classical statevector simulation.

    Used when no compact closed-form is available but simulation is feasible.
    ``max_qubits`` is advisory: indicate the largest instance the team has
    pre-simulated (or considers tractable).
    """

    max_qubits: int = 30

    def to_dict(self) -> dict[str, Any]:
        return {"kind": "simulate", "max_qubits": self.max_qubits}


@dataclass
class NoneReference:
    """No reference distribution available.

    Used for variational / parameterised circuits (QAOA, VQE) where the
    output depends on optimised angles, or for circuits whose output is
    essentially random (random circuits beyond simulation limits).
    """

    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"kind": "none"}
        if self.reason:
            d["reason"] = self.reason
        return d


ReferenceKind = SparseReference | UniformReference | SimulateReference | NoneReference


@dataclass
class ObjectiveSpec:
    """Semantic objective — the *answer* the circuit is meant to find.

    Complements the reference distribution: even when the distribution has
    many non-zero entries, the objective pins down what "correct" means.

    Examples of ``type`` values and their ``value`` payloads:

    * ``"marked_states"``   – list of target bitstrings (Grover)
    * ``"hidden_string"``   – the secret bitstring (BV)
    * ``"balanced_or_constant"`` – ``"balanced"`` or ``"constant"`` (DJ)
    * ``"phase"``           – estimated phase as a float (QPE)
    """

    type: str
    value: Any = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"type": self.type}
        if self.value is not None:
            d["value"] = self.value
        return d


@dataclass
class MetricApplicability:
    """Whether a standard metric applies to this benchmark and its ideal value."""

    applicable: bool
    ideal: float | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"applicable": self.applicable}
        if self.ideal is not None:
            d["ideal"] = self.ideal
        return d


@dataclass
class ReferenceSpec:
    """Complete reference specification for one benchmark instance.

    Fields
    ------
    circuit:
        Benchmark name (matches the registry key, e.g. ``"ghz"``).
    n_qubits:
        Total number of qubits in the circuit as returned by ``create_circuit``.
    measured_qubits:
        Indices (in circuit qubit order) of the qubits that contribute to the
        classical output string.  Ancilla omitted.
    bit_order:
        ``"qiskit-little-endian"`` 
    reference:
        Compact description of the ideal probability distribution.
    objective:
        Optional semantic answer.
    metrics:
        Map from metric name to applicability and ideal value.
        Standard keys: ``"hellinger_fidelity"``, ``"tvd"``,
        ``"success_probability"``, ``"linear_xeb"``.
    """

    circuit: str
    n_qubits: int
    measured_qubits: list[int]
    bit_order: str
    reference: ReferenceKind
    objective: ObjectiveSpec | None = None
    metrics: dict[str, MetricApplicability] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable dict representation."""
        d: dict[str, Any] = {
            "circuit": self.circuit,
            "n_qubits": self.n_qubits,
            "measured_qubits": self.measured_qubits,
            "bit_order": self.bit_order,
            "reference": self.reference.to_dict(),
        }
        if self.objective is not None:
            d["objective"] = self.objective.to_dict()
        if self.metrics:
            d["metrics"] = {k: v.to_dict() for k, v in self.metrics.items()}
        return d
