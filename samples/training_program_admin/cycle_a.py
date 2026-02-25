import cycle_b

def ping_a(x):
    if x <= 0: return "a"
    return "a" + cycle_b.ping_b(x-1)
