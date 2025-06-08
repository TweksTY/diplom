import streamlit as st
from streamlit import session_state as state
from utils.citation_types import Author
import utils.database as db



@st.dialog("Редагування автора")
def edit_author_dialog(author):
    conn = state['conn']
    if author:
        with st.form(key=f"edit_author_form_{author.id}"):
            first_name = st.text_input("Ім'я", value=author.first_name)
            last_name = st.text_input("Прізвище", value=author.last_name)
            middle_name = st.text_input("По батькові", value=author.middle_name or "")
            submit_button = st.form_submit_button(label="Зберегти")
            if submit_button:
                result = db.update_author(conn, Author(first_name, last_name, middle_name, author.id))
                if result is None:
                    st.session_state['success_message'] = f"Автор {author.id} успішно оновлений."
                    st.rerun()
                else:
                    st.error(result)

def main_page():
    if 'conn' not in state:
        state['conn'] = db.create_connection("citations.db")
        db.create_table(state['conn'])

    conn = state['conn']
    db.create_table(conn)
    st.set_page_config(page_title="Список авторів", page_icon=":book:", layout="wide", initial_sidebar_state="collapsed")

    if st.button(":arrow_left: Повернутися на попередню сторінку"):
        st.switch_page("index.py")
    if (st.session_state.get('success_message')):
        st.success(st.session_state['success_message'])
        st.session_state['success_message'] = None
    if (st.session_state.get('error_message')):
        st.error(st.session_state['error_message'])
        st.session_state['error_message'] = None
    authors = db.get_authors(conn)
    st.title("Список авторів")

    col1, col2, col3 = st.columns([12, 0.5, 0.5])
    for author in authors:
        with col1:
            with st.container(height=70, border=True):
                st.write(f"{author.first_name} {author.last_name}{' ' + author.middle_name if author.middle_name else ''}")
        with col2:
            with st.container(height=70, border=False):
                st.button(label=":pencil2:", key=f"edit_{author.id}", on_click=edit_author_dialog, args=(author,), use_container_width=True)
        with col3:
            with st.container(height=70, border=False):
                if st.button(label=":x:", key=f"delete_{author.id}", use_container_width=True):
                    result = db.delete_author(conn, author.id)
                    st.session_state.error_message = result if result else None
                    st.session_state.success_message = f"Автор {author.id} успішно видалений." if result is None else None
                    st.rerun()


main_page()