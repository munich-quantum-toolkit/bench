# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Calibration data for a (generic) device."""

from __future__ import annotations

from importlib import resources
from pathlib import Path


def get_device_calibration_path(filename: str) -> Path:
    """Get the path to the calibration file for a device."""
    calibration_path = resources.files("mqt.bench") / "calibration_files" / f"{filename}_calibration.json"

    if not calibration_path.is_file():
        msg = f"Calibration file not found: {calibration_path}"
        raise FileNotFoundError(msg)

    return Path(str(calibration_path))
