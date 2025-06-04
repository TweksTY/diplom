import streamlit as st
from streamlit import session_state as state
from citation_types import Book, Article, Dissertation, Site
import database as db


def create_list_from_entries(citations):
    return "\n".join([f"{i+1}. {c}" for i, c in enumerate(citations)])

@st.dialog("Перегляд списку джерел")
def show_list_dialog(citations):
    st.text_area("Список джерел", value=create_list_from_entries(citations), height=500, disabled=False)

if 'conn' not in state:
    state['conn'] = db.create_connection("citations.db")
    db.create_table(state['conn'])

conn = state['conn']
db.create_table(conn)
st.set_page_config(page_title="Цитування", page_icon=":book:", layout="wide", initial_sidebar_state="collapsed")



st.session_state.entry = None
st.session_state.is_first_load = True
CONTAINER_HEIGHT = 100
st.title("Біблографічні посилання")
cols = st.columns(2)
with cols[0]:
    type = st.selectbox("Стиль цитування", ["ДСТУ 8302:2015", "ДСТУ ГОСТ 7.1:2006", "APA", "MLA"])
with cols[1]:
    sort_type = st.selectbox("Сортування", ["За датою додавання", "За назвою"])

entries = db.get_entries(conn, sort_by='time' if sort_type == "За датою" else 'title')
cols = st.columns(4)
citations = []
with cols[0]:
    if st.button("Додати джерело", use_container_width=True):
        st.session_state['entry'] = None
        st.session_state['is_first_load'] = True
        st.switch_page("pages/test_page.py")
with cols[1]:
    if st.button("Пошук джерела", use_container_width=True):
        st.session_state['switch_page'] = None
        st.switch_page("pages/search_page.py")
with cols[2]:
    st.button("Переглянути список", use_container_width=True, on_click=show_list_dialog, args=(citations,))
with cols[3]:
    if st.button("Список авторів", use_container_width=True):
        st.switch_page("pages/authors_page.py")


col1, col2, col3 = st.columns([12, 0.5, 0.5])
for entry in entries:
    with col1:
        citation = ""
        if type == "ДСТУ 8302:2015":
            print(isinstance(entry, Site))
            citation = entry.get_DSTU2015_citation()
        elif type == "ДСТУ ГОСТ 7.1:2006":
            citation = entry.get_DSTU2006_citation()
        elif type == "APA":
            citation = entry.get_APA_citation()
        elif type == "MLA":
            citation = entry.get_MLA_citation()
        citations.append(citation)
        with st.container(height=CONTAINER_HEIGHT, border=True):
            st.write(citation)
    with col2:
        with st.container(height=CONTAINER_HEIGHT, border=False):
            if st.button(label=":pencil2:", key=entry.id, use_container_width=True):
                st.session_state['entry'] = entry
                st.session_state['is_first_load'] = True
                st.switch_page("pages/test_page.py")
    with col3:
        with st.container(height=CONTAINER_HEIGHT, border=False):
            if st.button(label=":x:", key=f"delete_{entry.id}", on_click=db.delete_entry, args=(conn, entry.id), use_container_width=True):
                st.success("Запис видалено")
                st.rerun()



st.download_button(
    "Завнтажити список",
    data=create_list_from_entries(citations),
    file_name="citations.txt",
    mime="text/plain",
    use_container_width=True
    )