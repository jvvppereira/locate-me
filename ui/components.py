import base64
import io
import streamlit as st
from typing import Optional
from PIL import Image, ImageOps
from config import (
    FACE_MATCH_THRESHOLD_DEFAULT,
    FACE_MATCH_THRESHOLD_MIN,
    FACE_MATCH_THRESHOLD_MAX,
    THUMBNAIL_SIZE,
    WARN_PHOTO_LIMIT,
)


def render_header():
    st.markdown(
        """
        <div style="text-align: center; padding: 1rem 0;">
            <h1>🔍 Locate-Me</h1>
            <p style="color: #666; font-size: 1.1rem;">Encontre suas fotos em pastas locais usando reconhecimento facial</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_step_indicator(current_step: int):
    steps = ["1. Pasta", "2. Referência", "3. Resultados"]
    cols = st.columns(3)
    for i, (col, step) in enumerate(zip(cols, steps), 1):
        with col:
            if i < current_step:
                st.markdown(f"✅ **{step}**")
            elif i == current_step:
                st.markdown(f"🔄 **{step}**")
            else:
                st.markdown(f"⏳ {step}")


def render_folder_input() -> Optional[str]:
    import os
    from config import LOCAL_IMAGES_PATH

    st.subheader("📁 Passo 1: Pasta com Imagens")
    st.markdown(
        "Informe o caminho da pasta contendo as fotos para busca."
    )

    default_path = LOCAL_IMAGES_PATH or ""
    if default_path and os.path.isdir(default_path):
        st.info(f"Usando pasta da variável de ambiente: `{default_path}`")

    path = st.text_input(
        "Caminho da pasta",
        value=default_path,
        placeholder="/caminho/para/sua/pasta/de/fotos",
        label_visibility="collapsed",
        help="Pode ser definido via variável de ambiente LOCAL_IMAGES_PATH",
    )

    path = path.strip() if path else None
    if path:
        if not os.path.exists(path):
            st.error(f"Caminho não encontrado: {path}")
            return None
        if not os.path.isdir(path):
            st.error(f"Não é um diretório: {path}")
            return None
        if not os.access(path, os.R_OK):
            st.error(f"Sem permissão de leitura: {path}")
            return None
    return path


def render_folder_info(photo_count: int, warning_limit: int = WARN_PHOTO_LIMIT):
    if photo_count == 0:
        st.error("Nenhuma imagem válida encontrada na pasta.")
        return False

    st.success(f"✅ Pasta escaneada: **{photo_count} imagens** encontradas")

    if photo_count > warning_limit:
        st.warning(
            f"⚠️ Muitas imagens ({photo_count}). O processamento pode levar alguns minutos. "
            f"Deseja continuar mesmo assim?"
        )
        return st.button("Continuar mesmo assim", type="primary")

    return st.button("Continuar para foto de referência", type="primary")


def render_reference_upload() -> Optional[bytes]:
    st.subheader("👤 Passo 2: Sua Foto de Referência")
    st.markdown("Faça upload de uma foto sua de rosto (JPG, PNG).")

    uploaded_file = st.file_uploader(
        "Escolha uma foto",
        type=["jpg", "jpeg", "png"],
        label_visibility="collapsed",
    )

    if uploaded_file:
        image_bytes = uploaded_file.read()
        st.image(image_bytes, caption="Foto de referência", width=300)
        return image_bytes
    return None


def render_face_feedback(num_faces: int, message: str):
    if num_faces == 0:
        st.error(f"❌ {message}")
    elif num_faces > 1:
        st.warning(f"⚠️ {message}")
    else:
        st.success(f"✅ {message}")


def render_progress_bar(processed: int, total: int, matches: int):
    progress = processed / total if total > 0 else 0
    st.progress(progress)
    st.markdown(f"**Processando:** {processed}/{total} fotos | **Matches encontrados:** {matches}")


def _image_to_base64(image_path: str, size: tuple = THUMBNAIL_SIZE) -> Optional[str]:
    try:
        with Image.open(image_path) as img:
            img = ImageOps.fit(img, size, centering=(0.5, 0.5))
            if img.mode != "RGB":
                img = img.convert("RGB")
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG", quality=85)
            return base64.b64encode(buffered.getvalue()).decode()
    except Exception:
        return None


def render_results_grid(matches: list):
    if not matches:
        st.info("Nenhum match encontrado. Tente com outra foto de referência ou pasta.")
        return

    st.subheader(f"🎯 Resultados: {len(matches)} match(es) encontrado(s)")

    flickr_username = st.session_state.get("flickr_username", "")
    flickr_album_id = st.session_state.get("flickr_album_id", "")

    cols_per_row = 4
    for i in range(0, len(matches), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            idx = i + j
            if idx >= len(matches):
                break
            match = matches[idx]
            with col:
                b64 = _image_to_base64(match.url_original.replace("file://", ""))
                
                # Build Flickr URL if configured, else fallback to local file
                if flickr_username and flickr_album_id:
                    flickr_url = f"https://www.flickr.com/photos/{flickr_username}/{match.display_id}/in/album-{flickr_album_id}/"
                else:
                    flickr_url = match.url_original
                
                if b64:
                    st.markdown(
                        f"""
                        <a href="{flickr_url}" target="_blank">
                            <img src="data:image/jpeg;base64,{b64}" style="width:100%; border-radius:8px;" />
                        </a>
                        """,
                        unsafe_allow_html=True,
                    )
                else:
                    st.image(match.url_original.replace("file://", ""), width=200)
                st.caption(f"{match.similarity_percent:.1f}% similar")
                st.caption(f"ID: {match.display_id}")


def render_results_list(matches: list):
    if not matches:
        return

    with st.expander("📋 Ver lista detalhada", expanded=False):
        for match in matches:
            st.markdown(
                f"**{match.title}**  \n"
                f"Similaridade: {match.similarity_percent:.1f}%  \n"
                f"Arquivo: `{match.url_original.replace('file://', '')}`  \n"
                f"---"
            )


def render_error(message: str):
    st.error(f"❌ {message}")


def render_info(message: str):
    st.info(f"ℹ️ {message}")


def render_threshold_slider() -> float:
    return st.slider(
        "Threshold de similaridade (cosine distance)",
        min_value=FACE_MATCH_THRESHOLD_MIN,
        max_value=FACE_MATCH_THRESHOLD_MAX,
        value=st.session_state.get("match_threshold", FACE_MATCH_THRESHOLD_DEFAULT),
        step=0.05,
        help="Menor = mais rigoroso (menos falsos positivos). Valor típico: 0.35-0.45",
        key="threshold_slider",
    )