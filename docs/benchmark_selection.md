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

The current release includes the following benchmark algorithms, with each
abbreviated `benchmark_name` mapped to its full description in the table below:

The `grover_for_loop` and `qwalk_for_loop` variants represent repeated algorithm
steps with Qiskit's structured `ForLoopOp`. Algorithm-level OpenQASM 3 output
keeps the loop intact. MQT Bench expands the loop when compiling for a target
that does not support this control-flow operation or when exporting OpenQASM 2.

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

See the
[benchmark description](https://www.cda.cit.tum.de/mqtbench/benchmark_description)
for further details on the individual benchmarks.
