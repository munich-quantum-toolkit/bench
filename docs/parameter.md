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

- `benchmark` (see {doc}`details <benchmark_selection>`) : `"ae"`, `"bv"`, `"dj"`, `"grover-noancilla"`, `"grover-v-chain"`, `"ghz"`, `"graphstate"`,
  `"qaoa"`, `"qft"`, `"qftentangled"`, `"qnn"`, `"qpeexact"`, `"qpeinexact"`,
  `"qwalk-noancilla"`, `"qwalk-v-chain"`, `"randomcircuit"`, `"vqerealamprandom"`, `"vqesu2random"`, `"vqetwolocalrandom"`,
  `"wstate"`, `"shor"`
- `level`: BenchmarkLevel.ALG, BenchmarkLevel.INDEP, BenchmarkLevel.NATIVEGATES, BenchmarkLevel.MAPPED
- `circuit_size`: for most of the cases this is equal to number of qubits
  (all scalable benchmarks except `"qwalk-v-chain"` and `"grover-v-chain"`) while for all other the qubit number is higher

- `target`: Target, which can also be instantiated based on gatesets using `get_target_for_gateset(gateset_name)` or based on a device using `get_device(device_name)`.
  Possible values for `gateset_name`:

```{code-cell} ipython3
:tags: [hide-input]
from mqt.bench.targets import get_available_native_gatesets

print(", ".join([gateset for gateset in get_available_native_gatesets()]))
```

(required for "nativegates" level)

Possible values for `device_name`:

```{code-cell} ipython3
:tags: [hide-input]
from mqt.bench.targets import get_available_devices

print(", ".join([device for device in get_available_devices()]))
```

(required for "mapped" level)

- `opt_level`: Optimization level for `"qiskit"` (`0`-`3`)

## Native Gate-Set Support

So far, MQT Bench supports the following native gatesets:

```{code-cell} ipython3
:tags: [hide-input]
from mqt.bench.targets import get_available_native_gatesets

for num, (gateset_name, gateset) in enumerate(get_available_native_gatesets().items()):
    print(f"{num+1}: {gateset_name} → {gateset}")
```

## Device Support

So far, MQT Bench supports the following devices:

```{code-cell} ipython3
:tags: [hide-input]
from mqt.bench.targets import get_available_devices

for num, (device_name, device) in enumerate(get_available_devices().items()):
    print(f"{num+1}: {device_name} with {device.num_qubits} qubits")
```

Examples how to use the {func}`~.mqt.bench.get_benchmark` method for all four abstraction levels can be found on the {doc}`Quickstart jupyter notebook <quickstart>`.
