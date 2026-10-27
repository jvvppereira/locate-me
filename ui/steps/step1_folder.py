import streamlit as st
from services.local_folder import LocalFolderService
from config import WARN_PHOTO_LIMIT
from ui.components import (
    render_step_indicator,
    render_folder_input,
    render_folder_info,
    render_error,
)


def step1_folder() -> bool:
    render_step_indicator(1)

    path = render_folder_input()

    if not path:
        return False

    with st.spinner("Escaneando pasta..."):
        service = LocalFolderService(path)
        try:
            photos = service.scan()
        except Exception as e:
            render_error(f"Erro ao escanear pasta: {str(e)}")
            return False

    if not photos:
        render_error("Nenhuma imagem válida encontrada na pasta.")
        return False

    st.session_state["album_photos"] = photos
    st.session_state["folder_path"] = path
    st.session_state["folder_service"] = service

    if render_folder_info(len(photos), WARN_PHOTO_LIMIT):
        st.session_state["step"] = 2
        st.rerun()

    return False