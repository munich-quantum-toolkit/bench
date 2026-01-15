OPENQASM 3.0;
include "qelib1.inc";

input int n;

qubit[n-1] q;
qubit anc;

h q;
x anc;

// Iteratively apply gates
for int i in [0:n-2] {
    pow(2**i) @ cp(3*pi/8) q[i], anc;
}

// Apply reverse QFT
for int i in [0:(n-2)/2] {
    swap q[i], q[n - 2 - i];
}
for int i in [0:n-2] {
    h q[i];
    for int j in [i+1:n-2] {
        cp(2*pi/2**(j-i+1)) q[j], q[i];
    }
}
