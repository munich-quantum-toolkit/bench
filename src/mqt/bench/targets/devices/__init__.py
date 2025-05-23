# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Initialization of the devices module."""

from __future__ import annotations

from functools import cache
from typing import TYPE_CHECKING

from .ibm import get_ibm_target
from .ionq import get_ionq_target
from ..gatesets.ionq import add_ionq_equivalences
from .iqm import get_iqm_target
from .quantinuum import get_quantinuum_target
from .rigetti import get_rigetti_target

if TYPE_CHECKING:
    from qiskit.transpiler import Target


__all__ = [
    "get_available_devices",
    "get_device_by_name",
]


@cache
def get_available_devices() -> list[Target]:
    """Return a list of available devices."""
    return [
        get_ibm_target("ibm_falcon_27"),
        get_ibm_target("ibm_falcon_127"),
        get_ibm_target("ibm_eagle_127"),
        get_ibm_target("ibm_heron_133"),
        get_ibm_target("ibm_heron_156"),
        get_ionq_target("ionq_forte_1"),
        get_ionq_target("ionq_aria_1"),
        get_iqm_target("iqm_crystal_5"),
        get_iqm_target("iqm_crystal_20"),
        get_iqm_target("iqm_crystal_54"),
        get_quantinuum_target("quantinuum_h2"),
        get_rigetti_target("rigetti_aspen_m3"),
    ]


@cache
def _device_map() -> dict[str, Target]:
    """Return a mapping of device names to Target objects."""
    return {d.description: d for d in get_available_devices()}


def get_device_by_name(device_name: str) -> Target:
    """Return the Target object for a given device name."""
    try:
        return _device_map()[device_name]
    except KeyError:
        msg = f"Device '{device_name}' not found."
        raise ValueError(msg) from None
