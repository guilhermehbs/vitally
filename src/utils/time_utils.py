import datetime as dt


def times_between(start: dt.time, end: dt.time, step_min: int = 30) -> list[str]:
    cur = dt.datetime.combine(dt.date.today(), start)
    end_dt = dt.datetime.combine(dt.date.today(), end)
    out: list[str] = []
    while cur <= end_dt:
        out.append(cur.strftime("%H:%M"))
        cur += dt.timedelta(minutes=step_min)
    return out
