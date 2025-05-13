---
file_format: mystnb
kernelspec:
  name: python3
mystnb:
  number_source_lines: true
---

```{code-cell} ipython3
:tags: [remove-cell]
%config InlineBackend.figure_formats = ['svg']
```

# Quickstart

```{code-cell} ipython3
from mqt.bench import CompilerSettings, QiskitSettings, get_benchmark
```

## Algorithmic Level

```{code-cell} ipython3
qc_algorithmic_level = get_benchmark(benchmark_name="dj", level="alg", circuit_size=5)
qc_algorithmic_level.draw(output="mpl")
```

## Target-independent Level

```{code-cell} ipython3
qc_target_independent_level = get_benchmark(benchmark_name="dj", level="indep", circuit_size=5)
qc_target_independent_level.draw(output="mpl")
```

## Target-dependent Native Gates Level

```{code-cell} ipython3
compiler_settings = CompilerSettings(qiskit=QiskitSettings(optimization_level=2))
qc_native_gates_level = get_benchmark(
    benchmark_name="dj",
    level="nativegates",
    circuit_size=5,
    compiler_settings=compiler_settings,
    gateset="ionq",
)
qc_native_gates_level.draw(output="mpl")
```

## Target-dependent Mapped Level

```{code-cell} ipython3
qc_mapped_level = get_benchmark(
    benchmark_name="dj",
    level="mapped",
    circuit_size=5,
    device_name="ionq_harmony",
)
qc_mapped_level.draw(output="mpl")
```
