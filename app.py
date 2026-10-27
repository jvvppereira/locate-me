import streamlit as st
from dotenv import load_dotenv

from config import STREAMLIT_CONFIG
from ui.components import render_header, render_error
from ui.steps import step1_folder, step2_reference, step3_results


load_dotenv()


def init_session_state():
    if "step" not in st.session_state:
        st.session_state["step"] = 1


def main():
    st.set_page_config(**STREAMLIT_CONFIG)

    init_session_state()

    render_header()

    step = st.session_state.get("step", 1)

    if step == 1:
        step1_folder()
    elif step == 2:
        step2_reference()
    elif step == 3:
        step3_results()


if __name__ == "__main__":
    main()