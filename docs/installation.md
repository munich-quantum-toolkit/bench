# Installation

The MQT Bench Python package is available on [PyPI](https://pypi.org/project/mqt.bench/) and can be installed on all major operating systems using all modern Python versions.

:::::{tip}
We highly recommend using [`uv`](https://docs.astral.sh/uv/) for working with Python projects.
It is an extremely fast Python package and project manager, written in Rust and developed by [Astral](https://astral.sh/) (the same team behind [`ruff`](https://docs.astral.sh/ruff/)).
It can act as a drop-in replacement for `pip` and `virtualenv`, and provides a more modern and faster alternative to the traditional Python package management tools.
It automatically handles the creation of virtual environments and the installation of packages, and is much faster than `pip`.
Additionally, it can even set up Python for you if it is not installed yet.

If you do not have `uv` installed yet, you can install it via:

::::{tab-set}
:::{tab-item} macOS and Linux

```console
$ curl -LsSf https://astral.sh/uv/install.sh | sh
```

:::
:::{tab-item} Windows

```console
$ powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

::::

Check out their excellent [documentation](https://docs.astral.sh/uv/) for more information.

:::::

::::{tab-set}
:sync-group: installer

:::{tab-item} uv _(recommended)_
:sync: uv

```console
$ uv pip install mqt.bench
```

:::

:::{tab-item} pip
:sync: pip

```console
(.venv) $ python -m pip install mqt.bench
```

:::
::::

Once installed, you can check if the installation was successful by running:

```console
(.venv) $ python -c "import mqt.bench; print(mqt.bench.__version__)"
```

which should print the installed version of the library.

## Integrating MQT Bench into your project

If you want to use the MQT Bench Python package in your own project, you can simply add it as a dependency in your `pyproject.toml` or `setup.py` file.
This will automatically install the MQT Bench package when your project is installed.

::::{tab-set}

:::{tab-item} uv _(recommended)_

```console
$ uv add mqt.bench
```

:::

:::{tab-item} pyproject.toml

```toml
[project]
# ...
dependencies = ["mqt.bench>=2.0.0"]
# ...
```

:::
