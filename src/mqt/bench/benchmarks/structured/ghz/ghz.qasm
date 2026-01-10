OPENQASM 3.0;
include "qelib1.inc";

input int n;

qubit[n] q;

h q[0];
for int i in [1:n-1] {
  cx q[i - 1], q[i];
}
