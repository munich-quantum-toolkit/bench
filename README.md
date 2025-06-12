[![PyPI](https://img.shields.io/pypi/v/mqt.bench?logo=pypi&style=flat-square)](https://pypi.org/project/mqt.bench/)
![OS](https://img.shields.io/badge/os-linux%20%7C%20macos%20%7C%20windows-blue?style=flat-square)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![CI](https://img.shields.io/github/actions/workflow/status/munich-quantum-toolkit/bench/ci.yml?branch=main&style=flat-square&logo=github&label=ci)](https://github.com/munich-quantum-toolkit/bench/actions/workflows/ci.yml)
[![CD](https://img.shields.io/github/actions/workflow/status/munich-quantum-toolkit/bench/cd.yml?style=flat-square&logo=github&label=cd)](https://github.com/munich-quantum-toolkit/bench/actions/workflows/cd.yml)
[![Documentation](https://img.shields.io/readthedocs/mqt-bench?logo=readthedocs&style=flat-square)](https://mqt.readthedocs.io/projects/bench)
[![codecov](https://img.shields.io/codecov/c/github/munich-quantum-toolkit/bench?style=flat-square&logo=codecov)](https://codecov.io/gh/munich-quantum-toolkit/bench)

<p align="center">
  <a href="https://mqt.readthedocs.io">
   <picture>
     <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/munich-quantum-toolkit/.github/refs/heads/main/docs/_static/logo-mqt-dark.svg" width="60%">
     <img src="https://raw.githubusercontent.com/munich-quantum-toolkit/.github/refs/heads/main/docs/_static/logo-mqt-light.svg" width="60%" alt="MQT Logo">
   </picture>
  </a>
</p>

# MQT Bench: Benchmarking Software and Design Automation Tools for Quantum Computing

MQT Bench is a quantum circuit benchmark suite with cross-level support, i.e., providing the same benchmark algorithms for different abstraction levels throughout the quantum computing
software stack.
MQT Bench is part of the [_Munich Quantum Toolkit_ (_MQT_)](https://mqt.readthedocs.io) and is hosted at [https://www.cda.cit.tum.de/mqtbench/](https://www.cda.cit.tum.de/mqtbench/).

<p align="center">
  <a href="https://mqt.readthedocs.io/projects/bench">
  <img width=30% src="https://img.shields.io/badge/documentation-blue?style=for-the-badge&logo=read%20the%20docs" alt="Documentation" />
  </a>
</p>

If you have any questions, feel free to create a [discussion](https://github.com/munich-quantum-toolkit/bench/discussions) or an [issue](https://github.com/munich-quantum-toolkit/bench/issues) on [GitHub](https://github.com/munich-quantum-toolkit/bench).

[<img src="https://raw.githubusercontent.com/munich-quantum-toolkit/bench/main/docs/_static/mqtbench.png" align="center" width="500" >](https://www.cda.cit.tum.de/mqtbench)

## Contributors and Supporters

The _[Munich Quantum Toolkit (MQT)](https://mqt.readthedocs.io)_ is developed by the [Chair for Design Automation](https://www.cda.cit.tum.de/) at the [Technical University of Munich](https://www.tum.de/) and supported by the [Munich Quantum Software Company (MQSC)](https://munichquantum.software).
Among others, it is part of the [Munich Quantum Software Stack (MQSS)](https://www.munich-quantum-valley.de/research/research-areas/mqss) ecosystem, which is being developed as part of the [Munich Quantum Valley (MQV)](https://www.munich-quantum-valley.de) initiative.

<p align="center">
  <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/munich-quantum-toolkit/.github/refs/heads/main/docs/_static/mqt-logo-banner-dark.svg" width="90%">
   <img src="https://raw.githubusercontent.com/munich-quantum-toolkit/.github/refs/heads/main/docs/_static/mqt-logo-banner-light.svg" width="90%" alt="MQT Partner Logos">
  </picture>
</p>

Thank you to all the contributors who have helped make MQT Bench a reality!

<p align="center">
<a href="https://github.com/munich-quantum-toolkit/bench/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=munich-quantum-toolkit/bench" />
</a>
</p>

## Getting Started

`mqt-bench` is available via [PyPI](https://pypi.org/project/mqt.bench/).

```console
(venv) $ pip install mqt.bench
```

The following code gives an example on the usage:

```python3
from mqt.bench import BenchmarkLevel, get_benchmark

# get a benchmark circuit on algorithmic level representing the GHZ state with 5 qubits
qc_algorithmic_level = get_benchmark(
    benchmark_name="ghz", level=BenchmarkLevel.ALG, circuit_size=5
)

# draw the circuit
print(qc_algorithmic_level.draw())
```

**Detailed documentation and examples are available at [ReadTheDocs](https://mqt.readthedocs.io/projects/bench).**

## Availability as a PennyLane Dataset

MQT Bench is also available as a [PennyLane dataset](https://pennylane.ai/datasets/single-dataset/mqt-bench).

## Cite This

If you want to cite MQT Bench, please use the following BibTeX entry:

```bibtex
@article{quetschlich2023mqtbench,
  title         = {{{MQT Bench}}: {Benchmarking Software and Design Automation Tools for Quantum Computing}},
  shorttitle    = {{MQT Bench}},
  journal       = {{Quantum}},
  author        = {Quetschlich, Nils and Burgholzer, Lukas and Wille, Robert},
  year          = {2023},
  doi           = {10.22331/q-2023-07-20-1062},
  eprint        = {2204.13719},
  primaryclass  = {quant-ph},
  archiveprefix = {arxiv},
  note          = {{{MQT Bench}} is available at \url{https://www.cda.cit.tum.de/mqtbench/}},
}
```

## Acknowledgements

This project received funding from the European Research Council (ERC) under the European
Union's Horizon 2020 research and innovation program (grant agreement No. 101001318), was
part of the Munich Quantum Valley, which is supported by the Bavarian state government with
funds from the Hightech Agenda Bayern Plus, and has been supported by the BMWK on the basis
of a decision by the German Bundestag through project QuaST, as well as by the BMK, BMDW,
and the State of Upper Austria in the frame of the COMET program (managed by the FFG).

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/munich-quantum-toolkit/.github/refs/heads/main/docs/_static/mqt-funding-footer-dark.svg" width="90%">
    <img src="https://raw.githubusercontent.com/munich-quantum-toolkit/.github/refs/heads/main/docs/_static/mqt-funding-footer-light.svg" width="90%" alt="MQT Funding Footer">
  </picture>
</p>
