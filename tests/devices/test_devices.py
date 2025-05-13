# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Tests for the device module."""
#
# from __future__ import annotations
#
# import re
# from typing import cast
#
# import pytest
#
# from mqt.bench.devices import (
#     get_ibm_target,
#     get_available_devices,
#     get_device_by_name,
#     get_native_gateset_by_name,
# )
# from mqt.bench.devices.calibration import get_device_calibration_path
# from mqt.bench.devices.ionq import DeviceCalibration, IonQHarmony
#
#
# @pytest.mark.parametrize("device", get_available_devices(), ids=lambda device: cast("str", device.name))
# def test_sanitized_devices(device: Device) -> None:
#     """Test that all devices can be sanitized and provide complete fidelity data."""
#     device.read_calibration()
#     device.sanitize_device()
#     assert device.calibration is not None
#     for qubit in range(device.num_qubits):
#         assert qubit in device.calibration.single_qubit_gate_fidelity
#         for gate in device.get_single_qubit_gates():
#             assert gate in device.calibration.single_qubit_gate_fidelity[qubit]
#             assert device.calibration.single_qubit_gate_fidelity[qubit][gate] > 0
#         assert qubit in device.calibration.readout_fidelity
#
#     for qubit1, qubit2 in device.coupling_map:
#         assert (qubit1, qubit2) in device.calibration.two_qubit_gate_fidelity
#         for gate in device.get_two_qubit_gates():
#             assert gate in device.calibration.two_qubit_gate_fidelity[qubit1, qubit2]
#             assert device.calibration.two_qubit_gate_fidelity[qubit1, qubit2][gate] > 0
#
#
# def test_unsupported_device() -> None:
#     """Test that unsupported devices raise errors."""
#     with pytest.raises(ValueError, match=r"Device unsupported not found in available devices."):
#         get_device_by_name("unsupported")
#     with pytest.raises(ValueError, match=r"Gateset unsupported not found in available gatesets."):
#         get_native_gateset_by_name("unsupported")
#
#
# def test_device_calibration_autoread() -> None:
#     """Test that all device calibration methods raise errors when no calibration data is available."""
#     IBMWashington()
#
#
# def test_device_calibration_errors() -> None:
#     """Test that all device calibration methods raise errors when no calibration data is available."""
#     device = IonQHarmony()
#     device.calibration = DeviceCalibration()
#     qubit1, qubit2 = -1, -2
#     gate = "wrong"
#
#    Test all methods with missing calibration data
#     with pytest.raises(ValueError, match=re.escape("Readout fidelity values not available.")):
#         device.get_readout_fidelity(0)
#     with pytest.raises(ValueError, match=re.escape("Readout duration values not available.")):
#         device.get_readout_duration(0)
#     with pytest.raises(ValueError, match=re.escape("Single-qubit gate fidelity values not available.")):
#         device.calibration.get_single_qubit_gate_fidelity("gate_type", 0)
#     with pytest.raises(ValueError, match=re.escape("Single-qubit gate duration values not available.")):
#         device.calibration.get_single_qubit_gate_duration("gate_type", 0)
#     with pytest.raises(ValueError, match=re.escape("Two-qubit gate fidelity values not available.")):
#         device.calibration.get_two_qubit_gate_fidelity("gate_type", 0, 1)
#     with pytest.raises(ValueError, match=re.escape("Two-qubit gate duration values not available.")):
#         device.calibration.get_two_qubit_gate_duration("gate_type", 0, 1)
#     with pytest.raises(ValueError, match=re.escape("Readout fidelity values not available.")):
#         device.calibration.get_readout_fidelity(0)
#     with pytest.raises(ValueError, match=re.escape("Readout duration values not available.")):
#         device.calibration.get_readout_duration(0)
#     with pytest.raises(ValueError, match=re.escape("T1 values not available.")):
#         device.calibration.get_t1(0)
#     with pytest.raises(ValueError, match=re.escape("T2 values not available.")):
#         device.calibration.get_t2(0)
#     with pytest.raises(ValueError, match=re.escape("Single-qubit gate fidelity values not available.")):
#         device.calibration.compute_average_single_qubit_gate_fidelity("gate")
#     with pytest.raises(ValueError, match=re.escape("Single-qubit gate duration values not available.")):
#         device.calibration.compute_average_single_qubit_gate_duration("gate")
#     with pytest.raises(ValueError, match=re.escape("Two-qubit gate fidelity values not available.")):
#         device.calibration.compute_average_two_qubit_gate_fidelity("gate")
#     with pytest.raises(ValueError, match=re.escape("Two-qubit gate duration values not available.")):
#         device.calibration.compute_average_two_qubit_gate_duration("gate")
#     with pytest.raises(ValueError, match=r"Readout fidelity values not available."):
#         device.calibration.compute_average_readout_fidelity()
#     with pytest.raises(ValueError, match=r"Gate wrong not supported by device ionq_harmony."):
#         device.get_single_qubit_gate_fidelity(gate, qubit1)
#     with pytest.raises(ValueError, match=r"Gate wrong not supported by device ionq_harmony."):
#         device.get_single_qubit_gate_duration(gate, qubit1)
#     with pytest.raises(ValueError, match=r"Gate wrong not supported by device ionq_harmony."):
#         device.get_two_qubit_gate_fidelity(gate, qubit1, qubit2)
#     with pytest.raises(ValueError, match=r"Gate wrong not supported by device ionq_harmony."):
#         device.get_two_qubit_gate_duration(gate, qubit1, qubit2)
#     with pytest.raises(ValueError, match=r"Readout fidelity values not available."):
#         device.get_readout_fidelity(qubit1)
#     with pytest.raises(ValueError, match=r"Readout duration values not available."):
#         device.get_readout_duration(qubit1)
#
#     with pytest.raises(ValueError, match=r"Single-qubit gate fidelity values not available."):
#         device.calibration.get_single_qubit_gate_fidelity(gate, qubit1)
#     with pytest.raises(ValueError, match=r"Single-qubit gate duration values not available."):
#         device.calibration.get_single_qubit_gate_duration(gate, qubit1)
#     with pytest.raises(ValueError, match=r"Two-qubit gate fidelity values not available."):
#         device.calibration.get_two_qubit_gate_fidelity(gate, qubit1, qubit2)
#     with pytest.raises(ValueError, match=r"Two-qubit gate duration values not available."):
#         device.calibration.get_two_qubit_gate_duration(gate, qubit1, qubit2)
#     with pytest.raises(ValueError, match=r"T1 values not available."):
#         device.calibration.get_t1(qubit1)
#     with pytest.raises(ValueError, match=r"T2 values not available."):
#         device.calibration.get_t2(qubit1)
#     with pytest.raises(ValueError, match=r"Single-qubit gate fidelity values not available."):
#         device.calibration.compute_average_single_qubit_gate_fidelity(gate)
#     with pytest.raises(ValueError, match=r"Single-qubit gate duration values not available."):
#         device.calibration.compute_average_single_qubit_gate_duration(gate)
#     with pytest.raises(ValueError, match=r"Two-qubit gate fidelity values not available."):
#         device.calibration.compute_average_two_qubit_gate_fidelity(gate)
#     with pytest.raises(ValueError, match=r"Two-qubit gate duration values not available."):
#         device.calibration.compute_average_two_qubit_gate_duration(gate)
#     with pytest.raises(ValueError, match=r"Readout fidelity values not available."):
#         device.calibration.compute_average_readout_fidelity()
#     with pytest.raises(ValueError, match=r"Readout duration values not available."):
#         device.calibration.compute_average_readout_duration()
#
#     device.read_calibration()
#     with pytest.raises(ValueError, match=f"Single-qubit fidelity for gate {gate} and qubit {qubit1} not available."):
#         device.calibration.get_single_qubit_gate_fidelity(gate, qubit1)
#     with pytest.raises(ValueError, match=f"Single-qubit duration for gate {gate} and qubit {qubit1} not available."):
#         device.calibration.get_single_qubit_gate_duration(gate, qubit1)
#     with pytest.raises(
#         ValueError,
#         match=f"Two-qubit fidelity for gate {gate} and qubits {qubit1} and {qubit2} not available.",
#     ):
#         device.calibration.get_two_qubit_gate_fidelity(gate, qubit1, qubit2)
#     with pytest.raises(
#         ValueError,
#         match=f"Two-qubit duration for gate {gate} and qubits {qubit1} and {qubit2} not available.",
#     ):
#         device.calibration.get_two_qubit_gate_duration(gate, qubit1, qubit2)
#     with pytest.raises(ValueError, match=f"Readout fidelity for qubit {qubit1} not available."):
#         device.calibration.get_readout_fidelity(qubit1)
#     with pytest.raises(ValueError, match=f"Readout duration for qubit {qubit1} not available."):
#         device.calibration.get_readout_duration(qubit1)
#     for gate in device.get_single_qubit_gates():
#         assert gate in device.gateset.gates
#     device.calibration = None
#     for gate in device.get_two_qubit_gates():
#         assert gate in device.gateset.gates
#     with pytest.raises(ValueError, match=f"T1 for qubit {qubit1} not available."):
#         device.calibration.get_t1(qubit1)
#     with pytest.raises(ValueError, match=f"T2 for qubit {qubit1} not available."):
#         device.calibration.get_t2(qubit1)
#
#
# def test_get_device_calibration_path() -> None:
#     """Test if the correct error message is shown if the calibration file does not exist."""
#     with pytest.raises(FileNotFoundError, match="Calibration file not found"):
#         get_device_calibration_path("wrong_path")
