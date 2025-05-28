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
from mqt.bench import BenchmarkLevel, get_benchmark
from mqt.bench.targets import get_device, get_target_for_gateset
```

## Algorithmic Level

```{code-cell} ipython3
qc_algorithmic_level = get_benchmark(benchmark="dj", level=BenchmarkLevel.ALG, circuit_size=5)
qc_algorithmic_level.draw(output="mpl")
```

## Target-independent Level

```{code-cell} ipython3
qc_target_independent_level = get_benchmark(benchmark="dj", level=BenchmarkLevel.INDEP, circuit_size=5)
qc_target_independent_level.draw(output="mpl")
```

## Target-dependent Native Gates Level

```{code-cell} ipython3
qc_native_gates_level = get_benchmark(
    benchmark="dj",
    level=BenchmarkLevel.NATIVEGATES,
    circuit_size=5,
    target=get_target_for_gateset("ionq_forte", 5),
    opt_level=2,
)
qc_native_gates_level.draw(output="mpl")
```

## Target-dependent Mapped Level

```{code-cell} ipython3
qc_mapped_level = get_benchmark(
    benchmark="dj",
    level=BenchmarkLevel.MAPPED,
    circuit_size=5,
    target=get_device("ionq_forte_36"),
)
qc_mapped_level.draw(output="mpl")
```
