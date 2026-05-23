# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

import mqt.bench.benchmark_generation as benchmark_generation

if __name__ == "__main__":
    for alg in ["ghz", "bv", "graphstate"]: # add QFT
        for code in ["shor", "stean"]:
            for qubits in range(3, 5):
                qc = benchmark_generation.get_benchmark(benchmark=alg, level=benchmark_generation.BenchmarkLevel.ALG, circuit_size=qubits, encoding=code)
                print(qc)
