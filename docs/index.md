# Welcome to MQT Bench's documentation!

MQT Bench is a tool for benchmarking quantum software tools.
It is part of the _{doc}`Munich Quantum Toolkit (MQT) <mqt:index>`_.

This documentation provides a comprehensive guide to the MQT Bench library, including {doc}`installation instructions <installation>`, a {doc}`quickstart guide <quickstart>`, and detailed {doc}`API documentation <api/mqt/bench/index>`.
The source code of MQT Bench is publicly available on GitHub at [munich-quantum-toolkit/bench](https://github.com/munich-quantum-toolkit/bench), while pre-built binaries are available via [PyPI](https://pypi.org/project/mqt.bench/) for all major operating systems and all modern Python versions.
MQT Bench is fully compatible with Qiskit 1.2 and above.

If you are interested in the theory behind MQT Bench, have a look at the publication {cite:p}`quetschlich2023mqtbench`.
Furthermore, MQT Bench is also available as a [PennyLane dataset](https://pennylane.ai/datasets/single-dataset/mqt-bench).

We appreciate any feedback and contributions to the project.
If you want to contribute, you can find more information in the {doc}`contribution guide <contributing>`.
If you are having trouble with the installation or the usage of MQT Bench, please let us know on our {doc}`support page <support>`.

---

```{toctree}
:hidden: true

self
```

```{toctree}
:caption: User Guide
:glob:
:hidden:
:maxdepth: 1

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
:caption: Developers
:glob:
:hidden:
:maxdepth: 1

contributing
support
development_guide
```

```{toctree}
:caption: Python API Reference
:glob:
:hidden:
:maxdepth: 3

api/mqt/bench/index
```

```{only} html
## Contributors and Supporters

The _[Munich Quantum Toolkit (MQT)](https://mqt.readthedocs.io)_ is developed by the [Chair for Design Automation](https://www.cda.cit.tum.de/) at the [Technical University of Munich](https://www.tum.de/) and supported by the [Munich Quantum Software Company (MQSC)](https://munichquantum.software).
Among others, it is part of the [Munich Quantum Software Stack (MQSS)](https://www.munich-quantum-valley.de/research/research-areas/mqss) ecosystem, which is being developed as part of the [Munich Quantum Valley (MQV)](https://www.munich-quantum-valley.de) initiative.

<div style="margin-top: 0.5em">
<div class="only-light" align="center">
  <img src="https://raw.githubusercontent.com/munich-quantum-toolkit/.github/refs/heads/main/docs/_static/mqt-logo-banner-light.svg" width="90%" alt="MQT Banner">
</div>
<div class="only-dark" align="center">
  <img src="https://raw.githubusercontent.com/munich-quantum-toolkit/.github/refs/heads/main/docs/_static/mqt-logo-banner-dark.svg" width="90%" alt="MQT Banner">
</div>
</div>

Thank you to all the contributors who have helped make MQT Bench a reality!

<p align="center">
<a href="https://github.com/munich-quantum-toolkit/bench/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=munich-quantum-toolkit/bench" />
</a>
</p>

The MQT will remain free, open-source, and permissively licensed—now and in the future.
We are firmly committed to keeping it open and actively maintained for the quantum computing community.

To support this endeavor, please consider:

- Starring and sharing our repositories: [https://github.com/munich-quantum-toolkit](https://github.com/munich-quantum-toolkit)
- Contributing code, documentation, tests, or examples via issues and pull requests
- Citing the MQT in your publications (see {doc}`References <references>`)
- Using the MQT in research and teaching, and sharing feedback and use cases
- Sponsoring us on GitHub: [https://github.com/sponsors/munich-quantum-toolkit](https://github.com/sponsors/munich-quantum-toolkit)

<p align="center">
<iframe src="https://github.com/sponsors/munich-quantum-toolkit/button" title="Sponsor munich-quantum-toolkit" height="32" width="114" style="border: 0; border-radius: 6px;"></iframe>
</p>
```
