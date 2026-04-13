OPENQASM 3.0;
include "qelib1.inc";

input int n;

qubit q;
bit[n] res;

for int i in [0:n-1] {
    for int j in [0:i-1] {
        if (res[n - 1 - j]) {
            p(2*pi/2**(i-j+1)) q;
        }
    }
    h q;
    res[n - 1 - i] = measure q;
}
