# Target models

Bench targets describe supported gates and connectivity for compilation. They
are static models, not a device-discovery or provider-submission API. All gate
parameters use radians. Calibration values are illustrative averages unless
stated otherwise; IBM models use seeded synthetic calibration.

The current hardware catalogue contains:

| Device                | Gates                       | Model                                                           |
| --------------------- | --------------------------- | --------------------------------------------------------------- |
| `aqt_ibex_12`         | `r`, `rz`, `rxx`            | IBEX Q1, all-to-all connectivity; Braket snapshot of 2026-10-02 |
| `ibm_heron_156`       | `id`, `x`, `sx`, `rz`, `cz` | 156-qubit Heron architecture                                    |
| `ionq_forte_36`       | `gpi`, `gpi2`, `rz`, `rzz`  | Forte architecture with virtual Z rotations                     |
| `iqm_crystal_5`       | `r`, `cz`                   | Ideal 5-qubit Crystal architecture, also used by IQM Spark      |
| `iqm_crystal_20`      | `r`, `cz`                   | Ideal Garnet architecture                                       |
| `iqm_crystal_54`      | `r`, `cz`                   | Ideal Emerald architecture, including all designed couplers     |
| `quantinuum_h2_56`    | `rx`, `ry`, `rz`, `rzz`     | H2 architecture                                                 |
| `rigetti_cepheus_107` | fixed `rx`, `rz`, `cz`      | Cepheus's 107 active qubits; Braket snapshot of 2026-10-02      |

All device models include measurement. A target's control-flow instructions
express Bench's compiler model; they do not promise provider submission support.
The ideal IQM models retain couplers that may be disabled in a live calibration.
For a particular execution, supply an up-to-date Qiskit `Target` from the
provider.

## Native gate conventions

IonQ GPI and GPI2 take one phase in radians. GPI is `i * R(pi, phase)`; GPI2 is
`R(pi / 2, phase)`. Forte supports arbitrary `rz` as a virtual frame change with
zero duration and error in the model. A serializer for pulse-only verbatim
execution must absorb these rotations into pulse phases. Bench does not perform
that serialization. The entangler is Qiskit's standard `rzz`; provider adapters
handle IonQ's `zz` spelling and turn-based parameters.

Rigetti exposes four standard `RXGate` capabilities under the names `rxpi`,
`rxpidg`, `rxpi2`, and `rxpi2dg`, with fixed angles pi, -pi, pi/2, and -pi/2.
These names let Qiskit distinguish the supported angles. RZ remains arbitrary.
The U equivalence preserves its global phase and uses the named quarter-turn
pulses; Core imports the same target's standard RX capabilities directly.

AQT's `prx` and `xx` operations correspond to Qiskit's `r` and `rxx`. No
three-parameter IonQ MS operation is required. IQM's `prx` also corresponds to
`r`. These compiler names are independent of provider serialization names.

## Physical qubit labels

`rigetti_cepheus_107` numbers its active wires from 0 to 106. The provider's
Cepheus-1-108Q snapshot has physical labels 0 through 107, excluding unavailable
qubit 8. The tuple `mqt.bench.targets.devices.rigetti.CEPHEUS_PHYSICAL_QUBITS`
maps each Bench wire to its provider label. Its 386 directed CZ connections form
the remaining 12-by-9 grid. Calibration errors and durations are left
unspecified.

Other architecture models also use zero-based wires. In particular, an IQM
provider serializer must translate these to the provider's qubit labels.

## Sources

The Braket snapshot uses the
[device capability API](https://docs.aws.amazon.com/braket/latest/APIReference/API_GetDevice.html).
[IonQ's native-gate guide](https://docs.ionq.com/features/getting-started-with-native-gates)
describes phase tracking and the GPI/GPI2/ZZ basis. The current catalogue also
follows
[IBM QPU information](https://quantum.cloud.ibm.com/docs/en/guides/qpu-information),
[IQM Spark](https://iqm.tech/products/iqm-spark/), and the
[Quantinuum system reference](https://docs.quantinuum.com/systems/support/system_reference.html).
