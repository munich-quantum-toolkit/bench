# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Initialization of the targets module."""

from __future__ import annotations

from importlib import resources
from pathlib import Path

from mqt.bench.targets.devices.ibm import get_ibm_target
from mqt.bench.targets.devices.ionq import get_ionq_target
from mqt.bench.targets.devices.iqm import get_iqm_target
from mqt.bench.targets.devices.quantinuum import get_quantinuum_target
from mqt.bench.targets.devices.rigetti import get_rigetti_target

from .devices import get_available_device_names, get_available_devices, get_device_by_name
from .gatesets import (
    get_available_native_gatesets,
    get_native_gateset_by_name,
)

__all__ = [
    "get_available_device_names",
    "get_available_devices",
    "get_available_native_gatesets",
    "get_device_by_name",
    "get_ibm_target",
    "get_ionq_target",
    "get_iqm_target",
    "get_native_gateset_by_name",
    "get_quantinuum_target",
    "get_rigetti_target",
]


def get_device_calibration_path(filename: str) -> Path:
    """Get the path to the calibration file for a device."""
    calibration_path = resources.files("mqt.bench") / "calibration_files" / f"{filename}_calibration.json"

    if not calibration_path.is_file():
        msg = f"Calibration file not found: {calibration_path}"
        raise FileNotFoundError(msg)

    return Path(str(calibration_path))
