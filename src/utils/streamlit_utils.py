import logging

import streamlit as st

logger = logging.getLogger("vitally_app")


def rerun_app() -> None:
    logger.debug("Solicitando rerun do Streamlit")
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()
    else:
        logger.critical("Streamlit sem método de rerun disponível")
        raise RuntimeError("Versão do Streamlit não possui rerun disponível")
