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
#   "mqt-nox @ git+https://github.com/munich-quantum-toolkit/nox.git@aa3af05513ba6522453c8f59f0db2623acbe2146",
# ]
# ///

"""Nox sessions."""

from __future__ import annotations

import os

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


def _coverage_args(session: nox.Session) -> list[str]:
    """Limit coverage to the latest locked session in pull request matrices."""
    if (
        session.parallel
        and "--cov" in session.posargs
        and os.environ.get("GITHUB_EVENT_NAME") in {"pull_request", "workflow_dispatch"}
        and os.environ.get("GITHUB_REF") != "refs/heads/main"
        and session.name != f"tests-{PYTHON_VERSIONS[-1]}"
    ):
        return ["--no-cov"]
    return []


@nox.session(python=PYTHON_VERSIONS, reuse_venv=True, default=True, allow_parallel=True)
def tests(session: nox.Session) -> None:
    """Run the test suite."""
    python.tests(session, pytest_args=_coverage_args(session))


@nox.session(python=PYTHON_VERSIONS, venv_backend="uv", default=True, allow_parallel=True)
def minimums(session: nox.Session) -> None:
    """Test the minimum versions of dependencies."""
    python.minimums(session, pytest_args=_coverage_args(session))


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

    Use ``--non-interactive`` to avoid serving.
    Pass ``-b linkcheck`` to check links.
    """
    python.docs(session, install_args=["--frozen"])


if __name__ == "__main__":
    nox.main()
