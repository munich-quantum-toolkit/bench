---
file_format: mystnb
kernelspec:
  name: python3
mystnb:
  number_source_lines: true
---

# Supported Benchmark Algorithms

Pass a benchmark name to {func}`~mqt.bench.get_benchmark`. Select a name below
for its factory options, size requirements, and circuit description.

```{code-cell} ipython3
---
tags: [hide-input]
mystnb:
  markdown_format: myst
---
from IPython.display import Markdown
from mqt.bench.benchmarks import get_benchmark_catalog

rows = ["| Name | Algorithm |", "| --- | --- |"]
for name, description in sorted(get_benchmark_catalog().items()):
    factory = f"mqt.bench.benchmarks.{name}.create_circuit"
    rows.append(f"| {{func}}`{name} <{factory}>` | {description or name} |")
Markdown("\n".join(rows))
```

## Arithmetic results

Adder and multiplier benchmarks measure only the arithmetic output into a
classical register named `result`. Bit `result[0]` is the least-significant bit.

| Benchmarks                                                              | Measured output                                                         |
| ----------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| `full_adder`, `half_adder`                                              | Sum, with carry-out as the most-significant bit                         |
| `modular_adder`                                                         | Sum modulo $2^n$, where $n$ is the input register width                 |
| `cdkm_ripple_carry_adder`, `vbe_ripple_carry_adder`, `draper_qft_adder` | Sum including carry-out for `full`/`half`; sum modulo $2^n$ for `fixed` |
| `multiplier`, `rg_qft_multiplier`, `hrs_cumulative_multiplier`          | Full $2n$-bit product                                                   |

The constructors leave the input qubits in their default zero state. To run a
specific addition or multiplication, prepare the operands before the arithmetic
operations. A mirror circuit measures all active qubits after the inverse,
including active input and helper qubits.
