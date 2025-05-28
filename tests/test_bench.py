# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Tests for the benchmark generation."""

from __future__ import annotations

import builtins
import io
import re
from datetime import date
from importlib import metadata
from pathlib import Path
from typing import TYPE_CHECKING, Callable, NoReturn, cast

from qiskit.circuit import Parameter
from qiskit.circuit.library import CXGate, HGate, RXGate, RZGate, XGate
from qiskit.transpiler import InstructionProperties, PassManager, Target
from qiskit.transpiler.passes import GatesInBasis

from mqt.bench.targets.devices import get_available_device_names, get_device
from mqt.bench.targets.gatesets import get_available_gateset_names, get_target_for_gateset

if TYPE_CHECKING:  # pragma: no cover
    import types

import functools
from enum import Enum

import pytest
from qiskit import QuantumCircuit, qpy

from mqt.bench.benchmark_generation import (
    BenchmarkLevel,
    get_benchmark,
    get_benchmark_alg,
    get_benchmark_indep,
    get_benchmark_mapped,
    get_benchmark_native_gates,
    get_module_for_benchmark,
    get_supported_benchmarks,
)
from mqt.bench.benchmarks import (
    ae,
    bmw_quark_cardinality,
    bmw_quark_copula,
    bv,
    dj,
    ghz,
    graphstate,
    grover,
    qaoa,
    qft,
    qftentangled,
    qnn,
    qpeexact,
    qpeinexact,
    qwalk,
    randomcircuit,
    shor,
    vqe_real_amp,
    vqe_su2,
    vqe_two_local,
    wstate,
)
from mqt.bench.output import (
    MQTBenchExporterError,
    OutputFormat,
    __qiskit_version__,
    generate_filename,
    generate_header,
    save_circuit,
    write_circuit,
)
from mqt.bench.targets import get_available_devices, get_available_native_gatesets


@pytest.fixture
def output_path() -> str:
    """Fixture to create the output path for the tests."""
    output_path = Path("./tests/test_output/")
    output_path.mkdir(parents=True, exist_ok=True)
    return str(output_path)


@pytest.mark.parametrize(
    ("benchmark", "input_value"),
    [
        (ae, 3),
        (bv, 3),
        (ghz, 2),
        (dj, 3),
        (graphstate, 3),
        (grover, 3),
        (qaoa, 3),
        (qft, 3),
        (qftentangled, 3),
        (qnn, 3),
        (qpeexact, 3),
        (qpeinexact, 3),
        (bmw_quark_cardinality, 3),
        (bmw_quark_copula, 4),
        (qwalk, 3),
        (randomcircuit, 3),
        (vqe_real_amp, 3),
        (vqe_su2, 3),
        (vqe_two_local, 3),
        (wstate, 3),
        (shor, 18),
    ],
)
def test_quantumcircuit_levels(benchmark: types.ModuleType, input_value: int) -> None:
    """Test the creation of the algorithm level benchmarks for the benchmarks."""
    qc = benchmark.create_circuit(input_value)
    assert isinstance(qc, QuantumCircuit)
    assert qc.num_qubits == input_value
    assert benchmark.__name__.split(".")[-1] in qc.name

    res_alg = get_benchmark_alg(qc)
    assert res_alg
    assert res_alg.num_qubits == input_value

    res_indep = get_benchmark_indep(qc)
    assert res_indep
    assert res_indep.num_qubits == input_value

    if benchmark != shor:
        for gateset_name in get_available_native_gatesets():
            gateset = get_target_for_gateset(gateset_name, num_qubits=qc.num_qubits)
            res_native_gates = get_benchmark_native_gates(
                qc,
                None,
                gateset,
                0,
            )

            assert res_native_gates
            assert res_native_gates.num_qubits == input_value

        for device in get_available_devices().values():
            res_mapped = get_benchmark_mapped(
                qc,
                None,
                device,
                0,
            )
            assert res_mapped


