
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, \
    QTableWidgetItem, QLabel, QLineEdit, QDialog, QFormLayout, QMessageBox, QTabWidget
from PyQt5.QtGui import QPixmap
import sqlite3
import sys
import os


class Lagerverwaltung:

    def __init__(self):
        self.con = sqlite3.connect("management.db")
        self.cur = self.con.cursor()

    def create_table(self):
        self.cur.execute(
            "CREATE TABLE IF NOT EXISTS LAGERVERWALTUNG(\n"
            "            Datum TEXT,\n"
            "            Bezeichnung TEXT,\n"
            "            Typ TEXT,\n"
            "            Menge INT,\n"
            "            Raum TEXT,\n"
            "            Schrank TEXT,\n"
            "            CONSTRAINT Datum_unique UNIQUE (Datum),\n"
            "            CONSTRAINT Bezeichnung_unique UNIQUE (Bezeichnung),\n"
            "            CONSTRAINT Typ_unique UNIQUE (Typ),\n"
            "            CONSTRAINT Menge_unique UNIQUE (Menge),\n"
            "            CONSTRAINT Raum_unique UNIQUE (Raum),\n"
            "            CONSTRAINT Schrank_unique UNIQUE (Schrank)\n"
            "            )"
        )
        self.con.commit()

    def insert_data(self, Datum, Bezeichnung, Typ, Menge, Raum, Schrank):
        try:
            # Überprüfen, ob der Artikel bereits existiert
            self.cur.execute("SELECT * FROM LAGERVERWALTUNG WHERE Bezeichnung=?", (Bezeichnung,))
            existing_row = self.cur.fetchone()
            if existing_row:
                QMessageBox.warning(None, "Fehler", f"Der Artikel '{Bezeichnung}' existiert bereits im Lager.")
            else:
                # Daten einfügen
                self.cur.execute(
                    "INSERT INTO LAGERVERWALTUNG (Datum, Bezeichnung, Typ, Menge, Raum, Schrank)\n"
                    "                VALUES (?, ?, ?, ?, ?, ?)",
                    (Datum, Bezeichnung, Typ, Menge, Raum, Schrank)
                )
                self.con.commit()
                print(f"Der Artikel '{Bezeichnung}' wurde erfolgreich hinzugefügt.")
        except sqlite3.IntegrityError as e:
            QMessageBox.warning(None, "Fehler", f"Datenfehler: {str(e)}")
        except Exception as e:
            QMessageBox.critical(None, "Fehler", f"Ein unerwarteter Fehler ist aufgetreten: {str(e)}")

    def retrieve_data(self):
        self.cur.execute('SELECT * FROM LAGERVERWALTUNG')
        return self.cur.fetchall()

    def update_data(self, id, Datum, Bezeichnung, Typ, Menge, Raum, Schrank):
        self.cur.execute("""
            UPDATE LAGERVERWALTUNG 
            SET Datum=?, Bezeichnung=?, Typ=?, Menge=?, Raum=?, Schrank=?
            WHERE rowid=?
        """, (Datum, Bezeichnung, Typ, Menge, Raum, Schrank, id))
        self.con.commit()

    def delete_data(self, id):
        self.cur.execute("DELETE FROM LAGERVERWALTUNG WHERE rowid=?", (id,))
        self.con.commit()

    def close_connection(self):
        self.con.close()


class AddDataDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Daten hinzufügen")
        self.setModal(True)

        layout = QFormLayout()

        self.date_edit = QLineEdit()
        self.name_edit = QLineEdit()
        self.type_edit = QLineEdit()
        self.quantity_edit = QLineEdit()
        self.room_edit = QLineEdit()
        self.cabinet_edit = QLineEdit()

        layout.addRow("Datum:", self.date_edit)
        layout.addRow("Bezeichnung:", self.name_edit)
        layout.addRow("Typ:", self.type_edit)
        layout.addRow("Menge:", self.quantity_edit)
        layout.addRow("Raum:", self.room_edit)
        layout.addRow("Schranknummer:", self.cabinet_edit)

        self.btn_add = QPushButton("Hinzufügen")
        self.btn_cancel = QPushButton("Abbrechen")
        self.btn_add.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

        layout.addRow(self.btn_add, self.btn_cancel)
        self.setLayout(layout)

    def get_data(self):
        return (
            self.date_edit.text(),
            self.name_edit.text(),
            self.type_edit.text(),
            self.quantity_edit.text(),
            self.room_edit.text(),
            self.cabinet_edit.text()
        )


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Lagerverwaltung")
        self.setGeometry(300, 300, 600, 400)

        self.lagerverwaltung = Lagerverwaltung()

        self.initUI()

    def initUI(self):
        # Hauptwidget erstellen
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # Layouts erstellen
        main_layout = QVBoxLayout()
        button_layout = QHBoxLayout()
        table_layout = QVBoxLayout()

        # Suchfeld erstellen
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Suchen...")
        self.search_field.textChanged.connect(self.filter_table)

        # Buttons erstellen
        self.btn_show_image = QPushButton("Bild anzeigen")
        self.btn_show_image.clicked.connect(self.show_image)

        btn_add = QPushButton("Hinzufügen")
        btn_delete = QPushButton("Löschen")
        btn_save = QPushButton("Speichern")
        btn_save_file = QPushButton("Speichern als Datei")
        btn_exit = QPushButton("Beenden")

        # Button-Layout konfigurieren
        button_layout.addWidget(self.search_field)
        button_layout.addWidget(self.btn_show_image)
        button_layout.addWidget(btn_add)
        button_layout.addWidget(btn_delete)
        button_layout.addWidget(btn_save)
        button_layout.addWidget(btn_exit)

        # Tabellenwidget erstellen
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(6)
        self.table_widget.setHorizontalHeaderLabels(["Datum", "Bezeichnung", "Typ", "Menge", "Raum", "Schranknummer"])

        # Tabelle in Layout einfügen
        table_layout.addWidget(QLabel("Lagerverzeichnis:"))
        table_layout.addWidget(self.table_widget)

        # Hauptlayout konfigurieren
        main_layout.addLayout(button_layout)
        main_layout.addLayout(table_layout)

        # Hauptwidget-Layout einstellen
        main_widget.setLayout(main_layout)

        # Signale und Slots verbinden
        btn_add.clicked.connect(self.add_data)
        btn_delete.clicked.connect(self.delete_selected_row)
        btn_save.clicked.connect(self.save_changes)  # Verbindung zum Speichern in die Datenbank
        btn_save.clicked.connect(self.save_to_file)  # Alternativ: Zum Speichern als Datei
        btn_exit.clicked.connect(self.close)

        # Daten in die Tabelle einfügen
        self.update_table()

        self.show()

    def add_data(self):
        try:
            # Öffnet den Dialog
            dialog = AddDataDialog(self)
            if dialog.exec_():
                # Holen der Daten aus dem Dialog
                data = dialog.get_data()

                # Prüfen, ob alle Felder ausgefüllt sind
                if all(data):  # Überprüft, ob keine Felder leer sind
                    # Daten in die Datenbank einfügen
                    self.lagerverwaltung.insert_data(*data)

                    # Tabelle aktualisieren
                    self.update_table()
                else:
                    QMessageBox.warning(self, "Fehler", "Bitte füllen Sie alle Felder aus.")
        except Exception as e:
            # Fehlerausgabe für Debugging
            QMessageBox.critical(self, "Fehler", f"Ein Fehler ist aufgetreten: {str(e)}")

    def delete_selected_row(self):
        selected_rows = set(index.row() for index in self.table_widget.selectedIndexes())
        for row in sorted(selected_rows, reverse=True):
            self.lagerverwaltung.delete_data(row + 1)  # Verwende row + 1, da Zeilenindex 0-basiert ist
        self.update_table()

    def update_table(self):
        data = self.lagerverwaltung.retrieve_data()
        self.table_widget.setRowCount(len(data))
        for row_idx, row_data in enumerate(data):
            for col_idx, cell_data in enumerate(row_data):
                self.table_widget.setItem(row_idx, col_idx, QTableWidgetItem(str(cell_data)))

    def changes_save(self):
        try:
            # Anzahl der Zeilen in der Tabelle
            row_count = self.table_widget.rowCount()
            data_list = []

            # Durchlaufe jede Zeile und sammle die Daten
            for row in range(row_count):
                row_data = []
                for col in range(self.table_widget.columnCount()):
                    item = self.table_widget.item(row, col)
                    if item is not None:
                        row_data.append(item.text())
                    else:
                        row_data.append('')  # Leere Zelle als leeren String speichern

                data_list.append(row_data)

            # Alle Daten in die Datenbank schreiben
            for row_index, row_data in enumerate(data_list):
                # Datenbankaktualisierung auf Basis der Tabellen-Daten (Update-Funktion anpassen)
                self.lagerverwaltung.update_data(
                    row_index + 1,  # Zeilen-ID (rowid)
                    row_data[0], row_data[1], row_data[2], row_data[3], row_data[4], row_data[5]
                )

            QMessageBox.information(self, "Erfolg", "Änderungen erfolgreich gespeichert!")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Ein Fehler ist aufgetreten: {str(e)}")

    def save_to_file(self):
        from PyQt5.QtWidgets import QFileDialog
        import csv

        # Zeigt einen Dialog an, um den Speicherort und Dateinamen zu wählen
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Speichern Unter",
            "",
            "CSV-Dateien (*.csv);;Alle Dateien (*)",
            options=options
        )

        if not file_path:
            return  # Abbrechen, wenn der Nutzer keinen Pfad auswählt

        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)

                # Schreibe die Header-Zeilen
                headers = [self.table_widget.horizontalHeaderItem(i).text() for i in
                           range(self.table_widget.columnCount())]
                writer.writerow(headers)

                # Schreibe die Tabellen-Daten
                for row in range(self.table_widget.rowCount()):
                    row_data = []
                    for col in range(self.table_widget.columnCount()):
                        item = self.table_widget.item(row, col)
                        row_data.append(item.text() if item is not None else "")  # Leere Zellen handhaben
                    writer.writerow(row_data)

            QMessageBox.information(self, "Erfolg", f"Datei erfolgreich gespeichert unter: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Ein Fehler ist aufgetreten: {str(e)}")

    def show_image(self):
        image_path = "Pictures/overview.jpg"
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                image_viewer = QLabel()
                image_viewer.setPixmap(pixmap)
                image_viewer.setWindowTitle("Bild anzeigen")
                image_viewer.show()
            else:
                QMessageBox.warning(self, "Fehler", "Das Bild konnte nicht angezeigt werden.")
        else:
            QMessageBox.warning(self, "Fehler", "Das Bild konnte nicht gefunden werden.")

    def filter_table(self):
        search_text = self.search_field.text().lower()
        for row in range(self.table_widget.rowCount()):
            row_hidden = True
            for col in range(self.table_widget.columnCount()):
                item = self.table_widget.item(row, col)
                if item is not None and search_text in item.text().lower():
                    row_hidden = False
                    break
            self.table_widget.setRowHidden(row, row_hidden)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())
