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