def test_bv() -> None:
    """Test the creation of the BV benchmark."""
    qc = bv.create_circuit(3)
    assert qc.depth() > 0
    assert qc.num_qubits == 3
    assert "bv" in qc.name

    qc = bv.create_circuit(3, dynamic=True)
    assert qc.depth() > 0
    assert qc.num_qubits == 3
    assert "bv" in qc.name

    with pytest.raises(ValueError, match=r"Length of hidden_string must be num_qubits - 1."):
        bv.create_circuit(3, hidden_string="wrong")


def test_dj_constant_oracle() -> None:
    """Test the creation of the DJ benchmark constant oracle."""
    qc = dj.create_circuit(5, False)
    assert qc.depth() > 0


@pytest.mark.parametrize(
    (
        "benchmark_name",
        "level",
        "circuit_size",
        "target",
        "opt_level",
    ),
    [
        # Algorithm-level tests
        ("dj", BenchmarkLevel.ALG, 3, None, None),
        ("wstate", BenchmarkLevel.ALG, 3, None, None),
        ("shor", BenchmarkLevel.ALG, 18, None, None),
        ("grover", BenchmarkLevel.ALG, 3, None, None),
        ("qwalk", BenchmarkLevel.ALG, 3, None, None),
        # Independent level tests
        ("ghz", BenchmarkLevel.INDEP, 3, None, 2),
        ("graphstate", BenchmarkLevel.INDEP, 3, None, 2),
        # Native gates level tests
        (
            "dj",
            BenchmarkLevel.NATIVEGATES,
            2,
            get_target_for_gateset("ionq_forte", num_qubits=5),
            0,
        ),
        ("qft", BenchmarkLevel.NATIVEGATES, 3, get_target_for_gateset("rigetti", 5), 2),
        # Mapped level tests
        (
            "ghz",
            BenchmarkLevel.MAPPED,
            3,
            get_device("ibm_falcon_127"),
            0,
        ),
        ("ghz", BenchmarkLevel.MAPPED, 3, get_device("ibm_falcon_27"), 2),
        (
            "ghz",
            BenchmarkLevel.MAPPED,
            3,
            get_device("ionq_aria_25"),
            0,
        ),
    ],
)
def test_get_benchmark(
    benchmark_name: str,
    level: BenchmarkLevel,
    circuit_size: int | None,
    target: Target | None,
    opt_level: int | None,
) -> None:
    """Test the creation of the benchmarks using the get_benchmark method."""
    qc = get_benchmark(
        benchmark_name,
        level,
        circuit_size,
        target,
        opt_level,
    )
    assert qc.depth() > 0
    if target:
        assert isinstance(qc, QuantumCircuit)
        for qc_instruction in qc.data:
            instruction = qc_instruction.operation
            gate_type = instruction.name
            assert gate_type in target.operation_names or gate_type == "barrier"


def test_get_benchmark_alg_with_quantum_circuit() -> None:
    """Test get_benchmark method with QuantumCircuit as input for algorithm level benchmarks."""
    qc = ae.create_circuit(3)
    qc_bench = get_benchmark(qc, BenchmarkLevel.ALG)

    assert qc == qc_bench


