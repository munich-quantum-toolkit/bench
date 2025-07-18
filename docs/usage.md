---
file_format: mystnb
kernelspec:
  name: python3
mystnb:
  number_source_lines: true
---

```{code-cell} ipython3
:tags: [remove-cell]
%config InlineBackend.figure_formats = ['svg']
```

# Repository Usage

There are three ways how to use this benchmark suite:

1. Via the webpage hosted at [https://www.cda.cit.tum.de/mqtbench/](https://www.cda.cit.tum.de/mqtbench/)
2. Via the pip package `mqt.bench`
3. Directly via this repository

Since the first way is rather self-explanatory, the other two ways are explained in more detail in the following.

(pip-usage)=

## Usage via pip package

MQT Bench is available via [PyPI](https://pypi.org/project/mqt.bench/)

```console
(venv) $ pip install mqt.bench
```

To generate a benchmark circuit, use the {func}`~.mqt.bench.get_benchmark` method.
The available parameters are described on the {doc}`parameter space description page <parameter>` and the algorithms are described on the {doc}`algorithm page <benchmark_selection>`.
For example, in order to obtain the _5_-qubit Deutsch-Josza benchmark on algorithm level, use the following:

```{code-cell} ipython3
from mqt.bench import BenchmarkLevel, get_benchmark

qc = get_benchmark("dj", BenchmarkLevel.ALG, 5)
qc.draw(output="mpl")
```

Examples can be found in the {doc}`quickstart` jupyter notebook.

## Usage directly via this repository

For that, the repository must be cloned and installed:

```
git clone https://github.com/munich-quantum-toolkit/bench.git mqt-bench
cd mqt-bench
pip install .
```

Afterwards, the package can be used as described {ref}`above <pip-usage>`.

## Usage via the Command Line Interface (CLI)

In addition to the Python API, **MQT Bench** provides a flexible and lightweight command-line interface (CLI) to generate individual benchmark circuits.

After installing the package, the CLI tool `mqt-bench` becomes available.

### Getting Started

Make sure the package is installed:

```bash
pip install mqt.bench
```

You can then view the available CLI options with:

```bash
mqt-bench --help
```

### CLI Options

```bash
options:
  -h, --help: show this help message and exit
  --level {alg,indep,nativegates,mapped}: Level to generate benchmarks for ("alg", "indep", "nativegates" or "mapped").
  --algorithm ALGORITHM: Name of the benchmark (e.g., 'grover', 'shor').
  --num-qubits NUM_QUBITS: Number of qubits for the benchmark.
  --optimization-level {0,1,2,3}: Qiskit compiler optimization level (0-3).
  --target TARGET: Target name for native gates and mapped level (e.g., 'ibm_falcon' or 'ibm_washington').
  --random-parameters, --no-random-parameters: Whether to assign random parameters to parametric circuits (default: True). Use --no-random-parameters to disable.
  --output-format {qasm2,qasm3,qpy}: Output format. Possible values: ['qasm2', 'qasm3', 'qpy'].
  --target-directory TARGET_DIRECTORY: Directory to save the output file (only used for 'qpy' or if --save is specified).
  --save: If set, save the output to a file instead of printing to stdout (e.g. for 'qpy', which is not available as text).
  --mirror: If set, generate the mirror version of the benchmark (circuit @ circuit.inverse()).
```

### Example Usage

To generate a 5-qubit Deutsch-Josza benchmark circuit at the algorithm level and print it in QASM 2 format, you can use the following command:

```bash
mqt-bench --level alg --algorithm dj --num-qubits 5 --output-format qasm2
```

To generate a 5-qubit Deutsch-Josza benchmark circuit at the mapped level for the IBM Falcon target and save it in QASM 3 format, you can use:

```bash
mqt-bench --level mapped --algorithm dj --num-qubits 5 --optimization-level 3 --target ibm_falcon_27 --output-format qasm3 --save
```

For more information on the available benchmarks and their parameters, please refer to the [parameter space description](parameter) and the [algorithm selection page](benchmark_selection).

### CLI Usage without Installation

If you prefer not to install the package, you can still use the CLI by running the following command from the root directory of the cloned repository:

```bash
uvx --from mqt-bench mqt-bench --level alg --algorithm ghz --num-qubits 5
```

This command uses `uvx` to run the CLI directly from the source code without installation.
