# Welcome to MQT Bench's documentation!

MQT Bench is a tool for benchmarking quantum software tools developed as part of the [Munich Quantum Toolkit](https://mqt.readthedocs.io) (_MQT_) [^1].

This documentation provides a comprehensive guide to the MQT Bench library, including {doc}`installation instructions <installation>`, a {doc}`quickstart guide <quickstart>`, and detailed {doc}`API documentation <api/mqt/bench/index>`.
The source code of MQT Bench is publicly available on GitHub at [munich-quantum-toolkit/bench](https://github.com/munich-quantum-toolkit/bench), while pre-built binaries are available via [PyPI](https://pypi.org/project/mqt.bench/) for all major operating systems and all modern Python versions.
MQT Bench is fully compatible with Qiskit 1.2 and above.

If you are interested in the theory behind MQT Bench, have a look at the publication {cite:labelpar}`quetschlich2023mqtbench`.
Furthermore, MQT Bench is also available as a [PennyLane dataset](https://pennylane.ai/datasets/single-dataset/mqt-bench).

We appreciate any feedback and contributions to the project. If you want to contribute, you can find more information in the {doc}`Contribution <contributing>` guide. If you are having trouble with the installation or the usage of MQT Bench, please let us know at our {doc}`Support <support>` page.

[^1]:
    The _[Munich Quantum Toolkit (MQT)](https://mqt.readthedocs.io)_ is a collection of software tools for quantum computing developed by the [Chair for Design Automation](https://www.cda.cit.tum.de/) at the [Technical University of Munich](https://www.tum.de/) as well as the [Munich Quantum Software Company (MQSC)](https://munichquantum.software).
    Among others, it is part of the [Munich Quantum Software Stack (MQSS)](https://www.munich-quantum-valley.de/research/research-areas/mqss) ecosystem, which is being developed as part of the [Munich Quantum Valley (MQV)](https://www.munich-quantum-valley.de) initiative.

---

```{toctree}
:hidden: true

self
```

```{toctree}
:caption: User Guide
:glob: true
:maxdepth: 2

installation
quickstart
usage
abstraction_levels
parameter
benchmark_selection
references
CHANGELOG
UPGRADING
```

```{toctree}
:maxdepth: 2
:titlesonly:
:caption: Developers
:glob:

contributing
support
development_guide
```

```{toctree}
:hidden:
:maxdepth: 6
:caption: Python API Reference

api/mqt/bench/index
```