def test_get_benchmark_faulty_parameters() -> None:
    """Test the get_benchmark method with faulty parameters."""
    match = "'wrong_name' is not a supported benchmark. Valid names"
    with pytest.raises(ValueError, match=match):
        get_benchmark("wrong_name", BenchmarkLevel.INDEP, 6)
    match = "`circuit_size` must be a positive integer when `benchmark` is a str."
    with pytest.raises(ValueError, match=match):
        get_benchmark(
            "dj",
            BenchmarkLevel.INDEP,
            -1,
            get_device("rigetti_ankaa_84"),
            1,
        )

    match = "No Shor instance for circuit_size=3. Available: 18, 42, 58, 74."
    with pytest.raises(ValueError, match=match):
        get_benchmark(
            "shor",
            BenchmarkLevel.INDEP,
            3,
            get_device("rigetti_ankaa_84"),
            1,
        )

    match = re.escape("Invalid `opt_level` '4'. Must be in the range [0, 3].")
    with pytest.raises(ValueError, match=match):
        get_benchmark(
            "qpeexact",
            BenchmarkLevel.INDEP,
            3,
            get_device("rigetti_ankaa_84"),
            4,
        )
    match = re.escape(f"Unknown gateset 'wrong_gateset'. Available gatesets: {get_available_gateset_names()}")
    with pytest.raises(ValueError, match=match):
        get_benchmark(
            "qpeexact",
            BenchmarkLevel.NATIVEGATES,
            3,
            get_target_for_gateset("wrong_gateset", 3),
            1,
        )
    match = re.escape(f"Unknown device 'wrong_device'. Available devices: {get_available_device_names()}")
    with pytest.raises(ValueError, match=match):
        get_benchmark(
            "qpeexact",
            BenchmarkLevel.MAPPED,
            3,
            get_device("wrong_device"),
            1,
        )


@pytest.mark.parametrize(
    "getter",
    [
        get_benchmark_alg,
        get_benchmark_indep,
        functools.partial(get_benchmark_native_gates, target=get_target_for_gateset("ionq_forte", 3)),
        functools.partial(get_benchmark_mapped, target=get_device("ionq_forte_36")),
        functools.partial(get_benchmark, level=BenchmarkLevel.ALG),
        functools.partial(get_benchmark, level=BenchmarkLevel.INDEP),
        functools.partial(
            get_benchmark, level=BenchmarkLevel.NATIVEGATES, target=get_target_for_gateset("ionq_forte", 3)
        ),
        functools.partial(get_benchmark, level=BenchmarkLevel.MAPPED, target=get_device("ionq_forte_36")),
    ],
    ids=lambda fn: fn.func.__name__ if isinstance(fn, functools.partial) else fn.__name__,
)
def test_invalid_circuit_size_combinations(getter: Callable[..., QuantumCircuit]) -> None:
    """All get_benchmark_* helpers must reject the two illegal argument combos."""
    qc = ae.create_circuit(3)

    # QuantumCircuit plus a circuit_size
    with pytest.raises(
        ValueError,
        match=r"`circuit_size` must be omitted or None when `benchmark` is a QuantumCircuit",
    ):
        getter(qc, circuit_size=1)

    # str with a bad/absent circuit_size
    for bad_size in (-1, None):
        with pytest.raises(
            ValueError,
            match=r"`circuit_size` must be a positive integer when `benchmark` is a str",
        ):
            getter("ae", circuit_size=bad_size)


def test_clifford_t() -> None:
    """Test the Clifford+T gateset."""
    qc = get_benchmark(
        benchmark="qft",
        level=BenchmarkLevel.NATIVEGATES,
        circuit_size=4,
        target=get_target_for_gateset("clifford+t", 4),
        opt_level=1,
    )

    clifford_t_target = get_target_for_gateset("clifford+t", num_qubits=4)
    pm = PassManager(GatesInBasis(target=clifford_t_target))
    pm.run(qc)
    assert pm.property_set["all_gates_in_basis"]


def test_get_module_for_benchmark() -> None:
    """Test the get_module_for_benchmark function."""
    for benchmark in get_supported_benchmarks():
        assert get_module_for_benchmark(benchmark.split("-")[0]) is not None


def test_benchmark_helper_shor() -> None:
    """Testing the Shor benchmarks."""
    shor_instances = ["xsmall", "small", "medium", "large", "xlarge"]
    for elem in shor_instances:
        res_shor = shor.get_instance(elem)
        assert res_shor


