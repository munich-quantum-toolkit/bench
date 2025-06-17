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

## [2.0.0] - 2025-06-20

### Added

- ✨ Improved device and gateset intermediate representation to Qiskit's Target ([#560]) ([**@burgholzer**, **@nquetschlich**])
- ✨ Add support for exporting to OpenQASM 3 ([#518]) ([**@simon1hofmann**, **@burgholzer**, **@nquetschlich**])
- ✨ Add support for exporting to Qiskit's QPY ([#518]) ([**@simon1hofmann**, **@burgholzer**, **@nquetschlich**])
- ✨ Add arithmetic benchmarks ([#586]) ([**@simon1hofmann**, **@burgholzer**])
- ✨ Add mirror circuit option for all benchmarks ([#577]) ([**@CreativeBinBag**, **@burgholzer**, **@nquetschlich**])
- ✨ Add symbolic parameters for variational benchmarks ([#581]) ([**@nquetschlich**, **@burgholzer**])
- ✨ Add distinct `get_benchmark` function per level ([#571]) ([**@simon1hofmann**, **@burgholzer**])
- ✨ Add support for compiling to the Clifford+T gateset ([#555]) ([**@simon1hofmann**, **@burgholzer**, **@nquetschlich**])
- ✨ Add HHL algorithm ([#582]) ([**@nquetschlich**, **@burgholzer**])
- ✨ Add Bernstein-Vazirani algorithm ([#505]) ([**@simon1hofmann**, **@burgholzer**, **@nquetschlich**])
- ✨ Add two benchmarks from BMW's QUARK framework ([#541]) ([**@fkiwit**])

### Changed

- ✨ Call `transpile` for optimization at the target-independent level ([#580]) ([**@simon1hofmann**, **@burgholzer**])
- ✨ Add registry for benchmarks, devices, and native gatesets ([#585, #572]) ([**@simon1hofmann**, **@burgholzer**])
- ✨ Re-add Python 3.9 support ([#531]) ([**@simon1hofmann**])
- 🎨 Update IonQ and Rigetti devices ([#570]) ([**@nquetschlich**, **@burgholzer**])
- 🎨 Refactor Shor's benchmark ([#548]) ([**@simon1hofmann**])
- 🎨 Re-implement amplitude estimation without Qiskit Application modules ([#506]) ([**@simon1hofmann**, **@burgholzer**, **@nquetschlich**])
- 🎨 Rename random circuit and VQE ansatz circuit benchmarks ([#508]) ([**@simon1hofmann**, **@nquetschlich**])
- 📝 Update and modernize project documentation ([#566]) ([**@simon1hofmann**])
- 📝 Add CHANGELOG and UPGRADING info ([#567]) ([**@simon1hofmann**])
- 🚚 Rebrand and move to MQT GitHub organization ([#544]) ([**@simon1hofmann**])

### Removed

- 🔥 Remove TKET-related functionality ([#519], [#510]) ([**@simon1hofmann**])
- 🔥 Remove Qiskit Application-based benchmarks ([#507]) ([**@simon1hofmann**, **@nquetschlich**])
- 🔥 Remove `benchviewer` and `evaluation` modules ([#504]) ([**@burgholzer**, **@nquetschlich**])
- 🔥 Remove Generation Logic for Webpage ([#538]) ([**@nquetschlich**])


## [1.1.9] - 2024-12-01

_📚 Refer to the [GitHub Release Notes](https://github.com/munich-quantum-toolkit/bench/releases) for previous changelogs._

[unreleased]: https://github.com/munich-quantum-toolkit/core/compare/v1.1.9...HEAD
