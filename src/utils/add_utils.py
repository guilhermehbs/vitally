import logging
import re

logger = logging.getLogger("vitally_app")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(email: str) -> bool:
    if not email:
        logger.debug("is_valid_email: vazio -> True")
        return True
    ok = bool(EMAIL_RE.fullmatch(email))
    logger.debug("is_valid_email(%s) -> %s", email, ok)
    return ok


def only_digits(s: str) -> str:
    digits = re.sub(r"\D", "", s or "")
    logger.debug("only_digits(%s) -> %s", s, digits)
    return digits


def validate_br_phone(digits: str) -> tuple[bool, str | None]:
    d = only_digits(digits)
    if len(d) not in (10, 11):
        return False, "Telefone deve ter 10 (fixo) ou 11 (celular) dígitos."
    if d[0] == "0" or d[1] == "0":
        return False, "DDD inválido."
    if len(d) == 11 and d[2] != "9":
        return False, "Para celular (11 dígitos), o número deve começar com 9."
    return True, None
