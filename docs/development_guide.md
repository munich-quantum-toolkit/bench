# Development Guide

Ready to contribute to the project? Here is how to set up a local development environment.

## Initial Setup

1. Fork the [munich-quantum-toolkit/bench](https://github.com/munich-quantum-toolkit/bench) repository on GitHub (see <https://docs.github.com/en/get-started/quickstart/fork-a-repo>).

2. Clone your fork locally

   > ```console
   > $ git clone git@github.com:your_name_here/mqt-bench
   > ```

3. Change into the project directory

   > ```console
   > $ cd mqt-bench
   > ```

4. Create a branch for local development

   > ```console
   > $ git checkout -b name-of-your-bugfix-or-feature
   > ```
   >
   > Now you can make your changes locally.

5. (Optional, **highly recommended**) Set up a virtual environment

   > ```console
   > $ python3 -m venv venv
   > $ source venv/bin/activate
   > ```

   ````{note}
   If you are using Windows, you can use the following command instead:

   ```console
   $ python3 -m venv venv
   $ venv\Scripts\activate.bat
   ```
   ````

   > Ensure that pip, setuptools, and wheel are up to date:
   >
   > ```console
   > (venv) $ pip install --upgrade pip setuptools wheel
   > ```

6. (Optional) Install [pre-commit](https://pre-commit.com/) to automatically run a set of checks before each commit.

   > ```console
   > (venv) $ pipx install pre-commit
   > (venv) $ pre-commit install
   > ```
   >
   > If you use macOS, then pre-commit is in brew, use {code}`brew install pre-commit`.

## Building the Python module

The recommended way of building the Python module is to perform an editable install using [pip](https://pip.pypa.io/en/stable/).

> ```console
> (venv) $ pip install -e .
> ```

The {code}`--editable` flag ensures that changes in the Python code are instantly available without re-running the command.

### Running Python Tests

The Python part of the code base is tested by unit tests using the [pytest](https://docs.pytest.org/en/latest/) framework.
The corresponding test files can be found in the {code}`tests/` directory.

> ```console
> (venv) $ pip install -e ".[test]"
> (venv) $ pytest
> ```

This installs all dependencies necessary to run the tests in an isolated environment, builds the Python package, and then runs the tests.

### Python Code Formatting and Linting

The Python code is formatted and linted using a collection of [pre-commit hooks](https://pre-commit.com/).
This collection includes:

- [ruff](https://docs.astral.sh/ruff/) -- an extremely fast Python linter and formatter, written in Rust.
- [mypy](http://mypy-lang.org/) -- a static type checker for Python code

You can install the hooks manually by running {code}`pre-commit install` in the project root directory.
The hooks will then be executed automatically when committing changes.

> ```console
> (venv) $ pre-commit run -a
> ```