def test_validate_input() -> None:
    """Test the _validate_input() method for various edge cases."""
    # Case 1: to_be_factored_number (N) < 3.
    with pytest.raises(ValueError, match=r"The input needs to be an odd integer greater than 3, was 2"):
        shor.create_circuit_from_num_and_coprime(2, 2)

    # Case 2: a < 2.
    with pytest.raises(ValueError, match=r"a must have value >= 2, was 1"):
        shor.create_circuit_from_num_and_coprime(15, 1)

    # Case 3: N is even (and thus not odd).
    with pytest.raises(ValueError, match=r"The input needs to be an odd integer greater than 3, was 4."):
        shor.create_circuit_from_num_and_coprime(4, 3)

    # Case 4: a >= N.
    with pytest.raises(
        ValueError, match=r"The integer a needs to satisfy a < N and gcd\(a, N\) = 1, was a = 15 and N = 15."
    ):
        shor.create_circuit_from_num_and_coprime(15, 15)

    # Case 5: gcd(a, N) != 1 (for example, N=15 and a=6, since gcd(15,6)=3).
    with pytest.raises(
        ValueError, match=r"The integer a needs to satisfy a < N and gcd\(a, N\) = 1, was a = 6 and N = 15."
    ):
        shor.create_circuit_from_num_and_coprime(15, 6)

    # Case 6: Valid input (should not raise any exception).
    try:
        shor.create_circuit_from_num_and_coprime(15, 2)
    except ValueError as e:
        pytest.fail(f"Unexpected ValueError raised for valid input: {e}")


def test_create_ae_circuit_with_invalid_qubit_number() -> None:
    """Testing the minimum number of qubits in the amplitude estimation circuit."""
    with pytest.raises(ValueError, match=r"Number of qubits must be at least 2 \(1 evaluation \+ 1 target\)."):
        get_benchmark("ae", BenchmarkLevel.INDEP, 1)


@pytest.mark.parametrize(
    ("level", "target", "expected"),
    [
        (BenchmarkLevel.ALG, None, "ghz_alg_5"),
        (BenchmarkLevel.INDEP, None, "ghz_indep_opt2_5"),
        (BenchmarkLevel.NATIVEGATES, get_target_for_gateset("ibm_falcon", 5), "ghz_nativegates_ibm_falcon_opt2_5"),
        (BenchmarkLevel.MAPPED, get_device("ibm_falcon_127"), "ghz_mapped_ibm_falcon_127_opt2_5"),
    ],
)
def test_generate_filename(level: str, target: Target, expected: str) -> None:
    """Test the generation of a filename."""
    filename = generate_filename(
        benchmark_name="ghz",
        level=level,
        num_qubits=5,
        target=target,
        opt_level=2,
    )
    assert filename == expected


@pytest.fixture(autouse=True)
def temp_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Ensure all files go into a temporary directory."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_generate_header_minimal(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test the generation of a minimal header."""
    monkeypatch.setattr(metadata, "version", lambda _: "9.9.9")
    hdr = generate_header(OutputFormat.QASM3, "indep")
    lines = hdr.splitlines()
    # first line has today's date
    assert lines[0] == f"// Benchmark created by MQT Bench on {date.today()}"
    # contains the fixed info lines
    assert "// For more info: https://www.cda.cit.tum.de/mqtbench/" in hdr
    assert "// MQT Bench version: 9.9.9" in hdr
    assert f"// Qiskit version: {__qiskit_version__}" in hdr
    assert f"// Output format: {OutputFormat.QASM3.value}" in hdr
    # no gateset or mapping lines when omitted
    assert "// Used gateset:" not in hdr
    assert "// Coupling map:" not in hdr


