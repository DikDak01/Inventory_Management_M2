from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QLabel, QLineEdit,
    QDialog, QFormLayout, QMessageBox, QFileDialog
)
from PyQt5.QtGui import QPixmap
import sqlite3
import sys
import os
import logging
import csv

# Initialisiere Logger für Fehlerprotokollierung
LOG_FILE = "error_log.txt"
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)


class Lagerverwaltung:
    """
    Represents a warehouse management system connecting to a SQLite database.

    This class provides methods to handle storage items in a warehouse by creating,
    adding, updating, retrieving, and deleting records in the database. All records
    are managed in a SQLite database table named `LAGERVERWALTUNG`.

    :ivar con: The SQLite connection object for interactions with the database.
    :type con: sqlite3.Connection
    :ivar cur: The SQLite cursor object used for executing database operations.
    :type cur: sqlite3.Cursor
    """
    def __init__(self):
        self.con = sqlite3.connect("management.db")
        self.cur = self.con.cursor()
        self.create_table()

    def create_table(self):
        # Datenbanktabelle erstellen oder falls vorhanden, entsprechend nutzen
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS LAGERVERWALTUNG (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                Datum TEXT NOT NULL,
                Bezeichnung TEXT NOT NULL,
                Typ TEXT NOT NULL,
                Menge INTEGER NOT NULL,
                Raum TEXT NOT NULL,
                Schrank TEXT NOT NULL,
                UNIQUE(Bezeichnung, Typ, Raum, Schrank)
            )
        """)
        self.con.commit()

    def insert_data(self, Datum, Bezeichnung, Typ, Menge, Raum, Schrank):
        try:
            # Daten in die Tabelle einfügen
            self.cur.execute("""
                INSERT INTO LAGERVERWALTUNG (Datum, Bezeichnung, Typ, Menge, Raum, Schrank)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (Datum, Bezeichnung, Typ, int(Menge), Raum, Schrank))
            self.con.commit()
        except sqlite3.IntegrityError:
            raise ValueError(f"Der Artikel '{Bezeichnung}' existiert bereits im Lager.")
        except Exception as e:
            logging.error("Fehler beim Einfügen von Daten: %s", e, exc_info=True)
            raise

    def retrieve_data(self):
        self.cur.execute("SELECT * FROM LAGERVERWALTUNG")
        return self.cur.fetchall()

    def update_data(self, id, Datum, Bezeichnung, Typ, Menge, Raum, Schrank):
        try:
            self.cur.execute("""
                UPDATE LAGERVERWALTUNG
                SET Datum = ?, Bezeichnung = ?, Typ = ?, Menge = ?, Raum = ?, Schrank = ?
                WHERE id = ?
            """, (Datum, Bezeichnung, Typ, int(Menge), Raum, Schrank, id))
            self.con.commit()
        except Exception as e:
            logging.error("Fehler beim Aktualisieren von Daten: %s", e, exc_info=True)
            raise

    def delete_data(self, id):
        self.cur.execute("DELETE FROM LAGERVERWALTUNG WHERE id = ?", (id,))
        self.con.commit()

    def close_connection(self):
        self.con.close()


