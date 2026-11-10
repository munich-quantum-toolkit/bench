# Welcome to MQT Bench's documentation

MQT Bench generates quantum circuits for benchmarking quantum software tools.
Choose an algorithm and a size, then generate the circuit at one of four
{doc}`abstraction levels <abstraction_levels>`. MQT Bench is part of the
_{doc}`Munich Quantum Toolkit (MQT) <mqt:index>`_.

- **[Generate online](https://mqt-bench.app/)**: Create and download benchmark
  circuits in your browser.
- **{doc}`Use Python or the CLI <usage>`**: Generate circuits from code or the
  command line.
- **{doc}`2026 paper and citation <references>`**: Benchmark generation for
  software evaluation, hardware design, and AI training.

Start with {doc}`installation` and {doc}`quickstart` to generate your first
circuit. The {doc}`benchmark catalogue <benchmark_selection>` lists the
algorithms and their parameters. Browse the
{doc}`API reference <api/mqt/bench/index>` for the Python interfaces. Circuits
are also available as a
[PennyLane dataset](https://pennylane.ai/datasets/single-dataset/mqt-bench).

The [source code](https://github.com/munich-quantum-toolkit/bench) is on GitHub
and the [Python package](https://pypi.org/project/mqt.bench/) is on PyPI. See
{doc}`references` for publications, {doc}`contributing` to contribute, or
{doc}`support` to get help.

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
error_correction
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
ai_usage
tooling
support
```

```{toctree}
:caption: Python API Reference
:glob:
:hidden:
:maxdepth: 3

api/mqt/bench/index
```

## Contributors and Supporters

MQT Bench is developed by the
[Chair for Design Automation](https://www.cda.cit.tum.de/) at the
[Technical University of Munich](https://www.tum.de/) and [MQSC](https://mq.sc).
Among others, it is part of the
[Munich Quantum Software Stack (MQSS)](https://www.munich-quantum-valley.de/research/research-areas/mqss)
ecosystem, which is being developed as part of the
[Munich Quantum Valley (MQV)](https://www.munich-quantum-valley.de) initiative.

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

The MQT will remain free, open-source, and permissively licensed—now and in the
future. We are firmly committed to keeping it open and actively maintained for
the quantum computing community.

To support this endeavor, please consider:

- Starring and sharing our repositories:
  <https://github.com/munich-quantum-toolkit>
- Contributing code, documentation, tests, or examples via issues and pull
  requests
- Citing the MQT in your publications (see {doc}`References <references>`)
- Using the MQT in research and teaching, and sharing feedback and use cases
- Sponsoring us on GitHub:
  <https://github.com/sponsors/munich-quantum-toolkit>

<p align="center">
<iframe src="https://github.com/sponsors/munich-quantum-toolkit/button" title="Sponsor munich-quantum-toolkit" height="32" width="114" style="border: 0; border-radius: 6px;"></iframe>
</p>
