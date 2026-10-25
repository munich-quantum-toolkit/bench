<!-- Entries in each category are sorted by merge time, with the latest PRs appearing first. -->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on a mixture of
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and
[Common Changelog](https://common-changelog.org). This project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html), with the exception
that minor releases may include breaking changes.

## [Unreleased]

### Added

- ✨ Expose benchmark options, seeds, and catalogues in the CLI; record
  generation settings in circuit metadata and export headers ([#1115])
  ([**@simon1hofmann**])
- ✨ Add Simon's algorithm benchmark ([#1079]) ([**gautham0104-neitizen**])
- ✨ Add the full 108-qubit Rigetti Cepheus architecture and document target
  models ([#1095]) ([**@simon1hofmann**], [**@burgholzer**])
- ✨ Add fractional IBM Heron targets with bounded RZZ angles ([#1087])
  ([**@burgholzer**], [**@simon1hofmann**])
- ✨ Add the IBM Nighthawk 120-qubit device and CZ gate set ([#1085])
  ([**@burgholzer**])
- ✨ Add the AQT IBEX 12-qubit device and native gate set ([#1084])
  ([**@burgholzer**])
- ✨ Add `SPDX-License-Identifier: MIT` to generated circuit headers ([#1083])
  ([**@simon1hofmann**])
- ✨ Add Bell-pair benchmark ([#1071]) ([**@NiranjanRSoorej06**])
- 👷 Enable testing on Python 3.15 ([#1054]) ([**@denialhaag**])
- ✨ Add quantum teleportation benchmark ([#1045]) ([**@AsharHusain**])
- ✨ Add ML-QAE benchmark ([#1044]) ([**@algovista-collab**])
- ✨ Add Superdense Coding benchmark ([#1037]) ([**@Anshu666666**])

### Changed

- ⚡ Test all Python versions on Linux and Python 3.15 on other platforms for
  ready pull requests. Keep the full matrix on main, merge queues, and manual
  runs ([#1112]) ([**@simon1hofmann**])
- ⬆️ Raise the minimum Qiskit version to 2.2.3 ([#1087])
  ([**@simon1hofmann**])
- ✨ Use gridsynth for native Clifford+T compilation on Qiskit 2.4.2 and newer,
  retaining Solovay-Kitaev on earlier supported versions ([#1081])
  ([**@simon1hofmann**])
- ✨ Measure arithmetic sums and products in a `result` register, excluding
  input and helper qubits ([#1065]) ([**@simon1hofmann**])

### Fixed

- 🐛 Preserve logical permutations in target-independent and native QASM
  exports, and ignore device capacity during native compilation ([#1116])
  ([**@simon1hofmann**])
- 🐛 Preserve existing files when export fails, create output directories, and
  report CLI argument and export errors on stderr ([#1115])
  ([**@simon1hofmann**])
- 🐛 Select Clifford+T synthesis from target capabilities instead of
  descriptions ([#1110]) ([**@simon1hofmann**])
- 🐛 Validate benchmark sizes and options, document factory constraints, and
  type supported keyword arguments ([#1108]) ([**@simon1hofmann**])
- 🐛 Validate qubit counts across benchmarks, including the Shor, Steane, and
  BMW copula benchmarks; combine size checks for Bell pairs and teleportation
  ([#1098]) ([#1106]) ([**@jyothikacodes**], [**@simon1hofmann**],
  [**@NiranjanRSoorej06**])
- 🐛 Keep native Clifford+T optimization in the target basis, including loops
  and mirrors, and preserve permutations in QASM exports ([#1093])
  ([**@simon1hofmann**], [**@burgholzer**])
- 🐛 Preserve native IonQ and Rigetti gate phases with local Qiskit lowering and
  mirror layouts; require Qiskit 2.1.2 or newer ([#1086]) ([**@burgholzer**],
  [**@simon1hofmann**])
- 📝 Fix API documentation markup, heading anchors, and notebook build
  concurrency ([#1088]) ([**@burgholzer**])
- 🐛 Preserve caller-provided circuits during benchmark generation ([#1077])
  ([**@AthulKampiyil**])
- 🐛 Default optimization level to 2 and require target for native gates and
  mapped levels in CLI ([#1076]) ([**@jyothikacodes**])
- 🐛 Compile native gates without device connectivity or simulated calibration,
  and keep coupling-map headers stable across Qiskit versions ([#1069], [#1067])
  ([**@simon1hofmann**], [**@burgholzer**], [**@denialhaag**])
- 🐛 Restore final measurements on all qubits in QAOA benchmarks ([#1059])
  ([**@flowerthrower**])
- 🐛 Report unsupported mirror circuits with a clear error and retain final
  measurements when inversion fails ([#1052]) ([**@simon1hofmann**])
- 🐛 Support two-qubit quantum walks with and without structured loops ([#1052])
  ([**@simon1hofmann**])
- 🐛 Preserve active qubit references when recompiling mirror circuits ([#1052])
  ([**@simon1hofmann**])
- 🐛 Preserve measurements and classical registers when compiling to Clifford+T
  ([#1047]) ([**@simon1hofmann**])
- 🐛 Expose `__version__` and `__version_tuple__` at the package root ([#1031])
  ([**@algovista-collab**])

### Removed

- 🔥 Remove the unused scikit-learn runtime dependency and its unused transitive
  dependencies ([#1114]) ([**@simon1hofmann**])
- 🔥 Remove retired IBM Falcon, Eagle, and 133-qubit Heron models ([#1089])
  ([**@burgholzer**])

## [2.3.0] - 2026-09-12

_If you are upgrading: please see [`UPGRADING.md`](UPGRADING.md#230)._

### Added

- ✨ Add optional structured loops to Grover's algorithm and quantum walk
  ([#997]) ([**@flowerthrower**])

### Changed

- ⬆️ Raise the minimum Qiskit version from 2.0.0 to 2.1.0 ([#1024])
  ([**@denialhaag**])
- 🔥 Drop support for Python 3.10 ([#999]) ([**@denialhaag**])
- 🍎 Stop testing on x86 macOS systems ([#999]) ([**@denialhaag**])

### Removed

- 🔥 Remove the `create_mqt_bench_zip` and `generate_mqt_bench` console scripts,
  whose target modules no longer exist ([#1011]) ([**@cnYui**])

## [2.2.3] - 2026-07-07

### Added

- ✨ Add Dynamic Quantum Fourier Transform benchmark ([#946])
  ([**@flowerthrower**])
- ✨ Add Iterative Quantum Phase Estimation (IQPE) benchmark ([#925])
  ([**@johanneswittmann9**])

### Fixed

- 🐛 Seed `GenericBackendV2` used by `get_target_for_gateset` to ensure
  reproducibility ([#952]) ([**@denialhaag**])
- 🐛 Make IQM Crystal device connectivity bidirectional ([#914])
  ([**@flowerthrower**])

## [2.2.2] - 2026-04-20

### Fixed

- 🚸 Fix compatibility with Qiskit 2.4 ([#895]) ([**@burgholzer**])

## [2.2.1] - 2026-03-23

Rerelease of 2.2.0: no code changes. The CD pipeline failed for v2.2.0 and
release artifacts are immutable, so this patch version republishes the same
release contents.

## [2.2.0] - 2026-03-23

_If you are upgrading: please see [`UPGRADING.md`](UPGRADING.md#220)._

### Added

- ✨ Add support for compiling `if_test` for all gatesets and devices ([#805])
  ([**@adnathanail**])
- ✨ Add benchmark for dynamical GHZ state generation ([#816]) ([**@TomasVF**])
- ✨ Add Shor's 9 Qubit Code benchmark ([#803]) ([**@adnathanail**])
- ✨ Add 7 Qubit Steane Code benchmark ([#814]) ([**@adnathanail**])

### Changed

- 🏷️ Replace `mypy` with `ty` for static type checking ([#794])
  ([**@burgholzer**])
- ⬆️ Increase minimum Qiskit version to 2.0.0 ([#803]) ([**@adnathanail**])

### Fixed

- 🐛 Fixed `num_state_qubits` calculation in `multiplier` and
  `vbe_ripple_carry_adder` circuits ([#865]) ([**@simon1hofmann**])

## [2.1.0] - 2025-10-18

_If you are upgrading: please see [`UPGRADING.md`](UPGRADING.md#210)._

### Added

- 👷 Enable testing on Python 3.14 ([#705]) ([**@denialhaag**])

### Changed

- ✨ Expose seed of graphstate generation ([#731]) ([**@ystade**])

### Fixed

- 🐛 Fix layout preservation and ensure native gate compliance for mirror
  circuit generation ([#709]) ([**@soroushfathi**], [**@burgholzer**])

### Removed

- 🔥 Drop support for Python 3.9 ([#671]) ([**@denialhaag**])

## [2.0.1] - 2025-07-28

### Changed

- 🎨 Rename CLI from `mqt.bench.cli` to `mqt-bench` ([#625]) ([**@burgholzer**],
  [**@nquetschlich**])
- 📝 Rewrite the usage documentation to include the CLI ([#625])
  ([**@burgholzer**], [**@nquetschlich**])

## [2.0.0] - 2025-06-24

_If you are upgrading: please see [`UPGRADING.md`](UPGRADING.md#200)._

### Added

- ✨ Add mirror circuit option for all benchmarks ([#577], [#603])
  ([**@CreativeBinBag**], [**@burgholzer**], [**@nquetschlich**])
- ✨ Add arithmetic benchmarks ([#586]) ([**@simon1hofmann**],
  [**@burgholzer**])
- ✨ Add registry for benchmarks, devices, and native gatesets ([#585], [#572])
  ([**@simon1hofmann**], [**@burgholzer**])
- ✨ Add symbolic parameters for variational benchmarks ([#581])
  ([**@nquetschlich**], [**@burgholzer**])
- ✨ Add distinct `get_benchmark` function per level ([#571])
  ([**@simon1hofmann**], [**@burgholzer**])
- ✨ Add HHL algorithm ([#582]) ([**@nquetschlich**], [**@burgholzer**])
- ✨ Add support for compiling to the Clifford+T gateset ([#555])
  ([**@simon1hofmann**], [**@burgholzer**], [**@nquetschlich**])
- ✨ Add two benchmarks from BMW's QUARK framework ([#541]) ([**@fkiwit**])
- ✨ Add support for exporting to OpenQASM 3 ([#518]) ([**@simon1hofmann**],
  [**@burgholzer**], [**@nquetschlich**])
- ✨ Add support for exporting to Qiskit's QPY ([#518]) ([**@simon1hofmann**],
  [**@burgholzer**], [**@nquetschlich**])
- ✨ Add Bernstein-Vazirani algorithm ([#505]) ([**@simon1hofmann**],
  [**@burgholzer**], [**@nquetschlich**])

### Changed

- ✨ Call `transpile` for optimization at the target-independent level ([#580])
  ([**@simon1hofmann**], [**@burgholzer**])
- 🎨 Adjust supported IonQ Devices and update all Calibration Data ([#570])
  ([**@nquetschlich**], [**@burgholzer**])
- 🎨 Correct the Rigetti gateset to only support RX gate with specific and not
  arbitrary angles and updated the calibration data ([#570])
  ([**@nquetschlich**], [**@burgholzer**])
- ✨ Switch device and gateset representation to Qiskit's Target ([#560])
  ([**@burgholzer**], [**@nquetschlich**])
- 📝 Update and modernize project documentation ([#566]) ([**@simon1hofmann**])
- 📝 Add CHANGELOG and UPGRADING info ([#567]) ([**@simon1hofmann**])
- 🎨 Shorten and improve the generation logic of the Shor benchmark ([#548])
  ([**@simon1hofmann**])
- 🚚 Rebrand and move to MQT GitHub organization ([#544]) ([**@simon1hofmann**])
- ✨ Re-add Python 3.9 support ([#531]) ([**@simon1hofmann**])
- 🎨 Rename random circuit and VQE ansatz circuit benchmarks ([#508])
  ([**@simon1hofmann**], [**@nquetschlich**])
- 🎨 Re-implement amplitude estimation without Qiskit Application modules
  ([#506]) ([**@simon1hofmann**], [**@burgholzer**], [**@nquetschlich**])

### Removed

- 🔥 Remove Generation Logic for Webpage ([#538]) ([**@nquetschlich**])
- 🔥 Remove TKET-related functionality ([#519], [#510]) ([**@simon1hofmann**])
- 🔥 Remove Qiskit Application-based benchmarks ([#507]) ([**@simon1hofmann**],
  [**@nquetschlich**])
- 🔥 Remove `benchviewer` and `evaluation` modules ([#504]) ([**@burgholzer**],
  [**@nquetschlich**])

## [1.1.9] - 2024-12-01

_📚 Refer to the [GitHub Release Notes] for previous changelogs._

<!-- Version links -->

[unreleased]: https://github.com/munich-quantum-toolkit/bench/compare/v2.3.0...HEAD
[2.3.0]: https://github.com/munich-quantum-toolkit/bench/releases/tag/v2.3.0
[2.2.3]: https://github.com/munich-quantum-toolkit/bench/releases/tag/v2.2.3
[2.2.2]: https://github.com/munich-quantum-toolkit/bench/releases/tag/v2.2.2
[2.2.1]: https://github.com/munich-quantum-toolkit/bench/releases/tag/v2.2.1
[2.2.0]: https://github.com/munich-quantum-toolkit/bench/releases/tag/v2.2.0
[2.1.0]: https://github.com/munich-quantum-toolkit/bench/releases/tag/v2.1.0
[2.0.1]: https://github.com/munich-quantum-toolkit/bench/releases/tag/v2.0.1
[2.0.0]: https://github.com/munich-quantum-toolkit/bench/releases/tag/v2.0.0
[1.1.9]: https://github.com/munich-quantum-toolkit/bench/releases/tag/v1.1.9

<!-- PR links -->

[#1116]: https://github.com/munich-quantum-toolkit/bench/pull/1116
[#1115]: https://github.com/munich-quantum-toolkit/bench/pull/1115
[#1114]: https://github.com/munich-quantum-toolkit/bench/pull/1114
[#1112]: https://github.com/munich-quantum-toolkit/bench/pull/1112
[#1110]: https://github.com/munich-quantum-toolkit/bench/pull/1110
[#1108]: https://github.com/munich-quantum-toolkit/bench/pull/1108
[#1106]: https://github.com/munich-quantum-toolkit/bench/pull/1106
[#1098]: https://github.com/munich-quantum-toolkit/bench/pull/1098
[#1095]: https://github.com/munich-quantum-toolkit/bench/pull/1095
[#1093]: https://github.com/munich-quantum-toolkit/bench/pull/1093
[#1089]: https://github.com/munich-quantum-toolkit/bench/pull/1089
[#1088]: https://github.com/munich-quantum-toolkit/bench/pull/1088
[#1087]: https://github.com/munich-quantum-toolkit/bench/pull/1087
[#1086]: https://github.com/munich-quantum-toolkit/bench/pull/1086
[#1085]: https://github.com/munich-quantum-toolkit/bench/pull/1085
[#1084]: https://github.com/munich-quantum-toolkit/bench/pull/1084
[#1083]: https://github.com/munich-quantum-toolkit/bench/pull/1083
[#1081]: https://github.com/munich-quantum-toolkit/bench/pull/1081
[#1079]: https://github.com/munich-quantum-toolkit/bench/pull/1079
[#1077]: https://github.com/munich-quantum-toolkit/bench/pull/1077
[#1076]: https://github.com/munich-quantum-toolkit/bench/pull/1076
[#1071]: https://github.com/munich-quantum-toolkit/bench/pull/1071
[#1069]: https://github.com/munich-quantum-toolkit/bench/pull/1069
[#1067]: https://github.com/munich-quantum-toolkit/bench/pull/1067
[#1065]: https://github.com/munich-quantum-toolkit/bench/pull/1065
[#1059]: https://github.com/munich-quantum-toolkit/bench/pull/1059
[#1054]: https://github.com/munich-quantum-toolkit/bench/pull/1054
[#1052]: https://github.com/munich-quantum-toolkit/bench/pull/1052
[#1047]: https://github.com/munich-quantum-toolkit/bench/pull/1047
[#1045]: https://github.com/munich-quantum-toolkit/bench/pull/1045
[#1044]: https://github.com/munich-quantum-toolkit/bench/pull/1044
[#1037]: https://github.com/munich-quantum-toolkit/bench/pull/1037
[#1031]: https://github.com/munich-quantum-toolkit/bench/pull/1031
[#1024]: https://github.com/munich-quantum-toolkit/bench/pull/1024
[#1011]: https://github.com/munich-quantum-toolkit/bench/pull/1011
[#999]: https://github.com/munich-quantum-toolkit/bench/pull/999
[#997]: https://github.com/munich-quantum-toolkit/bench/pull/997
[#952]: https://github.com/munich-quantum-toolkit/bench/pull/952
[#946]: https://github.com/munich-quantum-toolkit/bench/pull/946
[#925]: https://github.com/munich-quantum-toolkit/bench/pull/925
[#914]: https://github.com/munich-quantum-toolkit/bench/pull/914
[#895]: https://github.com/munich-quantum-toolkit/bench/pull/895
[#865]: https://github.com/munich-quantum-toolkit/bench/pull/865
[#816]: https://github.com/munich-quantum-toolkit/bench/pull/816
[#814]: https://github.com/munich-quantum-toolkit/bench/pull/814
[#805]: https://github.com/munich-quantum-toolkit/bench/pull/805
[#803]: https://github.com/munich-quantum-toolkit/bench/pull/803
[#794]: https://github.com/munich-quantum-toolkit/bench/pull/794
[#731]: https://github.com/munich-quantum-toolkit/bench/pull/731
[#709]: https://github.com/munich-quantum-toolkit/bench/pull/709
[#705]: https://github.com/munich-quantum-toolkit/bench/pull/705
[#671]: https://github.com/munich-quantum-toolkit/bench/pull/671
[#625]: https://github.com/munich-quantum-toolkit/bench/pull/625
[#603]: https://github.com/munich-quantum-toolkit/bench/pull/603
[#586]: https://github.com/munich-quantum-toolkit/bench/pull/586
[#585]: https://github.com/munich-quantum-toolkit/bench/pull/585
[#582]: https://github.com/munich-quantum-toolkit/bench/pull/582
[#581]: https://github.com/munich-quantum-toolkit/bench/pull/581
[#580]: https://github.com/munich-quantum-toolkit/bench/pull/580
[#577]: https://github.com/munich-quantum-toolkit/bench/pull/577
[#572]: https://github.com/munich-quantum-toolkit/bench/pull/572
[#571]: https://github.com/munich-quantum-toolkit/bench/pull/571
[#570]: https://github.com/munich-quantum-toolkit/bench/pull/570
[#567]: https://github.com/munich-quantum-toolkit/bench/pull/567
[#566]: https://github.com/munich-quantum-toolkit/bench/pull/566
[#560]: https://github.com/munich-quantum-toolkit/bench/pull/560
[#555]: https://github.com/munich-quantum-toolkit/bench/pull/555
[#548]: https://github.com/munich-quantum-toolkit/bench/pull/548
[#544]: https://github.com/munich-quantum-toolkit/bench/pull/544
[#541]: https://github.com/munich-quantum-toolkit/bench/pull/541
[#538]: https://github.com/munich-quantum-toolkit/bench/pull/538
[#531]: https://github.com/munich-quantum-toolkit/bench/pull/531
[#519]: https://github.com/munich-quantum-toolkit/bench/pull/519
[#518]: https://github.com/munich-quantum-toolkit/bench/pull/518
[#510]: https://github.com/munich-quantum-toolkit/bench/pull/510
[#508]: https://github.com/munich-quantum-toolkit/bench/pull/508
[#507]: https://github.com/munich-quantum-toolkit/bench/pull/507
[#506]: https://github.com/munich-quantum-toolkit/bench/pull/506
[#505]: https://github.com/munich-quantum-toolkit/bench/pull/505
[#504]: https://github.com/munich-quantum-toolkit/bench/pull/504

<!-- Contributor -->

[**@burgholzer**]: https://github.com/burgholzer
[**@ystade**]: https://github.com/ystade
[**@simon1hofmann**]: https://github.com/simon1hofmann
[**@nquetschlich**]: https://github.com/nquetschlich
[**@fkiwit**]: https://github.com/fkiwit
[**@CreativeBinBag**]: https://github.com/CreativeBinBag
[**@denialhaag**]: https://github.com/denialhaag
[**@soroushfathi**]: https://github.com/soroushfathi
[**@adnathanail**]: https://github.com/adnathanail
[**@TomasVF**]: https://github.com/TomasVF
[**@flowerthrower**]: https://github.com/flowerthrower
[**@johanneswittmann9**]: https://github.com/johanneswittmann9
[**@cnYui**]: https://github.com/cnYui
[**@algovista-collab**]: https://github.com/algovista-collab
[**@Anshu666666**]: https://github.com/Anshu666666
[**@AsharHusain**]: https://github.com/AsharHusain
[**@AthulKampiyil**]: https://github.com/AthulKampiyil
[**@jyothikacodes**]: https://github.com/jyothikacodes
[**@NiranjanRSoorej06**]: https://github.com/NiranjanRSoorej06

<!-- General links -->

[Keep a Changelog]: https://keepachangelog.com/en/1.1.0/
[Common Changelog]: https://common-changelog.org
[Semantic Versioning]: https://semver.org/spec/v2.0.0.html
[GitHub Release Notes]: https://github.com/munich-quantum-toolkit/bench/releases
