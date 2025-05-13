# Abstraction Levels

MQT Bench uses the structure proposed by the OpenQASM 3.0 specification {cite:labelpar}`Cross_2022` and offers benchmarks
on four different abstraction levels:

1. Algorithmic Level
2. Target-independent Level
3. Target-dependent Native Gates Level
4. Target-dependent Mapped Level

An example is given in the following:

## 1. Algorithmic Level

```{image} /_static/level_1.png
:align: center
:alt: Illustration of the algorithmic level
:width: 50%
```

Variational Quantum Algorithms (VQAs) are an emerging class of quantum algorithms with a wide range of
applications. A respective circuit is shown above, it represents an example of an ansatz function
frequently used for Variational Quantum Eigensolvers (VQEs), a subclass of VQAs. On this abstraction
level, the circuit is parameterized by the angles $\theta_i$ of the six single-qubit gates.

## 2. Target-independent Level

```{image} /_static/level_2.png
:align: center
:alt: Illustration of the target-independent level
:width: 50%
```

VQAs are hybrid quantum-classical algorithms, where the parameters of the quantum ansatz are
iteratively updated by a classical optimizer analogous to conventional gradient-based optimization.
Consider again the circuit from the previous figure. Assuming these parameters have been determined,
e.g., $\theta_i$ = −π for i = 0, ..., 5, they are now propagated and the resulting quantum circuit is
shown above.

## 3. Target-dependent Native Gates Level

```{image} /_static/level_3.png
:align: center
:alt: Illustration of the target-dependent native gates level
:width: 50%
```

Different quantum computer realizations support
different native gate-sets. In our example, we consider the
`ibmq_manila` device as the target device which natively supports I, X, √X, Rz and CX gates.
Consequently, the Ry gates in the previous figure have to be converted using only these native gates. In this case,
they are substituted by a sequence of X and Rz gates (denoted as • with a phase of −π).

## 4. Target-dependent Mapped Level

```{image} /_static/arch.png
:align: center
:alt: Illustration of the ``ibmq_manila`` device
:width: 15%
```

The architecture of the `ibmq_manila` device is shown above on the right and it defines between which qubits a two-qubit operation may be performed.
Since the circuit shown in the previous figure contains CX gates operating between all combination of qubits,
there is no mapping directly matching the target architecture's layout. As a consequence,
a non-trivial mapping followed by a round of optimization leads to the resulting circuit
shown below.

```{image} /_static/level_4.png
:align: center
:alt: Illustration of the target-dependent mapped level
:width: 50%
```

This is also the reason for the different sequence of CX gates compared
to the previous example.

This circuit is now executable on the `ibmq_manila` device, since all hardware induced requirements are fulfilled.
