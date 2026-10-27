import streamlit as st
import pandas as pd
from services.face_matcher import find_matches
from ui.components import (
    render_step_indicator,
    render_progress_bar,
    render_results_grid,
    render_results_list,
    render_error,
    render_threshold_slider,
)
from config import FACE_MATCH_THRESHOLD_DEFAULT, DEFAULT_FLICKR_USERNAME, DEFAULT_FLICKR_ALBUM_ID


def step3_results() -> bool:
    render_step_indicator(3)

    photos = st.session_state.get("album_photos", [])
    reference_embedding = st.session_state.get("reference_embedding")
    folder_service = st.session_state.get("folder_service")

    if not photos or reference_embedding is None or folder_service is None:
        render_error("Dados incompletos. Volte aos passos anteriores.")
        if st.button("Voltar ao início"):
            st.session_state.clear()
            st.rerun()
        return False

    st.subheader("🔄 Passo 3: Processando pasta...")

    # Threshold slider
    threshold = render_threshold_slider()
    st.session_state["match_threshold"] = threshold

    # Flickr link configuration (optional)
    st.markdown("**Configuração de link Flickr (opcional)**")
    col1, col2 = st.columns(2)
    with col1:
        flickr_username = st.text_input(
            "Flickr Username",
            value=st.session_state.get("flickr_username", DEFAULT_FLICKR_USERNAME),
            help="Username no Flickr (ex: pythonbrasil)",
            key="flickr_username_input",
        )
        st.session_state["flickr_username"] = flickr_username

    with col2:
        flickr_album_id = st.text_input(
            "Album ID",
            value=st.session_state.get("flickr_album_id", DEFAULT_FLICKR_ALBUM_ID),
            help="ID do álbum no Flickr",
            key="flickr_album_id_input",
        )
        st.session_state["flickr_album_id"] = flickr_album_id

    # Process button
    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        process_clicked = st.button("🔍 Processar", type="primary")
    with col_btn2:
        reprocess_clicked = st.button("🔄 Re-processar com novo threshold")

    # Check if we should process (first time or re-process)
    should_process = process_clicked or reprocess_clicked or "matches" in st.session_state

    if not should_process:
        st.info("Ajuste o threshold acima e clique em **Processar** para iniciar a busca.")
        return False

    progress_container = st.empty()

    def update_progress(processed: int, total: int, matches: int):
        with progress_container.container():
            render_progress_bar(processed, total, matches)

    def image_loader(photo):
        return folder_service.get_image_bytes(photo)

    with st.spinner("Buscando matches..."):
        matches = find_matches(
            photos,
            reference_embedding,
            threshold=threshold,
            image_loader=image_loader,
            progress_callback=update_progress
        )

    progress_container.empty()
    st.session_state["matches"] = matches

    render_results_grid(matches)
    render_results_list(matches)

    if matches:
        csv_data = pd.DataFrame([
            {
                "photo_id": m.photo_id,
                "title": m.title,
                "similarity_percent": round(m.similarity_percent, 1),
                "distance": round(m.distance, 4),
                "url_original": m.url_original,
                "url_thumbnail": m.url_thumbnail,
            }
            for m in matches
        ]).to_csv(index=False)

        st.download_button(
            "📥 Baixar resultados (CSV)",
            data=csv_data,
            file_name="locate_me_results.csv",
            mime="text/csv",
        )

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Nova busca"):
            for key in ["step", "album_photos", "reference_embedding", "matches", "reference_image_bytes", "num_reference_faces", "album_id", "match_threshold", "folder_path", "folder_service"]:
                st.session_state.pop(key, None)
            st.rerun()

    with col2:
        if st.button("🏠 Início"):
            st.session_state.clear()
            st.rerun()

    return True