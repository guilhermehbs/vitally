from datetime import date

DATE_FMT_DISPLAY = "%d/%m/%Y"


def format_date_br(d: date | None) -> str:
    return d.strftime(DATE_FMT_DISPLAY) if d else ""
