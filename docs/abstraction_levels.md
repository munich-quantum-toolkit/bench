# Abstraction Levels

MQT Bench provides four views of a circuit, based on the abstraction levels in
the OpenQASM 3 specification {cite:labelpar}`Cross_2022`. The figures follow a
three-qubit variational ansatz from its algorithmic form to a circuit mapped
onto a five-qubit line. For runnable examples at each level, see the
{doc}`quickstart`.

## 1. Algorithmic Level

`BenchmarkLevel.ALG` returns the circuit produced by the benchmark factory. It
can contain gates such as the six parameterized $R_y$ rotations in this ansatz.
Set `random_parameters=False` to keep the angles symbolic.

```{image} /_static/level_1.png
:align: center
:alt: Three qubits with parameterized Y rotations and CX gates
:width: 50%
```

## 2. Target-independent Level

`BenchmarkLevel.INDEP` uses Qiskit to optimize the circuit without choosing a
device. The figure shows the same ansatz with all six angles set to $\pi$.
Parameter binding is a separate choice at every level.

```{image} /_static/level_2.png
:align: center
:alt: The ansatz with each Y rotation set to pi
:width: 50%
```

## 3. Target-dependent Native Gates Level

`BenchmarkLevel.NATIVEGATES` compiles the circuit to the target's instructions.
At this level, a two-qubit gate can act on any pair. In the example gate set,
$X$, $R_z$, and CX are native. Each $R_y(\pi)$ can be expressed using
$R_z(-\pi)$ followed by $X$, up to a global phase.

```{image} /_static/level_3.png
:align: center
:alt: The Y rotations decomposed into native Z rotations and X gates
:width: 50%
```

## 4. Target-dependent Mapped Level

`BenchmarkLevel.MAPPED` places the logical qubits on a device and routes
two-qubit gates along its connections. The illustrative device has five qubits
in a line. No placement makes every pair of logical qubits neighbors.

```{image} /_static/arch.png
:align: center
:alt: Five physical qubits connected in a line from Q0 to Q4
:width: 15%
```

The mapped circuit uses physical qubits $Q_0$, $Q_1$, and $Q_2$. Each CX acts on
neighboring qubits. See the {doc}`parameter guide <parameter>` for the device
models available in MQT Bench.

```{image} /_static/level_4.png
:align: center
:alt: Circuit routed so every CX acts on adjacent physical qubits
:width: 50%
```
