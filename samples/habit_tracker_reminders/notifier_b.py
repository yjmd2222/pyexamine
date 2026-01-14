
def format_message(user: str, habit: str):
    return f"Hello {user}, keep up with {habit}."


def send_daily(user: str, habit: str):
    return format_message(user, habit)


def send_weekly(user: str, habit: str):
    return format_message(user, habit)


def schedule_next(day: str):
    return f"next:{day}"
