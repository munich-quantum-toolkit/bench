#!/usr/bin/env -S uv run --script --quiet
# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

# /// script
# dependencies = [
#   "nox>=2026.10.20",
#   "mqt-nox @ git+https://github.com/munich-quantum-toolkit/nox.git@cdd19440398f0efffdc99bd6ccb87090e157d99c",
# ]
# ///

"""Nox sessions."""

from __future__ import annotations

import nox
from mqt.nox import common, python

nox.needs_version = ">=2026.10.20"
nox.options.default_venv_backend = "uv"

PYPROJECT = nox.project.load_toml("pyproject.toml")
PYTHON_VERSIONS = nox.project.python_versions(PYPROJECT)


@nox.session(reuse_venv=True, default=True)
def lint(session: nox.Session) -> None:
    """Run the linter."""
    common.lint(session)


@nox.session(python=PYTHON_VERSIONS, reuse_venv=True, default=True)
def tests(session: nox.Session) -> None:
    """Run the test suite."""
    python.tests(session)


@nox.session(python=PYTHON_VERSIONS, reuse_venv=True, venv_backend="uv", default=True)
def minimums(session: nox.Session) -> None:
    """Test the minimum versions of dependencies."""
    python.minimums(session)


@nox.session(python=PYTHON_VERSIONS, reuse_venv=True, venv_backend="uv")
def qiskit(session: nox.Session) -> None:
    """Test against Qiskit's main branch."""
    python.qiskit(
        session,
        pytest_args=["-Wdefault:Qiskit:mqt.core.UntestedVersionWarning"],
    )


@nox.session(python="3.14", reuse_venv=True)
def docs(session: nox.Session) -> None:
    """Build the docs.

    Use "--non-interactive" to avoid serving. Pass "-b linkcheck" to check links.
    """
    python.docs(session, install_args=["--frozen"])


if __name__ == "__main__":
    nox.main()