def test_generate_header_with_options(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test the generation of a header with options."""
    monkeypatch.setattr(metadata, "version", lambda _: "0.1.0")
    gates = ["h", "x", "cx"]
    cmap = [[0, 1], [1, 2]]
    target = Target(num_qubits=3)

    # === Single-qubit gates ===
    # Define all-qubit props (or use None if not needed)
    x_props = {(q,): None for q in range(3)}
    h_props = {(q,): None for q in range(3)}

    target.add_instruction(HGate(), h_props)
    target.add_instruction(XGate(), x_props)

    # === Two-qubit CX gate on limited connectivity
    cx_props = {
        (0, 1): InstructionProperties(),
        (1, 2): InstructionProperties(),
    }
    target.add_instruction(CXGate(), cx_props)
    hdr = generate_header(OutputFormat.QASM2, level=BenchmarkLevel.MAPPED, target=target)

    assert f"// Used gateset: {gates}" in hdr
    assert f"// Coupling map: {cmap}" in hdr


def test_generate_header_pkg_not_installed(monkeypatch: pytest.MonkeyPatch) -> None:
    """metadata.version raises PackageNotFoundError."""
    monkeypatch.setattr(
        metadata,
        "version",
        lambda _pkg: (_ for _ in ()).throw(MQTBenchExporterError("boom")),
    )
    with pytest.raises(MQTBenchExporterError) as exc:
        generate_header(OutputFormat.QASM2, BenchmarkLevel.INDEP)

    msg = str(exc.value)
    assert "not installed" in msg.lower()
    assert "mqt.bench" in msg


@pytest.mark.parametrize("fmt", [OutputFormat.QASM2, OutputFormat.QASM3])
def test_write_circuit_qasm(tmp_path: Path, fmt: OutputFormat) -> None:
    """Test writing a QASM circuit."""
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)

    out = tmp_path / "test.qasm"
    write_circuit(qc, out, BenchmarkLevel.INDEP, fmt=fmt)

    text = out.read_text().splitlines()
    # header lines at top
    assert text[0].startswith("// Benchmark created by MQT Bench on")
    # QASM body present
    assert any(line.startswith("h ") for line in text), "H gate should appear"
    assert any(line.startswith("cx ") for line in text), "CX gate should appear"


def test_write_circuit_qpy(tmp_path: Path) -> None:
    """Test writing a QPY circuit with header embedded in metadata."""
    qc = QuantumCircuit(1)
    qc.x(0)
    out = tmp_path / "test.qpy"
    write_circuit(qc, out, BenchmarkLevel.INDEP, fmt=OutputFormat.QPY)

    data = out.read_bytes()
    assert data.startswith(b"QISKIT"), "QPY file must start with the QISKIT magic"

    with out.open("rb") as fd:
        loaded = list(qpy.load(fd))
    assert len(loaded) == 1
    circ = loaded[0]
    assert isinstance(circ, QuantumCircuit)

    header = circ.metadata["mqt_bench"]
    assert header.startswith(f"// Benchmark created by MQT Bench on {date.today()}")
    assert "// MQT Bench version:" in header
    assert "// Output format: qpy" in header


def test_write_circuit_io_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Simulate I/O error while writing."""
    qc = QuantumCircuit(1)
    qc.h(0)

    out = tmp_path / "readonly.qasm"

    # Monkey-patch builtins.open to throw OSError on any attempt to open for writing
    def fake_open(*args: str, **kwargs: str) -> NoReturn:
        msg = "disk full"
        raise OSError(msg)

    monkeypatch.setattr(Path, "open", fake_open)
    monkeypatch.setattr(metadata, "version", lambda _: "0.1.0")

    with pytest.raises(MQTBenchExporterError) as exc:
        write_circuit(qc, out, BenchmarkLevel.INDEP, fmt=OutputFormat.QASM2)

    msg = str(exc.value)
    assert "failed to write qasm2 file" in msg.lower()
    assert "disk full" in msg.lower()

    # restore Path.open so other tests continue unharmed
    monkeypatch.setattr(Path, "open", builtins.open)


def test_write_circuit_unsupported_format(tmp_path: Path) -> None:
    """Requesting an unsupported format should raise."""

    class FakeFormat(str, Enum):
        FAKE = "fake"

    qc = QuantumCircuit(1)

    with pytest.raises(MQTBenchExporterError) as exc:
        write_circuit(qc, tmp_path / "foo.fake", BenchmarkLevel.INDEP, fmt=FakeFormat.FAKE)  # type: ignore[arg-type]

    msg = str(exc.value)
    assert "unsupported output format" in msg.lower()
    assert "fake" in msg.lower()


def test_save_circuit_success(tmp_path: Path) -> None:
    """Happy-path save."""
    qc = QuantumCircuit(1)
    qc.h(0)

    assert save_circuit(qc, "foo", BenchmarkLevel.INDEP, OutputFormat.QASM2, target_directory=str(tmp_path))
    assert (tmp_path / "foo.qasm").exists()

    assert save_circuit(qc, "bar", BenchmarkLevel.INDEP, OutputFormat.QPY, target_directory=str(tmp_path))
    assert (tmp_path / "bar.qpy").exists()


def test_save_circuit_write_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """save_circuit returns False when write_circuit fails."""
    qc = QuantumCircuit(1)
    qc.h(0)

    monkeypatch.setattr(
        "mqt.bench.output.write_circuit",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(MQTBenchExporterError("boom")),
    )

    ok = save_circuit(qc, "baz", BenchmarkLevel.INDEP, OutputFormat.QASM3, target_directory=str(tmp_path))
    assert ok is False


@pytest.mark.parametrize("fmt", [OutputFormat.QASM2, OutputFormat.QASM3])
def test_write_circuit_qasm_to_text_stream(fmt: OutputFormat) -> None:
    """Test writing a QASM circuit to a text stream."""
    qc = QuantumCircuit(2)
    qc.cx(0, 1)

    buf = io.StringIO()
    write_circuit(qc, buf, BenchmarkLevel.INDEP, fmt=fmt)

    text = buf.getvalue().splitlines()
    assert text[0].startswith("// Benchmark created by MQT Bench on")
    assert any("cx" in line for line in text)


def test_write_circuit_qpy_to_binary_stream() -> None:
    """Test writing a QPY circuit to a binary stream."""
    qc = QuantumCircuit(1)
    qc.x(0)

    buf = io.BytesIO()
    write_circuit(qc, buf, BenchmarkLevel.INDEP, fmt=OutputFormat.QPY)

    buf.seek(0)
    magic = buf.read(6)
    assert magic == b"QISKIT"


def test_stream_mode_mismatch_raises() -> None:
    """Test that stream mode mismatch raises an error."""
    qc = QuantumCircuit(1)

    # Binary stream + QASM → error
    with pytest.raises(MQTBenchExporterError):
        write_circuit(qc, io.BytesIO(), BenchmarkLevel.INDEP, fmt=OutputFormat.QASM3)

    # Text stream + QPY → error
    with pytest.raises(MQTBenchExporterError):
        write_circuit(qc, io.StringIO(), BenchmarkLevel.INDEP, fmt=OutputFormat.QPY)


def test_custom_target() -> None:
    """Test the compilation with an external target that is not part of the pre-defined ones."""
    target = Target(num_qubits=3, description="custom_target")
    alpha = Parameter("alpha")
    beta = Parameter("beta")

    target.add_instruction(RXGate(alpha))
    target.add_instruction(RZGate(beta))

    cx_props = {
        (0, 1): None,
        (1, 2): None,
    }
    target.add_instruction(CXGate(), cx_props)

    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)

    for opt_level in [0, 1, 2, 3]:
        qc_native_gates = get_benchmark_native_gates(qc, None, target, opt_level)
        assert qc_native_gates.depth() > 0
        assert qc_native_gates.layout is None

    qc_mapped = get_benchmark_mapped(qc, None, target, 0)
    assert qc_mapped.depth() > 0
    assert qc_mapped.layout is not None


