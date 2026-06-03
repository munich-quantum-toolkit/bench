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

# Supported Benchmark Algorithms

The current release includes the following benchmark algorithms, with each abbreviated `benchmark_name` mapped to its full description in the table below:

```{code-cell} ipython3
:tags: [hide-input]
from mqt.bench.benchmarks import get_benchmark_catalog
import pandas as pd
from IPython.display import HTML

df = pd.DataFrame(
    [
        {"Actual Benchmark": desc or name, "benchmark_name": name}
        for name, desc in sorted(get_benchmark_catalog().items())
    ]
)

def dark_even_rows(s):
    return ['background-color:#262626;color:#f8f8f8' if s.name % 2 else '' for _ in s]

html = (
    df.style
      .apply(dark_even_rows, axis=1)                         # zebra rows
      .set_table_styles([
          # index cells in zebra rows
          {'selector': 'tr:nth-child(even) th',
           'props': [('background-color','#262626'),
                     ('color','#f8f8f8')]},

          # entire header row
          {'selector': 'thead th',
           'props': [('background-color','#3b3b3b'),
                     ('color','#f8f8f8')]}
      ], overwrite=False)
      .to_html()
)

HTML(html)
```

See the [benchmark description](https://www.cda.cit.tum.de/mqtbench/benchmark_description) for further details on the individual benchmarks.

## Dynamic Iterative Phase Estimation

The `iqpe` benchmark implements Iterative Quantum Phase Estimation as a dynamic circuit.
Unlike the standard QPE benchmarks, it reuses one measurement ancilla and one target eigenstate qubit instead of allocating a full quantum phase register.
Use `circuit_size=2`; the optional `num_bits` argument controls the number of mid-circuit measurement and classically controlled feedback iterations.
The benchmark reinitializes the reusable ancilla with measurement-conditioned feedback so it remains compatible with targets that do not expose a native reset operation.
