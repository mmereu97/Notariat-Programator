import json
import os
import sys
import sqlite3
import socket
import datetime
from datetime import timedelta
import calendar
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QGridLayout, QLabel, QPushButton, 
                            QFrame, QScrollArea, QComboBox, QLineEdit, 
                            QDialog, QDialogButtonBox, QMessageBox, QFormLayout,
                            QCalendarWidget, QCheckBox, QTextEdit, QToolTip)
from PyQt5.QtCore import Qt, QSize, QDate
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon

class AddEditAppointmentDialog(QDialog):
    """Dialog pentru adăugarea sau editarea unei programări"""
    def __init__(self, parent=None, day=None, time=None, client_name="", document_type="", 
                 document_types=None, edit_mode=False, observations="", appointment_id=None):
        super().__init__(parent)
        
        self.day = day
        self.time = time
        self.document_types = document_types or []
        self.edit_mode = edit_mode
        self.appointment_id = appointment_id  # Adăugăm ID-ul programării pentru ștergere
        
        # Configurare dialog
        title = "Editează programare" if edit_mode else "Adaugă programare nouă"
        self.setWindowTitle(title)
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        # Layout principal
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Titlu
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(title_label, alignment=Qt.AlignCenter)
        
        # Formular
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignRight)
        form_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        layout.addLayout(form_layout)
        
        # Stil pentru etichete
        label_font = QFont("Arial", 12)
        
        # Data
        if day:
            date_str = day.strftime('%d %B %Y')
            date_label = QLabel("Data:")
            date_label.setFont(label_font)
            date_info = QLabel(date_str)
            date_info.setFont(QFont("Arial", 12))
            form_layout.addRow(date_label, date_info)
        
        # Ora (acum editabilă)
        time_label = QLabel("Ora:")
        time_label.setFont(label_font)
        self.time_entry = QLineEdit()
        self.time_entry.setFont(QFont("Arial", 12))
        self.time_entry.setMinimumHeight(40)
        if time:
            self.time_entry.setText(time)
        form_layout.addRow(time_label, self.time_entry)
        
        # Tip document
        doc_type_label = QLabel("Tip document:")
        doc_type_label.setFont(label_font)
        self.doc_type_combo = QComboBox()
        self.doc_type_combo.setFont(QFont("Arial", 12))
        self.doc_type_combo.setMinimumHeight(40)
        self.doc_type_combo.addItems(self.document_types)
        
        # Inițializăm selecția
        if edit_mode and document_type and document_type in self.document_types:
            # Dacă suntem în modul de editare, folosim tipul existent
            self.doc_type_combo.setCurrentText(document_type)
        elif not edit_mode and parent and hasattr(parent, 'last_doc_type_selection') and parent.last_doc_type_selection in self.document_types:
            # Dacă suntem în modul de adăugare, folosim ultima selecție dacă există
            self.doc_type_combo.setCurrentText(parent.last_doc_type_selection)
        
        form_layout.addRow(doc_type_label, self.doc_type_combo)
        
        # Nume client
        client_label = QLabel("Nume client:")
        client_label.setFont(label_font)
        self.client_entry = QLineEdit()
        self.client_entry.setFont(QFont("Arial", 12))
        self.client_entry.setMinimumHeight(40)
        if client_name:
            self.client_entry.setText(client_name)
        form_layout.addRow(client_label, self.client_entry)
        
        # Observații
        observations_label = QLabel("Observații:")
        observations_label.setFont(label_font)
        self.observations_entry = QTextEdit()  # Folosim QTextEdit pentru text multiline
        self.observations_entry.setFont(QFont("Arial", 12))
        self.observations_entry.setMinimumHeight(80)  # Mai înalt pentru a permite mai mult text
        if observations:
            self.observations_entry.setText(observations)
        form_layout.addRow(observations_label, self.observations_entry)
        
        # Butoane
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)
        
        # Buton de ștergere (doar în modul de editare)
        if edit_mode and appointment_id is not None:
            # Adăugăm spațiu pentru aliniere la stânga
            button_layout.addStretch(1)
            
            # Buton Delete pentru ștergerea programării
            self.delete_btn = QPushButton("Șterge programare")
            self.delete_btn.setFont(QFont("Arial", 12))
            self.delete_btn.setMinimumSize(150, 40)
            self.delete_btn.setStyleSheet("background-color: #ffcccc;")  # Fundal roșu deschis
            button_layout.addWidget(self.delete_btn)
            
            # Adăugăm spațiu între butonul de ștergere și butoanele standard
            button_layout.addStretch(1)
        else:
            # Fără buton de ștergere, doar spațiu pentru aliniere
            button_layout.addStretch(2)
        
        # Butoanele standard de OK și Cancel
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        
        # Stilizare butoane
        ok_button = self.button_box.button(QDialogButtonBox.Ok)
        ok_button.setText("Salvează")
        ok_button.setFont(QFont("Arial", 12))
        ok_button.setMinimumSize(120, 40)
        
        cancel_button = self.button_box.button(QDialogButtonBox.Cancel)
        cancel_button.setText("Anulează")
        cancel_button.setFont(QFont("Arial", 12))
        cancel_button.setMinimumSize(120, 40)
        
        button_layout.addWidget(self.button_box)
    
    def get_values(self):
        """Returnează valorile introduse și salvează ultima selecție"""
        # Salvăm ultima selecție dacă există părinte
        if self.parent():
            self.set_last_selection(self.doc_type_combo.currentText())
            
        return {
            'client_name': self.client_entry.text(),
            'document_type': self.doc_type_combo.currentText(),
            'time': self.time_entry.text(),  # Adăugăm și ora editată
            'observations': self.observations_entry.toPlainText()
        }
        
    def set_last_selection(self, document_type):
        """Setează ultima selecție pentru tipul de document"""
        self.parent().last_doc_type_selection = document_type
        self.parent().save_document_types_to_json()


class AddDocumentTypeDialog(QDialog):
    """Dialog pentru adăugarea unui nou tip de document"""
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configurare dialog
        self.setWindowTitle("Adaugă tip document nou")
        self.setMinimumWidth(400)
        
        # Layout principal
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Titlu
        title_label = QLabel("Adaugă tip document nou")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title_label, alignment=Qt.AlignCenter)
        
        # Formular
        form_layout = QFormLayout()
        layout.addLayout(form_layout)
        
        # Nume tip document
        self.doc_type_entry = QLineEdit()
        form_layout.addRow("Nume tip document:", self.doc_type_entry)
        
        # Butoane
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
    
    def get_value(self):
        """Returnează numele tipului de document introdus"""
        return self.doc_type_entry.text()


