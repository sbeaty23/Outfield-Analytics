from datetime import date, timedelta


def schedule_range(
    season: int, start: date | None, end: date | None, *, today: date | None = None
) -> tuple[date, date]:
    today = today or date.today()
    if start is None and today.year != season:
        raise ValueError("Explicit dates are required outside the configured season")
    start = start or today
    end = end or min(start + timedelta(days=7), date(season, 12, 31))
    if start.year != season or end.year != season:
        raise ValueError("Schedule dates must be in the configured season")
    if end < start or (end - start).days >= 31:
        raise ValueError("Schedule range must be 31 inclusive days or fewer")
    return start, end
