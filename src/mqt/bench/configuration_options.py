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
    """A dictionary of configuration options.

    The keys of this dictionary are the names of the configuration options.
    The values are the values of the configuration options.
    """

    seed: int | None