class NotarialScheduler(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Configurare fereastră principală
        self.setWindowTitle("Programator Acte Notariale")
        self.setMinimumSize(2560, 1300)
    
        # Adăugăm setarea iconiței aici
        self.set_application_icon()

        # Nume stație/computer
        self.computer_name = socket.gethostname()
        
        # Data curentă (începutul săptămânii - luni)
        self.current_date = datetime.datetime.now()
        self.week_start = self.current_date - timedelta(days=self.current_date.weekday())
        
        # Traducere zilele săptămânii în română
        self.day_names_ro = [
            "Luni", "Marți", "Miercuri", "Joi", "Vineri", "Sâmbătă", "Duminică"
        ]
        
        # Traducere numele lunilor în română
        self.month_names_ro = [
            "Ianuarie", "Februarie", "Martie", "Aprilie", "Mai", "Iunie", 
            "Iulie", "August", "Septembrie", "Octombrie", "Noiembrie", "Decembrie"
        ]
        
        # Tipuri de documente disponibile
        self.document_types = [
            "Alipire",
            "Antecontract (promisiune bilaterală)",
            "Apartamentare",
            "Comodat",
            "Consultație",
            "Dezmembrare",
            "Donație",
            "Donație+Uzufruct",
            "Ipotecă",
            "Împrumut",
            "Încetare contract de Întreținere",
            "Închiriere",
            "Întreținere",
            "Novație",
            "Partaj voluntar",
            "Renunțare drept de Uzufruct",
            "Schimb",
            "Succesiune",
            "Superficie",
            "Supliment",
            "Vânzare +Uzufruct viager",
            "Vânzare Drepturi Succesorale",
            "Vânzare",
            "Liber"
        ]
        
        # Inițializare bază de date
        self.init_database()
        
        # Încarcă tipurile de documente din baza de date
        self.load_document_types()
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        
        # Creare interfață
        self.create_header(main_layout)
        self.create_calendar(main_layout)
        self.create_footer(main_layout)
    
    def init_database(self):
        """Inițializare bază de date SQLite și încărcare tipuri de documente din JSON"""
        print("Inițializare bază de date...")
        self.conn = sqlite3.connect('notarial_scheduler.db')
        self.cursor = self.conn.cursor()
        
        # Verifică dacă tabelul appointments există
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='appointments'")
        table_exists = self.cursor.fetchone()
        print(f"Tabelul appointments există: {table_exists is not None}")
        
        if table_exists:
            # Verifică dacă noile coloane există
            self.cursor.execute("PRAGMA table_info(appointments)")
            columns = [col[1] for col in self.cursor.fetchall()]
            print(f"Coloane existente în tabelul appointments: {columns}")
            
            # Adaugă coloanele lipsă dacă e necesar
            if 'status' not in columns:
                print("Adăugare coloană 'status'")
                self.cursor.execute('ALTER TABLE appointments ADD COLUMN status TEXT DEFAULT "active"')
            if 'modified_by' not in columns:
                print("Adăugare coloană 'modified_by'")
                self.cursor.execute('ALTER TABLE appointments ADD COLUMN modified_by TEXT')
            if 'deleted_by' not in columns:
                print("Adăugare coloană 'deleted_by'")
                self.cursor.execute('ALTER TABLE appointments ADD COLUMN deleted_by TEXT')
            if 'deleted_at' not in columns:
                print("Adăugare coloană 'deleted_at'")
                self.cursor.execute('ALTER TABLE appointments ADD COLUMN deleted_at TIMESTAMP')
            if 'modified_at' not in columns:
                print("Adăugare coloană 'modified_at'")
                self.cursor.execute('ALTER TABLE appointments ADD COLUMN modified_at TIMESTAMP')
            if 'observations' not in columns:
                print("Adăugare coloană 'observations'")
                self.cursor.execute('ALTER TABLE appointments ADD COLUMN observations TEXT')
            
            self.conn.commit()
        else:
            # Creare tabel programări dacă nu există
            print("Creare tabel appointments")
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY,
                day DATE,
                time TEXT,
                client_name TEXT,
                document_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                computer_name TEXT,
                status TEXT DEFAULT 'active',
                modified_by TEXT,
                deleted_by TEXT,
                deleted_at TIMESTAMP,
                modified_at TIMESTAMP,
                observations TEXT
            )
            ''')
        
        # Încercare încărcare tipuri documente din JSON
        json_loaded = self.load_document_types_from_json()
        
        # Dacă nu am reușit să încărcăm din JSON, folosim lista implicită și creăm JSON-ul
        if not json_loaded:
            print("Nu s-au găsit tipuri de documente în JSON, folosim lista implicită")
            
            # Inițializăm highlighted_types
            self.highlighted_types = {"Succesiune": True}
            
            # Salvăm în JSON pentru utilizare viitoare
            self.save_document_types_to_json()

    def set_application_icon(self):
        """Setează iconița aplicației pentru taskbar și titlu"""
        try:
            # Calea către iconița aplicației
            if getattr(sys, 'frozen', False):
                # Dacă rulăm din executabil
                application_path = os.path.dirname(sys.executable)
            else:
                # Dacă rulăm din sursă
                application_path = os.path.dirname(os.path.abspath(__file__))
                
            icon_path = os.path.join(application_path, "icon.ico")
            
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            print(f"Eroare la setarea iconiței: {e}")

    # 2. Modificare metodă pentru încărcarea tipurilor de documente, inclusiv flagul de evidențiere
    def load_document_types(self):
        """Încarcă tipurile de documente din fișierul JSON"""
        print("\n--- Încărcare tipuri de documente ---")
        
        # Salvăm tipurile vechi pentru referință
        old_types = getattr(self, 'document_types', [])
        
        # Încărcăm din JSON
        self.load_document_types_from_json()
        
        print(f"Tipuri de documente înainte: {old_types}")
        print(f"Tipuri de documente după: {self.document_types}")
        print(f"Tipuri evidențiate: {self.highlighted_types}")
        print("--- Sfârșit încărcare tipuri de documente ---\n")

    
    def create_header(self, parent_layout):
        """Creare antet cu butoane de navigare și afișare săptămână curentă"""
        header_layout = QHBoxLayout()
        parent_layout.addLayout(header_layout)
        
        # Buton săptămâna anterioară
        prev_btn = QPushButton("←")
        prev_btn.setFixedWidth(80)
        prev_btn.setFixedHeight(50)
        prev_btn.setFont(QFont("Arial", 16))
        prev_btn.clicked.connect(self.prev_week)
        header_layout.addWidget(prev_btn)
        
        # Etichetă săptămână curentă
        self.week_label = QLabel()
        self.week_label.setFont(QFont("Arial", 18, QFont.Bold))
        self.week_label.setAlignment(Qt.AlignCenter)
        self.update_week_label()
        header_layout.addWidget(self.week_label, 1)  # 1 = stretch factor
        
        # Buton calendar pentru navigare rapidă
        calendar_btn = QPushButton("Calendar")
        calendar_btn.setFixedHeight(50)
        calendar_btn.setFont(QFont("Arial", 12))
        calendar_btn.clicked.connect(self.show_calendar_dialog)
        header_layout.addWidget(calendar_btn)
        
        # Buton adăugare tip document
        add_doc_type_btn = QPushButton("Adaugă tip document")
        add_doc_type_btn.setFixedHeight(50)
        add_doc_type_btn.setFont(QFont("Arial", 12))
        add_doc_type_btn.clicked.connect(self.add_document_type)
        header_layout.addWidget(add_doc_type_btn)
        
        # Buton săptămâna următoare
        next_btn = QPushButton("→")
        next_btn.setFixedWidth(80)
        next_btn.setFixedHeight(50)
        next_btn.setFont(QFont("Arial", 16))
        next_btn.clicked.connect(self.next_week)
        header_layout.addWidget(next_btn)
    
    def create_calendar(self, parent_layout):
        """Creare vedere calendar săptămânal"""
        # Grid pentru zile
        self.calendar_grid = QGridLayout()
        parent_layout.addLayout(self.calendar_grid, 1)  # 1 = stretch factor
        
        # Creare frame-uri pentru zile
        self.day_frames = []
        for i in range(6):  # Luni până Sâmbătă
            day_date = self.week_start + timedelta(days=i)
            self.create_day_column(i, day_date)
    
    # Modificare create_day_column pentru a evidenția ziua curentă cu o culoare diferită
    def create_day_column(self, column, day_date):
        """Creare coloană pentru o zi"""
        # Frame pentru ziua respectivă
        day_frame = QFrame()
        day_frame.setFrameStyle(QFrame.Box | QFrame.Plain)
        day_frame.setLineWidth(2)
        
        # Set minimum width for day columns to allow for proper spacing
        day_frame.setMinimumWidth(400)
        
        self.calendar_grid.addWidget(day_frame, 0, column)
        
        # Layout pentru ziua respectivă
        day_layout = QVBoxLayout(day_frame)
        day_layout.setContentsMargins(5, 5, 5, 5)
        
        # Verificăm dacă ziua curentă este astăzi
        is_today = (day_date.year == datetime.datetime.now().year and 
                    day_date.month == datetime.datetime.now().month and 
                    day_date.day == datetime.datetime.now().day)
        
        # Antet zi - frame special pentru a permite stilizarea
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        header_frame.setLineWidth(1)
        header_frame.setAutoFillBackground(True)
        
        # Stilizare specială pentru ziua curentă
        if is_today:
            # Setăm un fundal distinctiv pentru ziua curentă - albastru-violet
            palette = QPalette()
            palette.setColor(QPalette.Background, QColor("#5D4037"))  
            header_frame.setPalette(palette)
        else:
            # Fundal normal pentru celelalte zile
            palette = QPalette()
            palette.setColor(QPalette.Background, QColor("#F0F0F0"))  # Gri foarte deschis
            header_frame.setPalette(palette)
        
        day_layout.addWidget(header_frame)
        
        # Layout pentru antetul zilei
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(5, 5, 5, 5)
        
        # Antet zi
        day_name = self.day_names_ro[day_date.weekday()]
        
        # Text pentru antet - ajustat în funcție de ziua curentă
        if is_today:
            header_text = f"{day_date.day} {self.month_names_ro[day_date.month-1]}\n{day_name}"
            day_header = QLabel(header_text)
            day_header.setFont(QFont("Arial", 16, QFont.Bold))  # Font mai mare și îngroșat
            day_header.setStyleSheet("color: white;")  # Text alb pentru contrast
        else:
            header_text = f"{day_date.day} {self.month_names_ro[day_date.month-1]}\n{day_name}"
            day_header = QLabel(header_text)
            day_header.setFont(QFont("Arial", 14, QFont.Bold))
        
        day_header.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(day_header)
        
        # Zonă cu scroll pentru intervale orare
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        day_layout.addWidget(scroll_area, 1)  # 1 = stretch factor
        
        # Widget pentru intervale orare
        hours_widget = QWidget()
        scroll_area.setWidget(hours_widget)
        hours_layout = QVBoxLayout(hours_widget)
        hours_layout.setContentsMargins(0, 0, 0, 0)
        hours_layout.setSpacing(2)
        
        # Creare intervale orare
        self.create_time_slots(hours_layout, day_date)
        
        # Salvare referință la frame
        self.day_frames.append(day_frame)

    
    def create_time_slots(self, parent_layout, day_date):
        """Creare intervale orare pentru o zi, inclusiv programări flexibile"""
        # Obținem toate programările pentru ziua curentă
        all_appointments = self.get_day_appointments(day_date)
        
        # Ore de lucru de la 8 la 20
        all_hours = []
        for hour in range(8, 21):
            all_hours.append(f"{hour}:00")
            
        # Adăugăm orele flexibile din programări
        for app in all_appointments:
            time_str = app[1]  # coloana time din baza de date
            if time_str not in all_hours:
                all_hours.append(time_str)
        
        # Sortăm toate orele
        all_hours.sort(key=self.sort_time_key)
        
        # Verificăm dacă există o programare de tip "Liber" în această zi
        free_time_starts_from = None
        for app in all_appointments:
            if app[3] == "Liber" and app[6] != 'deleted':  # Verifică tipul documentului și statusul
                free_time_starts_from = app[1]  # Ora de la care începe programul liber
                break
        
        # Creăm intervalele orare pentru fiecare oră din listă
        for time_str in all_hours:
            # Determinăm dacă această oră este după ora de început a programului liber
            is_after_free_time = False
            if free_time_starts_from:
                # Comparăm orele folosind funcția noastră de sortare
                is_after_free_time = self.sort_time_key(time_str) >= self.sort_time_key(free_time_starts_from)
            
            self.create_time_slot(parent_layout, day_date, time_str, is_after_free_time)
    
    def create_time_slot(self, parent_layout, day_date, time_str, is_free_time=False):
        """Creare un singur interval orar pentru o oră specifică"""
        time_slot_frame = QFrame()
        time_slot_frame.setFrameStyle(QFrame.Box | QFrame.Plain)
        time_slot_frame.setLineWidth(1)
        time_slot_frame.setMinimumHeight(80)  # Mărirea spațiului pentru programări
        
        # Determinăm dacă e oră fixă sau flexibilă
        is_full_hour = time_str.endswith(":00")
        
        # Culoare de fundal diferită în funcție de mai mulți factori
        if is_free_time:
            # Dacă este după ora marcată ca "Liber", folosim fundal roșu (aceeași culoare ca și cea pentru "Liber")
            base_color = "#FF5252"  # Roșu pentru orele după "Liber" - aceeași culoare ca și programarea "Liber"
        elif is_full_hour:
            # Rânduri alternative gri deschis pentru ore pare/impare
            hour = int(time_str.split(":")[0])
            if hour % 2 == 0:  # Ore pare (8, 10, 12...)
                base_color = "#F5F5F5"  # Gri foarte deschis pentru orele pare
            else:  # Ore impare (9, 11, 13...)
                base_color = "#FFFFFF"  # Alb pentru orele impare
        else:
            # Fundal specific pentru ore flexibile
            base_color = "#F0F8FF"  # Bleu deschis pentru ore flexibile
        
        # Setare culoare implicită pentru rândul curent
        try:
            palette = QPalette()
            palette.setColor(QPalette.Background, QColor(base_color))
            time_slot_frame.setAutoFillBackground(True)
            time_slot_frame.setPalette(palette)
        except Exception:
            time_slot_frame.setStyleSheet(f"QFrame {{ background-color: {base_color}; }}")
        
        # Verificare dacă există programare pentru a suprascrie fundalul
        appointments = self.get_appointments(day_date, time_str)
        
        # Filtrăm lista de programări pentru a afișa doar cele active
        active_appointments = [app for app in appointments if app[6] != 'deleted']
        deleted_appointments = [app for app in appointments if app[6] == 'deleted']
        
        # Setăm fundalul în funcție de tipul programării
        if active_appointments:
            appointment = active_appointments[0]
            status = appointment[6]
            doc_type = appointment[3]
            
            # Verificăm dacă acest tip de document trebuie evidențiat cu verde
            should_highlight = False
            is_free_time = doc_type == "Liber"  # Verifică dacă este tipul special "Liber"

            if not is_free_time and hasattr(self, 'highlighted_types'):
                if doc_type in self.highlighted_types:
                    should_highlight = self.highlighted_types[doc_type]
            else:
                # Încercăm să interogăm baza de date direct
                try:
                    self.cursor.execute('SELECT highlight FROM document_types WHERE name = ?', (doc_type,))
                    result = self.cursor.fetchone()
                    if result:
                        should_highlight = bool(result[0])
                except Exception:
                    pass

            # Aplicăm culoarea în funcție de setarea de evidențiere sau dacă este "Liber"
            try:
                palette = QPalette()
                
                if is_free_time:
                    # Roșu pentru marcarea timpului liber
                    palette.setColor(QPalette.Background, QColor("#FF5252"))  # Roșu pentru "Liber"
                elif should_highlight:
                    # Verde mai intens pentru tipurile evidențiate
                    palette.setColor(QPalette.Background, QColor("#81C784"))
                else:
                    # Galben pal pentru tipurile neevidentiate
                    palette.setColor(QPalette.Background, QColor("#FFF9C4"))  # Galben foarte pal
                
                time_slot_frame.setAutoFillBackground(True)
                time_slot_frame.setPalette(palette)
            except Exception:
                # Fallback
                if is_free_time:
                    time_slot_frame.setStyleSheet("QFrame { background-color: #FF5252; }")
                elif should_highlight:
                    time_slot_frame.setStyleSheet("QFrame { background-color: #81C784; }")
                else:
                    time_slot_frame.setStyleSheet("QFrame { background-color: #FFF9C4; }")
                
                time_slot_frame.setAutoFillBackground(True)
                time_slot_frame.setPalette(palette)
            except Exception:
                # Fallback
                if should_highlight:
                    time_slot_frame.setStyleSheet("QFrame { background-color: #81C784; }")
                else:
                    time_slot_frame.setStyleSheet("QFrame { background-color: #FFF9C4; }")
        
        parent_layout.addWidget(time_slot_frame)
        
        # Layout orizontal pentru conținutul principal
        time_slot_layout = QHBoxLayout(time_slot_frame)
        time_slot_layout.setContentsMargins(2, 2, 2, 2)
        
        # Layout vertical pentru oră și butoane
        hour_button_layout = QVBoxLayout()
        hour_button_layout.setContentsMargins(0, 0, 0, 0)
        hour_button_layout.setSpacing(2)
        time_slot_layout.addLayout(hour_button_layout)
        
        # Etichetă oră
        hour_label = QLabel(time_str)
        hour_label.setFixedWidth(60)
        hour_label.setFont(QFont("Arial", 11))
        hour_button_layout.addWidget(hour_label)
        
        # Verificăm mai întâi dacă există programări active
        if active_appointments:
            # Afișare programare existentă activă
            appointment = active_appointments[0]  # Prima programare activă
            
            # Verificăm statusul programării
            status = appointment[6]  # 'active' sau 'modified'
            
            # Butonul Edit sub oră
            edit_btn = QPushButton("Edit")
            edit_btn.setFixedWidth(50)
            edit_btn.setFixedHeight(30)
            edit_btn.setFont(QFont("Arial", 10))
            edit_btn.clicked.connect(
                lambda checked, d=day_date, t=time_str, a_id=appointment[0]: 
                self.edit_appointment(d, t, a_id)
            )
            hour_button_layout.addWidget(edit_btn)
            
            # Nu mai adăugăm butonul Delete aici - a fost eliminat
            
            # Spațiu pentru aliniere verticală
            hour_button_layout.addStretch(1)
            
            # Creăm un widget care va conține toate informațiile programării
            appointment_widget = QWidget()
            # Widget-ul interior trebuie să fie transparent
            appointment_widget.setStyleSheet("background-color: transparent;")
            
            appointment_layout = QVBoxLayout(appointment_widget)
            appointment_layout.setContentsMargins(0, 0, 0, 0)
            time_slot_layout.addWidget(appointment_widget, 1)  # 1 = stretch factor
            
            # Tip document - cu word wrap adaptiv
            doc_type_label = QLabel(appointment[3])
            doc_type_label.setStyleSheet("color: blue; background-color: transparent;")
            doc_type_label.setFont(QFont("Arial", 12))
            doc_type_label.setWordWrap(True)  # Activăm word wrap
            
            # Folosim înălțime adaptivă în funcție de lungimea textului
            if len(appointment[3]) > 45:  # Valoare modificată de la 30 la 45
                doc_type_label.setMinimumHeight(40)  # Înălțime pentru două rânduri
            else:
                doc_type_label.setMinimumHeight(20)  # Înălțime pentru un rând
                
            appointment_layout.addWidget(doc_type_label)
            
            # Nume client
            client_label = QLabel(appointment[2])
            client_label.setStyleSheet("background-color: transparent;")
            client_label.setFont(QFont("Arial", 12, QFont.Bold))
            appointment_layout.addWidget(client_label)
            
            # Verificăm dacă există observații și afișăm un indicator
            has_observations = False
            observations_text = ""
            
            # Verificăm dacă coloana observations există în rezultat
            if len(appointment) >= 12 and appointment[11] is not None and appointment[11].strip() != "":
                has_observations = True
                observations_text = appointment[11]
            
            # Adăugăm câmpul de observații dacă există
            if has_observations:
                observations_label = QLabel("Observații")
                observations_label.setStyleSheet("color: #D81B60; background-color: #FFECEF; border: 1px solid #D81B60; border-radius: 3px; padding: 2px 4px;")
                observations_label.setFixedWidth(100)
                observations_label.setToolTip(observations_text)
                appointment_layout.addWidget(observations_label)
            
            # Afișăm doar ultima informație despre statusul programării
            if status == 'modified':
                # Informații despre ultima modificare
                modified_info = QLabel(f"Modificat de {appointment[7]} la {appointment[8][:16]}")
                modified_info.setFont(QFont("Arial", 9))
                modified_info.setStyleSheet("color: #006400; background-color: transparent;")
                appointment_layout.addWidget(modified_info)
            else:
                # Doar informații despre creare
                created_info = QLabel(f"Creat de {appointment[5]} la {appointment[4][:16]}")
                created_info.setStyleSheet("background-color: transparent;")
                created_info.setFont(QFont("Arial", 9))
                appointment_layout.addWidget(created_info)
            
        elif deleted_appointments:
            # Avem programări șterse, dar nu active - afișăm info despre ștergere și buton +
            deleted_appointment = deleted_appointments[0]
            
            # Butonul + sub oră
            add_btn = QPushButton("+")
            add_btn.setFixedWidth(50)
            add_btn.setFixedHeight(30)
            add_btn.setFont(QFont("Arial", 14))
            add_btn.clicked.connect(
                lambda checked, d=day_date, t=time_str: self.add_appointment(d, t)
            )
            hour_button_layout.addWidget(add_btn)
            hour_button_layout.addStretch(1)
            
            # Widget pentru informații despre programarea ștearsă
            deleted_widget = QWidget()
            deleted_layout = QVBoxLayout(deleted_widget)
            deleted_layout.setContentsMargins(0, 0, 0, 0)
            time_slot_layout.addWidget(deleted_widget, 1)  # 1 = stretch factor
            
            # Informații despre ștergere
            info_text = f"[ȘTERS] {deleted_appointment[3]} - {deleted_appointment[2]}"
            deleted_info = QLabel(info_text)
            deleted_info.setStyleSheet("color: #9E9E9E; font-style: italic; background-color: transparent;")
            deleted_info.setFont(QFont("Arial", 10))
            deleted_layout.addWidget(deleted_info)
            
            # Adăugăm informații despre cine a șters programarea
            deleted_by_info = QLabel(f"Șters de {deleted_appointment[9]} la {deleted_appointment[10][:16]}")
            deleted_by_info.setFont(QFont("Arial", 9))
            deleted_by_info.setStyleSheet("color: #9E9E9E; font-style: italic; background-color: transparent;")
            deleted_layout.addWidget(deleted_by_info)
            
        else:
            # Nu există nicio programare - afișăm doar butonul +
            add_btn = QPushButton("+")
            add_btn.setFixedWidth(50)
            add_btn.setFixedHeight(30)
            add_btn.setFont(QFont("Arial", 14))
            add_btn.clicked.connect(
                lambda checked, d=day_date, t=time_str: self.add_appointment(d, t)
            )
            hour_button_layout.addWidget(add_btn)
            hour_button_layout.addStretch(1)
            
            # Spațiu gol în dreapta
            empty_widget = QWidget()
            time_slot_layout.addWidget(empty_widget, 1)  # 1 = stretch factor

    def sort_time_key(self, time_str):
        """Funcție pentru sortarea corectă a orelor în format string"""
        try:
            hour, minute = map(int, time_str.split(':'))
            return hour * 60 + minute  # Convertim totul în minute pentru sortare
        except:
            # Fallback în caz de eroare
            return 0
    
    def get_day_appointments(self, day):
        """Obține toate programările pentru o zi specifică"""
        self.cursor.execute(
            '''SELECT id, time, client_name, document_type, created_at, computer_name, 
                     status, modified_by, modified_at, deleted_by, deleted_at, observations 
               FROM appointments 
               WHERE day = ? 
               ORDER BY time''',  # Sortare după oră
            (day.strftime('%Y-%m-%d'),)
        )
        return self.cursor.fetchall()
    
    def add_appointment(self, day, time):
        """Adăugare programare nouă"""
        dialog = AddEditAppointmentDialog(
            self, day, time, document_types=self.document_types
        )
        
        if dialog.exec_() == QDialog.Accepted:
            values = dialog.get_values()
            
            # Verificăm dacă tipul de document este "Liber" și clientul nu a fost completat
            if values['document_type'] == "Liber" and (not values['client_name'] or values['client_name'].strip() == ""):
                values['client_name'] = "N/A"  # Completăm automat cu "N/A" pentru programările de tip "Liber"
                
            self.save_appointment(day, values['time'], values['client_name'], values['document_type'], values['observations'])
    
    def edit_appointment(self, day, time, appointment_id):
        """Editare programare existentă"""
        # Obținere date programare curentă
        self.cursor.execute(
            'SELECT client_name, document_type, time, observations FROM appointments WHERE id = ?',
            (appointment_id,)
        )
        appointment = self.cursor.fetchone()
        
        if not appointment:
            QMessageBox.critical(self, "Eroare", "Programarea nu a fost găsită.")
            return
        
        # Deschidem dialogul de editare cu toate câmpurile
        observations = appointment[3] if len(appointment) > 3 and appointment[3] else ""
        dialog = AddEditAppointmentDialog(
            self, day, appointment[2], appointment[0], appointment[1], 
            document_types=self.document_types, edit_mode=True, observations=observations,
            appointment_id=appointment_id  # Transmitem ID-ul programării
        )
        
        # Conectăm butonul de ștergere dacă există
        if hasattr(dialog, 'delete_btn'):
            dialog.delete_btn.clicked.connect(
                lambda: self.handle_delete_from_dialog(appointment_id, dialog)
            )
        
        if dialog.exec_() == QDialog.Accepted:
            values = dialog.get_values()
            self.update_appointment(appointment_id, values['client_name'], values['document_type'], values['time'], values['observations'])
    
    def handle_delete_from_dialog(self, appointment_id, dialog):
        """Gestionează ștergerea din dialogul de editare"""
        reply = QMessageBox.question(
            dialog,  # Folosim dialogul ca părinte
            "Confirmare", 
            "Sigur doriți să ștergeți această programare?",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Marcăm programarea ca ștearsă
            self.cursor.execute(
                '''UPDATE appointments 
                   SET status = 'deleted', 
                       deleted_by = ?, 
                       deleted_at = CURRENT_TIMESTAMP 
                   WHERE id = ?''', 
                (self.computer_name, appointment_id)
            )
            self.conn.commit()
            
            # Închidem dialogul și actualizăm afișarea
            dialog.reject()  # Folosim reject() pentru a închide dialogul
            self.refresh_calendar()

    def save_appointment(self, day, time, client_name, doc_type, observations=""):
        """Salvare programare nouă în baza de date"""
        if not client_name or not doc_type or not time:
            QMessageBox.critical(self, "Eroare", "Vă rugăm completați toate câmpurile.")
            return
        
        # Validare format oră
        if not self.validate_time_format(time):
            QMessageBox.critical(self, "Eroare", "Format oră invalid. Folosiți formatul HH:MM (exemplu: 12:30).")
            return
        
        self.cursor.execute(
            'INSERT INTO appointments (day, time, client_name, document_type, computer_name, status, observations) VALUES (?, ?, ?, ?, ?, "active", ?)',
            (day.strftime('%Y-%m-%d'), time, client_name, doc_type, self.computer_name, observations)
        )
        self.conn.commit()
        
        self.refresh_calendar()
    
    def update_appointment(self, appointment_id, client_name, doc_type, time, observations=""):
        """Actualizare programare existentă în baza de date"""
        if not client_name or not doc_type or not time:
            QMessageBox.critical(self, "Eroare", "Vă rugăm completați toate câmpurile.")
            return
        
        # Validare format oră
        if not self.validate_time_format(time):
            QMessageBox.critical(self, "Eroare", "Format oră invalid. Folosiți formatul HH:MM (exemplu: 12:30).")
            return
        
        self.cursor.execute(
            '''UPDATE appointments 
               SET client_name = ?, 
                   document_type = ?, 
                   time = ?,
                   status = 'modified', 
                   modified_by = ?, 
                   modified_at = CURRENT_TIMESTAMP,
                   observations = ?
               WHERE id = ?''',
            (client_name, doc_type, time, self.computer_name, observations, appointment_id)
        )
        self.conn.commit()
        
        self.refresh_calendar()
    
    def validate_time_format(self, time_str):
        """Validează formatul orei (HH:MM)"""
        try:
            # Verifică dacă formatul este corect
            if ":" not in time_str:
                return False
            
            hour, minute = map(int, time_str.split(':'))
            
            # Verifică dacă ora și minutul sunt în intervalul valid
            if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                return False
                
            return True
        except:
            return False

    def get_appointments(self, day, time):
        """Obținere programări pentru o zi și oră specifice"""
        try:
            self.cursor.execute(
                '''SELECT id, day, client_name, document_type, created_at, computer_name, 
                         status, modified_by, modified_at, deleted_by, deleted_at, observations 
                   FROM appointments 
                   WHERE day = ? AND time = ? 
                   ORDER BY status, created_at DESC''',
                (day.strftime('%Y-%m-%d'), time)
            )
        except sqlite3.OperationalError:
            # Dacă interogarea eșuează (de ex. coloanele noi nu există încă),
            # folosim o interogare simplificată care funcționează cu structura veche
            self.cursor.execute(
                '''SELECT id, day, client_name, document_type, created_at, computer_name,
                         'active' as status, NULL as modified_by, NULL as modified_at, 
                         NULL as deleted_by, NULL as deleted_at, NULL as observations
                   FROM appointments 
                   WHERE day = ? AND time = ? 
                   ORDER BY created_at DESC''',
                (day.strftime('%Y-%m-%d'), time)
            )
            
        return self.cursor.fetchall()
    
    def delete_appointment(self, appointment_id):
        """Marcarea unei programări ca ștearsă (nu o ștergem fizic din baza de date)"""
        reply = QMessageBox.question(
            self, 
            "Confirmare", 
            "Sigur doriți să ștergeți această programare?",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # In loc să ștergeți, actualizați statusul și adăugați informații despre ștergere
            self.cursor.execute(
                '''UPDATE appointments 
                   SET status = 'deleted', 
                       deleted_by = ?, 
                       deleted_at = CURRENT_TIMESTAMP 
                   WHERE id = ?''', 
                (self.computer_name, appointment_id)
            )
            self.conn.commit()
            self.refresh_calendar()
            
    def restore_appointment(self, appointment_id):
        """Restaurează o programare ștearsă"""
        self.cursor.execute(
            "UPDATE appointments SET status = 'active', deleted_by = NULL, deleted_at = NULL WHERE id = ?", 
            (appointment_id,)
        )
        self.conn.commit()
        self.refresh_calendar()
    
    def add_document_type(self):
        """Adăugare sau gestionare tip document cu layout pe două coloane și salvare în JSON"""
        print("\n--- Începerea procesului de adăugare tip document ---")
        
        # Creăm un dialog mai complex pentru gestionarea tipurilor de documente
        dialog = QDialog(self)
        dialog.setWindowTitle("Gestionare Tipuri de Documente")
        dialog.setMinimumWidth(900)  # Mărit pentru a acomoda două coloane
        dialog.setMinimumHeight(600)
        
        layout = QVBoxLayout(dialog)
        
        # Titlu
        title_label = QLabel("Tipuri de Documente Disponibile")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Descriere
        description = QLabel("Bifați tipurile de documente care trebuie evidențiate cu fundal verde.\n"
                             "Pentru a schimba ordinea sau a redenumi tipurile, editați fișierul document_types.json.")
        description.setAlignment(Qt.AlignCenter)
        layout.addWidget(description)
        
        # Facem un scroll area pentru tabelul de tipuri de documente
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(400)
        layout.addWidget(scroll_area)
        
        # Widget-ul interior pentru scroll area
        scroll_content = QWidget()
        scroll_area.setWidget(scroll_content)
        
        # Folosim un grid layout pentru a dispune tipurile pe două coloane
        grid_layout = QGridLayout(scroll_content)
        grid_layout.setColumnStretch(0, 1)  # Prima coloană pentru nume
        grid_layout.setColumnStretch(1, 0)  # A doua coloană pentru checkbox
        grid_layout.setColumnStretch(2, 1)  # A treia coloană pentru nume (a doua serie)
        grid_layout.setColumnStretch(3, 0)  # A patra coloană pentru checkbox (a doua serie)
        
        # Titluri pentru coloane
        col1_header = QLabel("Tip Document")
        col1_header.setFont(QFont("Arial", 12, QFont.Bold))
        grid_layout.addWidget(col1_header, 0, 0)
        
        col1_highlight = QLabel("Evidențiere")
        col1_highlight.setFont(QFont("Arial", 12, QFont.Bold))
        grid_layout.addWidget(col1_highlight, 0, 1)
        
        col2_header = QLabel("Tip Document")
        col2_header.setFont(QFont("Arial", 12, QFont.Bold))
        grid_layout.addWidget(col2_header, 0, 2)
        
        col2_highlight = QLabel("Evidențiere")
        col2_highlight.setFont(QFont("Arial", 12, QFont.Bold))
        grid_layout.addWidget(col2_highlight, 0, 3)
        
        # Calculăm numărul de rânduri pentru fiecare coloană
        total_types = len(self.document_types)
        rows_per_column = (total_types + 1) // 2  # Împărțim în două coloane (rotunjit în sus)
        
        # Dicționar pentru a ține evidența checkbox-urilor
        checkboxes = {}
        
        # Populăm grid-ul cu tipurile existente
        for i, doc_type in enumerate(self.document_types):
            # Determinăm în care coloană va fi acest element
            if i < rows_per_column:
                # Prima coloană
                col_offset = 0
                row = i + 1  # +1 pentru că rândul 0 are header-ele
            else:
                # A doua coloană
                col_offset = 2
                row = (i - rows_per_column) + 1  # +1 pentru header
                
            # Verificăm dacă tipul este evidențiat
            is_highlighted = self.highlighted_types.get(doc_type, False)
            
            # Nume tip document
            name_label = QLabel(doc_type)
            name_label.setFont(QFont("Arial", 11))
            name_label.setWordWrap(True)  # Permitem word wrap pentru nume lungi
            grid_layout.addWidget(name_label, row, col_offset)
            
            # Checkbox pentru evidențiere
            checkbox = QCheckBox()
            checkbox.setChecked(is_highlighted)
            
            # Dacă este bifat, adaugă un exemplu de fundal verde
            if is_highlighted:
                name_label.setStyleSheet("background-color: #81C784; padding: 5px;")
            
            grid_layout.addWidget(checkbox, row, col_offset + 1, Qt.AlignCenter)
            checkboxes[doc_type] = checkbox
        
        # Adăugare separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)
        
        # Formular pentru adăugarea unui nou tip de document
        add_form_layout = QHBoxLayout()
        layout.addLayout(add_form_layout)
        
        add_label = QLabel("Adaugă Tip Document Nou:")
        add_label.setFont(QFont("Arial", 11))
        add_form_layout.addWidget(add_label)
        
        new_doc_type_entry = QLineEdit()
        new_doc_type_entry.setFont(QFont("Arial", 11))
        add_form_layout.addWidget(new_doc_type_entry, 1)  # 1 = stretch factor
        
        new_highlight_checkbox = QCheckBox("Evidențiere")
        add_form_layout.addWidget(new_highlight_checkbox)
        
        add_button = QPushButton("Adaugă")
        add_button.setFont(QFont("Arial", 11))
        add_form_layout.addWidget(add_button)
        
        # Butoane dialog
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        ok_button = button_box.button(QDialogButtonBox.Ok)
        ok_button.setText("Salvează")
        ok_button.setFont(QFont("Arial", 12))
        
        cancel_button = button_box.button(QDialogButtonBox.Cancel)
        cancel_button.setText("Anulează")
        cancel_button.setFont(QFont("Arial", 12))
        
        layout.addWidget(button_box)
        
        # Funcție pentru adăugarea unui nou tip de document
        def add_new_doc_type():
            doc_type_name = new_doc_type_entry.text().strip()
            print(f"\nÎncercare adăugare tip document nou: '{doc_type_name}'")
            
            if not doc_type_name:
                print("Eroare: nume gol")
                QMessageBox.warning(dialog, "Avertisment", "Introduceți un nume pentru tipul de document.")
                return
            
            if doc_type_name in self.document_types:
                print("Eroare: tip existent")
                QMessageBox.warning(dialog, "Avertisment", "Acest tip de document există deja.")
                return
            
            try:
                # Adăugare în lista de tipuri
                self.document_types.append(doc_type_name)
                
                # Actualizăm highlighted_types
                self.highlighted_types[doc_type_name] = new_highlight_checkbox.isChecked()
                
                # Reconstruim interfața
                # Pentru simplitate, reîncărcăm dialogul
                QMessageBox.information(dialog, "Succes", 
                                      "Tip document adăugat cu succes. Închideți și redeschideți dialogul pentru a vedea actualizările.")
                
                # Golire câmp
                new_doc_type_entry.clear()
                new_highlight_checkbox.setChecked(False)
                
            except Exception as e:
                print(f"Eroare neașteptată: {e}")
                QMessageBox.critical(dialog, "Eroare", f"Eroare la adăugarea tipului de document: {e}")
        
        # Conectare butoane
        add_button.clicked.connect(add_new_doc_type)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        
        # Execută dialogul
        result = dialog.exec_()
        print(f"\nDialog închis cu rezultat: {result} (1=Acceptat, 0=Respins)")
        
        if result == QDialog.Accepted:
            # Salvează setările de evidențiere
            print("\nSalvare setări evidențiere:")
            for name, checkbox in checkboxes.items():
                is_checked = checkbox.isChecked()
                print(f"  - {name}: {'bifat' if is_checked else 'nebifat'}")
                self.highlighted_types[name] = is_checked
            
            # Salvare în JSON
            self.save_document_types_to_json()
            
            # Actualizează afișarea
            print("Actualizare calendar")
            self.refresh_calendar()
        
        print("--- Sfârșit proces adăugare tip document ---\n")
    
    def prev_week(self):
        """Navigare la săptămâna anterioară"""
        self.week_start -= timedelta(days=7)
        self.update_week_label()
        self.refresh_calendar()
    
    def next_week(self):
        """Navigare la săptămâna următoare"""
        self.week_start += timedelta(days=7)
        self.update_week_label()
        self.refresh_calendar()
    
    def update_week_label(self):
        """Actualizare etichetă săptămână cu datele săptămânii curente"""
        week_end = self.week_start + timedelta(days=6)
        text = f"Săptămâna {self.week_start.day} {self.month_names_ro[self.week_start.month-1]} - {week_end.day} {self.month_names_ro[week_end.month-1]} {week_end.year}"
        self.week_label.setText(text)
    
    def refresh_calendar(self):
        """Reîmprospătare vedere calendar"""
        # Ștergere coloane de zi existente
        for i in reversed(range(self.calendar_grid.count())): 
            item = self.calendar_grid.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    widget.deleteLater()
        
        # Golire listă frame-uri zile
        self.day_frames.clear()
        
        # Recreare calendar
        for i in range(6):  # Luni până Sâmbătă
            day_date = self.week_start + timedelta(days=i)
            self.create_day_column(i, day_date)
    
    def create_footer(self, parent_layout):
        """Creare subsol cu informații despre autor"""
        footer_frame = QFrame()
        footer_frame.setFrameStyle(QFrame.StyledPanel)
        footer_frame.setLineWidth(1)
        footer_frame.setFixedHeight(40)
        parent_layout.addWidget(footer_frame)
        
        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setContentsMargins(10, 5, 10, 5)
        
        # Spațiu gol în stânga
        spacer = QWidget()
        footer_layout.addWidget(spacer, 1)  # 1 = stretch factor
        
        # Numele autorului în dreapta
        author_label = QLabel("Mihai Mereu")
        author_label.setFont(QFont("Arial", 10, QFont.Bold))
        author_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        footer_layout.addWidget(author_label)
        
    def show_calendar_dialog(self):
        """Afișează un dialog cu calendar pentru navigare rapidă"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Selectează data")
        dialog.setMinimumWidth(800)  # Mărit de la 400 la 800
        dialog.setMinimumHeight(600)  # Adăugat înălțime minimă
        
        layout = QVBoxLayout(dialog)
        
        # Calendar
        calendar_widget = QCalendarWidget()
        calendar_widget.setGridVisible(True)
        calendar_widget.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        calendar_widget.setHorizontalHeaderFormat(QCalendarWidget.LongDayNames)  # Nume complete pentru zile
        
        # Setăm stilul pentru calendar pentru a-l face mai mare
        calendar_widget.setStyleSheet("""
            QCalendarWidget QToolButton {
                height: 50px;
                width: 150px;
                font-size: 18px;
            }
            QCalendarWidget QMenu {
                font-size: 18px;
            }
            QCalendarWidget QSpinBox {
                font-size: 18px;
            }
            QCalendarWidget QAbstractItemView:enabled {
                font-size: 18px;
                height: 50px;
            }
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                height: 60px;
            }
        """)
        
        # Facem ca celulele calendarului să fie mai mari
        calendar_widget.setMinimumSize(780, 500)
        
        # Setează data curentă ca data selectată implicit
        calendar_widget.setSelectedDate(QDate(self.week_start.year, self.week_start.month, self.week_start.day))
        
        layout.addWidget(calendar_widget)
        
        # Butoane
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        
        # Mărim și butoanele
        ok_button = button_box.button(QDialogButtonBox.Ok)
        ok_button.setFont(QFont("Arial", 14))
        ok_button.setMinimumSize(120, 40)
        
        cancel_button = button_box.button(QDialogButtonBox.Cancel)
        cancel_button.setFont(QFont("Arial", 14))
        cancel_button.setMinimumSize(120, 40)
        
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        if dialog.exec_() == QDialog.Accepted:
            selected_date = calendar_widget.selectedDate().toPyDate()
            # Convertim la datetime
            selected_date = datetime.datetime.combine(selected_date, datetime.time())
            # Calculăm începutul săptămânii pentru data selectată
            self.week_start = selected_date - timedelta(days=selected_date.weekday())
            self.update_week_label()
            self.refresh_calendar()

    def load_document_types_from_json(self):
        """Încarcă tipurile de documente din fișierul JSON"""
        json_file_path = 'document_types.json'
        
        try:
            # Verificăm dacă fișierul există
            if os.path.exists(json_file_path):
                with open(json_file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    
                    # Verificăm dacă avem structura așteptată în JSON
                    if isinstance(data, dict) and 'document_types' in data:
                        print(f"Încărcare tipuri documente din JSON: {len(data['document_types'])} tipuri găsite")
                        
                        # Actualizăm lista de tipuri de documente
                        self.document_types = data['document_types']
                        
                        # Încărcăm setările de evidențiere dacă există
                        if 'highlighted_types' in data:
                            self.highlighted_types = data['highlighted_types']
                        
                        # Încărcăm ultima selecție dacă există
                        if 'last_selection' in data:
                            self.last_doc_type_selection = data['last_selection']
                        
                        return True
            
            # Dacă ajungem aici, fie fișierul nu există, fie nu are formatul corect
            return False
            
        except Exception as e:
            print(f"Eroare la încărcarea tipurilor de documente din JSON: {e}")
            return False

    def save_document_types_to_json(self):
        """Salvează tipurile de documente în fișierul JSON"""
        json_file_path = 'document_types.json'
        
        try:
            # Construim dicționarul de date pentru JSON
            data = {
                'document_types': self.document_types,
                'highlighted_types': self.highlighted_types
            }
            
            # Adăugăm ultima selecție dacă există
            if hasattr(self, 'last_doc_type_selection'):
                data['last_selection'] = self.last_doc_type_selection
            
            # Salvăm în fișier
            with open(json_file_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
                
            print(f"Tipuri de documente salvate cu succes în {json_file_path}")
            return True
            
        except Exception as e:
            print(f"Eroare la salvarea tipurilor de documente în JSON: {e}")
            return False

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Aplicare stil
    app.setStyle("Fusion")
    
    window = NotarialScheduler()
    window.show()
    
    sys.exit(app.exec_())