@pytest.mark.parametrize(("benchmark", "size"), [("qft", 4), ("bv", 6)])
def test_alg_parity(benchmark: str, size: int) -> None:
    """Test parity of algorithm-level benchmarks."""
    qc_wrapper = get_benchmark_alg(benchmark, size)
    qc_ref = get_benchmark(benchmark, BenchmarkLevel.ALG, size)
    assert qc_wrapper == qc_ref


@pytest.mark.parametrize(("benchmark", "size"), [("qft", 4)])
def test_indep_parity(benchmark: str, size: int) -> None:
    """Test parity of target-independent benchmarks."""
    qc_wrapper = get_benchmark_indep(benchmark, size)
    qc_ref = get_benchmark(benchmark, BenchmarkLevel.INDEP, size)
    assert qc_wrapper == qc_ref


@pytest.mark.parametrize(("benchmark", "size", "opt_level"), [("qft", 4, 1), ("grover", 3, 2)])
def test_native_gate_parity(benchmark: str, size: int, opt_level: int) -> None:
    """Test parity of native gate-level benchmarks."""
    target = get_target_for_gateset("ionq_forte", num_qubits=size)
    qc_wrapper = get_benchmark_native_gates(
        benchmark,
        size,
        target,
        opt_level,
    )
    qc_ref = get_benchmark(
        benchmark,
        BenchmarkLevel.NATIVEGATES,
        size,
        target,
        opt_level,
    )
    assert qc_wrapper == qc_ref


