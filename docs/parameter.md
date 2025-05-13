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

# Parameter Space

The {func}`~mqt.bench.get_benchmark` function has the following signature:

- `benchmark_name` (see {doc}`details <benchmark_selection>`) : `"ae"`, `"bv"`, `"dj"`, `"grover-noancilla"`, `"grover-v-chain"`, `"ghz"`, `"graphstate"`,
  `"qaoa"`, `"qft"`, `"qftentangled"`, `"qnn"`, `"qpeexact"`, `"qpeinexact"`,
  `"qwalk-noancilla"`, `"qwalk-v-chain"`, `"randomcircuit"`, `"vqerealamprandom"`, `"vqesu2random"`, `"vqetwolocalrandom"`,
  `"wstate"`, `"shor"`
- `level`: `0` or `"alg"`, `1` or `"indep"`, `2` or `"nativegates"`, `3` or `"mapped"`
- `circuit_size`: for most of the cases this is equal to number of qubits
  (all scalable benchmarks except `"qwalk-v-chain"` and `"grover-v-chain"`) while for all other the qubit number is higher
- `compiler_settings`: Optimization level for `"qiskit"` (`0`-`3`)

- `gateset`:

```{code-cell} ipython3
:tags: [hide-input]
from mqt.bench.devices import get_available_native_gatesets

print(", ".join([gateset.name for gateset in get_available_native_gatesets()]))
```

(required for "nativegates" level)

- `device_name`:

```{code-cell} ipython3
:tags: [hide-input]
from mqt.bench.devices import get_available_devices

print(", ".join([device.name for device in get_available_devices()]))
```

(required for "mapped" level)

## Native Gate-Set Support

So far, MQT Bench supports the following native gatesets:

```{code-cell} ipython3
:tags: [hide-input]
from mqt.bench.devices import get_available_native_gatesets

for num, gateset in enumerate(get_available_native_gatesets()):
    print(f"{num+1}: {gateset.name} → {gateset.gates}")
```

## Device Support

So far, MQT Bench supports the following devices:

```{code-cell} ipython3
:tags: [hide-input]
from mqt.bench.devices import get_available_devices

for num, device in enumerate(get_available_devices()):
    print(f"{num+1}: {device.name} with {device.num_qubits} qubits")
```

Examples how to use the {func}`~.mqt.bench.get_benchmark` method for all four abstraction levels can be found on the {doc}`Quickstart jupyter notebook <quickstart>`.
