import streamlit as st
from streamlit import session_state as state
import utils.database as db
from utils.citation_types import Book, Article, Dissertation
from utils.citation_bits import specialties
from utils.page_generator import PageGenerator

pg = PageGenerator(entry=st.session_state.get('entry', None));
pg.generate_page()