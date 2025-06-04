import streamlit as st
from streamlit import session_state as state
import database as db
from citation_types import Book, Article, Dissertation
from citation_bits import specialties
from page_generator import PageGenerator

pg = PageGenerator(entry=st.session_state.get('entry', None));
pg.generate_page();