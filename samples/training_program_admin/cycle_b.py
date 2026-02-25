import cycle_c

def ping_b(x):
    if x <= 0: return "b"
    return "b" + cycle_c.ping_c(x-1)
