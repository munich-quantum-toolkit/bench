# Changelog

All notable changes to this project will be documented in this file.

The format is based on a mixture of [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [Common Changelog](https://common-changelog.org).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html), with the exception that minor releases may include breaking changes.

## [Unreleased]

_If you are upgrading: please see [`UPGRADING.md`](UPGRADING.md#unreleased)._

### Added

### Changed

### Removed

### Fixed

## [2.0.0] - 2025-06-xx

### Added

- ✨ Improved device and gateset intermediate representation to Qiskit's Target ([#560]) ([**@burgholzer**, **@nquetschlich**])
- ✨ Improved Output Logic and supported Formats (e.g., QASM3) ([#518]) ([**@simon1hofmann**, **@burgholzer**])
- ✨ Add arithmetic benchmarks ([#586]) ([**@simon1hofmann**, **@burgholzer**])
- ✨ Add mirror circuit option for all benchmarks ([#577]) ([**@CreativeBinBag**, **@burgholzer**, **@nquetschlich**])
- ✨ Add symbolic parameters for variation benchmarks ([#581]) ([**@nquetschlich**, **@burgholzer**])
- ✨ Add distinct `get_benchmark` function per level ([#571]) ([**@simon1hofmann**, **@burgholzer**])
- ✨ Add clifford+T gateset support ([#555]) ([**@simon1hofmann**, **@burgholzer**])
- ✨ Add HHL algorithm ([#582]) ([**@nquetschlich**, **@burgholzer**])
- ✨ Add Bernstein-Vazirani algorithm ([#505]) ([**@simon1hofmann**, **@burgholzer**])
- ✨ Add two benchmarks from BMW's QUARK framework ([#541]) ([**@fkiwit**])

### Changed

- ✨ Add transpile call at target-independent level ([#580]) ([**@simon1hofmann**, **@burgholzer**])
- ✨ Add registry for benchmarks, devices, and native gatesets ([#585, #572]) ([**@simon1hofmann**, **@burgholzer**])
- ✨ Add Hatchling and dependency groups ([#530]) ([**@nquetschlich**, **@burgholzer**])
- ✨ Re-add Python 3.9 support ([#531]) ([**@simon1hofmann**])
- ✨ Add test support for Python 3.13 ([#533]) ([**@simon1hofmann**])
- 🎨 Simplify imports ([#587]) ([**@simon1hofmann**])
- 🎨 Update IonQ and Rigetti devices ([#570]) ([**@nquetschlich**, **@burgholzer**])
- 🎨 Refactor Shor's benchmark ([#548]) ([**@simon1hofmann**])
- 🎨 Re-implement amplitude estimation without Qiskit Application modules ([#506]) ([**@simon1hofmann**, **@burgholzer**])
- 🎨 Rename random circuit and VQE ansatz circuit benchmarks ([#508]) ([**@simon1hofmann**])
- 🎨 Miscellaneous fixes ([#509]) ([**@simon1hofmann**])
- 📝 Update README and RtDs to new guidelines ([#573]) ([**@nquetschlich**])
- 📝 Add BMW QUARK copyright ([#583]) ([**@nquetschlich**])
- 📝 General documentation updates ([#566]) ([**@simon1hofmann**])
- 📝 Add CHANGELOG and UPGRADING info ([#567]) ([**@simon1hofmann**])
- 📝 Switch from `.rst` to `.md` ([#559]) ([**@simon1hofmann**])
- 📝 Rebrand and move to MQT GitHub org ([#544]) ([**@simon1hofmann**])
- 📝 Update links after repository migration ([#543]) ([**@Drewniok**])
- 📦 Introduce Hatchling and PEP 735 dependency groups ([#530]) ([**@nquetschlich**])
- 🔥 Disable server deployment for versions <2 ([#556]) ([**@nquetschlich**])

### Removed

- 🔥 Remove TKET dependency ([#519]) ([**@simon1hofmann**])
- 🔥 Remove TKET placement parameter ([#510]) ([**@simon1hofmann**])
- 🔥 Remove Qiskit Application-based benchmarks ([#507]) ([**@simon1hofmann**])
- 🔥 Remove `benchviewer` and `evaluation` modules ([#504]) ([**@burgholzer**])
- 🔥 Remove Generation Logic for Webpage ([#538]) ([**@nquetschlich**])

### Fixed

- 📝 Fix broken reference in README ([#584]) ([**@nquetschlich**])
- 📌 Restrict `qiskit-aer` dependency ([#481]) ([**@nquetschlich**])
- 👷 Adjust GitHub workflow URLs ([#500]) ([**@nquetschlich**])
- 🚨 Fix pending deprecation warnings ([#569]) ([**@simon1hofmann**])
- ⬇️ Add upper cap on dependencies due to fake backends ([#493]) ([**@nquetschlich**])
- ⚠️ Add additional filter warning ([#489]) ([**@nquetschlich**])

## [1.1.9] - 2024-12-01

_📚 Refer to the [GitHub Release Notes](https://github.com/munich-quantum-toolkit/bench/releases) for previous changelogs._

[unreleased]: https://github.com/munich-quantum-toolkit/core/compare/v1.1.9...HEAD
