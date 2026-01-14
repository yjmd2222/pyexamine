
def map_category(source: str, description: str):
    text = f"{source} {description}".lower()
    if "grocery" in text:
        return "groceries"
    elif "rent" in text:
        return "housing"
    elif "uber" in text or "taxi" in text:
        return "transport"
    elif "gym" in text or "fitness" in text:
        return "health"
    elif "netflix" in text or "spotify" in text:
        return "subscriptions"
    elif "restaurant" in text or "cafe" in text:
        return "dining"
    else:
        return "other"


def map_priority(tag: str):
    if tag == "urgent":
        label = "p0"
        rank = 0
        note = "urgent"
        return f"{label}:{rank}:{note}"
    elif tag == "high":
        label = "p1"
        rank = 1
        note = "high"
        return f"{label}:{rank}:{note}"
    elif tag == "medium":
        label = "p2"
        rank = 2
        note = "medium"
        return f"{label}:{rank}:{note}"
    elif tag == "low":
        label = "p3"
        rank = 3
        note = "low"
        return f"{label}:{rank}:{note}"
    elif tag == "defer":
        label = "p4"
        rank = 4
        note = "defer"
        return f"{label}:{rank}:{note}"
    elif tag == "snooze":
        label = "p5"
        rank = 5
        note = "snooze"
        return f"{label}:{rank}:{note}"
    elif tag == "maybe":
        label = "p6"
        rank = 6
        note = "maybe"
        return f"{label}:{rank}:{note}"
    else:
        label = "p7"
        rank = 7
        note = "other"
        return f"{label}:{rank}:{note}"


def map_bucket(code: str):
    if code == "a0":
        return "alpha"
    elif code == "b1":
        return "bravo"
    elif code == "c2":
        return "charlie"
    elif code == "d3":
        return "delta"
    elif code == "e4":
        return "echo"
    elif code == "f5":
        return "foxtrot"
    elif code == "g6":
        return "golf"
    elif code == "h7":
        return "hotel"
    elif code == "i8":
        return "india"
    elif code == "j9":
        return "juliet"
    elif code == "k10":
        return "kilo"
    else:
        return "other"


def map_status(code: str):
    if code == "new":
        label = "n1"
        score = 1
        note = "new"
        return f"{label}:{score}:{note}"
    else:
        if code == "open":
            label = "o2"
            score = 2
            note = "open"
            return f"{label}:{score}:{note}"
        if code == "review":
            label = "r3"
            score = 3
            note = "review"
            return f"{label}:{score}:{note}"
        if code == "blocked":
            label = "b4"
            score = 4
            note = "blocked"
            return f"{label}:{score}:{note}"
        if code == "closed":
            label = "c5"
            score = 5
            note = "closed"
            return f"{label}:{score}:{note}"
        return "unknown"
