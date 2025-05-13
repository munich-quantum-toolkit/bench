# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Module to manage IBM devices."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from qiskit_ibm_runtime.fake_provider import FakeMontrealV2, FakeTorino, FakeWashingtonV2

if TYPE_CHECKING:
    from qiskit.transpiler import Target

logger = logging.getLogger(__name__)


def get_ibm_target(device_name: str) -> Target:
    """Get the target device for a given name."""
    if device_name == "ibm_montreal":
        return FakeMontrealV2().target
    if device_name == "ibm_torino":
        return FakeTorino().target
    if device_name == "ibm_washington":
        return FakeWashingtonV2().target
    msg = f"Unknown IBM device: {device_name}"
    raise ValueError(msg)
