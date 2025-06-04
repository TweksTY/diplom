import streamlit as st
from streamlit import session_state as state
import database as db
from citation_types import Book, Article, Dissertation, Author, Proceeding, Site
from citation_bits import specialties
import datetime


    

class PageGenerator:

    def __validate_text_input(self, input_data):
        if len(input_data) < 1:
            return False, "Введіть дані"
        return True, ""

    def __validate_number_field(self, number):
        if number is None or number < 1:
            return False, "Число має бути більшим за 0"
        return True, ""

    def __init__(self, entry = None):
        if 'conn' not in state:
            state['conn'] = db.create_connection("citations.db")
            db.create_table(state['conn'])
        if entry is not None and st.session_state.get('is_first_load', True):
            st.session_state.authors = [author.to_dict() for author in entry.authors]
            st.session_state.is_first_load = False
        elif entry is None and st.session_state.get('is_first_load', True):
            st.session_state.authors = [{"first_name": "", "last_name": "", "middle_name": ""}]
            st.session_state.is_first_load = False
        self.entry = entry

        print("PageGenerator initialized with entry:", entry)

    def __validate_author(self, author):
        if len(author.first_name) < 1 or len(author.last_name) < 1:
            return False, "Автор має містити ім'я та прізвище"
        return True, ""

    def __check_pages_cited(self):
        if hasattr(self, 'pages_cited') and self.pages_cited:
            if '-' in self.pages_cited:
                pages = self.pages_cited.split('-')
                if len(pages) == 2:
                    try:
                        start_page = int(pages[0].strip())
                        end_page = int(pages[1].strip())
                        if start_page <= 0 or end_page <= 0:
                            return False, "Сторінки мають бути більшими за 0"
                        if start_page > end_page:
                            return False, "Перша сторінка не може бути більшою за останню"
                        return True, ""
                    except ValueError:
                        return False, "Сторінки мають бути числовими"
            else:
                if self.pages_cited.isdigit():
                    page_number = int(self.pages_cited.strip())
                    if page_number <= 0:
                        return False, "Сторінка має бути більшою за 0"
                    return True, ""
                return False, "Цитовані сторінки мають бути в форматі 'X-Y' або одна сторінка 'X'"
        elif hasattr(self, 'pages_cited') and not self.pages_cited:
            if st.session_state.get('edit_message', None):
                return False, "Введіть сторінки, що цитуються"
        return True, ""


    @st.dialog("Оберіть автора")
    def __choose_author_dialog(self, idx):
        authors = db.get_authors(state['conn'])
        if not authors:
            st.warning("Немає доступних авторів")
            return None
        
        author_names = [f"{author.first_name} {author.last_name}{' ' + author.middle_name if author.middle_name else ''}" for author in authors]
        selected_author = st.selectbox(f"Оберіть автора {idx+1}", author_names)
        
        if st.button("ОК"):
            st.session_state.authors[idx]["first_name"] = selected_author.split()[0]
            st.session_state.authors[idx]["last_name"] = selected_author.split()[1]
            if len(selected_author.split()) > 2:
                st.session_state.authors[idx]["middle_name"] = selected_author.split()[2]
            st.rerun()
        if st.button("Скасувати"):
            st.rerun()


    def __validate_issue_and_number(self):
        if (self.journal_issue == 0 and self.journal_number == 0):
            return False, "Введіть номер випуску або тому журналу"
        return True, ""

    def __validate_authors(self, authors):
        seen = set()
        if (self.type == 'Сайт'):
            if len(authors) == 1 and authors[0].is_empty():
                return True, ""
            
        if len(authors) > 1 and self.type == "Дисертація":      
            return False, "Дисертація може мати лише одного автора"
        for author in authors:
            valid, message = self.__validate_author(author)
            if not valid:
                return False, message
            # Create a tuple to uniquely identify an author
            author_id = (author.first_name.strip().lower(), author.last_name.strip().lower(), author.middle_name.strip().lower())
            if author_id in seen:
                return False, "Список авторів містить дублікати"
            seen.add(author_id)
        return True, ""

    def __save_entry(self, entry):
        entry_obj = None
        constructors = {
            "Book": Book,
            "Article": Article,
            "Dissertation": Dissertation,
            "Proceeding": Proceeding,
            "Site": Site
        }
        entry_obj = constructors[entry['type']](entry)

        #if (entry['type'] == "Book"):
        #    entry_obj = Book(entry)
        #elif (entry['type'] == "Article"):
        #    entry_obj = Article(entry)
        #elif (entry['type'] == "Dissertation"):
        #    entry_obj = Dissertation(entry)
        #elif (entry['type'] == "Proceeding"):
        #    entry_obj = Proceeding(entry)
        #elif (entry['type'] == "Site"):
        #    entry_obj = Site(entry)


        if (not entry_obj.id):
            db.insert_entry(state['conn'], entry_obj)
            return
        else:
            db.update_entry(state['conn'], entry_obj)
            return

    def __get_authors(self):
        return [
            Author(author['first_name'], author['last_name'], author['middle_name'])
            for author in st.session_state.authors
        ]

    def __render_online_fields(self):
        cols = st.columns([3, 1])
        with cols[0]:
            self.url = st.text_input("URL", value=getattr(self.entry, 'url', '') if self.entry else "")
            self.url_placeholder = st.empty()
        with cols[1]:
            date_value = getattr(self.entry, 'access_date', None)
            if date_value:
                date_value = datetime.datetime.strptime(date_value, "%d.%m.%Y").date()
            self.date = st.date_input(
                "Дата доступу",
                format="DD.MM.YYYY",
                value=date_value if date_value else 'today',
            )
        if (self.type == "Дисертація"):
            with cols[0]:
                self.db_name = st.text_input("Назва бази даних", value=getattr(self.entry, 'db_name', '') if self.entry else "")
                self.db_name_placeholder = st.empty()

    def __get_numerical_value(self, attribute, default_value=0):
        if (st.session_state.get('edit_message', None)):
            return getattr(self.entry, attribute, default_value) if self.entry else None
        else:
            return getattr(self.entry, attribute, default_value) if self.entry and getattr(self.entry, attribute, None) is not None else default_value

    def generate_page(self):

        # Function to add a new author
        def add_author():
            st.session_state.authors.append({"first_name": "", "last_name": "", "middle_name": ""})

        # Function to remove an author
        def remove_author(idx):
            if len(st.session_state.authors) > 1:
                st.session_state.authors.pop(idx)
        
        if st.button(":arrow_left: Повернутися на попередню сторінку"):
            st.session_state['is_first_load'] = False
            st.session_state['entry'] = None
            st.session_state['authors'].clear()
            if st.session_state.get('edit_message', None):
                st.session_state['edit_message'] = None
                st.switch_page("pages/search_page.py")
            else:
                st.switch_page("index.py")
                
        with st.container(border=True):
            if (st.session_state.get('edit_message', None)):
                st.warning(st.session_state['edit_message'])
                
            cols = st.columns([3, 1])
            with cols[0]:
                type_options = ('Книга', 'Стаття', 'Дисертація', 'Тези конференції', 'Сайт')
                if self.entry and hasattr(self.entry, 'type'):
                    if self.entry.type == "Book":
                        type_index = type_options.index('Книга')
                    elif self.entry.type == "Article":
                        type_index = type_options.index('Стаття')
                    elif self.entry.type == "Dissertation":
                        type_index = type_options.index('Дисертація')
                    elif self.entry.type == "Proceeding":
                        type_index = type_options.index('Тези конференції')
                    elif self.entry.type == "Site":
                        type_index = type_options.index('Сайт')
                    else:
                        type_index = 0
                else:
                    type_index = 0
                self.type = st.selectbox('Оберіть тип публікації', type_options, index=type_index)
            with cols[1]:
                self.language = st.selectbox('Оберіть мову джерела', ('Українська', 'English'), index=0 if self.entry is None or self.entry.language == 'uk' else 1)

            self.title = st.text_input("Назва", value = getattr(self.entry, 'title', '') if self.entry else "")
            self.title_placeholder = st.empty()
            self.text_fields = []
            self.number_fields = []
            # Initialize authors in session state if not present
            if "authors" not in st.session_state:
                st.session_state.authors = [{"first_name": "", "last_name": "", "middle_name": ""}]

            # Render author input fields
            for idx, author in enumerate(st.session_state.authors):
                cols = st.columns([3, 3, 3, 1])
                with cols[0]:
                    st.session_state.authors[idx]["first_name"] = st.text_input(
                        f"Ім'я автора {idx+1}", value=author["first_name"], key=f"author_first_name_{idx}" 
                    )
                    st.button("Обрати зі списку", key=f"select_author_{idx}", on_click=self.__choose_author_dialog, args=(idx,))
                with cols[1]:
                    st.session_state.authors[idx]["last_name"] = st.text_input(
                        f"Прізвище автора {idx+1}", value=author["last_name"], key=f"author_last_name_{idx}"
                    )
                with cols[2]:
                    st.session_state.authors[idx]["middle_name"] = st.text_input(
                        f"По батькові автора {idx+1}", value=author["middle_name"], key=f"author_middle_name_{idx}"
                    )
                with cols[3]:
                    if st.button("🗑️", key=f"remove_author_{idx}"):
                        remove_author(idx)
                        st.rerun()
            self.author_placeholder = st.empty()

            if st.button("Додати автора"):
                add_author()
                st.rerun()

            if (self.type == 'Сайт'):
                self.is_online = True
            else:
                self.is_online = st.checkbox("Джерело знайдено онлайн", value= True if self.entry and getattr(self.entry, 'url', 'None') else False)
            if self.is_online:
                self.__render_online_fields()
            match self.type:
                case 'Книга':
                    self.generate_book_page()
                case 'Стаття':
                    self.generate_article_page()
                case 'Дисертація':
                    self.generate_dissertation_page()
                case 'Тези конференції':
                    self.generate_proceeding_page()
                case 'Сайт':
                    self.generate_site_page()
            if st.button("Зберегти"):
                authors = self.__get_authors()
                valid, message = self.__validate_authors(authors)
                if not valid:
                    self.author_placeholder.error(message)
                    return
                
                valid, message = self.__validate_text_input(self.title)
                if not valid:
                    self.title_placeholder.error(message)
                    return

                if not st.session_state.get('edit_message', None):
                    for (text, placeholder) in self.text_fields:
                        valid, message = self.__validate_text_input(text)
                        if not valid:
                            placeholder.error(message)
                            return

                if self.is_online:
                    if not self.url or len(self.url) < 1:
                        self.url_placeholder.error("Введіть URL джерела")
                        return
                    if not self.url.startswith("http"):
                        self.url_placeholder.error("URL має починатися з 'http://' або 'https://'")
                        return
                    if not self.date:
                        self.date_placeholder.error("Введіть дату доступу")
                        return
                    if self.type == "Дисертація":
                        if not self.db_name or len(self.db_name) < 1:
                            self.db_name_placeholder.error("Введіть назву бази даних")
                            return

                

                entry = {
                    'id': self.entry.id if self.entry else None,
                    'type': type,
                    'language': 'uk' if self.language == "Українська" else 'en',
                    'title': self.title,
                    'authors': authors,
                    'url': getattr(self, 'url', '') if self.is_online else None,
                    'access_date': getattr(self, 'date', None).strftime("%d.%m.%Y") if self.is_online and getattr(self, 'date', None) else None
                }

                if self.type == "Книга":
                    if self.publishing_number and not self.publishing_number.isdigit():
                        self.publishing_number_placeholder.error("Номер видання має бути числом")
                        return
                    entry['type'] = "Book"
                    entry['city'] = getattr(self, 'city', None)
                    entry['pages_count'] = getattr(self, 'pages_count', None)
                    entry['year'] = getattr(self, 'year', None)
                    entry['publisher'] = getattr(self, 'publisher', None)
                    entry['publishing_number'] = getattr(self, 'publishing_number', None)
                    entry['publishing_type'] = getattr(self, 'publishing_type', None)
                    
                elif self.type == "Стаття":
                    valid, message = self.__check_pages_cited()
                    if not valid:
                        self.pages_cited_placeholder.error(message)
                        return
                    valid, message = self.__validate_issue_and_number()
                    if not valid:
                        self.issue_and_number_placeholder.error(message)
                        return
                    entry['pages_cited'] = self.pages_cited
                    entry['type'] = "Article"
                    entry['journal'] = getattr(self, 'journal', None)
                    entry['year'] = getattr(self, 'year', None)
                    entry['issue'] = getattr(self, 'journal_issue', None)
                    entry['number'] = getattr(self, 'journal_number', None)
                    entry['pages_count'] = 0

                elif self.type == "Дисертація":
                    entry['year'] = self.year
                    entry['type'] = "Dissertation"
                    entry['degree'] = self.degree if self.is_ukrainian else None
                    entry['dissertation_type'] = self.dissertation_type
                    entry['db_name'] = self.db_name if self.is_online else None
                    entry['city'] = self.city
                    entry['pages_count'] = self.pages_count
                    entry['specialty_code'] = self.specialty_code if self.is_ukrainian else None
                    entry['university'] = self.university
                    entry['specialty'] = self.specialty if self.is_ukrainian else None
                
                elif self.type == "Тези конференції":
                    valid, message = self.__check_pages_cited()
                    if not valid:
                        self.pages_cited_placeholder.error(message)
                        return
                    entry['pages_cited'] = self.pages_cited
                    entry['type'] = "Proceeding"
                    entry['conference'] = self.conference
                    entry['publishing_type'] = self.publishing_type
                    entry['conference_city'] = self.conference_city
                    entry['conference_date'] = getattr(self, 'conference_date', None).strftime("%d.%m.%Y") if self.is_online and getattr(self, 'conference_date', None) else None
                    entry['publisher'] = self.publisher
                    entry['city'] = self.city
                    entry['year'] = self.year
                
                elif self.type == "Сайт":
                    entry['type'] = "Site"
                    entry['publisher'] = self.publisher

                for key in entry:
                    if (entry[key] is not None and isinstance(entry[key], str)):
                        entry[key] = entry[key].strip()
                self.__save_entry(entry)
                st.session_state.authors.clear()
                st.session_state.entry = None
                st.session_state.edit_message = None
                st.switch_page("index.py")
        
    
    def generate_book_page(self):
        self.city = st.text_input("Місто видання", value=getattr(self.entry, 'city', '') if self.entry else "")
        self.city_placeholder = st.empty()
        self.text_fields.append((self.city, self.city_placeholder,))
        self.pages_count = st.number_input(
            "Кількість сторінок",
            min_value=1,
            max_value=5000,
            value=self.__get_numerical_value('pages_count', 1)
        )
        self.pages_count_placeholder = st.empty()
        self.year = st.number_input(
            "Рік видання", 
            min_value=1900, 
            max_value=2100, 
            value=self.__get_numerical_value('year', 2023)
            )
        self.year_placeholder = st.empty()
        self.publisher = st.text_input("Видавництво", value=getattr(self.entry, 'publisher', ''))
        self.publisher_placeholder = st.empty()
        self.text_fields.append((self.publisher, self.publisher_placeholder,))
        cols = st.columns(2)
        with cols[0]:
            self.publishing_number = st.text_input("Номер видання", value=getattr(self.entry, 'publishing_number', ''))
            self.publishing_number_placeholder = st.empty()
        with cols[1]:
            self.publishing_type = st.text_input("Тип видання (монографія, підручник тощо)", value=getattr(self.entry, 'publishing_type', ''))

    def generate_article_page(self):

        self.journal = st.text_input("Назва журналу", value=getattr(self.entry, 'journal', ''))
        self.journal_placeholder = st.empty()
        self.text_fields.append((self.journal, self.journal_placeholder,))

        self.year = st.number_input(
            "Рік видання", 
            min_value=1900, 
            max_value=2100, 
            value=self.__get_numerical_value('year', 2023)
            )
        self.year_placeholder = st.empty()

        cols = st.columns(2)
        with cols[0]:
            self.journal_issue = st.number_input(
                "Номер випуску (0 якщо відсутній)",
                min_value=0, 
                max_value=500, 
                value=self.__get_numerical_value('issue', 1)
                )
        with cols[1]:
            self.journal_number = st.number_input("Номер тому (0 якщо відсутній)", min_value=0, max_value=500, value=self.__get_numerical_value('number', 1))
        self.issue_and_number_placeholder = st.empty()
        self.pages_cited = st.text_input("Сторінки, що цитуються (через '-')", value = getattr(self.entry, 'pages_cited', '') if self.entry else '')
        self.pages_cited_placeholder = st.empty()

    def generate_dissertation_page(self):

        self.dissertation_type = st.text_input("Тип дисертації (кандидатська/докторська)", value=getattr(self.entry, 'dissertation_type', ''))
        self.dissertation_type_placeholder = st.empty()
        self.text_fields.append((self.dissertation_type, self.dissertation_type_placeholder,))

        self.type_placeholder = st.empty()
        self.is_ukrainian = st.checkbox("Дисертація, видана в Україні?", value=True if self.entry and getattr(self.entry, 'degree', '') else False)
        if self.is_ukrainian:
            degree_options = ("кандидат наук", "доктор наук", "доктор філософії")
            if self.entry and hasattr(self.entry, 'type') and self.entry.degree in degree_options:
                degree_index = degree_options.index(self.entry.degree)
            else:
                degree_index = 0
            self.degree = st.selectbox("Науковий ступінь", degree_options, degree_index)
            self.degree_placeholder = st.empty()
            self.specialty = st.selectbox("Спеціальність", options=specialties.keys(), index=specialties.get(self.entry.specialty, 0) if self.entry and hasattr(self.entry, 'specialty') else 0)
            self.specialty_code = st.text_input("Код спеціальності", value=getattr(self.entry, 'specialty_code', ''), placeholder="Наприклад: 05.02.01")
            self.specialty_code_placeholder = st.empty()
        self.university = st.text_input("Університет", getattr(self.entry, 'university', ''))
        self.university_placeholder = st.empty()
        self.city = st.text_input("Місто", getattr(self.entry, 'city', ''))
        self.city_placeholder = st.empty()
        self.year = st.number_input(
            "Рік захисту", 
            min_value=1900, 
            max_value=2100, 
            value=self.__get_numerical_value('year', 2023)
            )
        self.pages_count = st.number_input(
            "Кількість сторінок",
            min_value=1,
            max_value=5000,
            value=self.__get_numerical_value('pages_count', 1)
        )

    def generate_proceeding_page(self):
        self.conference = st.text_input("Назва збірника", value=getattr(self.entry, 'conference', ''))
        self.conference_placeholder = st.empty()
        self.text_fields.append((self.conference, self.conference_placeholder,))
        self.publishing_type = st.text_input("Тип видання", value=getattr(self.entry, 'publishing_type', ''))
        self.publishing_type_placeholder = st.empty()
        self.text_fields.append((self.publishing_type, self.publishing_type_placeholder,))
        self.conference_city = st.text_input("Місто проведення конференції", value=getattr(self.entry, 'conference_city', ''))
        self.conference_city_placeholder = st.empty()
        self.text_fields.append((self.conference_city, self.conference_city_placeholder,))
        date_value = getattr(self.entry, 'conference_date', None)
        if date_value:
            date_value = datetime.datetime.strptime(date_value, "%d.%m.%Y").date()
        self.conference_date = st.date_input(
                        "Дата проведення конференції",
                        format="DD.MM.YYYY",
                        value=date_value if date_value else 'today',
                    )
        self.publisher = st.text_input("Видавництво або університет", value=getattr(self.entry, 'publisher', ''))
        self.publisher_placeholder = st.empty()
        self.text_fields.append((self.publisher, self.publisher_placeholder,))
        self.city = st.text_input("Місто видавця", value=getattr(self.entry, 'city', ''))
        self.city_placeholder = st.empty()
        self.text_fields.append((self.city, self.city_placeholder,))
        self.year = st.number_input(
            "Рік видання", 
            min_value=1900, 
            max_value=2100, 
            value=self.__get_numerical_value('year', 2023)
            )
        self.year_placeholder = st.empty()
        self.pages_cited = st.text_input("Сторінки, що цитуються (через '-')", value = getattr(self.entry, 'pages_cited', '') if self.entry else '')
        self.pages_cited_placeholder = st.empty()
    
    def generate_site_page(self):
        self.publisher = st.text_input("Назва сайту", value=getattr(self.entry, 'publisher', ''))
        self.date_placeholder = st.empty()