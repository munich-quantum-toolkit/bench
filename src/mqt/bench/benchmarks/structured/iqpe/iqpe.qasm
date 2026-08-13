OPENQASM 3.0;
include "qelib1.inc";

input int precision;

qubit q;
qubit anc;
bit[precision] res;

x anc;

for int i in [precision - 1:0:-1] {
    h q;
    pow(2**i) @ cp(3*pi/8) q, anc;
    for int j in [i + 1:precision - 1] {
        if (res[j]) {
            p(2*pi/2**(j-i+1)) q;
        }
    }
    h q;
    res[i] = measure q;
    reset q;
}
