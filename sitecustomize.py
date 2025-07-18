# Copyright (c) 2023 - 2025 Chair for Design Automation, TUM
# Copyright (c) 2025 Munich Quantum Software Company GmbH
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Site customization shim to enable multiprocess coverage collection in tests.

See: https://coverage.readthedocs.io/en/latest/subprocess.html.
"""

from __future__ import annotations

try:
    import coverage

    coverage.process_startup()
except ImportError:
    # The 'coverage' module is optional. If it is not installed,
    # we skip enabling multiprocess coverage collection.
    pass
