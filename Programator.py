import requests
from bs4 import BeautifulSoup
import re
import json
import os
import sys
import sqlite3
import socket
import datetime
import atexit
import signal
from datetime import timedelta
import calendar
from PyQt5.QtWidgets import (QMenu, QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QGridLayout, QLabel, QPushButton,
                            QFrame, QScrollArea, QComboBox, QLineEdit,
                            QDialog, QDialogButtonBox, QMessageBox, QFormLayout,
                            QCalendarWidget, QCheckBox, QTextEdit, QToolTip,                          # --- ÎNCEPUT IMPORTURI LIPSA ---
                            QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
                            QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt, QSize, QDate, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon, QTextCharFormat

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

class EventsManagementDialog(QDialog):
    """Dialog pentru gestionarea evenimentelor (aniversări, memento-uri etc.)"""
    def __init__(self, parent_scheduler):
        super().__init__(parent_scheduler)
        self.parent_scheduler = parent_scheduler # Păstrăm o referință la fereastra principală

        self.setWindowTitle("Gestionare Evenimente")
        self.setMinimumSize(1000, 700)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)

        # Titlu
        title_label = QLabel("Gestionare Evenimente")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Formular pentru adăugare/editare
        form_group = QWidget() # Folosim un QWidget pentru a grupa elementele formularului
        form_layout = QFormLayout(form_group)
        form_layout.setLabelAlignment(Qt.AlignRight)
        form_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        form_layout.setSpacing(10) # Spațiere între label și câmp

        # Data evenimentului
        self.date_edit = QCalendarWidget(self)
        self.date_edit.setGridVisible(True)
        self.date_edit.setMaximumHeight(300) # O înălțime rezonabilă pentru calendar
        self.date_edit.setMinimumWidth(400) # Lățime minimă
        form_layout.addRow("Data eveniment:", self.date_edit)

        # Descriere eveniment
        self.description_edit = QTextEdit(self)
        self.description_edit.setFont(QFont("Arial", 11))
        self.description_edit.setPlaceholderText("Introduceți descrierea evenimentului (ex: Ziua X, Expirare ITP)")
        self.description_edit.setFixedHeight(80)
        form_layout.addRow("Descriere:", self.description_edit)

        # Recurență
        self.recurring_checkbox = QCheckBox("Eveniment recurent (anual)", self)
        self.recurring_checkbox.setFont(QFont("Arial", 11))
        form_layout.addRow(self.recurring_checkbox) # Adăugăm direct checkbox-ul

        layout.addWidget(form_group) # Adăugăm widget-ul grup la layout-ul principal

        # Butoane pentru formular
        form_buttons_layout = QHBoxLayout()
        self.add_event_btn = QPushButton(QIcon.fromTheme("list-add", QIcon("fallback_add_icon.png")), "Adaugă Eveniment Nou") # Adaugă un fallback icon
        self.add_event_btn.setFont(QFont("Arial", 11, QFont.Bold))
        self.add_event_btn.setIconSize(QSize(24,24))
        self.add_event_btn.clicked.connect(self.add_event)
        form_buttons_layout.addWidget(self.add_event_btn)

        self.save_event_btn = QPushButton(QIcon.fromTheme("document-save", QIcon("fallback_save_icon.png")), "Salvează Modificări")
        self.save_event_btn.setFont(QFont("Arial", 11, QFont.Bold))
        self.save_event_btn.setIconSize(QSize(24,24))
        self.save_event_btn.setEnabled(False) # Inițial dezactivat
        self.save_event_btn.clicked.connect(self.save_event)
        form_buttons_layout.addWidget(self.save_event_btn)

        self.clear_form_btn = QPushButton(QIcon.fromTheme("edit-clear", QIcon("fallback_clear_icon.png")), "Curăță Formular")
        self.clear_form_btn.setFont(QFont("Arial", 11))
        self.clear_form_btn.setIconSize(QSize(24,24))
        self.clear_form_btn.clicked.connect(self.clear_form)
        form_buttons_layout.addWidget(self.clear_form_btn)

        form_buttons_layout.addStretch(1) # Împinge butoanele la stânga
        layout.addLayout(form_buttons_layout)


        # Tabel pentru afișarea evenimentelor
        self.events_table = QTableWidget(self)
        self.events_table.setColumnCount(5) # ID, Data, Descriere, Recurent, Acțiuni
        self.events_table.setHorizontalHeaderLabels(["ID", "Data", "Descriere", "Recurent", "Acțiuni"])
        
        # Setarea modului de redimensionare pentru coloane
        self.events_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch) # ID (va fi ascuns)
        self.events_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents) # Data
        self.events_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch) # Descriere - ia spațiul rămas
        self.events_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents) # Recurent
        self.events_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents) # Acțiuni

        self.events_table.setColumnHidden(0, True) # Ascundem coloana ID

        self.events_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.events_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.events_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.events_table.itemSelectionChanged.connect(self.load_selected_event_to_form)
        self.events_table.setSortingEnabled(True)

        layout.addWidget(self.events_table)

        # Butoane de dialog (Închide)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Close)
        close_button = self.button_box.button(QDialogButtonBox.Close)
        if close_button: # Verifică dacă butonul a fost creat
            close_button.setText("Închide")
            close_button.setFont(QFont("Arial", 11, QFont.Bold))
            close_button.setMinimumSize(120, 40)

        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.current_event_id = None
        self.load_events_to_table()
        self.clear_form()

    def load_events_to_table(self):
        self.events_table.setSortingEnabled(False) # Dezactivăm sortarea pe durata încărcării
        self.events_table.setRowCount(0)
        events = self.parent_scheduler.get_all_events()

        for event_data in events:
            row_position = self.events_table.rowCount()
            self.events_table.insertRow(row_position)

            event_id, event_date_str, description, is_recurring, _, _ = event_data

            try:
                date_obj = datetime.datetime.strptime(event_date_str, '%Y-%m-%d').date()
                formatted_date_str = date_obj.strftime('%d ')
                month_index = date_obj.month - 1
                if 0 <= month_index < len(self.parent_scheduler.month_names_ro):
                    formatted_date_str += self.parent_scheduler.month_names_ro[month_index]
                else: # Fallback dacă indexul e greșit
                    formatted_date_str += date_obj.strftime('%B') # Numele lunii în engleză
                formatted_date_str += date_obj.strftime(' %Y')
            except ValueError:
                formatted_date_str = event_date_str # Fallback

            id_item = QTableWidgetItem(str(event_id))
            date_item = QTableWidgetItem(formatted_date_str)
            desc_item = QTableWidgetItem(description)
            rec_item = QTableWidgetItem("Da" if is_recurring else "Nu")
            rec_item.setTextAlignment(Qt.AlignCenter)

            self.events_table.setItem(row_position, 0, id_item)
            self.events_table.setItem(row_position, 1, date_item)
            self.events_table.setItem(row_position, 2, desc_item)
            self.events_table.setItem(row_position, 3, rec_item)
            
            # Buton Ștergere
            delete_btn_widget = QWidget()
            delete_btn_layout = QHBoxLayout(delete_btn_widget)
            delete_btn_layout.setContentsMargins(0,0,0,0) # Fără margini interne
            delete_btn_layout.setAlignment(Qt.AlignCenter) # Aliniază butonul în centru
            delete_btn = QPushButton(QIcon.fromTheme("edit-delete", QIcon("fallback_delete_icon.png")), "Șterge")
            delete_btn.setFont(QFont("Arial", 10))
            delete_btn.setStyleSheet("color: red;")
            delete_btn.setFixedSize(QSize(80,28)) # Dimensiune fixă pentru buton
            delete_btn.clicked.connect(lambda checked, eid=event_id: self.delete_event(eid))
            delete_btn_layout.addWidget(delete_btn)
            self.events_table.setCellWidget(row_position, 4, delete_btn_widget)
            self.events_table.setRowHeight(row_position, 35) # Înălțime rând

        self.events_table.setSortingEnabled(True)
        self.events_table.sortByColumn(1, Qt.DescendingOrder) # Sortează după data (coloana 1)

    def load_selected_event_to_form(self):
        selected_rows = self.events_table.selectionModel().selectedRows()
        if not selected_rows:
            # self.clear_form() # Nu curățăm formularul dacă doar se deselectează
            return

        selected_row_index = selected_rows[0].row()
        
        # Preluare ID din modelul de date al tabelului (mai sigur decât din textul item-ului)
        # Presupunem că ID-ul este în prima coloană (index 0)
        id_item = self.events_table.item(selected_row_index, 0)
        if not id_item:
            self.clear_form()
            return
            
        self.current_event_id = int(id_item.text())

        # Căutăm evenimentul în lista completă pentru datele originale
        original_event_data = None
        all_events_from_db = self.parent_scheduler.get_all_events() # Preluare directă din BD
        for ev in all_events_from_db:
            if ev[0] == self.current_event_id:
                original_event_data = ev
                break
        
        if not original_event_data:
            QMessageBox.warning(self, "Eroare", "Evenimentul selectat nu a fost găsit (ID: {self.current_event_id}). Este posibil să fi fost șters recent.")
            self.clear_form()
            return

        _, event_date_str, description, is_recurring, _, _ = original_event_data

        try:
            date_obj = datetime.datetime.strptime(event_date_str, '%Y-%m-%d').date()
            self.date_edit.setSelectedDate(QDate(date_obj.year, date_obj.month, date_obj.day))
        except ValueError:
             QMessageBox.warning(self, "Eroare Data", f"Data evenimentului '{event_date_str}' este invalidă.")
             self.date_edit.setSelectedDate(QDate.currentDate()) # Fallback

        self.description_edit.setText(description)
        self.recurring_checkbox.setChecked(bool(is_recurring))

        self.add_event_btn.setEnabled(False)
        self.save_event_btn.setEnabled(True)

    def clear_form(self):
        self.current_event_id = None
        self.date_edit.setSelectedDate(QDate.currentDate())
        self.description_edit.clear()
        self.recurring_checkbox.setChecked(False)
        self.events_table.clearSelection()

        self.add_event_btn.setEnabled(True)
        self.save_event_btn.setEnabled(False)

    def add_event(self):
        event_date_py = self.date_edit.selectedDate().toPyDate()
        event_date_str = event_date_py.strftime('%Y-%m-%d')
        description = self.description_edit.toPlainText().strip()
        is_recurring = 1 if self.recurring_checkbox.isChecked() else 0

        if not description:
            QMessageBox.warning(self, "Lipsă Descriere", "Vă rugăm introduceți o descriere pentru eveniment.")
            return

        if self.parent_scheduler.add_event_to_db(event_date_str, description, is_recurring):
            QMessageBox.information(self, "Succes", "Eveniment adăugat cu succes.")
            self.load_events_to_table()
            self.clear_form()
            # self.parent_scheduler.refresh_calendar() # Se face la închiderea dialogului
        else:
            # Mesajul de eroare e deja afișat de add_event_to_db
            pass

    def save_event(self):
        if self.current_event_id is None:
            return

        event_date_py = self.date_edit.selectedDate().toPyDate()
        event_date_str = event_date_py.strftime('%Y-%m-%d')
        description = self.description_edit.toPlainText().strip()
        is_recurring = 1 if self.recurring_checkbox.isChecked() else 0

        if not description:
            QMessageBox.warning(self, "Lipsă Descriere", "Vă rugăm introduceți o descriere pentru eveniment.")
            return

        if self.parent_scheduler.update_event_in_db(self.current_event_id, event_date_str, description, is_recurring):
            QMessageBox.information(self, "Succes", "Eveniment actualizat cu succes.")
            self.load_events_to_table()
            self.clear_form()
            # self.parent_scheduler.refresh_calendar() # Se face la închiderea dialogului
        else:
            # Mesajul de eroare e deja afișat de update_event_in_db
            pass

    def delete_event(self, event_id):
        reply = QMessageBox.question(self, "Confirmare Ștergere",
                                     "Sunteți sigur că doriți să ștergeți acest eveniment?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.parent_scheduler.delete_event_from_db(event_id):
                QMessageBox.information(self, "Succes", "Eveniment șters cu succes.")
                self.load_events_to_table()
                # Dacă evenimentul șters era cel selectat, curățăm formularul
                if self.current_event_id == event_id:
                    self.clear_form()
                # self.parent_scheduler.refresh_calendar() # Se face la închiderea dialogului
            else:
                # Mesajul de eroare e deja afișat de delete_event_from_db
                pass

    def reject(self):
        self.parent_scheduler.refresh_calendar() # Actualizează calendarul principal la închidere
        super().reject()

    # accept() nu este necesar dacă singurul buton standard este "Close" (care declanșează reject)
    # def accept(self):
    #     self.parent_scheduler.refresh_calendar()
    #     super().accept()

class NotarialScheduler(QMainWindow):
    def __init__(self):
        super().__init__()

        # Adăugăm un flag pentru a preveni duplicarea înregistrărilor la pornire
        self.initial_startup = True
        
        # Configurare fereastră principală
        self.setWindowTitle("Programator Acte Notariale")
        self.setMinimumSize(1600, 900)
        
        # Încercăm să restaurăm poziția și dimensiunea ferestrei salvate
        if not self.restore_window_position():
            # Dacă nu avem setări salvate, folosim valorile implicite
            self.resize(2560, 1300)  # Dimensiune inițială pentru ecran Full HD
        
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        
        # Adăugăm setarea iconiței aici
        self.set_application_icon()

        # Nume stație/computer
        self.computer_name = socket.gethostname()
        # Verifică și creează lock-ul de aplicație
        if not self.check_app_lock():
            sys.exit(1)
        
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
            "Dezmembrare + vânzare",
            "Divorț",
            "Donație",
            "Donație+Uzufruct",
            "Ipotecă",
            "Liber",
            "Novație",
            "Partaj voluntar",
            "Renunțare drept de Uzufruct",
            "Schimb",
            "Succesiune",
            "Superficie",
            "Supliment",
            "Testament",
            "Vânzare",
            "Vânzare Drepturi Succesorale",
            "Vânzare+Uzufruct viager",
            "Împrumut",
            "Încetare contract de Întreținere",
            "Închiriere",
            "Întreținere"
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
        self.update_last_action_label()

        # La final, după ce interfața este configurată și datele încărcate
        # Setăm flag-ul la False pentru a permite înregistrarea următoarelor intervenții
        self.initial_startup = False
    
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
            self.conn.commit() # Adăugat commit aici pentru siguranță

        # ######################################################################
        # ### START MODIFICARE PENTRU ZILE NELUCRĂTOARE ###
        # ######################################################################

        # Creare tabel pentru zile nelucrătoare dacă nu există
        print("Creare tabel non_working_days (dacă nu există)")
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS non_working_days (
            holiday_date DATE PRIMARY KEY
        )
        ''')
        self.conn.commit()

        # Inițializăm setul de zile nelucrătoare (va fi populat de load_non_working_days)
        self.non_working_days_set = set()
        self.load_non_working_days()

        # ######################################################################
        # ### END MODIFICARE PENTRU ZILE NELUCRĂTOARE   ###
        # ######################################################################

        # ######################################################################
        # ### START MODIFICARE PENTRU EVENIMENTE (NOU) ###
        # ######################################################################
        print("Creare tabel events (dacă nu există)")
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_date DATE NOT NULL,
            description TEXT NOT NULL,
            is_recurring INTEGER DEFAULT 0, -- 0 pentru False, 1 pentru True
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by TEXT
        )
        ''')
        self.conn.commit()
        # ######################################################################
        # ### END MODIFICARE PENTRU EVENIMENTE   ###
        # ######################################################################

        # Inițializare culori implicite
        self.default_colors = {
            "color1": "#81C784",  # Verde (culoarea originală)
            "color2": "#FFF9C4",  # Galben pal
            "color3": "#90CAF9",  # Albastru deschis
            "color4": "#CE93D8"   # Mov deschis
        }

        # Inițializare nume culori implicite
        self.color_names = {
            "color1": "Verde",
            "color2": "Galben",
            "color3": "Albastru",
            "color4": "Mov"
        }

        # Culorile actuale (vor fi încărcate din JSON)
        self.colors = self.default_colors.copy()

        # Document colors - înlocuiește highlighted_types
        self.document_colors = {}  # Exemplu: {"Succesiune": "color1", "Donație": "color2"}

        # Încercare încărcare tipuri documente din JSON
        json_loaded = self.load_document_types_from_json()

        # Dacă nu am reușit să încărcăm din JSON, folosim lista implicită și creăm JSON-ul
        if not json_loaded:
            print("Nu s-au găsit tipuri de documente în JSON, folosim lista implicită")

            # Inițializăm document_colors (fostul highlighted_types)
            self.document_colors = {"Succesiune": "color1"}

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

    def save_window_position(self):
        """Salvează poziția și dimensiunea ferestrei în JSON"""
        window_settings = {
            'x': self.x(),
            'y': self.y(),
            'width': self.width(),
            'height': self.height(),
            'maximized': self.isMaximized(),
            'screen': {
                'name': QApplication.primaryScreen().name(),
                'width': QApplication.primaryScreen().size().width(),
                'height': QApplication.primaryScreen().size().height()
            }
        }
        
        # Numele fișierului JSON pentru setările ferestrei
        settings_file = 'window_settings.json'
        
        try:
            with open(settings_file, 'w', encoding='utf-8') as file:
                json.dump(window_settings, file, ensure_ascii=False, indent=4)
            print(f"Poziția și dimensiunea ferestrei salvate în {settings_file}")
        except Exception as e:
            print(f"Eroare la salvarea poziției ferestrei: {e}")

    def restore_window_position(self):
        """Restaurează poziția și dimensiunea ferestrei din JSON"""
        settings_file = 'window_settings.json'
        
        try:
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as file:
                    settings = json.load(file)
                
                # Verifică dacă rezoluția ecranului s-a schimbat
                current_screen = QApplication.primaryScreen()
                current_width = current_screen.size().width()
                current_height = current_screen.size().height()
                saved_width = settings.get('screen', {}).get('width', 0)
                saved_height = settings.get('screen', {}).get('height', 0)
                
                # Calculează factorul de scalare dacă rezoluția s-a schimbat
                width_scale = 1.0
                height_scale = 1.0
                
                if saved_width > 0 and saved_height > 0:
                    width_scale = current_width / saved_width
                    height_scale = current_height / saved_height
                
                # Aplică poziția și dimensiunea, ajustate pentru noua rezoluție
                x = int(settings.get('x', 0) * width_scale)
                y = int(settings.get('y', 0) * height_scale)
                width = int(settings.get('width', 1600) * width_scale)
                height = int(settings.get('height', 900) * height_scale)
                
                # Asigură-te că fereastra nu e prea mare pentru ecran
                if width > current_width:
                    width = current_width - 100
                if height > current_height:
                    height = current_height - 100
                    
                # Asigură-te că fereastra e vizibilă pe ecranul curent
                if x < 0:
                    x = 0
                if y < 0:
                    y = 0
                if x + width > current_width:
                    x = 0
                if y + height > current_height:
                    y = 0
                
                # Setează poziția și dimensiunea
                self.resize(width, height)
                self.move(x, y)
                
                # Aplică starea maximizată dacă era salvată astfel
                if settings.get('maximized', False):
                    self.showMaximized()
                    
                print(f"Poziția și dimensiunea ferestrei restaurate din {settings_file}")
                return True
        except Exception as e:
            print(f"Eroare la restaurarea poziției ferestrei: {e}")
        
        return False

    # ######################################################################
    # ### START METODE PENTRU GESTIONAREA ZILELOR NELUCRĂTOARE ###
    # ######################################################################

    def load_non_working_days(self):
        """Încarcă zilele nelucrătoare din baza de date."""
        try:
            self.cursor.execute("SELECT holiday_date FROM non_working_days")
            # Stocăm ca un set de obiecte datetime.date pentru căutare rapidă
            self.non_working_days_set = {datetime.datetime.strptime(row[0], '%Y-%m-%d').date() for row in self.cursor.fetchall()}
            print(f"Zile nelucrătoare încărcate: {len(self.non_working_days_set)}")
        except Exception as e:
            print(f"Eroare la încărcarea zilelor nelucrătoare: {e}")
            self.non_working_days_set = set() # Asigurăm că este un set gol în caz de eroare

    def add_non_working_day(self, date_obj_param):
        """Adaugă o zi nelucrătoare în baza de date și actualizează setul."""
        date_obj = None
        if isinstance(date_obj_param, QDate):
            date_obj = date_obj_param.toPyDate()
        elif isinstance(date_obj_param, datetime.datetime):
            date_obj = date_obj_param.date()
        elif isinstance(date_obj_param, datetime.date):
            date_obj = date_obj_param
        else:
            print(f"Tip de dată neașteptat în add_non_working_day: {type(date_obj_param)}")
            return False

        if date_obj and date_obj not in self.non_working_days_set:
            try:
                self.cursor.execute("INSERT INTO non_working_days (holiday_date) VALUES (?)", (date_obj.strftime('%Y-%m-%d'),))
                self.conn.commit()
                self.non_working_days_set.add(date_obj)
                print(f"Ziua {date_obj} marcată ca nelucrătoare.")
                return True
            except sqlite3.IntegrityError: # Ar trebui să nu se întâmple datorită verificării setului
                print(f"Ziua {date_obj} este deja marcată ca nelucrătoare (eroare de integritate BD).")
                # Sincronizăm setul dacă există o discrepanță
                if date_obj not in self.non_working_days_set: self.non_working_days_set.add(date_obj)
                return False
            except Exception as e:
                print(f"Eroare la adăugarea zilei nelucrătoare {date_obj} în BD: {e}")
                return False
        elif date_obj in self.non_working_days_set:
            print(f"Ziua {date_obj} este deja în setul de zile nelucrătoare.")
            return False # Deja există, nu e o eroare, dar nu s-a adăugat nimic nou
        return False

    def remove_non_working_day(self, date_obj_param):
        """Șterge o zi nelucrătoare din baza de date și actualizează setul."""
        date_obj = None
        if isinstance(date_obj_param, QDate):
            date_obj = date_obj_param.toPyDate()
        elif isinstance(date_obj_param, datetime.datetime):
            date_obj = date_obj_param.date()
        elif isinstance(date_obj_param, datetime.date):
            date_obj = date_obj_param
        else:
            print(f"Tip de dată neașteptat în remove_non_working_day: {type(date_obj_param)}")
            return False

        if date_obj and date_obj in self.non_working_days_set:
            try:
                self.cursor.execute("DELETE FROM non_working_days WHERE holiday_date = ?", (date_obj.strftime('%Y-%m-%d'),))
                self.conn.commit()
                self.non_working_days_set.remove(date_obj)
                print(f"Ziua {date_obj} marcată ca lucrătoare.")
                return True
            except Exception as e:
                print(f"Eroare la ștergerea zilei nelucrătoare {date_obj} din BD: {e}")
                return False
        elif date_obj:
            print(f"Ziua {date_obj} nu era în setul de zile nelucrătoare.")
            return False # Nu era în set, nu e o eroare, dar nu s-a șters nimic
        return False

    def is_workday(self, date_obj_param):
        """Verifică dacă o dată este zi lucrătoare."""
        date_obj = None
        if isinstance(date_obj_param, datetime.datetime):
            date_obj = date_obj_param.date()
        elif isinstance(date_obj_param, datetime.date):
            date_obj = date_obj_param
        elif isinstance(date_obj_param, QDate):
            date_obj = date_obj_param.toPyDate()
        else:
            print(f"Tip de dată neașteptat în is_workday: {type(date_obj_param)}")
            return False # Considerăm nelucrătoare în caz de tip necunoscut

        if date_obj is None: # Ar trebui să nu se întâmple cu logica de mai sus
            return False

        # Sâmbătă (5) sau Duminică (6)
        if date_obj.weekday() >= 5:
            return False
        if date_obj in self.non_working_days_set:
            return False
        return True

    def add_business_days(self, start_date_param, num_days):
        """Adaugă un număr de zile lucrătoare la o dată de început."""
        current_date = None
        if isinstance(start_date_param, datetime.datetime):
            current_date = start_date_param.date()
        elif isinstance(start_date_param, datetime.date):
            current_date = start_date_param
        elif isinstance(start_date_param, QDate):
            current_date = start_date_param.toPyDate()
        else:
            print(f"Tip de dată neașteptat pentru start_date în add_business_days: {type(start_date_param)}")
            # Întoarcem data de început ca fallback sau ridicăm o eroare
            return start_date_param 

        if current_date is None: # Ar trebui să nu se întâmple
            return start_date_param

        days_added = 0
        # Verificăm dacă num_days este un întreg pozitiv
        if not isinstance(num_days, int) or num_days < 0:
            print(f"Numărul de zile ({num_days}) trebuie să fie un întreg non-negativ.")
            return current_date # Sau o valoare default / ridică eroare

        # Optimizare: dacă num_days este 0, returnăm direct data de început
        if num_days == 0:
            # Trebuie să ne asigurăm că data de început în sine este o zi lucrătoare
            # dacă cerința este ca rezultatul să fie *următoarea* zi lucrătoare
            # Pentru "data + X zile lucrătoare", data de start poate fi nelucrătoare.
            # Ajustăm bucla while să înceapă verificarea de la current_date + 1 zi.
            # Dacă cerința este "X zile lucrătoare începând de *astăzi inclusiv*", logica e alta.
            # Presupunem că "data + 45 zile" înseamnă 45 de zile lucrătoare *după* data curentă.
            pass


        temp_date = current_date # Folosim o variabilă temporară pentru incrementare
        while days_added < num_days:
            temp_date += timedelta(days=1)
            if self.is_workday(temp_date):
                days_added += 1
        return temp_date

    # ######################################################################
    # ### END METODE PENTRU GESTIONAREA ZILELOR NELUCRĂTOARE   ###
    # ######################################################################

    # --- START METODE PENTRU GESTIONAREA EVENIMENTELOR (NOU) ---

    def show_events_management_dialog(self):
        """Afișează dialogul pentru gestionarea evenimentelor."""
        dialog = EventsManagementDialog(self)
        dialog.exec_()
        # Refresh-ul calendarului este gestionat în metodele reject/accept ale dialogului

    def add_event_to_db(self, event_date_str, description, is_recurring):
        """Adaugă un eveniment nou în baza de date."""
        try:
            self.cursor.execute('''
                INSERT INTO events (event_date, description, is_recurring, created_by)
                VALUES (?, ?, ?, ?)
            ''', (event_date_str, description, is_recurring, self.computer_name))
            self.conn.commit()
            print(f"Eveniment adăugat: {event_date_str} - {description}")
            # Logare intervenție
            self.log_intervention(f"EVENIMENT ADĂUGAT: '{description}' pentru data {event_date_str}{' (recurent)' if is_recurring else ''} de către {self.computer_name}")
            return True
        except sqlite3.Error as e:
            print(f"Eroare SQLite la adăugarea evenimentului în BD: {e}")
            QMessageBox.critical(self, "Eroare Bază de Date", f"Nu s-a putut adăuga evenimentul:\n{e}")
            return False
        except Exception as e:
            print(f"Eroare generală la adăugarea evenimentului în BD: {e}")
            QMessageBox.critical(self, "Eroare Necunoscută", f"A apărut o eroare la adăugarea evenimentului:\n{e}")
            return False


    def update_event_in_db(self, event_id, event_date_str, description, is_recurring):
        """Actualizează un eveniment existent în baza de date."""
        try:
            self.cursor.execute('''
                UPDATE events
                SET event_date = ?, description = ?, is_recurring = ?
                WHERE id = ?
            ''', (event_date_str, description, is_recurring, event_id))
            self.conn.commit()
            print(f"Eveniment actualizat ID {event_id}: {event_date_str} - {description}")
            self.log_intervention(f"EVENIMENT MODIFICAT (ID: {event_id}): '{description}' pentru data {event_date_str}{' (recurent)' if is_recurring else ''} de către {self.computer_name}")
            return True
        except sqlite3.Error as e:
            print(f"Eroare SQLite la actualizarea evenimentului ID {event_id} în BD: {e}")
            QMessageBox.critical(self, "Eroare Bază de Date", f"Nu s-a putut actualiza evenimentul:\n{e}")
            return False
        except Exception as e:
            print(f"Eroare generală la actualizarea evenimentului ID {event_id} în BD: {e}")
            QMessageBox.critical(self, "Eroare Necunoscută", f"A apărut o eroare la actualizarea evenimentului:\n{e}")
            return False

    def delete_event_from_db(self, event_id):
        """Șterge un eveniment din baza de date."""
        try:
            # Preluăm descrierea pentru logare înainte de ștergere
            self.cursor.execute("SELECT description, event_date, is_recurring FROM events WHERE id = ?", (event_id,))
            event_details = self.cursor.fetchone()
            desc_for_log = f"ID {event_id}"
            if event_details:
                desc_for_log = f"'{event_details[0]}' (data: {event_details[1]}{', recurent' if event_details[2] else ''}, ID: {event_id})"

            self.cursor.execute('DELETE FROM events WHERE id = ?', (event_id,))
            self.conn.commit()
            print(f"Eveniment șters ID {event_id}")
            self.log_intervention(f"EVENIMENT ȘTERS: {desc_for_log} de către {self.computer_name}")
            return True
        except sqlite3.Error as e:
            print(f"Eroare SQLite la ștergerea evenimentului ID {event_id} din BD: {e}")
            QMessageBox.critical(self, "Eroare Bază de Date", f"Nu s-a putut șterge evenimentul:\n{e}")
            return False
        except Exception as e:
            print(f"Eroare generală la ștergerea evenimentului ID {event_id} din BD: {e}")
            QMessageBox.critical(self, "Eroare Necunoscută", f"A apărut o eroare la ștergerea evenimentului:\n{e}")
            return False

    def get_all_events(self):
        """Prelucrează toate evenimentele din baza de date."""
        try:
            self.cursor.execute('''
                SELECT id, event_date, description, is_recurring, created_at, created_by
                FROM events
                ORDER BY event_date DESC, id DESC
            ''') # Sortare și după ID pentru consistență
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Eroare la preluarea tuturor evenimentelor: {e}")
            return []

    def get_events_for_day(self, day_date_obj): # day_date_obj este un obiect datetime.date
        """Prelucrează evenimentele pentru o anumită zi (inclusiv cele recurente),
           FĂRĂ a adăuga sufixul '(Anual)' la afișarea în calendar."""
        events_for_display = []
        try:
            # Evenimente non-recurente pentru data exactă
            self.cursor.execute('''
                SELECT description
                FROM events
                WHERE event_date = ? AND is_recurring = 0
                ORDER BY id
            ''', (day_date_obj.strftime('%Y-%m-%d'),))
            for row in self.cursor.fetchall():
                events_for_display.append(row[0]) # Doar descrierea

            # Evenimente recurente care se potrivesc cu ziua și luna
            # Ne asigurăm că anul evenimentului din BD este <= anul zilei afișate
            day_month_str = day_date_obj.strftime('%m-%d')
            current_year_str = day_date_obj.strftime('%Y')
            self.cursor.execute(f'''
                SELECT description
                FROM events
                WHERE strftime('%m-%d', event_date) = ? 
                  AND is_recurring = 1
                  AND strftime('%Y', event_date) <= ?
                ORDER BY id
            ''', (day_month_str, current_year_str))
            for row in self.cursor.fetchall():
                events_for_display.append(row[0]) # MODIFICAT: Doar descrierea, fără "(Anual)"

            return events_for_display
        except Exception as e:
            print(f"Eroare la preluarea evenimentelor pentru ziua {day_date_obj}: {e}")
            return []
    # --- END METODE PENTRU GESTIONAREA EVENIMENTELOR ---

    def load_document_types(self):
        """Încarcă tipurile de documente din fișierul JSON"""
        print("\n--- Încărcare tipuri de documente ---")
        
        # Salvăm tipurile vechi pentru referință
        old_types = getattr(self, 'document_types', [])
        
        # Încărcăm din JSON
        self.load_document_types_from_json()
        
        print(f"Tipuri de documente înainte: {old_types}")
        print(f"Tipuri de documente după: {self.document_types}")
        print(f"Asocieri tip document - culoare: {self.document_colors}")
        print("--- Sfârșit încărcare tipuri de documente ---\n")
    
    def show_color_settings_dialog(self):
        """Dialog pentru configurarea culorilor disponibile"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Configurare Culori")
        dialog.setMinimumWidth(700)  # Lățime mărită
        dialog.setMinimumHeight(500)  # Înălțime mărită
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(20)  # Spațiere mărită
        layout.setContentsMargins(20, 20, 20, 20)  # Margini mai mari
        
        # Titlu
        title_label = QLabel("Personalizare Culori")
        title_label.setFont(QFont("Arial", 20, QFont.Bold))  # Font mărit
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Explicație
        description = QLabel("Configurați culorile pentru tipurile de documente (format HEX: #RRGGBB)")
        description.setAlignment(Qt.AlignCenter)
        description.setWordWrap(True)
        description.setFont(QFont("Arial", 14))  # Font mărit
        layout.addWidget(description)
        
        # Form layout pentru câmpurile de culori
        form_layout = QFormLayout()
        form_layout.setVerticalSpacing(20)  # Spațiere verticală mărită
        form_layout.setHorizontalSpacing(15)  # Spațiere orizontală mărită
        form_layout.setLabelAlignment(Qt.AlignRight)  # Aliniere etichete la dreapta
        layout.addLayout(form_layout)
        
        # Inițializăm dicționarul pentru noile culori
        new_colors = {}
        color_entries = {}
        color_previews = {}
        
        # Creăm câmpurile pentru fiecare culoare
        for i in range(4):
            color_key = f"color{i+1}"
            color_name = self.color_names.get(color_key, f"Culoarea {i+1}")
            
            # Obținem codul de culoare curent
            current_color = self.colors.get(color_key, self.default_colors.get(color_key, "#FFFFFF"))
            new_colors[color_key] = current_color
            
            # Layout orizontal pentru intrare și preview
            row_layout = QHBoxLayout()
            row_layout.setSpacing(15)  # Spațiere mărită între elemente
            
            # Câmp text pentru cod culoare
            color_entry = QLineEdit(current_color)
            color_entry.setFont(QFont("Arial", 14))  # Font mărit
            color_entry.setMinimumHeight(40)  # Înălțime mărită
            color_entry.setMaximumWidth(150)  # Lățime maximă mărită
            color_entries[color_key] = color_entry
            row_layout.addWidget(color_entry)
            
            # Preview culoare
            color_preview = QFrame()
            color_preview.setFrameStyle(QFrame.Box)
            color_preview.setFixedSize(50, 50)  # Dimensiune mărită
            color_preview.setStyleSheet(f"background-color: {current_color}; border: 2px solid black;")  # Bordură adăugată
            color_previews[color_key] = color_preview
            row_layout.addWidget(color_preview)
            
            # Buton pentru a actualiza preview-ul
            update_btn = QPushButton("Verifică")
            update_btn.setFont(QFont("Arial", 14))  # Font mărit
            update_btn.setMinimumHeight(40)  # Înălțime mărită
            update_btn.setFixedWidth(120)  # Lățime fixă mărită
            
            # Folosim o funcție closure pentru a păstra referința la key-ul curent
            def create_update_function(key):
                return lambda: update_color_preview(key)
            
            update_btn.clicked.connect(create_update_function(color_key))
            row_layout.addWidget(update_btn)
            
            # Adăugăm și numele culorii
            name_entry = QLineEdit(color_name)
            name_entry.setFont(QFont("Arial", 14))  # Font mărit
            name_entry.setMinimumHeight(40)  # Înălțime mărită
            name_entry.setPlaceholderText("Nume culoare")
            row_layout.addWidget(name_entry, 1)  # 1 = stretch factor
            
            # Etichetă pentru culoare
            color_label = QLabel(f"Culoarea {i+1}:")
            color_label.setFont(QFont("Arial", 14, QFont.Bold))  # Font mărit și îngroșat
            color_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            # Adăugăm rândul complet în formular
            form_layout.addRow(color_label, row_layout)
        
        # Funcție pentru actualizarea preview-ului de culoare
        def update_color_preview(color_key):
            hex_code = color_entries[color_key].text().strip()
            # Verificăm dacă codul HEX este valid
            if hex_code.startswith("#") and (len(hex_code) == 7 or len(hex_code) == 9):
                try:
                    # Actualizăm preview-ul
                    color_previews[color_key].setStyleSheet(f"background-color: {hex_code}; border: 2px solid black;")
                    new_colors[color_key] = hex_code
                except:
                    QMessageBox.warning(dialog, "Eroare", f"Codul de culoare {hex_code} nu este valid.")
            else:
                QMessageBox.warning(dialog, "Eroare", "Codul de culoare trebuie să fie în format #RRGGBB.")
        
        # Butoane OK/Cancel
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        
        # Stilizare butoane
        ok_button = button_box.button(QDialogButtonBox.Ok)
        ok_button.setText("Salvează")
        ok_button.setFont(QFont("Arial", 14))  # Font mărit
        ok_button.setMinimumSize(180, 60)  # Buton mai mare
        
        cancel_button = button_box.button(QDialogButtonBox.Cancel)
        cancel_button.setText("Anulează")
        cancel_button.setFont(QFont("Arial", 14))  # Font mărit
        cancel_button.setMinimumSize(180, 60)  # Buton mai mare
        
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box, alignment=Qt.AlignRight)
        
        # Executăm dialogul
        if dialog.exec_() == QDialog.Accepted:
            # Salvăm noile valori de culori
            for color_key, entry in color_entries.items():
                hex_code = entry.text().strip()
                if hex_code.startswith("#") and (len(hex_code) == 7 or len(hex_code) == 9):
                    self.colors[color_key] = hex_code
            
            # Actualizăm și numele culorilor
            for i, row in enumerate(range(form_layout.rowCount())):
                color_key = f"color{i+1}"
                # Obținem layout-ul orizontal
                row_item = form_layout.itemAt(row, QFormLayout.FieldRole)
                if row_item and isinstance(row_item.layout(), QHBoxLayout):
                    # Găsim QLineEdit pentru nume (ultimul widget din layout)
                    name_widget = row_item.layout().itemAt(row_item.layout().count() - 1).widget()
                    if isinstance(name_widget, QLineEdit):
                        self.color_names[color_key] = name_widget.text().strip()
            
            # Salvăm configurația și actualizăm calendarul
            self.save_document_types_to_json()
            self.refresh_calendar()
            return True
        
        return False

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

        # Widget curs valutar
        currency_widget = CurrencyWidget(self)
        header_layout.addWidget(currency_widget)

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
        calendar_btn.setMinimumWidth(120)
        calendar_btn.clicked.connect(self.show_calendar_dialog)
        header_layout.addWidget(calendar_btn)

        # Buton "Azi"
        today_btn = QPushButton("Azi")
        today_btn.setFixedHeight(50)
        today_btn.setFont(QFont("Arial", 12))
        today_btn.setMinimumWidth(100)
        today_btn.clicked.connect(self.go_to_today)
        header_layout.addWidget(today_btn)

        # Buton adăugare tip document
        add_doc_type_btn = QPushButton("Adaugă tip document")
        add_doc_type_btn.setFixedHeight(50)
        add_doc_type_btn.setFont(QFont("Arial", 12))
        add_doc_type_btn.setMinimumWidth(220)
        add_doc_type_btn.clicked.connect(self.add_document_type)
        header_layout.addWidget(add_doc_type_btn)

        # --- START ADAUGARE BUTON EVENIMENTE (NOU) ---
        events_btn = QPushButton("Evenimente")
        events_btn.setFixedHeight(50)
        events_btn.setFont(QFont("Arial", 12))
        events_btn.setMinimumWidth(150) # Ajustează lățimea dacă este necesar
        events_btn.clicked.connect(self.show_events_management_dialog)
        header_layout.addWidget(events_btn)
        # --- END ADAUGARE BUTON EVENIMENTE ---

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
        
        # Setăm stretch factor pentru fiecare coloană pentru a asigura distribuirea uniformă
        for i in range(6):
            self.calendar_grid.setColumnStretch(i, 1)
        
        # Creare frame-uri pentru zile
        self.day_frames = []
        for i in range(6):  # Luni până Sâmbătă
            day_date = self.week_start + timedelta(days=i)
            self.create_day_column(i, day_date)
    
    def create_day_column(self, column, day_date): # day_date este un obiect datetime.datetime
        """Creare coloană pentru o zi, cu tooltip, marcare sărbători și evenimente"""
        # ... (codul de la începutul funcției rămâne la fel) ...
        day_frame = QFrame()
        day_frame.setFrameStyle(QFrame.Box | QFrame.Plain)
        day_frame.setLineWidth(2)
        day_frame.setMinimumWidth(250)
        self.calendar_grid.addWidget(day_frame, 0, column)

        day_layout = QVBoxLayout(day_frame)
        day_layout.setContentsMargins(5, 5, 5, 5)

        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.NoFrame)
        header_frame.setLineWidth(0)
        header_frame.setAutoFillBackground(True)

        current_day_as_date_obj = day_date.date()

        is_today = (current_day_as_date_obj == datetime.datetime.now().date())
        is_holiday_manually_marked = (current_day_as_date_obj.weekday() < 5 and
                                     not self.is_workday(current_day_as_date_obj))

        header_frame_palette = QPalette()
        header_text_color_css = "color: black;"

        # Determinăm culoarea de fundal a header-ului zilei
        header_bg_color_obj = QColor("#F0F0F0") # Gri deschis standard
        if is_today:
            header_bg_color_obj = QColor("#5D4037") # Maro închis
            header_text_color_css = "color: #FFD700;" # Auriu
        elif is_holiday_manually_marked:
            header_bg_color_obj = QColor("red")
            header_text_color_css = "color: white;"
        
        header_frame_palette.setColor(QPalette.Background, header_bg_color_obj)
        header_frame.setPalette(header_frame_palette)
        day_layout.addWidget(header_frame)

        header_content_layout = QVBoxLayout(header_frame)
        header_content_layout.setContentsMargins(5, 3, 5, 3) 
        header_content_layout.setSpacing(2) # Mărit puțin spațiul între elementele din header

        day_name_ro = self.day_names_ro[current_day_as_date_obj.weekday()]
        header_date_text = f"{current_day_as_date_obj.day} {self.month_names_ro[current_day_as_date_obj.month-1]}"
        
        day_header_label_date = QLabel(header_date_text)
        day_header_label_dayname = QLabel(day_name_ro)

        font_size_header = 15 if is_today else 13 
        common_font_header = QFont("Arial", font_size_header, QFont.Bold)
        
        day_header_label_date.setFont(common_font_header)
        day_header_label_date.setStyleSheet(header_text_color_css + "background-color: transparent;")
        day_header_label_date.setAlignment(Qt.AlignCenter)
        header_content_layout.addWidget(day_header_label_date)
        
        day_header_label_dayname.setFont(common_font_header)
        day_header_label_dayname.setStyleSheet(header_text_color_css + "background-color: transparent;")
        day_header_label_dayname.setAlignment(Qt.AlignCenter)
        header_content_layout.addWidget(day_header_label_dayname)

        if is_holiday_manually_marked:
            holiday_label = QLabel("SĂRBĂTOARE LEGALĂ")
            holiday_font = QFont("Arial", 12, QFont.Bold, italic=True) 
            holiday_label.setFont(holiday_font)
            sarbatoare_text_color = "white" if not is_today else "#FFD700" 
            holiday_label.setStyleSheet(f"color: {sarbatoare_text_color}; background-color: transparent; padding: 0px; margin-top: 1px;")
            holiday_label.setAlignment(Qt.AlignCenter)
            header_content_layout.addWidget(holiday_label)

        events_today = self.get_events_for_day(current_day_as_date_obj)
        if events_today:
            for event_desc in events_today:
                event_label = QLabel(event_desc)
                # --- FONT EVENIMENT (presupunem că e 12pt acum) ---
                event_font = QFont("Arial", 12, QFont.DemiBold) # Sau QFont.Normal dacă DemiBold e prea gros
                event_label.setFont(event_font)
                
                # --- STILIZARE EVENIMENT CU FUNDAL ȘI CHENAR (spre MOV) ---
                
                # OPȚIUNEA 1: Mov Lavandă Deschis (semi-transparent)
                #event_bg_color = "rgba(230, 230, 250, 0.85)" # Lavender semi-transparent (85% opacitate)
                #event_text_color_name = "#483D8B" # DarkSlateBlue (un mov închis, ar trebui să meargă bine)
                #event_border_color_name = "#483D8B" # Sau un gri: "#9370DB" (MediumPurple mai deschis pentru chenar)

                # OPȚIUNEA 2: Mov Prună Deschis (mai opac)
                event_bg_color = "#DDA0DD" # Plum (Prună deschis) - complet opac
                event_text_color_name = "black" # Negru pentru contrast maxim pe Plum
                                                 # Sau un alb: "white" dacă Plum este suficient de închis
                event_border_color_name = "#BA55D3" # MediumOrchid (un mov puțin mai închis pentru chenar)
                                                    # Sau chiar "black" pentru chenar
                
                # OPȚIUNEA 3: Mov Thistle (Foarte deschis)
                #event_bg_color = "#D8BFD8" # Thistle - complet opac
                #event_text_color_name = "#4B0082" # Indigo (un mov foarte închis pentru text)
                #event_border_color_name = "#8A2BE2" # BlueViolet (pentru chenar)

                event_label.setStyleSheet(
                    f"color: {event_text_color_name}; "
                    f"background-color: {event_bg_color}; "
                    f"border: 1px solid {event_border_color_name}; "
                    f"border-radius: 3px; "
                    f"padding: 2px 4px; "
                    f"margin-top: 2px; "
                )
                event_label.setAlignment(Qt.AlignCenter)
                event_label.setWordWrap(True)
                header_content_layout.addWidget(event_label)
        
        # ... (codul pentru tooltip rămâne la fel) ...
        data_preemptiune = self.add_business_days(current_day_as_date_obj, 47) 
        formatted_data_preemptiune = (f"{data_preemptiune.day} "
                                      f"{self.month_names_ro[data_preemptiune.month-1]} "
                                      f"{data_preemptiune.year}")

        data_finala_intermediara = data_preemptiune + timedelta(days=32)
        ziua_saptamanii_intermediare = data_finala_intermediara.weekday()
        data_finala_efectiva = data_finala_intermediara
        if ziua_saptamanii_intermediare == 5: 
            data_finala_efectiva += timedelta(days=3) 
        elif ziua_saptamanii_intermediare == 6: 
            data_finala_efectiva += timedelta(days=2) 
        
        while not self.is_workday(data_finala_efectiva):
             data_finala_efectiva += timedelta(days=1)
        
        formatted_data_finala = (f"{data_finala_efectiva.day} "
                                 f"{self.month_names_ro[data_finala_efectiva.month-1]} "
                                 f"{data_finala_efectiva.year}")

        tooltip_lines = []
        if is_holiday_manually_marked:
             tooltip_lines.append("ZI NELUCRĂTOARE (SĂRBĂTOARE LEGALĂ)")
        elif current_day_as_date_obj.weekday() >= 5 : 
             tooltip_lines.append("ZI NELUCRĂTOARE (WEEKEND)")

        tooltip_lines.append(f"Data preempțiune (+47 zile lucrătoare): {formatted_data_preemptiune}")
        tooltip_lines.append(f"Data finală (preempțiune + 32 zile cal., ajustată): {formatted_data_finala}")

        tooltip_text = "\n".join(tooltip_lines)
        if tooltip_text:
            header_frame.setToolTip(tooltip_text)
        else:
            header_frame.setToolTip("")

        # ... (codul pentru ScrollArea și time_slots rămâne la fel) ...
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        day_layout.addWidget(scroll_area, 1) 

        hours_widget = QWidget()
        scroll_area.setWidget(hours_widget)
        hours_layout = QVBoxLayout(hours_widget)
        hours_layout.setContentsMargins(0, 0, 0, 0)
        hours_layout.setSpacing(2)

        self.create_time_slots(hours_layout, day_date) 

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
        
        # Filtrăm programările active
        active_appointments = [app for app in all_appointments if app[6] != 'deleted']
        
        # Sortăm programările după timp pentru procesare cronologică
        active_appointments.sort(key=lambda app: self.sort_time_key(app[1]))
        
        # Inițializăm dicționarul pentru a stoca informații despre intervale blocate
        free_intervals = {}
        
        # Identificăm programările de tip "Liber" și calculăm câte intervale să blocăm
        for app in active_appointments:
            if app[3] == "Liber":  # Verificăm tipul documentului
                free_time = app[1]  # Ora de la care începe programul liber
                client_name = app[2]  # Numele clientului (poate conține numărul de intervale)
                
                # Determinăm câte intervale orare să blocăm
                blocks_count = 0  # 0 = toate intervalele rămase din zi
                
                if client_name.isdigit():
                    # Dacă numele clientului este un număr, îl folosim pentru numărul de intervale
                    blocks_count = int(client_name)
                
                # Stocăm informațiile pentru utilizare ulterioară
                free_intervals[free_time] = {
                    'blocks_count': blocks_count,
                    'next_appointment': None,  # Va fi setat mai târziu dacă există
                    'affected_slots': []  # Va stoca intervalele afectate
                }
        
        # Identificăm pentru fiecare programare "Liber" prima programare non-Liber care o urmează
        for free_time, info in free_intervals.items():
            free_time_value = self.sort_time_key(free_time)
            
            # Găsim prima programare care nu este de tip "Liber" după această programare "Liber"
            for app in active_appointments:
                app_time = app[1]
                app_time_value = self.sort_time_key(app_time)
                
                # Verificăm dacă această programare este după programarea "Liber" și nu este de tip "Liber"
                if app_time_value > free_time_value and app[3] != "Liber":
                    # Am găsit prima programare non-Liber după această programare Liber
                    info['next_appointment'] = app_time
                    break
        
        # Calculăm exact care intervale orare sunt afectate de fiecare programare "Liber"
        for free_time, info in free_intervals.items():
            free_time_value = self.sort_time_key(free_time)
            blocks_count = info['blocks_count']
            next_appointment = info['next_appointment']
            next_appointment_value = self.sort_time_key(next_appointment) if next_appointment else None
            
            # Determinăm intervalele afectate
            count = 0
            for time_str in all_hours:
                time_value = self.sort_time_key(time_str)
                
                # Verificăm dacă acest interval este după programarea "Liber"
                if time_value >= free_time_value:
                    # Verificăm dacă am ajuns la programarea următoare (dacă există)
                    if next_appointment and time_value >= next_appointment_value:
                        break
                        
                    # Verificăm dacă am atins numărul maxim de intervale blocate
                    if blocks_count > 0 and count >= blocks_count:
                        break
                        
                    info['affected_slots'].append(time_str)
                    count += 1
        
        # Creăm intervalele orare pentru fiecare oră din listă
        for time_str in all_hours:
            # Determinăm dacă această oră este blocată de o programare "Liber"
            is_free_time = False
            
            for free_time, info in free_intervals.items():
                if time_str in info['affected_slots']:
                    is_free_time = True
                    break
            
            self.create_time_slot(parent_layout, day_date, time_str, is_free_time)
    
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
            # Dacă este după ora marcată ca "Liber", folosim fundal roșu
            base_color = "#FF5252"  # Roșu pentru orele după "Liber"
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
            doc_type = appointment[3]
            
            # Verificăm dacă este tipul special "Liber"
            is_free_time = doc_type == "Liber"
            
            # Verificăm dacă acest tip de document are culoare asociată
            color_key = None
            if not is_free_time and hasattr(self, 'document_colors'):
                color_key = self.document_colors.get(doc_type)
            
            # Aplicăm culoarea corespunzătoare
            try:
                palette = QPalette()
                
                if is_free_time:
                    # Roșu pentru marcarea timpului liber
                    palette.setColor(QPalette.Background, QColor("#FF5252"))
                elif color_key and color_key in self.colors:
                    # Culoarea specifică asociată tipului de document
                    palette.setColor(QPalette.Background, QColor(self.colors[color_key]))
                else:
                    # Culoare implicită pentru programări fără culoare specifică
                    palette.setColor(QPalette.Background, QColor("#FFF9C4"))  # Galben foarte pal
                
                time_slot_frame.setAutoFillBackground(True)
                time_slot_frame.setPalette(palette)
            except Exception:
                # Fallback în caz de eroare
                if is_free_time:
                    time_slot_frame.setStyleSheet("QFrame { background-color: #FF5252; }")
                elif color_key and color_key in self.colors:
                    time_slot_frame.setStyleSheet(f"QFrame {{ background-color: {self.colors[color_key]}; }}")
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
            
            # Verificăm dacă tipul de document este "Liber"
            if values['document_type'] == "Liber":
                # Verificăm dacă clientul conține un număr sau este gol
                client_name = values['client_name'].strip()
                if not client_name:
                    # Dacă e gol, folosim N/A (comportamentul implicit - tot restul zilei blocat)
                    values['client_name'] = "N/A"
                elif client_name.isdigit():
                    # Dacă e un număr, îl păstrăm ca atare (va specifica numărul de intervale blocate)
                    values['client_name'] = client_name
                else:
                    # Dacă nu e număr, adăugăm un mesaj în observații pentru clarificare
                    if not values['observations']:
                        values['observations'] = ""
                    values['observations'] += f"\nNotă: S-a introdus \"{client_name}\" în loc de un număr. " + \
                                             "Pentru a specifica numărul exact de intervale blocate, " + \
                                             "introduceți doar un număr (1, 2, 3, etc.)."
                    # Păstrăm valoarea introdusă (va fi interpretată ca N/A - tot restul zilei blocat)
                    
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
            
            # Verificăm dacă tipul de document este "Liber"
            if values['document_type'] == "Liber":
                # Verificăm dacă clientul conține un număr sau este gol
                client_name = values['client_name'].strip()
                if not client_name:
                    # Dacă e gol, folosim N/A (comportamentul implicit - tot restul zilei blocat)
                    values['client_name'] = "N/A"
                elif client_name.isdigit():
                    # Dacă e un număr, îl păstrăm ca atare (va specifica numărul de intervale blocate)
                    values['client_name'] = client_name
                else:
                    # Dacă nu e număr, adăugăm un mesaj în observații pentru clarificare
                    if not values['observations']:
                        values['observations'] = ""
                    values['observations'] += f"\nNotă: S-a introdus \"{client_name}\" în loc de un număr. " + \
                                             "Pentru a specifica numărul exact de intervale blocate, " + \
                                             "introduceți doar un număr (1, 2, 3, etc.)."
                    # Păstrăm valoarea introdusă (va fi interpretată ca N/A - tot restul zilei blocat)
            
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
            # Obținem timestamp-ul curent formatat
            current_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Marcăm programarea ca ștearsă - folosim timestamp-ul generat din Python
            self.cursor.execute(
                '''UPDATE appointments 
                   SET status = 'deleted', 
                       deleted_by = ?, 
                       deleted_at = ? 
                   WHERE id = ?''', 
                (self.computer_name, current_timestamp, appointment_id)
            )
            self.conn.commit()
            
            # Închidem dialogul și actualizăm afișarea
            dialog.reject()  # Folosim reject() pentru a închide dialogul
            self.refresh_calendar()
            self.update_last_action_label()  # Actualizăm label-ul

    def save_appointment(self, day, time, client_name, doc_type, observations=""):
        """Salvare programare nouă în baza de date"""
        if not client_name or not doc_type or not time:
            QMessageBox.critical(self, "Eroare", "Vă rugăm completați toate câmpurile.")
            return
        
        # Validare format oră
        if not self.validate_time_format(time):
            QMessageBox.critical(self, "Eroare", "Format oră invalid. Folosiți formatul HH:MM (exemplu: 12:30).")
            return
        
        # Obținem timestamp-ul curent formatat
        current_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.cursor.execute(
            'INSERT INTO appointments (day, time, client_name, document_type, computer_name, status, observations, created_at) VALUES (?, ?, ?, ?, ?, "active", ?, ?)',
            (day.strftime('%Y-%m-%d'), time, client_name, doc_type, self.computer_name, observations, current_timestamp)
        )
        
        # Obținem ID-ul nou creat
        appointment_id = self.cursor.lastrowid
        self.conn.commit()
        
        # Logăm observațiile dacă există
        if observations and observations.strip():
            self.log_observations_changes(appointment_id, "", observations, "creare")
        
        self.refresh_calendar()
        self.update_last_action_label()  # Actualizăm label-ul

    # Modificare în metoda update_appointment - folosește direct ora PC-ului
    def update_appointment(self, appointment_id, client_name, doc_type, time, observations=""):
        """Actualizare programare existentă în baza de date"""
        if not client_name or not doc_type or not time:
            QMessageBox.critical(self, "Eroare", "Vă rugăm completați toate câmpurile.")
            return
        
        # Validare format oră
        if not self.validate_time_format(time):
            QMessageBox.critical(self, "Eroare", "Format oră invalid. Folosiți formatul HH:MM (exemplu: 12:30).")
            return
        
        # Obținem observațiile vechi pentru comparație
        self.cursor.execute('SELECT observations FROM appointments WHERE id = ?', (appointment_id,))
        result = self.cursor.fetchone()
        old_observations = result[0] if result and result[0] else ""
        
        # Obținem timestamp-ul curent formatat
        current_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Actualizăm programarea - folosim timestamp-ul generat din Python
        self.cursor.execute(
            '''UPDATE appointments 
               SET client_name = ?, 
                   document_type = ?, 
                   time = ?,
                   status = 'modified', 
                   modified_by = ?, 
                   modified_at = ?,
                   observations = ?
               WHERE id = ?''',
            (client_name, doc_type, time, self.computer_name, current_timestamp, observations, appointment_id)
        )
        self.conn.commit()
        
        # Logăm modificările la observații
        self.log_observations_changes(appointment_id, old_observations, observations, "modificare")
        
        self.refresh_calendar()
        self.update_last_action_label()  # Actualizăm label-ul
    
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
            # Obținem observațiile pentru logging înainte de a marca programarea ca ștearsă
            self.cursor.execute('SELECT observations FROM appointments WHERE id = ?', (appointment_id,))
            result = self.cursor.fetchone()
            old_observations = result[0] if result and result[0] else ""
            
            # Obținem timestamp-ul curent formatat
            current_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # In loc să ștergeți, actualizați statusul și adăugați informații despre ștergere
            # Folosim timestamp-ul generat din Python
            self.cursor.execute(
                '''UPDATE appointments 
                   SET status = 'deleted', 
                       deleted_by = ?, 
                       deleted_at = ?
                   WHERE id = ?''', 
                (self.computer_name, current_timestamp, appointment_id)
            )
            self.conn.commit()
            
            # Logăm ștergerea observațiilor dacă există
            if old_observations and old_observations.strip():
                self.log_observations_changes(appointment_id, old_observations, "", "ștergere")
            
            self.refresh_calendar()
            self.update_last_action_label()  # Actualizăm label-ul
            
    def restore_appointment(self, appointment_id):
        """Restaurează o programare ștearsă"""
        self.cursor.execute(
            "UPDATE appointments SET status = 'active', deleted_by = NULL, deleted_at = NULL WHERE id = ?", 
            (appointment_id,)
        )
        self.conn.commit()
        self.refresh_calendar()
        self.update_last_action_label()  # Actualizăm label-ul
    
    def add_document_type(self):
        """Adăugare sau gestionare tip document cu layout pe două coloane și salvare în JSON"""
        print("\n--- Începerea procesului de adăugare tip document ---")
        
        # Definim EditableLabel pentru redenumire cu dublu-click
        class EditableLabel(QLabel):
            """Etichetă care permite editarea cu dublu click"""
            def __init__(self, text, parent=None):
                super().__init__(text, parent)
                self.text = text
                self.setWordWrap(True)
                self.setFont(QFont("Arial", 14))  # Font mărit
                
            def mouseDoubleClickEvent(self, event):
                self.startEditing()
                
            def startEditing(self):
                # Obține informația despre tipul de document
                doc_type = self.text
                parent_dialog = self.parent().window()
                
                # Creează dialog pentru editare
                edit_dialog = QDialog(parent_dialog)
                edit_dialog.setWindowTitle("Redenumire Tip Document")
                edit_dialog.setMinimumWidth(600)  # Lățime mărită
                edit_dialog.setMinimumHeight(300)  # Înălțime minimă adăugată
                
                # Layout pentru dialog
                layout = QVBoxLayout(edit_dialog)
                layout.setSpacing(15)  # Spațiere mărită între elemente
                
                # Mesaj explicativ
                info_label = QLabel("Redenumește tipul de document:")
                info_label.setFont(QFont("Arial", 14))  # Font mărit
                layout.addWidget(info_label)
                
                # Câmp text pentru noul nume
                edit_field = QLineEdit(doc_type)
                edit_field.setFont(QFont("Arial", 14))  # Font mărit
                edit_field.setMinimumHeight(40)  # Înălțime mărită
                edit_field.selectAll()
                layout.addWidget(edit_field)
                
                # Avertisment
                warning_label = QLabel("Atenție: Redenumirea va afecta toate programările existente. "
                                    "Asigurați-vă că actualizați și programările existente dacă este necesar.")
                warning_label.setWordWrap(True)
                warning_label.setFont(QFont("Arial", 12))  # Font mărit
                warning_label.setStyleSheet("color: #FF5252;")
                layout.addWidget(warning_label)
                
                # Butoane
                button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
                
                # Stilizare butoane
                ok_button = button_box.button(QDialogButtonBox.Ok)
                ok_button.setText("Salvează")
                ok_button.setFont(QFont("Arial", 14))
                ok_button.setMinimumSize(150, 50)  # Butoane mai mari
                
                cancel_button = button_box.button(QDialogButtonBox.Cancel)
                cancel_button.setText("Anulează")
                cancel_button.setFont(QFont("Arial", 14))
                cancel_button.setMinimumSize(150, 50)  # Butoane mai mari
                
                layout.addWidget(button_box)
                
                button_box.accepted.connect(edit_dialog.accept)
                button_box.rejected.connect(edit_dialog.reject)
                
                # Execută dialog
                if edit_dialog.exec_() == QDialog.Accepted:
                    new_name = edit_field.text().strip()
                    
                    # Verifică dacă numele e gol
                    if not new_name:
                        QMessageBox.warning(parent_dialog, "Eroare", "Numele tipului de document nu poate fi gol.")
                        return
                        
                    # Verifică dacă numele există deja
                    scheduler = parent_dialog.parent()  # NotarialScheduler
                    if new_name in scheduler.document_types and new_name != doc_type:
                        QMessageBox.warning(parent_dialog, "Eroare", "Acest tip de document există deja.")
                        return
                        
                    # Confirmarea modificării în baza de date
                    reply = QMessageBox.question(
                        parent_dialog,
                        "Confirmare", 
                        f"Sigur doriți să redenumiti tipul de document din \"{doc_type}\" în \"{new_name}\"?\n\n"
                        "Toate programările existente cu acest tip vor fi actualizate.",
                        QMessageBox.Yes | QMessageBox.No, 
                        QMessageBox.No
                    )
                    
                    if reply == QMessageBox.Yes:
                        try:
                            # Actualizează numele în lista de tipuri
                            index = scheduler.document_types.index(doc_type)
                            scheduler.document_types[index] = new_name
                            
                            # Actualizăm și document_colors dacă e necesar
                            if doc_type in scheduler.document_colors:
                                color = scheduler.document_colors[doc_type]
                                del scheduler.document_colors[doc_type]
                                scheduler.document_colors[new_name] = color
                            
                            # Actualizează toate programările existente
                            scheduler.cursor.execute(
                                "UPDATE appointments SET document_type = ? WHERE document_type = ?",
                                (new_name, doc_type)
                            )
                            scheduler.conn.commit()
                            
                            # Salvează configurația
                            scheduler.save_document_types_to_json()
                            
                            # Actualizează eticheta din dialog
                            self.setText(new_name)
                            self.text = new_name
                            
                            QMessageBox.information(
                                parent_dialog,
                                "Succes",
                                f"Tipul de document a fost redenumit în \"{new_name}\".\n"
                                "Toate programările au fost actualizate."
                            )
                            
                        except Exception as e:
                            QMessageBox.critical(
                                parent_dialog,
                                "Eroare",
                                f"Nu s-a putut redenumi tipul de document: {e}"
                            )
        
        # Creăm un dialog mai complex pentru gestionarea tipurilor de documente
        dialog = QDialog(self)
        dialog.setWindowTitle("Gestionare Tipuri de Documente")
        dialog.setMinimumWidth(1920)  # Lățime mărită semnificativ pentru 2K
        dialog.setMinimumHeight(1080)  # Înălțime mărită semnificativ pentru 2K
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(20)  # Spațiere mărită între elemente
        layout.setContentsMargins(20, 20, 20, 20)  # Margini mai mari
        
        # Titlu
        title_label = QLabel("Tipuri de Documente Disponibile")
        title_label.setFont(QFont("Arial", 20, QFont.Bold))  # Font mărit
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Descriere
        description = QLabel("Alegeți culoarea pentru fiecare tip de document din lista de mai jos.\n"
                             "Pentru a redenumi un tip de document, faceți dublu-click pe numele lui.")
        description.setAlignment(Qt.AlignCenter)
        description.setFont(QFont("Arial", 14))  # Font mărit
        layout.addWidget(description)
        
        # Facem un scroll area pentru tabelul de tipuri de documente
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(500)  # Înălțime mărită
        layout.addWidget(scroll_area)
        
        # Widget-ul interior pentru scroll area
        scroll_content = QWidget()
        scroll_area.setWidget(scroll_content)
        
        # Folosim un grid layout pentru a dispune tipurile pe două coloane
        grid_layout = QGridLayout(scroll_content)
        grid_layout.setVerticalSpacing(15)  # Spațiere verticală mărită
        grid_layout.setHorizontalSpacing(20)  # Spațiere orizontală mărită
        grid_layout.setContentsMargins(20, 20, 20, 20)  # Margini mai mari
        grid_layout.setColumnStretch(0, 1)  # Prima coloană pentru nume
        grid_layout.setColumnStretch(1, 0)  # A doua coloană pentru combobox
        grid_layout.setColumnStretch(2, 1)  # A treia coloană pentru nume (a doua serie)
        grid_layout.setColumnStretch(3, 0)  # A patra coloană pentru combobox (a doua serie)
        
        # Titluri pentru coloane
        col1_header = QLabel("Tip Document")
        col1_header.setFont(QFont("Arial", 16, QFont.Bold))  # Font mărit
        grid_layout.addWidget(col1_header, 0, 0)
        
        col1_highlight = QLabel("Culoare")
        col1_highlight.setFont(QFont("Arial", 16, QFont.Bold))  # Font mărit
        grid_layout.addWidget(col1_highlight, 0, 1)
        
        col2_header = QLabel("Tip Document")
        col2_header.setFont(QFont("Arial", 16, QFont.Bold))  # Font mărit
        grid_layout.addWidget(col2_header, 0, 2)
        
        col2_highlight = QLabel("Culoare")
        col2_highlight.setFont(QFont("Arial", 16, QFont.Bold))  # Font mărit
        grid_layout.addWidget(col2_highlight, 0, 3)
        
        # Calculăm numărul de rânduri pentru fiecare coloană
        total_types = len(self.document_types)
        rows_per_column = (total_types + 1) // 2  # Împărțim în două coloane (rotunjit în sus)
        
        # Dicționar pentru a ține evidența combobox-urilor
        comboboxes = {}
        
        # Lista de opțiuni pentru combobox
        color_options = ["Nicio culoare"] + [f"{self.color_names.get(f'color{i+1}', f'Culoarea {i+1}')}" for i in range(4)]
        
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
                
            # Verificăm dacă tipul are culoare asociată
            current_color = self.document_colors.get(doc_type, None)
            
            # Nume tip document - folosim EditableLabel pentru a permite redenumirea
            name_label = EditableLabel(doc_type, dialog)
            name_label.setMinimumHeight(40)  # Înălțime mărită
            grid_layout.addWidget(name_label, row, col_offset)
            
            # Combobox pentru culoare
            combobox = QComboBox()
            combobox.setFont(QFont("Arial", 14))  # Font mărit
            combobox.setMinimumHeight(40)  # Înălțime mărită
            combobox.addItems(color_options)
            
            # Setăm selectia curentă
            if current_color:
                color_index = 0  # Implicit "Nicio culoare"
                for i in range(4):
                    color_key = f"color{i+1}"
                    if current_color == color_key:
                        color_index = i + 1  # +1 pentru că prima opțiune e "Nicio culoare"
                        break
                combobox.setCurrentIndex(color_index)
                
                # Aplicăm culoarea de fundal pentru nume
                if current_color in self.colors:
                    name_label.setStyleSheet(f"background-color: {self.colors[current_color]}; padding: 10px; border-radius: 5px;")  # Padding mărit
            
            grid_layout.addWidget(combobox, row, col_offset + 1)
            comboboxes[doc_type] = combobox
        
        # Adăugare separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setLineWidth(2)  # Linie mai groasă
        layout.addWidget(separator)
        
        # Formular pentru adăugarea unui nou tip de document
        add_form_layout = QHBoxLayout()
        add_form_layout.setSpacing(15)  # Spațiere mărită
        layout.addLayout(add_form_layout)
        
        add_label = QLabel("Adaugă Tip Document Nou:")
        add_label.setFont(QFont("Arial", 16))  # Font mărit
        add_form_layout.addWidget(add_label)
        
        new_doc_type_entry = QLineEdit()
        new_doc_type_entry.setFont(QFont("Arial", 14))  # Font mărit
        new_doc_type_entry.setMinimumHeight(50)  # Înălțime mărită
        add_form_layout.addWidget(new_doc_type_entry, 1)  # 1 = stretch factor
        
        new_color_combo = QComboBox()
        new_color_combo.setFont(QFont("Arial", 14))  # Font mărit
        new_color_combo.setMinimumHeight(50)  # Înălțime mărită
        new_color_combo.addItems(color_options)
        add_form_layout.addWidget(new_color_combo)
        
        add_button = QPushButton("Adaugă")
        add_button.setFont(QFont("Arial", 14, QFont.Bold))  # Font mărit și îngroșat
        add_button.setMinimumSize(150, 50)  # Buton mai mare
        add_form_layout.addWidget(add_button)
        
        # Butoane dialog
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(20)  # Spațiere mărită
        layout.addLayout(bottom_layout)
        
        # Buton pentru configurarea culorilor
        colors_button = QPushButton("Configurare Culori")
        colors_button.setFont(QFont("Arial", 14))  # Font mărit
        colors_button.setMinimumSize(200, 60)  # Buton mai mare
        colors_button.clicked.connect(self.show_color_settings_dialog)
        bottom_layout.addWidget(colors_button)
        
        # Spațiu pentru aliniere
        bottom_layout.addStretch(1)
        
        # Butoanele standard
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        ok_button = button_box.button(QDialogButtonBox.Ok)
        ok_button.setText("Salvează")
        ok_button.setFont(QFont("Arial", 14))  # Font mărit
        ok_button.setMinimumSize(180, 60)  # Buton mai mare
        
        cancel_button = button_box.button(QDialogButtonBox.Cancel)
        cancel_button.setText("Anulează")
        cancel_button.setFont(QFont("Arial", 14))  # Font mărit
        cancel_button.setMinimumSize(180, 60)  # Buton mai mare
        
        bottom_layout.addWidget(button_box)
        
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
                
                # Sortăm tipurile în ordine alfabetică
                self.document_types.sort()
                
                # Setăm culoarea dacă s-a selectat una
                color_index = new_color_combo.currentIndex()
                if color_index > 0:  # 0 = Nicio culoare
                    color_key = f"color{color_index}"
                    self.document_colors[doc_type_name] = color_key
                
                # Reconstruim interfața
                # Pentru simplitate, reîncărcăm dialogul
                QMessageBox.information(dialog, "Succes", 
                                      "Tip document adăugat cu succes. Închideți și redeschideți dialogul pentru a vedea actualizările.")
                
                # Golire câmp
                new_doc_type_entry.clear()
                new_color_combo.setCurrentIndex(0)
                
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
            # Salvează setările de culoare
            print("\nSalvare setări culoare:")
            for name, combobox in comboboxes.items():
                color_index = combobox.currentIndex()
                if color_index == 0:  # "Nicio culoare" selectat
                    if name in self.document_colors:
                        del self.document_colors[name]
                        print(f"  - {name}: culoare ștearsă")
                else:
                    color_key = f"color{color_index}"
                    self.document_colors[name] = color_key
                    print(f"  - {name}: {color_key}")
            
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

    def go_to_today(self): # <<< AICI POȚI ADĂUGA NOUA METODĂ
        """Navigare la săptămâna curentă"""
        self.current_date = datetime.datetime.now()
        self.week_start = self.current_date - timedelta(days=self.current_date.weekday())
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
        """Creare subsol cu informații despre autor și ultima intervenție"""
        footer_frame = QFrame()
        footer_frame.setFrameStyle(QFrame.StyledPanel)
        footer_frame.setLineWidth(1)
        footer_frame.setFixedHeight(50)  # Mărește înălțimea de la 40 la 50
        parent_layout.addWidget(footer_frame)
        
        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setContentsMargins(10, 5, 10, 5)
        
        # Label pentru ultima intervenție - font mărit
        self.last_action_label = QLabel("Ultima intervenție: -")
        self.last_action_label.setFont(QFont("Arial", 12, QFont.Bold))  # Mărit de la 10 la 12
        self.last_action_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        # Modificăm layout-ul pentru a oferi mai mult spațiu orizontal
        footer_layout.addWidget(self.last_action_label, 3)  # Creștem stretch factor-ul de la 1 la 3
        
        # Numele autorului în dreapta - font mărit
        author_label = QLabel("Mihai Mereu")
        author_label.setFont(QFont("Arial", 12, QFont.Bold))  # Mărit de la 10 la 12
        author_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        author_label.setFixedWidth(180)  # Mărit de la 150 la 180 pentru a acomoda fontul mai mare
        footer_layout.addWidget(author_label)
        
        # Inițializăm label-ul cu ultima acțiune
        self.update_last_action_label()

    def log_intervention(self, action_text):
        """Scrie o intervenție în fișierul de log, păstrând un istoric complet"""
        try:
            # Creăm un nume de fișier bazat pe data curentă (un fișier per lună)
            current_date = datetime.datetime.now()
            log_filename = f"interventii_{current_date.year}_{current_date.month:02d}.log"
            
            # Adăugăm timestamp actual pentru însemnarea în log
            timestamp = current_date.strftime("%Y-%m-%d %H:%M:%S")
            
            # Verificăm ultima linie din log pentru a evita duplicarea
            last_log_line = ""
            try:
                if os.path.exists(log_filename):
                    with open(log_filename, "r", encoding="utf-8") as read_file:
                        lines = read_file.readlines()
                        if lines:
                            last_log_line = lines[-1].strip()
            except Exception:
                pass
            
            # Construim noua linie de log
            new_log_line = f"[{timestamp}] {action_text}"
            
            # Verificăm dacă nu este o duplicare a ultimei înregistrări
            if new_log_line != last_log_line:
                # Scriem în fișierul de log (mod append)
                with open(log_filename, "a", encoding="utf-8") as log_file:
                    # Adăugăm timestamp și textul intervenției
                    log_file.write(f"{new_log_line}\n")
                    
                print(f"Intervenție înregistrată în log: {log_filename}")
            else:
                print(f"Intervenție duplicată, nu a fost înregistrată în log")
                
        except Exception as e:
            print(f"Eroare la scrierea în fișierul de log: {e}")

    def log_observations_changes(self, appointment_id, old_observations, new_observations, action_type="modificare"):
        """
        Înregistrează modificările făcute la câmpul de observații în fișierul de log general
        
        Parameters:
        -----------
        appointment_id : int
            ID-ul programării
        old_observations : str
            Textul observațiilor înainte de modificare
        new_observations : str
            Textul observațiilor după modificare
        action_type : str
            Tipul acțiunii: "creare", "modificare", "ștergere"
        """
        try:
            # Obținem detalii despre programare pentru context
            self.cursor.execute('''
                SELECT day, time, client_name, document_type
                FROM appointments
                WHERE id = ?
            ''', (appointment_id,))
            
            appointment_details = self.cursor.fetchone()
            if not appointment_details:
                print(f"Nu s-au găsit detalii pentru programarea cu ID-ul {appointment_id}")
                return
                
            day, time, client_name, document_type = appointment_details
            
            # Determinăm tipul de modificare și formatăm mesajul corespunzător
            if action_type == "creare":
                if new_observations and new_observations.strip():
                    change_description = f"OBSERVAȚII NOI: \"{new_observations}\""
                else:
                    # Nu logăm dacă nu s-au adăugat observații la creare
                    return
            elif action_type == "modificare":
                if old_observations == new_observations:
                    # Nu logăm dacă nu s-a schimbat nimic
                    return
                elif not old_observations or old_observations.strip() == "":
                    change_description = f"OBSERVAȚII ADĂUGATE: \"{new_observations}\""
                elif not new_observations or new_observations.strip() == "":
                    change_description = f"OBSERVAȚII ȘTERSE: Era: \"{old_observations}\""
                else:
                    change_description = f"OBSERVAȚII MODIFICATE:\n  Vechi: \"{old_observations}\"\n  Nou: \"{new_observations}\""
            else:  # ștergere
                if old_observations and old_observations.strip():
                    change_description = f"OBSERVAȚII ȘTERSE (odată cu programarea): \"{old_observations}\""
                else:
                    # Nu logăm dacă nu erau observații
                    return
                    
            # Formatăm data programării pentru afișare
            appointment_date = datetime.datetime.strptime(day, "%Y-%m-%d")
            formatted_date = f"{appointment_date.day} {self.month_names_ro[appointment_date.month-1]} {appointment_date.year}"
            
            # Creăm mesajul pentru log
            action_text = f"{action_type.upper()} OBSERVAȚII - Programare {client_name}, {document_type}, {formatted_date}, ora {time} - {change_description}"
            
            # Folosim metoda existentă pentru a scrie în log
            self.log_intervention(action_text)
                
        except Exception as e:
            print(f"Eroare la scrierea modificărilor observațiilor în fișierul de log: {e}")

    # 2. Adăugăm o metodă nouă pentru a obține ultima intervenție
    def update_last_action_label(self):
        """Actualizează label-ul cu informații despre ultima intervenție și scrie în log"""
        try:
            # Obținem cea mai recentă modificare din baza de date (creată, modificată sau ștearsă)
            self.cursor.execute('''
                SELECT 
                    CASE
                        WHEN modified_at IS NOT NULL AND deleted_at IS NULL THEN 'modificată'
                        WHEN deleted_at IS NOT NULL THEN 'ștearsă'
                        ELSE 'creată'
                    END as action_type,
                    CASE
                        WHEN modified_at IS NOT NULL AND deleted_at IS NULL THEN modified_at
                        WHEN deleted_at IS NOT NULL THEN deleted_at
                        ELSE created_at
                    END as action_time,
                    day, 
                    time, 
                    document_type, 
                    client_name,
                    CASE
                        WHEN modified_at IS NOT NULL AND deleted_at IS NULL THEN modified_by
                        WHEN deleted_at IS NOT NULL THEN deleted_by
                        ELSE computer_name
                    END as action_by
                FROM appointments
                ORDER BY 
                    CASE
                        WHEN modified_at IS NOT NULL AND deleted_at IS NULL THEN modified_at
                        WHEN deleted_at IS NOT NULL THEN deleted_at
                        ELSE created_at
                    END DESC
                LIMIT 1
            ''')
            
            last_action = self.cursor.fetchone()
            
            if last_action:
                action_type, action_time, day, time, doc_type, client_name, action_by = last_action
                
                # Formatăm datele pentru afișare
                try:
                    # Data acțiunii (creare/modificare/ștergere)
                    action_datetime = datetime.datetime.strptime(action_time, "%Y-%m-%d %H:%M:%S")
                    # Folosim luna cu nume întreg
                    formatted_time = action_datetime.strftime("%d %B %Y %H:%M")
                    # Înlocuim numele lunii în engleză cu numele lunii în română
                    month_index = action_datetime.month - 1
                    month_name_ro = self.month_names_ro[month_index]
                    formatted_time = formatted_time.replace(action_datetime.strftime("%B"), month_name_ro)
                    
                    # Data programării
                    appointment_date = datetime.datetime.strptime(day, "%Y-%m-%d")
                    # Folosim luna cu nume întreg
                    formatted_appointment_date = appointment_date.strftime("%d %B %Y")
                    # Înlocuim numele lunii în engleză cu numele lunii în română
                    month_index = appointment_date.month - 1
                    month_name_ro = self.month_names_ro[month_index]
                    formatted_appointment_date = formatted_appointment_date.replace(appointment_date.strftime("%B"), month_name_ro)
                except:
                    # În caz de eroare, folosim string-urile originale
                    formatted_time = action_time[:16]
                    formatted_appointment_date = day
                
                # Construim textul pentru ultima intervenție cu formatul nou
                action_text = f"Ultima intervenție: programare {action_type} de către {action_by}, {formatted_time}. ({doc_type}, {client_name}, {formatted_appointment_date})"
                
                # Permitem textului să fie mai lung (dublăm lungimea maximă)
                max_length = 200  # Număr extins de caractere care încap în label
                if len(action_text) > max_length:
                    action_text = action_text[:max_length-3] + "..."
                
                self.last_action_label.setText(action_text)
                
                # Nu înregistrăm în log dacă suntem la pornirea inițială a aplicației
                if hasattr(self, 'initial_startup') and self.initial_startup:
                    print("Pornire inițială - nu se scrie în log ultima intervenție")
                else:
                    # Adăugăm înregistrarea în log
                    self.log_intervention(action_text)
            else:
                self.last_action_label.setText("Ultima intervenție: -")
                    
        except Exception as e:
            print(f"Eroare la actualizarea informațiilor despre ultima intervenție: {e}")
            self.last_action_label.setText("Ultima intervenție: -")
        
    def show_calendar_dialog(self):
        """Afișează un dialog cu calendar pentru navigare rapidă și marcare zile nelucrătoare"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Selectează data / Marchează SĂRBĂTORI LEGALE") 
        dialog.setMinimumWidth(800)
        dialog.setMinimumHeight(600)
        
        layout = QVBoxLayout(dialog)
        
        calendar_widget = QCalendarWidget()
        calendar_widget.setGridVisible(True)
        calendar_widget.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        calendar_widget.setHorizontalHeaderFormat(QCalendarWidget.LongDayNames)
        
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
            }
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                height: 60px;
            }
            QCalendarWidget QTableView {
                font-size: 14px; 
                selection-background-color: lightblue;
            }
            QCalendarWidget QTableView::item {
                height: 35px; 
                width: 35px;
            }
        """)
        
        calendar_widget.setMinimumSize(780, 500)
        # Setează data curentă a calendarului la începutul săptămânii afișate
        current_qdate = QDate(self.week_start.year, self.week_start.month, self.week_start.day)
        calendar_widget.setSelectedDate(current_qdate) 
        # Poți de asemenea să setezi luna vizibilă:
        # calendar_widget.setCurrentPage(self.week_start.year, self.week_start.month)
        
        # Formatare pentru zilele de sărbătoare (fundal ROȘU)
        holiday_format = QTextCharFormat()
        holiday_format.setBackground(QColor("red")) # Roșu pur
        # Pentru un roșu mai puțin intens, poți folosi:
        # holiday_format.setBackground(QColor(255, 138, 128)) # Exemplu: #FF8A80
        # holiday_format.setForeground(QColor("white")) # Opțional: text alb pe fundal roșu

        default_day_format = QTextCharFormat() # Format implicit pentru resetare

        # Aplicăm formatarea la încărcare pentru sărbătorile deja marcate
        # self.non_working_days_set este deja populat de load_non_working_days() din SQLite
        for holiday_py_date in self.non_working_days_set:
            q_date = QDate(holiday_py_date.year, holiday_py_date.month, holiday_py_date.day)
            calendar_widget.setDateTextFormat(q_date, holiday_format)

        def calendar_context_menu(position):
            selected_q_date = calendar_widget.selectedDate() # Ia data efectiv selectată de utilizator în widget
            selected_py_date = selected_q_date.toPyDate()

            menu = QMenu(calendar_widget)
            is_weekend = selected_py_date.weekday() >= 5 

            if selected_py_date in self.non_working_days_set: # Este o sărbătoare marcată
                action_mark_workday = menu.addAction("Demarchează sărbătoarea (devine lucrătoare)")
            elif is_weekend:
                info_action = menu.addAction("Weekend (nelucrătoare implicit)")
                info_action.setEnabled(False)
            else: # Este zi L-V și nu e în setul de sărbători
                action_mark_holiday = menu.addAction("Marchează ca SĂRBĂTOARE LEGALĂ")

            action = menu.exec_(calendar_widget.mapToGlobal(position))

            if action:
                original_non_working_days_set_size = len(self.non_working_days_set)

                if action.text() == "Marchează ca SĂRBĂTOARE LEGALĂ":
                    if self.add_non_working_day(selected_py_date): # Salvează în SQLite
                        calendar_widget.setDateTextFormat(selected_q_date, holiday_format)
                elif action.text() == "Demarchează sărbătoarea (devine lucrătoare)":
                    if self.remove_non_working_day(selected_py_date): # Șterge din SQLite
                        calendar_widget.setDateTextFormat(selected_q_date, default_day_format)
                
                if len(self.non_working_days_set) != original_non_working_days_set_size:
                    self.refresh_calendar() # Actualizează calendarul principal
        
        calendar_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        calendar_widget.customContextMenuRequested.connect(calendar_context_menu)
        
        layout.addWidget(calendar_widget)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        ok_button = button_box.button(QDialogButtonBox.Ok)
        ok_button.setFont(QFont("Arial", 14))
        ok_button.setMinimumSize(120, 40)
        
        cancel_button = button_box.button(QDialogButtonBox.Cancel)
        cancel_button.setFont(QFont("Arial", 14))
        cancel_button.setMinimumSize(120, 40)
        
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog_result = dialog.exec_()

        if dialog_result == QDialog.Accepted:
            selected_date_py = calendar_widget.selectedDate().toPyDate()
            selected_date_dt = datetime.datetime.combine(selected_date_py, datetime.time.min)
            self.week_start = selected_date_dt - timedelta(days=selected_date_dt.weekday())
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

                        # Sortăm lista alfabetic
                        self.document_types.sort()
                        
                        # Încărcăm informațiile despre culori
                        if 'colors' in data:
                            self.colors = data['colors']
                        else:
                            self.colors = self.default_colors.copy()
                        
                        # Încărcăm numele culorilor
                        if 'color_names' in data:
                            self.color_names = data['color_names']
                        
                        # Încărcăm asocierile tipuri-culori
                        if 'document_colors' in data:
                            self.document_colors = data['document_colors']
                        elif 'highlighted_types' in data:
                            # Compatibilitate cu versiunea veche
                            self.document_colors = {}
                            for doc_type, highlighted in data['highlighted_types'].items():
                                if highlighted:
                                    self.document_colors[doc_type] = "color1"  # Culoarea 1 = Verde (original)
                        
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
                'document_colors': self.document_colors,
                'colors': self.colors,
                'color_names': self.color_names
            }
            
            # Adăugăm ultima selecție dacă există
            if hasattr(self, 'last_doc_type_selection'):
                data['last_selection'] = self.last_doc_type_selection
            
            # Salvăm în fișier
            with open(json_file_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
                
            print(f"Tipuri de documente și configurație culori salvate cu succes în {json_file_path}")
            return True
            
        except Exception as e:
            print(f"Eroare la salvarea tipurilor de documente în JSON: {e}")
            return False

    def check_app_lock(self):
        """Verifică dacă aplicația este deja deschisă în rețea"""
        # Folosim un fișier în același director cu baza de date pentru lock
        self.lock_file = 'notarial_scheduler.lock'
        
        try:
            # Verifică dacă există deja un lock
            if os.path.exists(self.lock_file):
                # Citim conținutul pentru a vedea cine deține lock-ul
                try:
                    with open(self.lock_file, 'r') as f:
                        lock_info = f.read().strip()
                    
                    # Verificăm dacă lock-ul este vechi (mai mult de 4 ore)
                    try:
                        lock_parts = lock_info.split('|')
                        if len(lock_parts) >= 2:
                            lock_time_str = lock_parts[1]
                            lock_time = datetime.datetime.strptime(lock_time_str, "%Y-%m-%d %H:%M:%S")
                            current_time = datetime.datetime.now()
                            
                            # Dacă lock-ul este mai vechi de 4 ore, îl considerăm invalid
                            if (current_time - lock_time).total_seconds() > 4 * 3600:  # 4 ore în secunde
                                print(f"Lock vechi detectat ({lock_time_str}), va fi șters automat.")
                                os.remove(self.lock_file)
                                # Continuă cu crearea unui nou lock
                            else:
                                # Lock valid - arată dialogul și închide aplicația
                                self.show_lock_dialog(lock_info)
                                return False
                        else:
                            # Format lock invalid - arată dialogul și închide aplicația
                            self.show_lock_dialog(lock_info)
                            return False
                    except Exception as e:
                        print(f"Eroare la verificarea timpului lock-ului: {e}")
                        # În caz de eroare, presupunem că lock-ul este valid
                        self.show_lock_dialog(lock_info)
                        return False
                except Exception as e:
                    print(f"Eroare la citirea fișierului lock: {e}")
                    # Dacă nu putem citi fișierul, încercăm să-l ștergem
                    try:
                        os.remove(self.lock_file)
                    except:
                        pass
            
            # Creează lock-ul cu informații despre computer și timp
            with open(self.lock_file, 'w') as f:
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ip_address = "necunoscut"
                try:
                    ip_address = socket.gethostbyname(socket.gethostname())
                except:
                    pass
                
                lock_info = f"{self.computer_name} ({ip_address})|{current_time}"
                f.write(lock_info)
            
            print(f"Lock creat: {lock_info}")
            
            # Înregistrează o funcție pentru ștergerea lock-ului la închiderea aplicației
            atexit.register(self.remove_app_lock)
            
            # Adaugă și un handler pentru închiderea anormală
            signal.signal(signal.SIGINT, self.signal_handler)
            signal.signal(signal.SIGTERM, self.signal_handler)
            
            return True
        
        except Exception as e:
            print(f"Eroare la verificarea/crearea lock-ului: {e}")
            QMessageBox.warning(
                None, 
                "Avertisment", 
                f"Nu s-a putut verifica sau crea lock-ul aplicației: {e}\n\n"
                "Continuarea poate duce la probleme de sincronizare dacă aplicația "
                "este deschisă simultan pe mai multe stații."
            )
            return True  # Continuăm oricum

    def show_lock_dialog(self, lock_info):
        """Afișează dialogul că aplicația este deja deschisă"""
        # Extrage doar partea cu numele computerului
        computer_info = lock_info.split('|')[0] if '|' in lock_info else lock_info
        
        dialog = QDialog(None)
        dialog.setWindowTitle("Aplicație deja deschisă")
        dialog.setMinimumWidth(400)
        dialog.setMinimumHeight(200)
        
        layout = QVBoxLayout(dialog)
        
        # Pictogramă de avertizare
        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignCenter)
        # Putem folosi un emoji pentru avertizare
        icon_label.setText("⚠️")
        icon_label.setFont(QFont("Arial", 48))
        layout.addWidget(icon_label)
        
        # Mesaj
        message = QLabel(
            f"Aplicația este deja deschisă pe stația:\n{computer_info}\n\n"
            "Nu puteți deschide aplicația simultan de pe mai multe stații."
        )
        message.setAlignment(Qt.AlignCenter)
        message.setWordWrap(True)
        message.setFont(QFont("Arial", 12))
        layout.addWidget(message)
        
        # Butoane
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)
        
        # Buton de închidere
        close_btn = QPushButton("Închide")
        close_btn.setFont(QFont("Arial", 12))
        close_btn.setMinimumSize(120, 40)
        close_btn.clicked.connect(lambda: sys.exit(1))
        button_layout.addWidget(close_btn)
        
        # Buton de forțare (pentru situații când lock-ul a rămas blocat)
        force_btn = QPushButton("Forțează deschidere")
        force_btn.setFont(QFont("Arial", 12))
        force_btn.setMinimumSize(180, 40)
        force_btn.setStyleSheet("background-color: #ffcccc;")  # Roșu deschis
        force_btn.clicked.connect(lambda: self.force_open(dialog))
        button_layout.addWidget(force_btn)
        
        dialog.exec_()

    def force_open(self, dialog):
        """Forțează deschiderea aplicației prin ștergerea lock-ului"""
        reply = QMessageBox.question(
            dialog, 
            "Confirmare forțare", 
            "Forțarea deschiderii aplicației când aceasta este deja deschisă "
            "pe o altă stație poate duce la probleme de sincronizare și pierderi de date.\n\n"
            "Sunteți sigur că doriți să continuați?",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                os.remove(self.lock_file)
                print("Lock șters prin forțare")
                
                # Creăm un lock nou
                with open(self.lock_file, 'w') as f:
                    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ip_address = "necunoscut"
                    try:
                        ip_address = socket.gethostbyname(socket.gethostname())
                    except:
                        pass
                    
                    lock_info = f"{self.computer_name} ({ip_address})|{current_time}"
                    f.write(lock_info)
                
                # Înregistrează o funcție pentru ștergerea lock-ului la închiderea aplicației
                atexit.register(self.remove_app_lock)
                
                # Adaugă și un handler pentru închiderea anormală
                signal.signal(signal.SIGINT, self.signal_handler)
                signal.signal(signal.SIGTERM, self.signal_handler)
                
                # Închide dialogul și continuă
                dialog.accept()
            except Exception as e:
                QMessageBox.critical(
                    dialog, 
                    "Eroare", 
                    f"Nu s-a putut șterge lock-ul: {e}\n\nAplicația va fi închisă."
                )
                sys.exit(1)

    def remove_app_lock(self):
        """Șterge fișierul lock la închiderea aplicației"""
        try:
            if hasattr(self, 'lock_file') and os.path.exists(self.lock_file):
                os.remove(self.lock_file)
                print("Lock șters cu succes")
        except Exception as e:
            print(f"Eroare la ștergerea lock-ului: {e}")

    def signal_handler(self, sig, frame):
        """Handler pentru semnale de închidere"""
        self.remove_app_lock()
        sys.exit(0)

    def closeEvent(self, event):
        """Handler pentru închiderea ferestrei principale"""
        # Salvează poziția și dimensiunea ferestrei
        self.save_window_position()
        
        # Șterge lock-ul aplicației
        self.remove_app_lock()
        
        # Acceptă evenimentul de închidere
        event.accept()

    def moveEvent(self, event):
        """Handler pentru evenimentul de mișcare a ferestrei"""
        super().moveEvent(event)
        # Folosim un timer pentru a evita salvarea prea frecventă
        QTimer.singleShot(500, self.save_window_position)

    def resizeEvent(self, event):
        """Handler pentru evenimentul de redimensionare a ferestrei"""
        super().resizeEvent(event)
        # Folosim un timer pentru a evita salvarea prea frecventă
        QTimer.singleShot(500, self.save_window_position)

class EditableLabel(QLabel):
    """Etichetă care permite editarea cu dublu click"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.text = text
        self.setWordWrap(True)
        
    def mouseDoubleClickEvent(self, event):
        self.startEditing()
        
    def startEditing(self):
        # Obține informația despre tipul de document și index
        doc_type = self.text
        parent_dialog = self.parent().window()
        
        # Creează dialog pentru editare
        edit_dialog = QDialog(parent_dialog)
        edit_dialog.setWindowTitle("Redenumire Tip Document")
        edit_dialog.setMinimumWidth(400)
        
        # Layout pentru dialog
        layout = QVBoxLayout(edit_dialog)
        
        # Mesaj explicativ
        info_label = QLabel("Redenumește tipul de document:")
        info_label.setFont(QFont("Arial", 11))
        layout.addWidget(info_label)
        
        # Câmp text pentru noul nume
        edit_field = QLineEdit(doc_type)
        edit_field.setFont(QFont("Arial", 11))
        edit_field.selectAll()
        layout.addWidget(edit_field)
        
        # Avertisment
        warning_label = QLabel("Atenție: Redenumirea va afecta toate programările existente. "
                            "Asigurați-vă că actualizați și programările existente dacă este necesar.")
        warning_label.setWordWrap(True)
        warning_label.setStyleSheet("color: #FF5252;")
        layout.addWidget(warning_label)
        
        # Butoane
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(button_box)
        
        button_box.accepted.connect(edit_dialog.accept)
        button_box.rejected.connect(edit_dialog.reject)
        
        # Execută dialog
        if edit_dialog.exec_() == QDialog.Accepted:
            new_name = edit_field.text().strip()
            
            # Verifică dacă numele e gol
            if not new_name:
                QMessageBox.warning(parent_dialog, "Eroare", "Numele tipului de document nu poate fi gol.")
                return
                
            # Verifică dacă numele există deja
            scheduler = parent_dialog.parent()  # NotarialScheduler
            if new_name in scheduler.document_types and new_name != doc_type:
                QMessageBox.warning(parent_dialog, "Eroare", "Acest tip de document există deja.")
                return
                
            # Confirmarea modificării în baza de date
            reply = QMessageBox.question(
                parent_dialog,
                "Confirmare", 
                f"Sigur doriți să redenumiti tipul de document din \"{doc_type}\" în \"{new_name}\"?\n\n"
                "Toate programările existente cu acest tip vor fi actualizate.",
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                try:
                    # Actualizează numele în lista de tipuri
                    index = scheduler.document_types.index(doc_type)
                    scheduler.document_types[index] = new_name
                    
                    # Actualizăm și document_colors dacă e necesar
                    if doc_type in scheduler.document_colors:
                        color = scheduler.document_colors[doc_type]
                        del scheduler.document_colors[doc_type]
                        scheduler.document_colors[new_name] = color
                    
                    # Actualizează toate programările existente
                    scheduler.cursor.execute(
                        "UPDATE appointments SET document_type = ? WHERE document_type = ?",
                        (new_name, doc_type)
                    )
                    scheduler.conn.commit()
                    
                    # Salvează configurația
                    scheduler.save_document_types_to_json()
                    
                    # Actualizează eticheta din dialog
                    self.setText(new_name)
                    self.text = new_name
                    
                    QMessageBox.information(
                        parent_dialog,
                        "Succes",
                        f"Tipul de document a fost redenumit în \"{new_name}\".\n"
                        "Toate programările au fost actualizate."
                    )
                    
                except Exception as e:
                    QMessageBox.critical(
                        parent_dialog,
                        "Eroare",
                        f"Nu s-a putut redenumi tipul de document: {e}"
                    )

class CurrencyFetcher(QThread):
    """Thread separat pentru preluarea cursului valutar BNR"""
    currency_fetched = pyqtSignal(dict)
    
    def run(self):
        try:
            print("\n--- Încercare preluare curs valutar ---")
            # Obținem ora curentă pentru logging
            current_time = datetime.datetime.now().strftime("%H:%M:%S")
            print(f"[{current_time}] Inițiere preluare curs valutar")
            
            # Preluăm cursul de pe site-ul alternativ
            currency_data = self.fetch_currency()
            print(f"Date curs obținute: {currency_data}")
            self.currency_fetched.emit(currency_data)
        except Exception as e:
            print(f"Eroare critică la obținerea cursului valutar: {e}")
            # Emitem un dict gol în caz de eroare
            self.currency_fetched.emit({})
    
    def fetch_currency(self):
        """Preia cursul Euro-Leu de pe cursbnr.ro"""
        try:
            url = "https://www.cursbnr.ro/"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            
            print(f"GET request la {url}")
            response = requests.get(url, headers=headers, timeout=10)
            print(f"Status code: {response.status_code}")
            
            if response.status_code != 200:
                print(f"Eroare HTTP: {response.status_code}")
                return {}
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Căutăm elementul cu EURO
            euro_elements = soup.find_all(string=re.compile('EURO', re.IGNORECASE))
            print(f"Am găsit {len(euro_elements)} elemente cu 'EURO'")
            
            result = {}
            
            for elem in euro_elements:
                parent = elem.parent
                if not parent:
                    continue
                    
                # Urcăm în ierarhie pentru a găsi blocul cu rata
                container = parent
                for _ in range(3):  # Urcăm maxim 3 niveluri
                    if container:
                        container = container.parent
                
                if not container:
                    continue
                    
                container_text = container.get_text()
                
                # Căutăm valoarea Euro
                rate_match = re.search(r'(\d+[.,]\d+)\s*(?:RON|lei)', container_text, re.IGNORECASE)
                if rate_match:
                    euro_rate = rate_match.group(1).replace(',', '.')
                    print(f"Valoare extrasă: {euro_rate}")
                    
                    # Căutăm variația directă în lei
                    variation_match = re.search(r'1 EURO = \d+[.,]\d+ Lei\s*([+-]?\d+[.,]\d+)', container_text, re.IGNORECASE)
                    variation = 0.0
                    direction = 'same'
                    
                    if variation_match:
                        variation_str = variation_match.group(1).replace(',', '.')
                        variation = float(variation_str)
                        print(f"Variație: {variation} Lei")
                        direction = 'up' if variation > 0 else 'down' if variation < 0 else 'same'
                    
                    result = {
                        'rate': float(euro_rate),
                        'variation': variation,
                        'direction': direction
                    }
                    
                    # Calculăm cursul precedent în funcție de variație
                    prev_rate = float(euro_rate) - variation
                    result['prev_rate'] = prev_rate
                    
                    # Adăugăm și timpul actualizării
                    result['update_time'] = datetime.datetime.now().strftime("%H:%M")
                    
                    return result
            
            return {}
            
        except Exception as e:
            print(f"Eroare la preluarea cursului: {e}")
            return {}

class CurrencyWidget(QFrame):
    """Widget pentru afișarea cursului valutar"""
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configurare widget
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setLineWidth(1)
        self.setFixedHeight(60)
        self.setMinimumWidth(340)  # Mărit pentru a încăpea ambele cursuri
        self.setAutoFillBackground(True)
        
        # Fundal alb
        palette = QPalette()
        palette.setColor(QPalette.Background, QColor("#FFFFFF"))
        self.setPalette(palette)
        
        # Layout pentru widget
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(15)  # Spațiere mărită între elemente
        
        # Layout pentru cursul precedent
        prev_layout = QVBoxLayout()
        layout.addLayout(prev_layout)
        
        # Etichetă pentru cursul precedent
        self.prev_header = QLabel("Curs precedent:")
        self.prev_header.setFont(QFont("Arial", 9, QFont.Bold))
        self.prev_header.setStyleSheet("color: #666666;")
        prev_layout.addWidget(self.prev_header)
        
        # Valoarea cursului precedent
        self.prev_rate_label = QLabel("...")
        self.prev_rate_label.setFont(QFont("Arial", 11))
        self.prev_rate_label.setStyleSheet("color: #666666;")
        prev_layout.addWidget(self.prev_rate_label)
        
        # Separator vertical
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: #CCCCCC;")
        layout.addWidget(separator)
        
        # Săgeată pentru direcție
        self.arrow_label = QLabel()
        self.arrow_label.setFixedSize(30, 30)
        self.arrow_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.arrow_label)
        
        # Layout pentru informații curs actual
        info_layout = QVBoxLayout()
        layout.addLayout(info_layout)
        
        # Etichetă pentru cursul actual
        self.current_header = QLabel("Curs actual:")
        self.current_header.setFont(QFont("Arial", 9, QFont.Bold))
        info_layout.addWidget(self.current_header)
        
        # Valoarea cursului
        self.rate_label = QLabel("...")
        self.rate_label.setFont(QFont("Arial", 12, QFont.Bold))
        info_layout.addWidget(self.rate_label)
        
        # Layout pentru informații despre actualizare
        update_layout = QVBoxLayout()
        layout.addLayout(update_layout)
        
        # Etichetă pentru ora actualizării
        self.update_time_label = QLabel("")
        self.update_time_label.setFont(QFont("Arial", 9))
        self.update_time_label.setStyleSheet("color: #666666;")
        update_layout.addWidget(self.update_time_label, alignment=Qt.AlignRight | Qt.AlignVCenter)
        
        # Variația cursului
        self.variation_label = QLabel("Se încarcă...")
        self.variation_label.setFont(QFont("Arial", 9))
        update_layout.addWidget(self.variation_label, alignment=Qt.AlignRight | Qt.AlignVCenter)
        
        # Starea inițială - "Loading..."
        self.update_display(None)
        
        # Thread pentru preluarea cursului
        self.currency_thread = None
        
        # Timer pentru actualizare periodică
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.fetch_currency)
        
        # Preluăm cursul imediat și apoi o dată la 60 de minute
        self.fetch_currency()
        self.update_timer.start(60 * 60 * 1000)  # Actualizare la fiecare oră
    
    def fetch_currency(self):
        """Pornește thread-ul pentru preluarea cursului valutar"""
        if self.currency_thread is None or not self.currency_thread.isRunning():
            self.currency_thread = CurrencyFetcher()
            self.currency_thread.currency_fetched.connect(self.on_currency_fetched)
            self.currency_thread.start()
    
    def on_currency_fetched(self, data):
        """Primește datele despre curs și actualizează afișarea"""
        self.update_display(data)
    
    def update_display(self, data):
        """Actualizează afișarea cu datele primite"""
        if not data:
            # Afișare "Loading..." sau valoare implicită
            self.rate_label.setText("...")
            self.prev_rate_label.setText("...")
            self.variation_label.setText("Se încarcă...")
            self.variation_label.setStyleSheet("color: gray;")
            self.arrow_label.setText("")
            self.update_time_label.setText("")
            return

        # Actualizare valoare curs actual
        rate = data.get('rate', 0.0)
        self.rate_label.setText(f"{rate:.4f} Lei")

        # Actualizare curs precedent
        prev_rate = data.get('prev_rate', 0.0)
        self.prev_rate_label.setText(f"{prev_rate:.4f} Lei")

        # Obținem ora curentă pentru afișarea momentului actualizării
        current_time = datetime.datetime.now().strftime("%H:%M")
        self.update_time_label.setText(f"Actualizat: {current_time}")

        # Actualizare variație
        variation = data.get('variation', 0.0)
        direction = data.get('direction', 'same')

        if direction == 'up': # Cursul crește (Euro mai scump)
            self.variation_label.setText(f"+{variation:.4f} Lei")
            self.variation_label.setStyleSheet("color: red;")
            self.arrow_label.setText("▲")
            self.arrow_label.setStyleSheet("color: red; font-size: 18px;")

            # Evidențiem cursul actual ca fiind mai mare
            self.rate_label.setStyleSheet("color: red;")
            self.current_header.setStyleSheet("color: red;")

        elif direction == 'down': # Cursul scade (Euro mai ieftin)
            self.variation_label.setText(f"{variation:.4f} Lei")
            self.variation_label.setStyleSheet("color: green;") # Modificat din albastru înapoi în verde
            self.arrow_label.setText("▼")
            self.arrow_label.setStyleSheet("color: green; font-size: 18px;") # Modificat din albastru înapoi în verde

            # Evidențiem cursul actual ca fiind mai mic
            self.rate_label.setStyleSheet("color: green;") # Modificat din albastru înapoi în verde
            self.current_header.setStyleSheet("color: green;") # Modificat din albastru înapoi în verde

        else: # Cursul rămâne la fel
            self.variation_label.setText("0.0000 Lei")
            self.variation_label.setStyleSheet("color: gray;")
            self.arrow_label.setText("●")
            self.arrow_label.setStyleSheet("color: gray; font-size: 18px;")

            # Resetăm stilurile
            self.rate_label.setStyleSheet("color: black;")
            self.current_header.setStyleSheet("color: black;")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Aplicare stil
    app.setStyle("Fusion")
    
    window = NotarialScheduler()
    window.show()
    
    sys.exit(app.exec_())