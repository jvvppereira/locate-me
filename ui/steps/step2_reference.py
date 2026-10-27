import streamlit as st
from services.face_matcher import get_reference_embedding
from ui.components import (
    render_step_indicator,
    render_reference_upload,
    render_face_feedback,
    render_error,
)


def step2_reference() -> bool:
    render_step_indicator(2)

    image_bytes = render_reference_upload()

    if not image_bytes:
        return False

    with st.spinner("Analisando rosto..."):
        embedding, num_faces, message = get_reference_embedding(image_bytes)

    render_face_feedback(num_faces, message)

    if embedding is None:
        return False

    st.session_state["reference_embedding"] = embedding
    st.session_state["reference_image_bytes"] = image_bytes
    st.session_state["num_reference_faces"] = num_faces

    if st.button("Iniciar busca", type="primary"):
        st.session_state["step"] = 3
        st.rerun()

    return False