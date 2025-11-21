"""
Scattered functionality continuation.
"""

from . import module_gamma


def beta_helper(value):
    return module_gamma.gamma_helper(value) + 2
