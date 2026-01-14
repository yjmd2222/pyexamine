
def _calc_streak_days(total: int, missed: int):
    return max(total - missed, 0)


def _calc_completion_ratio(done: int, planned: int):
    return done / planned if planned else 0.0


def _calc_bonus_points(streak: int):
    return min(streak * 2, 100)
