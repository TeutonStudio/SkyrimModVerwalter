import PyQt6
from PyQt6.QtWidgets import QDialogButtonBox
from pathlib import Path



class PfadDialog(PyQt6.QtWidgets.QDialog):
    def __init__(self, titel: str, aktueller_pfad: Path, parent=None):
        super().__init__(parent)
        self.setWindowTitle(titel)
        self.resize(700, 120)

        self.eingabe = PyQt6.QtWidgets.QLineEdit(str(aktueller_pfad))
        self.button_durchsuchen = PyQt6.QtWidgets.QPushButton("Durchsuchen...")

        self.button_durchsuchen.clicked.connect(self.ordner_waehlen)

        layout = PyQt6.QtWidgets.QFormLayout()
        zeile = PyQt6.QtWidgets.QHBoxLayout()
        zeile.addWidget(self.eingabe)
        zeile.addWidget(self.button_durchsuchen)

        layout.addRow("Pfad:", zeile)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        haupt = PyQt6.QtWidgets.QVBoxLayout()
        haupt.addLayout(layout)
        haupt.addWidget(buttons)
        self.setLayout(haupt)

    def ordner_waehlen(self):
        ordner = PyQt6.QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Ordner wählen",
            self.eingabe.text(),
        )
        if ordner:
            self.eingabe.setText(ordner)

    def pfad(self) -> Path:
        return Path(self.eingabe.text()).expanduser()
