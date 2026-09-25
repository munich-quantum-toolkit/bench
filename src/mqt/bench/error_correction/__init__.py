# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Initialization of the error correction module."""

# ruff: file-ignore[non-empty-init-module]

from __future__ import annotations

from .ec_transpiler import ECTranspiler, LogicalQubit
from .shor_transpiler import ShorTranspiler
from .steane_transpiler import SteaneTranspiler

__all__ = [
    "ECTranspiler",
    "LogicalQubit",
    "ShorTranspiler",
    "SteaneTranspiler",
    "get_available_encoding_names",
    "get_transpiler",
]


_TRANSPILERS: dict[str, type[ECTranspiler]] = {cls.CODE_NAME: cls for cls in (ShorTranspiler, SteaneTranspiler)}


def get_available_encoding_names() -> list[str]:
    """Return the names of all supported error-correcting codes, i.e. the valid ``encoding`` values."""
    return sorted(_TRANSPILERS)


def get_transpiler(encoding: str) -> type[ECTranspiler]:
    """Return the transpiler class for the given error-correcting code.

    Arguments:
        encoding: Name of the error-correcting code (see :func:`get_available_encoding_names`).

    Raises:
        ValueError: If ``encoding`` is not a supported error-correcting code.
    """
    if encoding not in _TRANSPILERS:
        msg = (
            f"'{encoding}' is not a supported error-correcting code. Available codes: {get_available_encoding_names()}"
        )
        raise ValueError(msg)
    return _TRANSPILERS[encoding]
