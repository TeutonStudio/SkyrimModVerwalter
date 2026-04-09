import PyQt6
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from kern.modpack_verwalter import ModPackVerwalter
from kern.status_speicher import StatusSpeicher
from kern.symlink_verwalter import SymlinkVerwalter
from kern.umgebung_verwalter import Umgebung
from schnittstelle.modliste_widget import ModItem, ModListe
from schnittstelle.pfad_dialog import PfadDialog


class VerwalterFenster(QMainWindow):
    def __init__(self, umgebung: Umgebung):
        super().__init__()
        self.umgebung = umgebung
        self.status_speicher = StatusSpeicher(self.umgebung)
        self.modpack = ModPackVerwalter(self.umgebung, self.status_speicher)
        self.symlink_verwalter = SymlinkVerwalter(
            self.umgebung,
            self.status_speicher,
        )

        self.setWindowTitle("Skyrim Mod Verwalter")
        self.resize(PyQt6.QtCore.QSize(900, 600))

        self.liste = ModListe()
        self.status_label = QLabel("Bereit.")
        self.label_mod_ordner = QLabel()
        self.label_data_ordner = QLabel()

        self.button_aktualisieren = QPushButton("Modliste neu laden")
        self.button_erzeuge = QPushButton("Erzeuge symbolische Modlinks!")
        self.button_vernichte = QPushButton("Vernichte symbolische Modlinks!")

        self.button_aktualisieren.clicked.connect(self.aktualisieren)
        self.button_erzeuge.clicked.connect(self.deploy_symlinks)
        self.button_vernichte.clicked.connect(self.undeploy_symlinks)

        self.liste.reihenfolge_geaendert.connect(self.speichere_status)
        self.liste.itemChanged.connect(self.speichere_status)

        self._baue_menue()

        button_leiste = QHBoxLayout()
        button_leiste.addWidget(self.button_aktualisieren)
        button_leiste.addWidget(self.button_erzeuge)
        button_leiste.addWidget(self.button_vernichte)

        anzeige = QVBoxLayout()
        anzeige.addWidget(self.label_mod_ordner)
        anzeige.addWidget(self.label_data_ordner)
        anzeige.addWidget(self.liste)
        anzeige.addLayout(button_leiste)
        anzeige.addWidget(self.status_label)

        zentral_widget = QWidget()
        zentral_widget.setLayout(anzeige)
        self.setCentralWidget(zentral_widget)

        self.aktualisiere_pfad_labels()
        self.aktualisieren()

    def _baue_menue(self) -> None:
        menueleiste = self.menuBar()
        menue_umgebung = menueleiste.addMenu("Umgebung")

        action_spielpfad = QAction("Spielpfad", self)
        action_modpfad = QAction("Modpfad", self)

        action_spielpfad.triggered.connect(self.dialog_spielpfad)
        action_modpfad.triggered.connect(self.dialog_modpfad)

        menue_umgebung.addAction(action_spielpfad)
        menue_umgebung.addAction(action_modpfad)

    def aktualisiere_pfad_labels(self) -> None:
        self.label_mod_ordner.setText(f"Mods-Ordner: {self.umgebung.mod_ordner}")
        self.label_data_ordner.setText(f"Data-Ordner: {self.umgebung.data_ordner}")

    def dialog_spielpfad(self) -> None:
        dialog = PfadDialog("Spielpfad ändern", self.umgebung.spiel_ordner, self)
        if not dialog.exec():
            return

        neuer_pfad = dialog.pfad()
        if not neuer_pfad.exists() or not neuer_pfad.is_dir():
            QMessageBox.warning(
                self,
                "Ungültiger Pfad",
                f"Der Spielpfad ist kein gültiger Ordner:\n{neuer_pfad}",
            )
            return

        self.umgebung.spiel_ordner = neuer_pfad
        self.aktualisiere_pfad_labels()
        self.status_label.setText("Spielpfad aktualisiert.")

    def dialog_modpfad(self) -> None:
        dialog = PfadDialog("Modpfad ändern", self.umgebung.mod_ordner, self)
        if not dialog.exec():
            return

        neuer_pfad = dialog.pfad()
        if not neuer_pfad.exists() or not neuer_pfad.is_dir():
            QMessageBox.warning(
                self,
                "Ungültiger Pfad",
                f"Der Modpfad ist kein gültiger Ordner:\n{neuer_pfad}",
            )
            return

        self.umgebung.mod_ordner = neuer_pfad
        self.aktualisiere_pfad_labels()
        self.aktualisieren()
        self.status_label.setText("Modpfad aktualisiert.")

    def speichere_status(self) -> None:
        try:
            self.status_speicher.speichere_mod_status(
                self.liste.alle_mods_in_reihenfolge()
            )
        except Exception as exc:
            self.status_label.setText(f"Status konnte nicht gespeichert werden: {exc}")

    def aktualisieren(self) -> None:
        self.liste.blockSignals(True)
        self.liste.clear()

        try:
            mods = self.modpack.lade_modliste()
        except FileNotFoundError:
            self.liste.blockSignals(False)
            self.status_label.setText("Mods-Ordner existiert nicht.")
            QMessageBox.warning(
                self,
                "Ordner fehlt",
                f"Der Mods-Ordner wurde nicht gefunden:\n{self.umgebung.mod_ordner}",
            )
            return

        if not mods:
            self.liste.blockSignals(False)
            self.status_label.setText("Keine Mod-Unterordner gefunden.")
            return

        for mod_name, aktiviert in mods:
            self.liste.addItem(ModItem(mod_name, aktiviert))

        self.liste.blockSignals(False)
        self.speichere_status()
        self.status_label.setText(f"{len(mods)} Mods gefunden.")

    def deploy_symlinks(self) -> None:
        aktive_mods = self.liste.ausgewaehlte_mods_in_reihenfolge()
        if not aktive_mods:
            QMessageBox.information(
                self,
                "Keine Mods gewählt",
                "Es wurden keine Mods ausgewählt.",
            )
            return

        self.speichere_status()
        deployment_map, plugins, konflikte = self.modpack.berechne_deployment(
            aktive_mods
        )
        ergebnis = self.symlink_verwalter.deploy_symlinks(
            aktive_mods,
            deployment_map,
            plugins,
            konflikte,
        )

        self.status_label.setText(ergebnis.status_text)
        QMessageBox.information(self, "Deploy abgeschlossen", ergebnis.detail_text)

    def undeploy_symlinks(self, stumm: bool = False) -> None:
        ergebnis = self.symlink_verwalter.undeploy_symlinks(stumm=stumm)

        if ergebnis.manifest_fehler is not None:
            if not stumm:
                QMessageBox.warning(
                    self,
                    "Manifest defekt",
                    f"Manifest konnte nicht gelesen werden:\n{ergebnis.manifest_fehler}",
                )
            return

        if not ergebnis.manifest_vorhanden:
            if not stumm:
                QMessageBox.information(
                    self,
                    "Nichts zu tun",
                    "Kein Manifest vorhanden.",
                )
            return

        self.status_label.setText(ergebnis.status_text)

        if not stumm:
            QMessageBox.information(
                self,
                "Undeploy abgeschlossen",
                ergebnis.detail_text,
            )

    def closeEvent(self, event) -> None:
        self.speichere_status()
        self.undeploy_symlinks(stumm=True)
        event.accept()
