# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""MQT Bench."""

from __future__ import annotations

from importlib.metadata import version

from mqt.bench.benchmark_generation import (
    BenchmarkLevel,
    get_benchmark,
    get_benchmark_alg,
    get_benchmark_indep,
    get_benchmark_mapped,
    get_benchmark_native_gates,
)

__version__ = version("mqt-bench")
__version_tuple__ = tuple(int(part) if part.isdecimal() else part for part in __version__.split("."))

__all__ = [
    "BenchmarkLevel",
    "__version__",
    "__version_tuple__",
    "get_benchmark",
    "get_benchmark_alg",
    "get_benchmark_indep",
    "get_benchmark_mapped",
    "get_benchmark_native_gates",
]
