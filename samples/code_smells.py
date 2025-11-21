"""
Synthetic code-smell fixtures for documentation/tests.
Each block is intentionally naive to trip specific detectors.
"""

# Excessive Comments / Duplicate Code / Data Class / Lazy Class / Dead Code -----------------
# Excessive comments: long comment block with little code following.
# Duplicate code: foo_a and foo_b share the same body.
# Data class & Lazy class: PlainContainer only holds fields/getters; MinimalService barely does work.
# Dead code: unused_helper is never referenced.

# A noisy comment block (excessive comments)
# This function is intentionally wrapped in verbose comments.
# It has multiple lines of mostly comments to resemble a “commented dump”.
# Another filler comment line.
# Yet another comment line to increase the ratio.
# A final comment line to exaggerate the smell.
def foo_a(x, y):
    return (x * y) + (x - y)


# Duplicate code sibling
def foo_b(x, y):
    return (x * y) + (x - y)


class PlainContainer:
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def get_name(self):
        return self.name

    def get_value(self):
        return self.value


class MinimalService:
    def ping(self):
        return "ok"


def unused_helper(flag=False):
    temp = [1, 2, 3]
    if flag:
        temp.reverse()
    return temp


# Inappropriate Intimacy / Middle Man / Large Class (SIZE2) ---------------------------------
class BillingProfile:
    def __init__(self):
        self.card_number = "1234"
        self.expiry = "01/30"
        self.cvv = "999"

    def masked(self):
        return f"****-{self.card_number[-4:]}"


class BillingFacade:
    """Thin wrapper delegating to BillingProfile (middle man flavor)."""

    def __init__(self):
        self.profile = BillingProfile()

    def reveal_expiry(self):
        # Intimate access into internal fields (inappropriate intimacy)
        return self.profile.expiry

    def reveal_cvv(self):
        return self.profile.cvv

    def masked_card(self):
        return self.profile.masked()


class MonolithicHandler:
    """Large/SIZE2-ish: many small, disjoint methods collected here."""

    def step1(self): pass
    def step2(self): pass
    def step3(self): pass
    def step4(self): pass
    def step5(self): pass
    def step6(self): pass
    def step7(self): pass
    def step8(self): pass
    def step9(self): pass
    def step10(self): pass
    def step11(self): pass
    def step12(self): pass
    def step13(self): pass
    def step14(self): pass
    def step15(self): pass


# Feature Envy / Speculative Generality ------------------------------------------------------
class Cart:
    def __init__(self, items):
        self.items = items

    def total(self):
        return sum(self.items)


def print_cart(cart: Cart):
    # Feature envy: leans on cart internals instead of doing its own work.
    for i in cart.items:
        print(i)
    print(cart.total())


class AbstractFutureProof:
    """Speculative: abstract-ish hooks that do nothing yet."""

    def hook_a(self):  # empty template hooks
        pass

    def hook_b(self):
        pass


# Message Chains -----------------------------------------------------------------------------
class Node:
    def __init__(self, child=None):
        self.child = child

    def get_child(self):
        return self.child

    def value(self):
        return "leaf"


def chain_demo():
    root = Node(Node(Node(Node())))
    return root.get_child().get_child().get_child().value()
