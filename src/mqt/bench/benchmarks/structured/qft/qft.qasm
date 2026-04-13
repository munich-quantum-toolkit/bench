OPENQASM 3.0;
include "qelib1.inc";

input int n;

qubit[n] q;

for int i in [0:n-1] {
    h q[i];
    for int j in [i+1:n-1] {
        cp(2*pi/2**(j-i+1)) q[j], q[i];
    }
}
for int i in [0:(n-1)/2] {
    swap q[i], q[n - 1 - i];
}
