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
from pathlib import Path

import nox

nox.needs_version = ">=2026.10.20"
nox.options.default_venv_backend = "uv"

PYTHON_ALL_VERSIONS = ["3.11", "3.12", "3.13", "3.14", "3.15"]

if os.environ.get("CI", None):
    nox.options.error_on_missing_interpreters = True
    nox.options.parallel = "auto"


@nox.session(reuse_venv=True, default=True)
def lint(session: nox.Session) -> None:
    """Run the linter."""
    if shutil.which("prek") is None:
        session.install("prek")

    session.run("prek", "run", "--all-files", *session.posargs, external=True)


def _run_tests(session: nox.Session, *pytest_args: str, locked: bool = False) -> None:
    env = {"UV_PROJECT_ENVIRONMENT": session.virtualenv.location}
    command = ("uv", "run", "--locked", "--no-dev", "--group", "test") if locked else ()
    posargs = session.posargs
    if session.parallel:
        pytest_args += ("-n", "0")
        env["COVERAGE_FILE"] = str(Path(session.virtualenv.location).resolve() / ".coverage")
        # The reusable workflow passes the same report path to every session.
        posargs = [
            f"{arg.removesuffix('.xml')}-{session.name}.xml"
            if arg.startswith("--cov-report=xml:") and arg.endswith(".xml")
            else arg
            for arg in posargs
        ]
    session.run(
        *command,
        "pytest",
        *pytest_args,
        *posargs,
        "--cov-config=pyproject.toml",
        env=env,
    )


@nox.session(python=PYTHON_ALL_VERSIONS, reuse_venv=True, default=True, allow_parallel=True)
def tests(session: nox.Session) -> None:
    """Run the test suite."""
    _run_tests(session, locked=True)


@nox.session(python=PYTHON_ALL_VERSIONS, default=True, allow_parallel=True)
def minimums(session: nox.Session) -> None:
    """Test the minimum versions of dependencies."""
    session.install("--resolution=lowest-direct", "--group", "test", "--editable", ".")
    _run_tests(session, "-Wdefault")
    session.run("uv", "pip", "tree")


@nox.session(python=PYTHON_ALL_VERSIONS)
def qiskit(session: nox.Session) -> None:
    """Tests against the latest version of Qiskit."""
    session.install("--group", "test", "--editable", ".")
    session.install("qiskit[qasm3-import] @ git+https://github.com/Qiskit/qiskit.git")
    _run_tests(session)
    session.run("uv", "pip", "show", "qiskit")


@nox.session(python="3.14", reuse_venv=True)
def docs(session: nox.Session) -> None:
    """Build the docs. Use "--non-interactive" to avoid serving. Pass "-b linkcheck" to check links."""
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", dest="builder", default="html", help="Build target (default: html)")
    args, posargs = parser.parse_known_args(session.posargs)

    serve = args.builder == "html" and session.interactive
    if serve:
        session.install("sphinx-autobuild")

    env = {"UV_PROJECT_ENVIRONMENT": session.virtualenv.location}
    shared_args = [
        "-n",  # nitpicky mode
        "-T",  # full tracebacks
        f"-b={args.builder}",
        "docs",
        f"docs/_build/{args.builder}",
        *posargs,
    ]

    session.run(
        "uv",
        "run",
        "--no-dev",
        "--group",
        "docs",
        "--frozen",
        "sphinx-autobuild" if serve else "sphinx-build",
        *shared_args,
        env=env,
    )


if __name__ == "__main__":
    nox.main()
