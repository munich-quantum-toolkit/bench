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

# Usage

There are multiple ways how to use this repository and the MQT Bench package.

1. Via the webpage hosted at [https://www.cda.cit.tum.de/mqtbench/](https://www.cda.cit.tum.de/mqtbench/),
2. Programmatically via the Python package [`mqt-bench`](https://pypi.org/project/mqt-bench/), or
3. Via the command line interface (CLI) of the [`mqt-bench`](https://pypi.org/project/mqt-bench/) package.

## Usage via the Webpage

The MQT Bench webpage provides an interactive, no-code interface to generate and download
benchmark circuits.
You can access it at [https://www.cda.cit.tum.de/mqtbench/](https://www.cda.cit.tum.de/mqtbench/).

## Usage via the `mqt-bench` Python package

After following the [installation guide](installation), you can use the `mqt-bench` package in your Python code.

To generate a benchmark circuit, use the {func}`~.mqt.bench.get_benchmark` method.
The available parameters are described on the {doc}`parameter space description page <parameter>` and the algorithms are described on the {doc}`algorithm page <benchmark_selection>`.
For example, in order to obtain the _5_-qubit Deutsch-Josza benchmark on algorithm level, use the following:

```{code-cell} ipython3
from mqt.bench import BenchmarkLevel, get_benchmark

qc = get_benchmark("dj", BenchmarkLevel.ALG, 5)
qc.draw(output="mpl")
```

Further examples can be found in the {doc}`quickstart` guide.

## Usage via the Command Line Interface (CLI)

In addition to the Python API, **MQT Bench** provides a flexible and lightweight command-line interface (CLI) to generate individual benchmark circuits.

The easiest way to get started with the CLI is via [`uv`](https://docs.astral.sh/uv/). Simply run

```shell
uvx mqt-bench <options>
```

You do not need to install the package for this, as `uv` will handle everything for you.
You don't even need to have Python installed, as `uv` will download a pre-built binary for your platform.

Alternatively, installing the `mqt-bench` Python package as described in the [installation guide](installation) will also provide you with the CLI.

### CLI Options

The available options can be viewed by running the command:

```shell
mqt-bench --help
```

```{code-cell} python3
:tags: [remove-input]

import subprocess

result = subprocess.run(["mqt-bench", "--help"], check=True, capture_output=True, text=True)
print(result.stdout)
```

### Example Usage

To generate a 5-qubit Deutsch-Josza benchmark circuit at the algorithm level and print it in OpenQASM 3 format, you can use the following command:

```shell
mqt-bench --level alg --algorithm dj --num-qubits 5 --output-format qasm3
```

```{code-cell} python3
---
mystnb:
  text_lexer: 'qasm3'

tags: [remove-input]
---
import subprocess

result = subprocess.run(
    ["mqt-bench", "--level", "alg", "--algorithm", "dj", "--num-qubits", "5", "--output-format", "qasm3"],
    check=True,
    capture_output=True,
    text=True
)
print(result.stdout)
```

To generate a 5-qubit Deutsch-Josza benchmark circuit at the mapped level for the 27-qubit IBM Falcon target and save it in OpenQASM 3 format, you can use:

```shell
mqt-bench --level mapped --algorithm dj --num-qubits 5 --optimization-level 3 --target ibm_falcon_27 --output-format qasm3 --save
```

```{code-cell} python3
:tags: [remove-input]
import subprocess

result = subprocess.run(
    [
        "mqt-bench",
        "--level", "mapped",
        "--algorithm", "dj",
        "--num-qubits", "5",
        "--optimization-level", "3",
        "--target", "ibm_falcon_27",
        "--output-format", "qasm3",
        "--save"
    ],
    check=True,
    capture_output=True,
    text=True
)
print(result.stdout)
filename = result.stdout.strip()
```

The command will output the filename where the generated circuit is saved, which you can then use, for example to display the contents of the file:

```{code-cell} python3
---
mystnb:
  text_lexer: 'qasm3'

tags: [hide-input]
---
# The generated circuit will be saved in the current directory.
with open(filename, "r") as file:
    print(file.read())
```

```{code-cell} python3
:tags: [remove-cell]

import os
# Clean up the generated file
os.remove(filename)
```

For more information on the available benchmarks and their parameters, please refer to the [parameter space description](parameter) and the [algorithm selection page](benchmark_selection).
