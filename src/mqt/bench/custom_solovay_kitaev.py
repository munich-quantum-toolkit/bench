# Copyright (c) 2023 - 2026 Chair for Design Automation, TUM
# Copyright (c) 2025 - 2026 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

# This code is part of Qiskit.
#
# (C) Copyright IBM 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Modified Solovay-Kitaev transpiler.

Remove once Qiskit minimum version is increased to 2.0.0
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from qiskit.circuit.gate import Gate
from qiskit.transpiler.passes import SolovayKitaev
from qiskit.transpiler.passes.utils.control_flow import trivial_recurse

if TYPE_CHECKING:
    from qiskit.dagcircuit import DAGCircuit


class CustomSolovayKitaev(SolovayKitaev):  # type: ignore[misc]
    """Modified version of Solovay-Kitaev transpiler pass.

    Backporting this PR https://github.com/Qiskit/qiskit/pull/13690/changes from Qiskit 2.0.0
    Ignores operations on which the algorithm cannot run - e.g. control-flow operations.
    """

    @trivial_recurse  # type: ignore[untyped-decorator]
    def run(self, dag: DAGCircuit) -> DAGCircuit:
        """Run the ``SolovayKitaev`` pass on `dag`.

        Args:
            dag: The input dag.

        Returns:
            Output dag with 1q gates synthesized in the discrete target basis.

        Copied from https://github.com/alexanderivrii/qiskit-terra/blob/5d819130c4e47f4a81be1522365e92a66c55958b/qiskit/transpiler/passes/synthesis/solovay_kitaev_synthesis.py
        """
        for node in dag.op_nodes():
            # ignore operations on which the algorithm cannot run
            if (node.op.num_qubits != 1) or node.is_parameterized() or (not hasattr(node.op, "to_matrix")):
                continue

            # we do not check the input matrix as we know it comes from a Qiskit gate, so
            # we know it will generate a valid SU(2) matrix
            check_input = not isinstance(node.op, Gate)

            matrix = node.op.to_matrix()

            # call solovay kitaev
            # *accessing private attribute is necessary for this backport*
            approximation = self._sk.run(matrix, self.recursion_degree, return_dag=True, check_input=check_input)

            # convert to a dag and replace the gate by the approximation
            dag.substitute_node_with_dag(node, approximation)

        return dag
