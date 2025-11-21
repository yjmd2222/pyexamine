"""
Part of a scattered functionality + cyclic dependency fixture.
Alpha calls Beta; Beta calls Gamma; Gamma calls Alpha.
"""

from . import module_beta


def alpha_helper(value):
    return module_beta.beta_helper(value) + 1
