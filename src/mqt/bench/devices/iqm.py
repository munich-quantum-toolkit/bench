from qiskit.transpiler import Target, InstructionProperties
from qiskit.circuit.library import RGate, CZGate, Measure
from qiskit.circuit import Parameter
import json
from pathlib import Path

from .calibration import get_device_calibration_path


def create_iqm_target(calibration_path: Path) -> Target:
    with calibration_path.open() as json_file:
        calib = json.load(json_file)

    num_qubits = calib["num_qubits"]
    connectivity = calib["connectivity"]
    name = calib["name"]

    oneq_errors = calib["error"]["one_q"]
    twoq_errors = calib["error"]["two_q"]
    readout_errors = calib["error"]["readout"]

    oneq_duration = calib["timing"]["one_q"] * 1e-9
    twoq_duration = calib["timing"]["two_q"] * 1e-9
    readout_duration = calib["timing"]["readout"] * 1e-9

    target = Target(num_qubits=num_qubits, description=name)

    theta = Parameter("theta")
    phi = Parameter("phi")

    # === Single-qubit R gate with per-qubit fidelity ===
    r_props = {
        (q,): InstructionProperties(
            duration=oneq_duration,
            error=oneq_errors[str(q)]
        )
        for q in range(num_qubits)
    }
    target.add_instruction(RGate(theta, phi), r_props)

    # === Per-qubit measurement ===
    measure_props = {
        (q,): InstructionProperties(
            duration=readout_duration,
            error=readout_errors[str(q)]
        )
        for q in range(num_qubits)
    }
    target.add_instruction(Measure(), measure_props)

    # === Two-qubit CZ gate with per-direction errors ===
    cz_props = {}
    for q1, q2 in connectivity:
        key = f"{q1}-{q2}"
        error = twoq_errors[key]
        props = InstructionProperties(duration=twoq_duration, error=error)

        # Add both directions
        cz_props[(q1, q2)] = props
        cz_props[(q2, q1)] = props  # assume symmetric for now

    target.add_instruction(CZGate(), cz_props)


    return target


def get_iqm_adonis_target() -> Target:
    return create_iqm_target(get_device_calibration_path("iqm_adonis"))


def get_iqm_apollo_target() -> Target:
    return create_iqm_target(get_device_calibration_path("iqm_apollo"))