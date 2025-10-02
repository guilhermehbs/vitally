from __future__ import annotations

import os
import sys
import ssl
import smtplib
import logging
from datetime import date, timedelta
from email.message import EmailMessage
from typing import Iterable

from dotenv import load_dotenv
from sqlalchemy import select, and_

from src.db import SessionLocal
from src.models_sql import PacienteSQL

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("send_reminders")

def build_message(sender: str, to_email: str, to_name: str | None, vencimento: date) -> EmailMessage:
    assunto = "Lembrete de pagamento - Vitally"
    nome = to_name or "Paciente"
    venc_br = vencimento.strftime("%d/%m/%Y")

    texto = (
        f"Olá, {nome}!\n\n"
        f"Este é um lembrete de pagamento. Sua próxima cobrança está prevista para {venc_br}.\n"
        f"Se já realizou o pagamento, desconsidere este e-mail.\n\n"
        f"Abraços,\nEquipe Vitally"
    )

    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height:1.5;">
        <p>Olá, <strong>{nome}</strong>!</p>
        <p>Este é um lembrete de pagamento. Sua <strong>próxima cobrança</strong> está prevista para
           <strong>{venc_br}</strong>.</p>
        <p>Se já realizou o pagamento, por favor desconsidere este e-mail.</p>
        <p>Abraços,<br/>Equipe Vitally</p>
      </body>
    </html>
    """

    msg = EmailMessage()
    msg["Subject"] = assunto
    msg["From"] = sender
    msg["To"] = to_email
    msg.set_content(texto)
    msg.add_alternative(html, subtype="html")
    return msg

def send_email(host: str, port: int, username: str | None, password: str | None, use_tls: bool, message: EmailMessage) -> None:
    if use_tls:
        context = ssl.create_default_context()
        with smtplib.SMTP(host, port) as smtp:
            smtp.starttls(context=context)
            if username and password:
                smtp.login(username, password)
            smtp.send_message(message)
    else:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(host, port, context=context) as smtp:
            if username and password:
                smtp.login(username, password)
            smtp.send_message(message)

def get_pacientes_com_vencimento_em_ate_7_dias() -> Iterable[PacienteSQL]:
    hoje = date.today()
    limite = hoje + timedelta(days=7)
    log.info("Buscando pacientes com data_proxima_cobranca entre %s e %s", hoje, limite)

    with SessionLocal() as s:
        stmt = (
            select(PacienteSQL)
            .where(
                and_(
                    PacienteSQL.ativo.is_(True),
                    PacienteSQL.data_proxima_cobranca.is_not(None),
                    PacienteSQL.data_proxima_cobranca >= hoje,
                    PacienteSQL.data_proxima_cobranca <= limite,
                )
            )
            .order_by(PacienteSQL.data_proxima_cobranca.asc())
        )
        return s.execute(stmt).scalars().all()

def main() -> int:
    load_dotenv()

    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    smtp_from = os.getenv("SMTP_FROM")
    smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() in {"1", "true", "yes"}

    if not smtp_host or not smtp_from:
        log.critical("SMTP_HOST e/ou SMTP_FROM não configurados. Abortando.")
        return 2

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        log.warning(
            "DATABASE_URL não está definido no ambiente. "
            "O src.db pode estar resolvendo via outras fontes. Siga se souber o que está fazendo."
        )
    else:
        log.info("Usando DATABASE_URL configurado.")

    try:
        pacientes = get_pacientes_com_vencimento_em_ate_7_dias()
    except Exception as e:
        log.critical("Falha ao consultar banco: %s", e, exc_info=True)
        return 3

    if not pacientes:
        log.info("Nenhum paciente com vencimento nos próximos 7 dias. Nada a enviar.")
        return 0

    enviados = 0
    pulados_sem_email = 0
    falhas = 0

    for p in pacientes:
        if not p.email:
            pulados_sem_email += 1
            log.warning("Paciente id=%s nome=%s sem e-mail. Pulando.", p.id, p.nome)
            continue

        try:
            msg = build_message(
                sender=smtp_from,
                to_email=p.email,
                to_name=p.nome,
                vencimento=p.data_proxima_cobranca,
            )
            send_email(
                host=smtp_host,
                port=smtp_port,
                username=smtp_user,
                password=smtp_pass,
                use_tls=smtp_use_tls,
                message=msg,
            )
            enviados += 1
            log.info("Lembrete enviado para id=%s email=%s venc=%s", p.id, p.email, p.data_proxima_cobranca)
        except Exception as e:
            falhas += 1
            log.error("Falha ao enviar e-mail para id=%s email=%s: %s", p.id, p.email, e, exc_info=True)

    log.info("Resumo: enviados=%s, sem_email=%s, falhas=%s", enviados, pulados_sem_email, falhas)
    return 0 if falhas == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
