OPENQASM 3.0;
include "qelib1.inc";

qubit psi;
qubit q1;
qubit q2;

// Alice has a qubit in an unknown state.
h psi;

// Alice and Bob share an entangled Bell pair.
h q1;
cx q1, q2;

// Alice prepares the teleport operation.
cx psi, q1;
h psi;

// Alice then measures her qubits.
bit a = measure psi;
bit b1 = measure q1;

// Bob applies corrections based on the measurement result.
if (b1) {
  x q2;
}
if (a) {
  z q2;
}

// Now q2 is in the previous state of a.