class AddDataDialog(QDialog):
    """
    Dialog for adding data.

    This class represents a modal dialog window allowing users to input
    various types of data through a form. It contains input fields for
    different attributes like date, description, type, amount, room,
    and cabinet. Two buttons, 'Add' and 'Cancel,' are provided for
    accepting or rejecting the dialog input respectively.

    :ivar inputs: Dictionary holding labels as keys and corresponding
        QLineEdit widgets as values. These widgets capture user input
        for respective attributes.
    :type inputs: dict[str, QLineEdit]
    :ivar btn_add: QPushButton allowing the user to confirm and
        accept the dialog input.
    :type btn_add: QPushButton
    :ivar btn_cancel: QPushButton allowing the user to cancel and
        reject the dialog input.
    :type btn_cancel: QPushButton
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Daten hinzufügen")
        self.setModal(True)

        layout = QFormLayout()
        self.inputs = {
            "Datum": QLineEdit(),
            "Bezeichnung": QLineEdit(),
            "Typ": QLineEdit(),
            "Menge": QLineEdit(),
            "Raum": QLineEdit(),
            "Schrank": QLineEdit()
        }

        for label, widget in self.inputs.items():
            layout.addRow(label, widget)

        self.btn_add = QPushButton("Hinzufügen")
        self.btn_cancel = QPushButton("Abbrechen")
        self.btn_add.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

        layout.addRow(self.btn_add, self.btn_cancel)
        self.setLayout(layout)

    def get_data(self):
        return {key: widget.text() for key, widget in self.inputs.items()}


class MainWindow(QMainWindow):
    """
    Represents the main window of the "Lagerverwaltung" application.

    Provides the graphical user interface for managing inventory data with
    functionalities such as adding, deleting, filtering, and exporting inventory
    information. This window includes widgets for interaction and visualization,
    and connects to the logical backend for data management.

    :ivar search_field: Input field for searching/filtering table entries.
    :type search_field: QLineEdit
    :ivar table_widget: Table displaying inventory data.
    :type table_widget: QTableWidget
    :ivar lagerverwaltung: Backend logic for inventory management.
    :type lagerverwaltung: Lagerverwaltung
    """
    def __init__(self):
        super().__init__()
        self.search_field = None
        self.setWindowTitle("Lagerverwaltung")
        self.setGeometry(300, 300, 800, 500)

        self.lagerverwaltung = Lagerverwaltung()
        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        main_layout = QVBoxLayout()
        button_layout = QHBoxLayout()
        table_layout = QVBoxLayout()

        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Suchen...")
        self.search_field.textChanged.connect(self.filter_table)



        buttons = {
            "Bild anzeigen": self.show_image,
            "Hinzufügen": self.add_data,
            "Löschen": self.delete_selected_row,
            "Speichern": self.save_changes,
            "Speichern als Datei": self.save_to_file,
            "Beenden": self.close
        }

        for label, callback in buttons.items():
            button = QPushButton(label)
            button.clicked.connect(callback)
            button_layout.addWidget(button)

        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(6)
        self.table_widget.setHorizontalHeaderLabels(["Datum", "Bezeichnung", "Typ", "Menge", "Raum", "Schrank"])
        table_layout.addWidget(QLabel("Lagerverzeichnis:"))
        table_layout.addWidget(self.table_widget)

        main_layout.addWidget(self.search_field)
        main_layout.addLayout(button_layout)
        main_layout.addLayout(table_layout)
        main_widget.setLayout(main_layout)

        self.update_table()

    def show_image(self):
        image_path = "Pictures/overview.jpg"


        if not os.path.exists(image_path):
            print(f"Bild nicht gefunden: {image_path}")
            return

        # Dialog erzeugen
        self.dialog = QDialog(self)
        self.dialog.setWindowTitle("Bild anzeigen")
        self.dialog.resize(600, 400)

        # QPixmap zum Laden des Bildes
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            print("Fehler: Bild konnte nicht geladen werden.")
            return

        # QLabel, um das Bild anzuzeigen
        label = QLabel()
        label.setPixmap(pixmap)
        label.setScaledContents(True)

        # Layout für den Dialog einrichten
        layout = QVBoxLayout()
        layout.addWidget(label)
        self.dialog.setLayout(layout)

        # Dialog anzeigen
        self.dialog.exec_()

    def add_data(self):
        dialog = AddDataDialog(self)

        if dialog.exec_():
            data = dialog.get_data()

            if all(data.values()):
                try:
                    self.lagerverwaltung.insert_data(
                        data["Datum"], data["Bezeichnung"], data["Typ"], data["Menge"],
                        data["Raum"], data["Schrank"]
                    )
                    self.update_table()
                    QMessageBox.information(self, "Erfolg", "Daten wurden erfolgreich hinzugefügt.")
                except ValueError as e:
                    QMessageBox.warning(self, "Fehler", str(e))
            else:
                QMessageBox.warning(self, "Fehler", "Bitte füllen Sie alle Felder aus.")

    def delete_selected_row(self):
        selected_items = self.table_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Fehler", "Bitte wählen Sie eine Zeile aus.")
            return

        row = selected_items[0].row()
        item_id = int(self.table_widget.item(row, 0).text())

        self.lagerverwaltung.delete_data(item_id)
        self.update_table()

    def update_table(self):
        self.table_widget.setRowCount(0)

        data = self.lagerverwaltung.retrieve_data()
        for row_idx, row_data in enumerate(data):
            self.table_widget.insertRow(row_idx)
            for col_idx, cell_data in enumerate(row_data[1:]):  # IDs auslassen
                self.table_widget.setItem(row_idx, col_idx, QTableWidgetItem(str(cell_data)))

    def save_changes(self):
        for row in range(self.table_widget.rowCount()):
            row_data = [self.table_widget.item(row, col).text() for col in range(self.table_widget.columnCount())]
            self.lagerverwaltung.update_data(row + 1, *row_data)
        QMessageBox.information(self, "Erfolg", "Daten wurden gespeichert.")

    def save_to_file(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Speichern als", "", "CSV-Datei (*.csv)")
        if not file_path:
            return

        with open(file_path, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Datum", "Bezeichnung", "Typ", "Menge", "Raum", "Schrank"])

            for row in range(self.table_widget.rowCount()):
                row_data = [
                    self.table_widget.item(row, col).text() if self.table_widget.item(row, col) else ""
                    for col in range(self.table_widget.columnCount())
                ]
                writer.writerow(row_data)

        QMessageBox.information(self, "Erfolg", "Daten wurden erfolgreich exportiert.")

    def filter_table(self):
        search_text = self.search_field.text().lower()
        for row in range(self.table_widget.rowCount()):
            show_row = False
            for col in range(self.table_widget.columnCount()):
                item = self.table_widget.item(row, col)
                if search_text in (item.text().lower() if item else ""):
                    show_row = True
                    break
            self.table_widget.setRowHidden(row, not show_row)

    def closeEvent(self, event):
        self.lagerverwaltung.close_connection()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
