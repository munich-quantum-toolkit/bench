# Welcome to MQT Bench's documentation!

MQT Bench is a tool for benchmarking quantum software tools developed as part of the [Munich Quantum Toolkit](https://mqt.readthedocs.io) (_MQT_) [^footnote-1].

We recommend you to start with the {doc}`quickstart guide <quickstart>`.
If you are interested in the theory behind MQT Bench, have a look at the publication {cite:labelpar}`quetschlich2023mqtbench`.
Furthermore, MQT Bench is also available as a [PennyLane dataset](https://pennylane.ai/datasets/single-dataset/mqt-bench).

We appreciate any feedback and contributions to the project. If you want to contribute, you can find more information in the {doc}`Contribution <contributing>` guide. If you are having trouble with the installation or the usage of MQT Bench, please let us know at our {doc}`Support <support>` page.

[^footnote-1]:
    The [Munich Quantum Toolkit](https://mqt.readthedocs.io/) (_MQT_) is a collection of software tools
    for quantum computing developed by the
    [Chair for Design Automation](https://www.cda.cit.tum.de/) at the
    [Technical University of Munich](https://www.tum.de/) as well as the
    [Munich Quantum Software Company (MQSC)](https://munichquantum.software).

---

```{toctree}
:hidden: true

self
```

```{toctree}
:caption: User Guide
:glob: true
:maxdepth: 1

quickstart
usage
abstraction_levels
parameter
benchmark_selection
references
```

```{toctree}
:caption: Developers
:glob: true
:maxdepth: 1

contributing
development_guide
support
```

```{toctree}
:caption: Python API Reference
:maxdepth: 1

api/mqt/bench/index
```
