#!/usr/bin/env -S uv run --script --quiet
# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

# /// script
# dependencies = ["nox"]
# ///

"""Nox sessions."""

from __future__ import annotations

import argparse
import os
import shutil
from typing import TYPE_CHECKING

import nox

if TYPE_CHECKING:
    from collections.abc import Sequence


nox.needs_version = ">=2026.08.10"
nox.options.default_venv_backend = "uv"
nox.options.parallel = 5

if os.environ.get("CI", None):
    nox.options.error_on_missing_interpreters = True

PYTHON_ALL_VERSIONS = ["3.10", "3.11", "3.12", "3.13", "3.14"]


def _get_session_env(session: nox.Session) -> dict[str, str]:
    """Return the environment that a session installs the project in."""
    return {"UV_PROJECT_ENVIRONMENT": session.virtualenv.location}


@nox.session(reuse_venv=True, default=True)
def lint(session: nox.Session) -> None:
    """Run the linter."""
    if shutil.which("prek") is None:
        session.install("prek")

    session.run("prek", "run", "--all-files", *session.posargs, external=True)


@nox.session(python=PYTHON_ALL_VERSIONS, reuse_venv=True, default=True, allow_parallel=True)
def tests(session: nox.Session) -> None:
    """Run the test suite."""
    session.run(
        "uv",
        "run",
        "--no-dev",
        "--group",
        "test",
        "pytest",
        *session.posargs,
        "--cov-config=pyproject.toml",
        env=_get_session_env(session),
    )


def _run_tests_without_lockfile(
    session: nox.Session,
    *,
    install_args: Sequence[str] = (),
    extra_packages: Sequence[str] = (),
    pytest_run_args: Sequence[str] = (),
) -> None:
    """Run the test suite against a resolution that deviates from the lockfile."""
    env = _get_session_env(session)
    uv_pip_install = ["uv", "pip", "install", "--python", session.virtualenv.location, *install_args]

    session.run(
        *uv_pip_install,
        "--group",
        "test",
        "--editable",
        ".",
        env=env,
    )
    if extra_packages:
        session.run(*uv_pip_install, *extra_packages, env=env)
    session.run(
        "pytest",
        *pytest_run_args,
        *session.posargs,
        "--cov-config=pyproject.toml",
        env=env,
    )


@nox.session(python=PYTHON_ALL_VERSIONS, reuse_venv=True, venv_backend="uv", default=True, allow_parallel=True)
def minimums(session: nox.Session) -> None:
    """Test the minimum versions of dependencies."""
    _run_tests_without_lockfile(
        session,
        install_args=["--resolution=lowest-direct"],
        pytest_run_args=["-Wdefault"],
    )
    session.run("uv", "pip", "tree", "--python", session.virtualenv.location)


@nox.session(reuse_venv=True, venv_backend="uv", python=PYTHON_ALL_VERSIONS, allow_parallel=True)
def qiskit(session: nox.Session) -> None:
    """Tests against the latest version of Qiskit."""
    _run_tests_without_lockfile(
        session,
        extra_packages=["qiskit[qasm3-import] @ git+https://github.com/Qiskit/qiskit.git"],
    )
    session.run("uv", "pip", "show", "--python", session.virtualenv.location, "qiskit")


@nox.session(reuse_venv=True)
def docs(session: nox.Session) -> None:
    """Build the docs.

    Use ``--non-interactive`` to avoid serving.
    Pass ``-b linkcheck`` to check links.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", dest="builder", default="html", help="Build target (default: html)")
    args, posargs = parser.parse_known_args(session.posargs)

    serve = args.builder == "html" and session.interactive
    if serve:
        session.install("sphinx-autobuild")

    session.run(
        "uv",
        "run",
        "--no-dev",
        "--group",
        "docs",
        "--frozen",
        "sphinx-autobuild" if serve else "sphinx-build",
        "-n",  # nitpicky mode
        "-T",  # full tracebacks
        f"-b={args.builder}",
        "docs",
        f"docs/_build/{args.builder}",
        *posargs,
        env=_get_session_env(session),
    )


if __name__ == "__main__":
    nox.main()
