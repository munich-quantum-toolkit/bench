from qiskit.transpiler import Target, InstructionProperties
from qiskit.circuit.library import RXGate, RYGate, RZGate, RZZGate, Measure
from qiskit.circuit import Parameter
import json
from pathlib import Path

from .calibration import get_device_calibration_path


def create_quantinuum_target(calibration_path: Path) -> Target:
    with calibration_path.open() as json_file:
        calib = json.load(json_file)

    num_qubits = calib["num_qubits"]
    connectivity = calib["connectivity"]
    name = calib["name"]

    oneq_fidelity = calib["fidelity"]["1q"]["mean"]
    twoq_fidelity = calib["fidelity"]["2q"]["mean"]
    spam_fidelity = calib["fidelity"]["spam"]["mean"]

    target = Target(num_qubits=num_qubits, description=name)

    # Define symbolic parameters
    theta = Parameter("theta")
    phi = Parameter("phi")
    alpha = Parameter("alpha")

    # === Add single-qubit gates ===
    rx_props = {
        (q,): InstructionProperties(error=1 - oneq_fidelity)
        for q in range(num_qubits)
    }
    ry_props = {
        (q,): InstructionProperties(error=1 - oneq_fidelity)
        for q in range(num_qubits)
    }
    rz_props = {
        (q,): InstructionProperties(error=0.0)
        for q in range(num_qubits)
    }
    measure_props = {
        (q,): InstructionProperties(error=1 - spam_fidelity)
        for q in range(num_qubits)
    }

    target.add_instruction(RXGate(theta), rx_props)
    target.add_instruction(RYGate(phi), ry_props)
    target.add_instruction(RZGate(theta), rz_props)
    target.add_instruction(Measure(), measure_props)

    # === Add two-qubit RZZ gates ===
    rzz_props = {
        (q1, q2): InstructionProperties(error=1 - twoq_fidelity)
        for q1, q2 in connectivity
    }
    target.add_instruction(RZZGate(alpha), rzz_props)

    return target


def get_quantinuum_h2_target() -> Target:
    return create_quantinuum_target(get_device_calibration_path("quantinuum_h2"))