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

# MQT Bench - Benchmarking Software and Design Automation Tools for Quantum Computing

MQT Bench is a quantum circuit benchmark suite with cross-level support, i.e., providing the same benchmark algorithms for different abstraction levels throughout the quantum computing software stack.
MQT Bench is hosted at [https://mqt-bench.app/](https://mqt-bench.app/).
It is part of the [_Munich Quantum Toolkit (MQT)_](https://mqt.readthedocs.io).

<p align="center">
  <a href="https://mqt.readthedocs.io/projects/bench">
  <img width=30% src="https://img.shields.io/badge/documentation-blue?style=for-the-badge&logo=read%20the%20docs" alt="Documentation" />
  </a>
</p>

## Key Features

- **Comprehensive Quantum Benchmark Suite:** Provides a wide range of quantum circuit benchmarks, including algorithms such as GHZ, QAOA, QFT, Grover, Shor, and many more. [List of benchmarks](https://mqt.readthedocs.io/projects/bench/en/latest/benchmark_selection.html)
- **Cross-Level Benchmark Generation:** Supports four abstraction levels—algorithmic, target-independent, target-dependent native gates, and target-dependent mapped—enabling benchmarking across the entire quantum software stack. [Abstraction levels](https://mqt.readthedocs.io/projects/bench/en/latest/abstraction_levels.html)
- **Flexible Target and Gateset Support:** Generate circuits for various hardware targets and native gatesets, including IBM, IonQ, Quantinuum, Rigetti, and more. [Supported devices and gatesets](https://mqt.readthedocs.io/projects/bench/en/latest/parameter.html)
- **Python API, CLI, and Web Interface:** Use MQT Bench programmatically via Python, from the command line, or through an interactive web interface—whichever fits your workflow. [Usage guide](https://mqt.readthedocs.io/projects/bench/en/latest/usage.html)
- **Parameterized and Mirror Circuits:** Easily generate parameterized circuits (with random or symbolic parameters) and mirror circuits for robust benchmarking and error detection. [Quickstart](https://mqt.readthedocs.io/projects/bench/en/latest/quickstart.html)
- **Export to Standard Formats:** Save generated circuits in OpenQASM 2, OpenQASM 3, and QPY formats for compatibility with other quantum tools. [Output formats](https://mqt.readthedocs.io/projects/bench/en/latest/quickstart.html#output-formats)
- **Extensible and Open Source:** Actively maintained, fully open-source, and designed for easy integration and extension within the quantum computing community.

If you have any questions, feel free to create a [discussion](https://github.com/munich-quantum-toolkit/bench/discussions) or an [issue](https://github.com/munich-quantum-toolkit/bench/issues) on [GitHub](https://github.com/munich-quantum-toolkit/bench).

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
  <img src="https://contrib.rocks/image?repo=munich-quantum-toolkit/bench" alt="Contributors to munich-quantum-toolkit/bench" />
  </a>
</p>

The MQT will remain free, open-source, and permissively licensed—now and in the future.
We are firmly committed to keeping it open and actively maintained for the quantum computing community.

To support this endeavor, please consider:

- Starring and sharing our repositories: https://github.com/munich-quantum-toolkit
- Contributing code, documentation, tests, or examples via issues and pull requests
- Citing the MQT in your publications (see [Cite This](#cite-this))
- Citing our research in your publications (see [References](https://mqt.readthedocs.io/projects/bench/en/latest/references.html))
- Using the MQT in research and teaching, and sharing feedback and use cases
- Sponsoring us on GitHub: https://github.com/sponsors/munich-quantum-toolkit

<p align="center">
  <a href="https://github.com/sponsors/munich-quantum-toolkit">
  <img width=20% src="https://img.shields.io/badge/Sponsor-white?style=for-the-badge&logo=githubsponsors&labelColor=black&color=blue" alt="Sponsor the MQT" />
  </a>
</p>

## Getting Started

`mqt.bench` is available via [PyPI](https://pypi.org/project/mqt.bench/).

```console
(.venv) $ pip install mqt.bench
```

The following code gives an example on the usage:

```python3
from mqt.bench import BenchmarkLevel, get_benchmark

# Get a benchmark circuit on algorithmic level representing the GHZ state with 5 qubits
qc_algorithmic_level = get_benchmark(
    benchmark="ghz", level=BenchmarkLevel.ALG, circuit_size=5
)

# Draw the circuit
print(qc_algorithmic_level.draw())
```

> [!NOTE]
> MQT Bench is also available as a [PennyLane dataset](https://pennylane.ai/datasets/single-dataset/mqt-bench).

**Detailed documentation and examples are available at [ReadTheDocs](https://mqt.readthedocs.io/projects/bench).**

## System Requirements

MQT Bench can be installed on all major operating systems with all [officially supported Python versions](https://devguide.python.org/versions/).
Building (and running) is continuously tested under Linux, macOS, and Windows using the [latest available system versions for GitHub Actions](https://github.com/actions/runner-images).

## Cite This

Please cite the work that best fits your use case.

### MQT Bench (the tool)

When citing the software itself or results produced with it, cite the MQT Bench paper:

```bibtex
@article{quetschlich2023mqtbench,
  title        = {{{MQT Bench}}: {Benchmarking Software and Design Automation Tools for Quantum Computing}},
  shorttitle   = {{MQT Bench}},
  author       = {Quetschlich, Nils and Burgholzer, Lukas and Wille, Robert},
  year         = {2023},
  journal      = {{Quantum}},
  volume       = {7},
  pages        = {1062},
  doi          = {10.22331/q-2023-07-20-1062},
  note         = {{{MQT Bench}} is available at \url{https://mqt-bench.app/}},
  eprint       = {2204.13719},
  eprinttype   = {arxiv}
}
```

### The Munich Quantum Toolkit (the project)

When discussing the overall MQT project or its ecosystem, cite the MQT Handbook:

```bibtex
@inproceedings{mqt,
  title        = {The {{MQT}} Handbook: {{A}} Summary of Design Automation Tools and Software for Quantum Computing},
  shorttitle   = {{The MQT Handbook}},
  author       = {Wille, Robert and Berent, Lucas and Forster, Tobias and Kunasaikaran, Jagatheesan and Mato, Kevin and Peham, Tom and Quetschlich, Nils and Rovara, Damian and Sander, Aaron and Schmid, Ludwig and Schoenberger, Daniel and Stade, Yannick and Burgholzer, Lukas},
  year         = 2024,
  booktitle    = {IEEE International Conference on Quantum Software (QSW)},
  doi          = {10.1109/QSW62656.2024.00013},
  eprint       = {2405.17543},
  eprinttype   = {arxiv},
  addendum     = {A live version of this document is available at \url{https://mqt.readthedocs.io}}
}
```

---

## Acknowledgements

The Munich Quantum Toolkit has been supported by the European Research Council (ERC) under the European Union's Horizon 2020 research and innovation program (grant agreement No. 101001318), the Bavarian State Ministry for Science and Arts through the Distinguished Professorship Program, as well as the Munich Quantum Valley, which is supported by the Bavarian state government with funds from the Hightech Agenda Bayern Plus.

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/munich-quantum-toolkit/.github/refs/heads/main/docs/_static/mqt-funding-footer-dark.svg" width="90%">
    <img src="https://raw.githubusercontent.com/munich-quantum-toolkit/.github/refs/heads/main/docs/_static/mqt-funding-footer-light.svg" width="90%" alt="MQT Funding Footer">
  </picture>
</p>
