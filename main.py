from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QLabel, QLineEdit, QDialog, QFormLayout, QMessageBox
from PyQt5.QtGui import QPixmap
import sqlite3
import sys
import os

#TODO: Fehlermeldung abfangen und Code optimieren
#TODO: PDF Viewer einbinden
#TODO: Materialinfos anzeigen (Rechnungen, Auftrag und und)
#TODO: Reiter einbinden (Material, Verbrauchsmaterial, Projekte)
#TODO: KI implementieren


class Lagerverwaltung:

    def __init__(self):
        self.con = sqlite3.connect("management.db")
        self.cur = self.con.cursor()

    def create_table(self):
        self.cur.execute(
            """CREATE TABLE IF NOT EXISTS LAGERVERWALTUNG(
            Datum TEXT,
            Bezeichnung TEXT,
            Typ TEXT,
            Menge INT,
            Raum TEXT,
            Schrank TEXT,
            CONSTRAINT Datum_unique UNIQUE (Datum),
            CONSTRAINT Bezeichnung_unique UNIQUE (Bezeichnung),
            CONSTRAINT Typ_unique UNIQUE (Typ),
            CONSTRAINT Menge_unique UNIQUE (Menge),
            CONSTRAINT Raum_unique UNIQUE (Raum),
            CONSTRAINT Schrank_unique UNIQUE (Schrank)
            )"""
        )
        self.con.commit()

    def insert_data(self, Datum, Bezeichnung, Typ, Menge, Raum, Schrank):
        # Überprüfen, ob der Artikel bereits existiert
        self.cur.execute("SELECT * FROM LAGERVERWALTUNG")
        existing_row = self.cur.fetchone()
        if existing_row:
            print(f"Der Artikel '{Bezeichnung}' existiert bereits im Lager.")
        else:
            self.cur.execute(
                """INSERT INTO LAGERVERWALTUNG (Datum, Bezeichnung, Typ, Menge, Raum, Schrank)
                VALUES (?, ?, ?, ?, ?, ?)""", (Datum, Bezeichnung, Typ, Menge, Raum, Schrank)
            )
            self.con.commit()
            print(f"Der Artikel '{Bezeichnung}' wurde erfolgreich hinzugefügt.")

    def retrieve_data(self):
        self.cur.execute("SELECT * FROM LAGERVERWALTUNG")
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
            int(self.quantity_edit.text()),
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

        # Button "Bild anzeigen" erstellen
        self.btn_show_image = QPushButton("Bild anzeigen")
        self.btn_show_image.clicked.connect(self.show_image)

        # Buttons erstellen
        btn_add = QPushButton("Hinzufügen")
        btn_edit = QPushButton("Bearbeiten")
        btn_delete = QPushButton("Löschen")
        btn_exit = QPushButton("Beenden")

        # Button-Layout konfigurieren
        button_layout.addWidget(self.btn_show_image)
        button_layout.addWidget(btn_add)
        button_layout.addWidget(btn_edit)
        button_layout.addWidget(btn_delete)
        button_layout.addWidget(self.search_field)
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
        btn_edit.clicked.connect(self.edit_data)
        btn_delete.clicked.connect(self.delete_data)
        btn_exit.clicked.connect(self.close)

        # Daten in die Tabelle einfügen
        self.update_table()

        self.show()

    def add_data(self):
        dialog = AddDataDialog()
        if dialog.exec_():
            data = dialog.get_data()
            self.lagerverwaltung.insert_data(*data)
            self.update_table()  # Tabelle aktualisieren

    def edit_data(self):
        # Hier könntest du die Bearbeitung von Daten implementieren, z.B. indem du die ausgewählte Zeile der Tabelle bearbeitbar machst
        selected_items = self.table_widget.selectedItems()
        if selected_items:
            # Nur die erste ausgewählte Zelle verwenden, um die Zeilennummer zu erhalten
            row = selected_items[0].row()
            dialog = AddDataDialog()
            # Daten in Dialogfeld setzen
            for col in range(self.table_widget.columnCount()):
                dialog_layout_item = dialog.layout().itemAt(col * 2, QFormLayout.FieldRole)
                if dialog_layout_item is not None:
                    widget = dialog_layout_item.widget()
                    if widget is not None:
                        widget.setText(self.table_widget.item(row, col).text())
            if dialog.exec_():
                data = dialog.get_data()
                self.lagerverwaltung.update_data(row + 1, *data)  # Verwende row + 1, da Zeilenindex 0-basiert ist
                self.update_table()

    def delete_data(self):
        #TODO: löschen der gesamten Zeile ist noch fehlerhaft
        selected_row = self.table_widget.currentRow()
        if selected_row != -1:
            artikel_id = int(self.table_widget.item(selected_row, 0).text())
            reply = QMessageBox.question(self, 'Löschen', 'Möchten Sie den ausgewählten Artikel löschen?',
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.lagerverwaltung.delete_artikel(artikel_id)
                self.update_table()

    def delete_selected_row(self):
        selected_rows = set(index.row() for index in self.table_widget.selectedIndexes())
        for row in sorted(selected_rows, reverse=True):
            self.lagerverwaltung.delete_data(row + 1)  # Verwende row + 1, da Zeilenindex 0-basiert ist
        self.update_table()  # Tabelle aktualisieren

    def update_table(self):
        # Daten aus der Datenbank abrufen und in die Tabelle einfügen
        data = self.lagerverwaltung.retrieve_data()
        self.table_widget.setRowCount(len(data))
        for row_idx, row_data in enumerate(data):
            for col_idx, cell_data in enumerate(row_data):
                self.table_widget.setItem(row_idx, col_idx, QTableWidgetItem(str(cell_data)))

    def show_image(self):
        # Pfad zum Bild
        image_path = "Pictures/overview.jpg"
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                # Widget erstellen, wenn es nicht existiert
                if not hasattr(self, 'image_viewer'):
                    self.image_viewer = QLabel()
                self.image_viewer.setPixmap(pixmap)
                self.image_viewer.setWindowTitle("Bild anzeigen")
                self.image_viewer.show()
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