@pytest.mark.parametrize(("benchmark", "size", "opt_level"), [("qft", 4, 1)])
def test_mapped_parity(benchmark: str, size: int, opt_level: int) -> None:
    """Test parity of mapped benchmarks."""
    target = get_device("ibm_falcon_127")
    qc_wrapper = get_benchmark_mapped(
        benchmark,
        size,
        target,
        opt_level,
    )
    qc_ref = get_benchmark(
        benchmark,
        BenchmarkLevel.MAPPED,
        size,
        target,
        opt_level,
    )
    assert qc_wrapper == qc_ref


@pytest.mark.parametrize(("benchmark", "size", "opt_level"), [("qft", 4, 4), ("ae", 3, -1)])
def test_validate_opt_level(benchmark: str, size: int, opt_level: int) -> None:
    """Test opt_level validation."""
    match = re.escape(f"Invalid `opt_level` '{opt_level}'. Must be in the range [0, 3].")
    with pytest.raises(ValueError, match=match):
        get_benchmark_indep(
            benchmark,
            circuit_size=size,
            opt_level=opt_level,
        )

    target = get_device("ibm_falcon_127")
    with pytest.raises(ValueError, match=match):
        get_benchmark_native_gates(
            benchmark,
            circuit_size=size,
            target=target,
            opt_level=opt_level,
        )
    with pytest.raises(ValueError, match=match):
        get_benchmark_mapped(
            benchmark,
            circuit_size=size,
            target=target,
            opt_level=opt_level,
        )
    with pytest.raises(ValueError, match=match):
        get_benchmark(
            benchmark,
            level=BenchmarkLevel.INDEP,
            circuit_size=size,
            target=target,
            opt_level=opt_level,
        )


@pytest.mark.parametrize(("benchmark", "size", "opt_level"), [("qft", 4, 1)])
def test_target_must_be_supplied(benchmark: str, size: int, opt_level: int) -> None:
    """Test target must be supplied for mapped and native-gates levels."""
    with pytest.raises(
        TypeError, match=re.escape("get_benchmark_native_gates() missing 1 required positional argument: 'target'")
    ):
        get_benchmark_native_gates(
            benchmark,
            circuit_size=size,
            opt_level=opt_level,
        )
    with pytest.raises(
        TypeError, match=re.escape("get_benchmark_mapped() missing 1 required positional argument: 'target'")
    ):
        get_benchmark_mapped(
            benchmark,
            circuit_size=size,
            opt_level=opt_level,
        )


def test_assert_never_runtime() -> None:
    """Test that assert_never raises an error at runtime."""
    bad_level = cast("BenchmarkLevel", object())

    with pytest.raises(AssertionError):
        # get_benchmark will fall through the if-chain and hit assert_never
        get_benchmark("qft", level=bad_level, circuit_size=3)
