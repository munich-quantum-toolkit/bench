from __future__ import annotations
from functools import cache

from qiskit.circuit.controlflow import ControlFlowOp
from qiskit.circuit.library.standard_gates import __dict__ as gate_dict
from qiskit.transpiler import Target

from .ibm import get_ibm_target
from .ionq import get_ionq_target
from .iqm import get_iqm_target
from .quantinuum import get_quantinuum_target
from .rigetti import get_rigetti_target

DEVICE_TO_GATESET = {
    "ibm_montreal": "ibm_falcon",
    "ibm_washington": "ibm_falcon",
    "ibm_torino": "ibm_heron_r1",
    "ionq_harmony": "ionq",
    "ionq_aria1": "ionq",
    "iqm_adonis": "iqm",
    "iqm_apollo": "iqm",
    "quantinuum_h2": "quantinuum",
    "rigetti_aspen_m3": "rigetti",
}

@cache
def get_available_devices() -> list[Target]:
    return [
        get_ibm_target("ibm_montreal"),
        get_ibm_target("ibm_torino"),
        get_ibm_target("ibm_washington"),
        get_ionq_target("ionq_harmony"),
        get_ionq_target("ionq_aria1"),
        get_iqm_target("iqm_adonis"),
        get_iqm_target("iqm_apollo"),
        get_quantinuum_target("quantinuum_h2"),
        get_rigetti_target("rigetti_aspen_m3"),
    ]


@cache
def get_available_device_names() -> list[str]:
    return [device.description for device in get_available_devices()]


@cache
def _device_map() -> dict[str, Target]:
    return {d.description: d for d in get_available_devices()}


def get_device_by_name(device_name: str) -> Target:
    try:
        return _device_map()[device_name]
    except KeyError:
        raise ValueError(f"Device {device_name} not found.") from None


@cache
def get_available_native_gatesets(num_qubits: int = 20) -> dict[str, Target]:
    """Return mapping: gateset_name → Target (deduplicated)."""
    gatesets: dict[str, Target] = {}

    for device in get_available_devices():
        device_name = device.description
        gateset_name = DEVICE_TO_GATESET[device_name]

        if gateset_name in gatesets:
            continue  # already built

        target = Target(description=gateset_name, num_qubits=num_qubits)

        for op_name in device.operation_names:
            try:
                inst_props = device[op_name]
                inst_obj = inst_props.default_inst
                if inst_obj is None or isinstance(inst_obj, ControlFlowOp):
                    continue
                inst_class = inst_obj if isinstance(inst_obj, type) else type(inst_obj)
                target.add_instruction(inst_class)
            except Exception:
                continue

        gatesets[gateset_name] = target

    # Add Clifford+T manually
    from qiskit.circuit.library.standard_gates import __dict__ as gate_dict
    clifford = Target(num_qubits=num_qubits, description="clifford+t")
    for name in [
        "i", "x", "y", "z", "h", "s", "sdg", "t", "tdg", "sx", "sxdg",
        "cx", "cy", "cz", "swap", "iswap", "dcx", "ecr", "measure", "barrier"
    ]:
        try:
            gate_class = gate_dict[name.upper()]
            clifford.add_instruction(gate_class)
        except Exception:
            continue

    gatesets["clifford+t"] = clifford
    return gatesets


def get_native_gateset_by_name(name: str, num_qubits: int = 20) -> Target:
    gatesets = get_available_native_gatesets(num_qubits)
    try:
        return gatesets[name]
    except KeyError:
        raise ValueError(f"Gateset '{name}' not found.") from None


__all__ = [
    "get_available_device_names",
    "get_available_devices",
    "get_available_native_gatesets",
    "get_device_by_name",
    "get_native_gateset_by_name",
]