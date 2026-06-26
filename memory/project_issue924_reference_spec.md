---
name: project-issue924-reference-spec
description: Maria's contribution to MQT Bench issue #924 — add noise-free reference outputs for benchmark circuits
metadata:
  type: project
---

Maria is contributing to munich-quantum-toolkit/bench issue #924, which adds expected noise-free output distributions to MQT Bench circuits so downstream users can validate experiments.

**Why:** Without knowing how the circuit generator constructs the oracle (e.g., Grover), users have no ground-truth to test against.

**What was built:**

- `_reference.py` — type hierarchy: `SparseReference`, `UniformReference`, `SimulateReference`, `NoneReference`, `ObjectiveSpec`, `MetricApplicability`, `ReferenceSpec` with `to_dict()` for JSON serialisation
- `_registry.py` — parallel reference registry with `register_reference` decorator and `get_reference_factory_by_name`
- `__init__.py` — public `get_reference_spec(name, size, **kwargs)` and lazy-load-aware `has_reference(name)`
- `create_reference` functions added to: `ghz` (sparse 50/50), `wstate` (uniform hamming_weight==1), `bv` (sparse deterministic), `dj` (sparse deterministic from fixed seed), `grover` (sparse + marked-states objective), `qpeexact` (sparse phase readout), `randomcircuit` (simulate)
- `tests/test_reference.py` — 52 tests covering all kinds, JSON round-trip, and metric fields

**Architecture decisions:**

- `create_reference` mirrors `create_circuit` in each benchmark file, registered via `@register_reference`
- Spec is always poly-size: sparse table, uniform predicate, or "simulate"
- `bit_order: "qiskit-little-endian"` — only Qiskit is used in this repo (no tket/cirq)
- Grover marked state = all-ones on search register (oracle is `mcp(π, q, flag)`)
- DJ/BV/QPE output strings reproduced from the same fixed seeds without running circuits
- Qiskit string convention: reversed hidden_string for BV, reversed b_str for DJ

**What's left for maintainers:**

- Add `create_reference` to the remaining ~25 benchmarks (QAOA, VQE, QFT, adders, AE, etc.)
- QAOA/VQE probably get `NoneReference` (outputs depend on optimised angles)
- Arithmetic circuits could get `SparseReference` if the maintainers know the inputs

**How to apply:** When touching benchmark files, check if a `create_reference` companion is needed. Follow the pattern in `ghz.py` or `bv.py`.
