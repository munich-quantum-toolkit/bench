---
file_format: mystnb
kernelspec:
  name: python3
mystnb:
  number_source_lines: true
  execution_in_temp: true
---

# Usage

## Usage via the Webpage

Use the [web interface](https://mqt-bench.app/) to generate and download a
benchmark interactively, or use Python or the CLI to automate generation.

When you use the web interface to generate and download circuits, also cite the
2026 paper (see {doc}`references`).

## Usage via the `mqt-bench` Python package

After {doc}`installation`, pass a name from the
{doc}`benchmark catalogue <benchmark_selection>`, a level, and a size to
{func}`~mqt.bench.get_benchmark`. This call returns a five-qubit Deutsch–Jozsa
circuit at the algorithmic level:

```{code-cell} ipython3
from mqt.bench import BenchmarkLevel, get_benchmark

qc = get_benchmark("dj", BenchmarkLevel.ALG, 5)
print(qc.draw(output="text"))
```

Further examples can be found in the {doc}`quickstart` guide.

## Usage via the Command Line Interface (CLI)

Installing MQT Bench provides the `mqt-bench` command. To try it in an isolated
environment with [uv](https://docs.astral.sh/uv/), run `uvx mqt-bench --help`.

### CLI Options

List the available options with `mqt-bench --help`:

```{code-cell} python3
:tags: [remove-input]

import subprocess

result = subprocess.run(["mqt-bench", "--help"], check=True, capture_output=True, text=True)
print(result.stdout)
```

### Example Usage

List benchmark names and descriptions, or available gate sets and devices:

```shell
mqt-bench --list-benchmarks
mqt-bench --list-targets
```

Use `--seed` to reproduce random parameters and the choices of factories that
accept a seed. Pass factory options through `--benchmark-options` as a JSON
object:

```shell
mqt-bench --level alg --algorithm graphstate --num-qubits 6 --seed 42
mqt-bench --level alg --algorithm qwalk --num-qubits 3 --benchmark-options '{"depth": 5, "for_loop": true}'
```

The Python API accepts the same options as keyword arguments. With
`random_parameters=True`, `seed` also controls the numeric values assigned to
symbolic parameters. Omitting `seed` preserves each factory's default.

OpenQASM is printed to stdout by default. For example, generate a five-qubit
Deutsch–Jozsa circuit in OpenQASM 3:

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

Pass `--save` to write OpenQASM to a file. QPY and QIR bitcode always write a
file. `--target-directory` selects the output directory. The CLI prints the
saved path. This command maps the circuit to the IBM Heron device model:

```shell
mqt-bench --level mapped --algorithm dj --num-qubits 5 --optimization-level 3 --target ibm_heron_156 --output-format qasm3 --save
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
        "--target", "ibm_heron_156",
        "--output-format", "qasm3",
        "--save"
    ],
    check=True,
    capture_output=True,
    text=True
)
print(result.stdout)
```

For the Python equivalents of the CLI options, see the {doc}`parameter` guide.

## Docker

From a Git clone, build the image and run the CLI:

```bash
docker build -t mqt-bench .
docker run --rm mqt-bench --algorithm ghz --num-qubits 3 --level alg
```

Use `docker run --rm -t mqt-bench --help` for colored CLI help.
