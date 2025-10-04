import streamlit as st

from src.models.paciente_model import Paciente
from src.services.clinica_service import ClinicaService


def get_ativos(service: ClinicaService) -> list[Paciente]:
    try:
        ativos = list(service.listar_pacientes(only_active=True))
    except Exception as exc:
        st.error(f"Erro ao listar pacientes: {exc}")
        return []
    return ativos
