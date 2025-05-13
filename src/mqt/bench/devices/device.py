# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Device class for representing quantum devices."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Gateset:
    """A class to represent a set of native gates."""

    name: str
    gates: list[str]
