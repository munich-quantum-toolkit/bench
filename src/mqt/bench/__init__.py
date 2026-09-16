# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""MQT Bench."""

from __future__ import annotations

from mqt.bench.benchmark_generation import (
    BenchmarkLevel,
    get_benchmark,
    get_benchmark_alg,
    get_benchmark_indep,
    get_benchmark_mapped,
    get_benchmark_native_gates,
)

from ._version import version as __version__
from ._version import version_tuple as __version_tuple__

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
