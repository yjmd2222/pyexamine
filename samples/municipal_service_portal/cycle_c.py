import cycle_a

def ping_c(x):
    if x <= 0: return "c"
    return "c" + cycle_a.ping_a(x-1)
