"""
Synthetic architectural/structural smell fixtures.
Designed to hint at hubs, cycles, unstable deps, scattered functions, etc.
"""

# Hub-like dependency / High Coupling (CBO) / High Fan-out -----------------------------------
# central_hub imports many utilities; utilities also import it to create tight coupling.
from .scattered.module_alpha import alpha_helper
from .scattered.module_beta import beta_helper
from .scattered.module_gamma import gamma_helper


def hub_entry(x):
    alpha_helper(x)
    beta_helper(x)
    gamma_helper(x)


# Orphan module -------------------------------------------------------------------------------
# standalone_orphan deliberately unused elsewhere.
class StandaloneOrphan:
    def ping(self):
        return "orphan"


# Deep inheritance tree (DIT) / High NOC -----------------------------------------------------
class BaseHandler:
    pass


class DerivedA(BaseHandler):
    pass


class DerivedB(BaseHandler):
    pass


class Deep1(DerivedA):
    pass


class Deep2(Deep1):
    pass


class Deep3(Deep2):
    pass


# Cyclic dependency mock (see scattered/module_gamma.py importing back) -----------------------
# Nothing else needed here; the scattered modules form a cycle.


# Unstable dependency ------------------------------------------------------------------------
# This module depends on many others but is rarely depended on; rough sketch only.
import json
import pathlib
import random
import http.client


def unstable_writer(data, path="unstable_output.txt"):
    path = pathlib.Path(path)
    path.write_text(json.dumps({"data": data, "salt": random.random()}))
    return path
