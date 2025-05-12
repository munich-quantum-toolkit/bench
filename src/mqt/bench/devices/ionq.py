from qiskit.transpiler import Target, InstructionProperties
from qiskit.circuit.library import RXGate, RYGate, RZGate, RXXGate, Measure
import json
from pathlib import Path
from qiskit.circuit import Parameter

from .calibration import get_device_calibration_path

def create_ionq_target(calibration_path: Path) -> Target:
    with calibration_path.open() as json_file:
        calib = json.load(json_file)

    target = Target(num_qubits=calib["num_qubits"], description=calib["name"])
    num_qubits = calib["num_qubits"]
    connectivity = calib["connectivity"]

    # Gate durations and fidelities
    oneq_fidelity = calib["fidelity"]["1q"]["mean"]
    twoq_fidelity = calib["fidelity"]["2q"]["mean"]
    spam_fidelity = calib["fidelity"]["spam"]["mean"]
    t1 = calib["timing"]["t1"]
    t2 = calib["timing"]["t2"]

    oneq_duration = calib["timing"]["1q"]
    twoq_duration = calib["timing"]["2q"]
    readout_duration = calib["timing"]["readout"]

    theta = Parameter('theta')
    phi = Parameter('phi')
    lam = Parameter('lambda')

    # === Add single-qubit gates ===
    rx_props = {
        (q,): InstructionProperties(duration=oneq_duration, error=1 - oneq_fidelity)
        for q in range(num_qubits)
    }
    ry_props = {
        (q,): InstructionProperties(duration=oneq_duration, error=1 - oneq_fidelity)
        for q in range(num_qubits)
    }
    rz_props = {
        (q,): InstructionProperties(duration=0.0, error=0.0)
        for q in range(num_qubits)
    }
    measure_props = {
        (q,): InstructionProperties(duration=readout_duration, error=1 - spam_fidelity)
        for q in range(num_qubits)
    }

    target.add_instruction(RXGate(theta), rx_props)
    target.add_instruction(RYGate(phi), ry_props)
    target.add_instruction(RZGate(lam), rz_props)
    target.add_instruction(Measure(), measure_props)

    # === Add two-qubit gates ===
    alpha = Parameter('alpha')
    rxx_props = {
        (q1, q2): InstructionProperties(duration=twoq_duration, error=1 - twoq_fidelity)
        for q1, q2 in connectivity
    }
    target.add_instruction(RXXGate(alpha), rxx_props)



    return target


def get_ionq_harmony_target() -> Target:
    return create_ionq_target(get_device_calibration_path("ionq_harmony"))


def get_ionq_aria1_target() -> Target:
    return create_ionq_target(get_device_calibration_path("ionq_aria1"))
