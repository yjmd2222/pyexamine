"""
Completes the scatter/cycle by calling back into Alpha.
"""

from . import module_alpha


def gamma_helper(value):
    # Back edge to alpha creates a simple cycle: alpha -> beta -> gamma -> alpha
    return module_alpha.alpha_helper(value) + 3
