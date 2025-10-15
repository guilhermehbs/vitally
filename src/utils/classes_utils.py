import uuid
from datetime import date, datetime, time, timedelta

import pandas as pd

DIA_FIELDS = [
    ("Segunda", "aula_seg", "MO"),
    ("Terça", "aula_ter", "TU"),
    ("Quarta", "aula_qua", "WE"),
    ("Quinta", "aula_qui", "TH"),
    ("Sexta", "aula_sex", "FR"),
    ("Sábado", "aula_sab", "SA"),
    ("Domingo", "aula_dom", "SU"),
]


def build_classes_csv(paciente) -> bytes:
    rows = []
    for nome_dia, field, _ in DIA_FIELDS:
        rows.append(
            {
                "PacienteId": paciente.id,
                "Paciente": paciente.nome,
                "Dia": nome_dia,
                "Tem Aula": "Sim" if getattr(paciente, field, False) else "Não",
            }
        )
    df = pd.DataFrame(rows)
    return df.to_csv(index=False).encode("utf-8")


def build_times_csv(fisioterapeuta) -> bytes:
    rows = []
    for nome_dia, field, _ in DIA_FIELDS:
        rows.append(
            {
                "FisioterapeutaID": fisioterapeuta.id,
                "Fisioterapeuta": fisioterapeuta.nome,
                "Dia": nome_dia,
                "Tem Aula": "Sim" if getattr(fisioterapeuta, field, False) else "Não",
            }
        )
    df = pd.DataFrame(rows)
    return df.to_csv(index=False).encode("utf-8")


def next_weekday_on_or_after(start: date, target_weekday: int) -> date:
    delta = (target_weekday - start.weekday()) % 7
    return start + timedelta(days=delta)


def build_classes_ics(
    paciente,
    start_on: date | None = None,
    start_time_str: str = "08:00",
    duration_minutes: int = 60,
    tzid: str = "America/Sao_Paulo",
) -> bytes:
    if start_on is None:
        start_on = date.today()

    marked = [
        (label, field, ical)
        for (label, field, ical) in DIA_FIELDS
        if getattr(paciente, field, False)
    ]

    if not marked:
        return (
            "BEGIN:VCALENDAR\r\n"
            "VERSION:2.0\r\n"
            "PRODID:-//Vitally//Pilates Plan//PT-BR\r\n"
            f"BEGIN:VTIMEZONE\r\nTZID:{tzid}\r\nEND:VTIMEZONE\r\n"
            "END:VCALENDAR\r\n"
        ).encode()

    wday_order: dict[str, int] = {"MO": 0, "TU": 1, "WE": 2, "TH": 3, "FR": 4, "SA": 5, "SU": 6}
    first_ical: str = sorted([i for _, _, i in marked], key=lambda x: wday_order[x])[0]
    first_weekday = wday_order[first_ical]
    start_date_first = next_weekday_on_or_after(start_on, first_weekday)

    hh, mm = map(int, start_time_str.split(":"))
    dtstart = datetime.combine(start_date_first, time(hour=hh, minute=mm))
    dtend = dtstart + timedelta(minutes=duration_minutes)

    byday: str = ",".join(i for *_, i in marked)
    uid: str = f"{paciente.id}-{uuid.uuid4()}@vitally"

    def fmt(dt: datetime) -> str:
        return dt.strftime("%Y%m%dT%H%M%S")

    lines: list[str] = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Vitally//Pilates Plan//PT-BR",
        "BEGIN:VTIMEZONE",
        f"TZID:{tzid}",
        "END:VTIMEZONE",
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"SUMMARY:Aulas de Pilates - {paciente.nome}",
        f"DTSTART;TZID={tzid}:{fmt(dtstart)}",
        f"DTEND;TZID={tzid}:{fmt(dtend)}",
        f"RRULE:FREQ=WEEKLY;BYDAY={byday}",
        "DESCRIPTION:Plano de aulas gerado pelo Vitally",
        "END:VEVENT",
        "END:VCALENDAR",
        "",
    ]
    return ("\r\n".join(lines)).encode("utf-8")


def build_times_ics(
    fisio,
    start_on: date | None = None,
    start_time_str: str = "08:00",
    duration_minutes: int = 60,
    tzid: str = "America/Sao_Paulo",
) -> bytes:
    if start_on is None:
        start_on = date.today()

    marked = [
        (label, field, ical) for (label, field, ical) in DIA_FIELDS if getattr(fisio, field, False)
    ]

    if not marked:
        return (
            "BEGIN:VCALENDAR\r\n"
            "VERSION:2.0\r\n"
            "PRODID:-//Vitally//Pilates Plan//PT-BR\r\n"
            f"BEGIN:VTIMEZONE\r\nTZID:{tzid}\r\nEND:VTIMEZONE\r\n"
            "END:VCALENDAR\r\n"
        ).encode()

    wday_order: dict[str, int] = {"MO": 0, "TU": 1, "WE": 2, "TH": 3, "FR": 4, "SA": 5, "SU": 6}
    first_ical: str = sorted([i for _, _, i in marked], key=lambda x: wday_order[x])[0]
    first_weekday = wday_order[first_ical]
    start_date_first = next_weekday_on_or_after(start_on, first_weekday)

    hh, mm = map(int, start_time_str.split(":"))
    dtstart = datetime.combine(start_date_first, time(hour=hh, minute=mm))
    dtend = dtstart + timedelta(minutes=duration_minutes)

    byday: str = ",".join(i for *_, i in marked)
    uid: str = f"{fisio.id}-{uuid.uuid4()}@vitally"

    def fmt(dt: datetime) -> str:
        return dt.strftime("%Y%m%dT%H%M%S")

    lines: list[str] = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Vitally//Pilates Plan//PT-BR",
        "BEGIN:VTIMEZONE",
        f"TZID:{tzid}",
        "END:VTIMEZONE",
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"SUMMARY:Aulas de Pilates - {fisio.nome}",
        f"DTSTART;TZID={tzid}:{fmt(dtstart)}",
        f"DTEND;TZID={tzid}:{fmt(dtend)}",
        f"RRULE:FREQ=WEEKLY;BYDAY={byday}",
        "DESCRIPTION:Plano de aulas gerado pelo Vitally",
        "END:VEVENT",
        "END:VCALENDAR",
        "",
    ]
    return ("\r\n".join(lines)).encode("utf-8")
