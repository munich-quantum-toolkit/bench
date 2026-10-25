# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
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

    All fields are optional. Each factory accepts only its documented options.
    The shared seed also controls random parameter values and is passed to
    factories that accept it.
    """

    seed: int | None
    """Random seed for parameter values and factories that accept a seed (None for random behavior)."""
