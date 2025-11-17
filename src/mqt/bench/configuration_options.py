# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Configuration options for the MQT Bench library."""

from __future__ import annotations

from typing import TypedDict

__all__ = ["ConfigurationOptions"]


class ConfigurationOptions(TypedDict, total=False):
    """Configuration options for benchmark generation.

    All fields are optional. Currently supported options:

    Attributes:
        seed: Random seed for deterministic benchmark generation (None for random behavior).
    """

    seed: int | None
