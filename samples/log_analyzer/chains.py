class Node:
    def __init__(self, child=None):
        self.child = child
        self.value = "x"


def extract_path(node: Node):
    return node.child.child.child.value
