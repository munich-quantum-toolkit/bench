OPENQASM 3.0;

// Quantum Multiplexer (Uniformly Controlled RY Gates)
// Applies 2^n different RY rotations based on n control qubits

input int n;
int num_controls = n - 1;
input angle[2**num_controls] angles;


qubit[num_controls] controls;
qubit target;
bit[num_controls + 1] c;

int num_states = 2**num_controls;

for int state in [0:num_states-1] {
    // We want to apply angles[state] when controls equal 'state'
    // State is a binary number: e.g., state=5 = 0b101 for 3 controls
    // means control[0]=1, control[1]=0, control[2]=1

    // Extract each bit: if 0, we need to flip the corresponding qubit
    // Bit i is: (state >> i) & 1
    for int bit_pos in [0:num_controls-1] {
        int bit_value = (state >> bit_pos) & 1;
        if (bit_value == 0) {
            x controls[bit_pos];  // Flip this control
        }
    }

    // Apply fully-controlled gate (all controls must be |1⟩)
    ctrl(num_controls) @ ry(angles[state]) controls[0:num_controls-1], target;

    // Flip controls back
    for int bit_pos in [0:num_controls-1] {
        int bit_value = (state >> bit_pos) & 1;
        if (bit_value == 0) {
            x controls[bit_pos];  // Flip back
        }
    }
}
