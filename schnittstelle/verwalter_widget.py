import PyQt6
from PyQt6.QtGui import QActionGroup
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
from types import SimpleNamespace

from kern.kopie_verwalter import KopieVerwalter
from kern.modpack_verwalter import ModPackVerwalter
from kern.status_speicher import StatusSpeicher
from kern.symlink_verwalter import SymlinkVerwalter
from kern.umgebung_verwalter import SKYRIM_ORDNERNAME, Umgebung
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
        self.kopie_verwalter = KopieVerwalter(
            self.umgebung,
            self.status_speicher,
        )
        self.modding_variante = "symlink"

        self.setWindowTitle("Skyrim Mod Verwalter")
        self.resize(PyQt6.QtCore.QSize(900, 600))

        self.liste = ModListe()
        self.status_label = QLabel("Bereit.")
        self.label_steamapps_ordner = QLabel()
        self.label_mod_ordner = QLabel()
        self.label_data_ordner = QLabel()

        self.button_aktualisieren = QPushButton("Modliste neu laden")
        self.button_erzeuge = QPushButton("Erzeuge symbolische Modlinks!")
        self.button_vernichte = QPushButton("Vernichte symbolische Modlinks!")

        self.button_aktualisieren.clicked.connect(self.aktualisieren)
        self.button_erzeuge.clicked.connect(self.deploy_aktive_variante)
        self.button_vernichte.clicked.connect(self.undeploy_aktive_variante)

        self.liste.reihenfolge_geaendert.connect(self.speichere_status)
        self.liste.itemChanged.connect(self.speichere_status)

        self._baue_menue()
        self.aktualisiere_varianten_ui()

        button_leiste = QHBoxLayout()
        button_leiste.addWidget(self.button_aktualisieren)
        button_leiste.addWidget(self.button_erzeuge)
        button_leiste.addWidget(self.button_vernichte)

        anzeige = QVBoxLayout()
        anzeige.addWidget(self.label_steamapps_ordner)
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
        menue_modpack = menueleiste.addMenu("Modpack")
        menue_variante = menueleiste.addMenu("Modding variante")

        action_spielpfad = QAction("Steamapps-Pfad", self)
        action_modpfad = QAction("Modpfad", self)
        action_json_aufraeumen = QAction("JSON aufräumen", self)
        self.action_symlinks = QAction("Symlinks", self)
        self.action_kopie = QAction("Kopie", self)
        self.varianten_gruppe = QActionGroup(self)

        action_spielpfad.triggered.connect(self.dialog_steamappspfad)
        action_modpfad.triggered.connect(self.dialog_modpfad)
        action_json_aufraeumen.triggered.connect(self.json_aufraeumen)
        self.action_symlinks.triggered.connect(
            lambda checked: self.setze_modding_variante("symlink", checked)
        )
        self.action_kopie.triggered.connect(
            lambda checked: self.setze_modding_variante("kopie", checked)
        )

        self.varianten_gruppe.setExclusive(True)
        self.action_symlinks.setCheckable(True)
        self.action_kopie.setCheckable(True)
        self.varianten_gruppe.addAction(self.action_symlinks)
        self.varianten_gruppe.addAction(self.action_kopie)
        self.action_symlinks.setChecked(True)

        menue_umgebung.addAction(action_spielpfad)
        menue_umgebung.addAction(action_modpfad)
        menue_modpack.addAction(action_json_aufraeumen)
        menue_variante.addAction(self.action_symlinks)
        menue_variante.addAction(self.action_kopie)

    def aktualisiere_pfad_labels(self) -> None:
        self.label_steamapps_ordner.setText(
            f"Steamapps-Ordner: {self.umgebung.steamapps_ordner}"
        )
        self.label_mod_ordner.setText(f"Mods-Ordner: {self.umgebung.mod_ordner}")
        self.label_data_ordner.setText(f"Data-Ordner: {self.umgebung.data_ordner}")

    def dialog_steamappspfad(self) -> None:
        dialog = PfadDialog(
            "Steamapps-Pfad ändern",
            self.umgebung.steamapps_ordner,
            self,
        )
        if not dialog.exec():
            return

        neuer_pfad = dialog.pfad()
        if not neuer_pfad.exists() or not neuer_pfad.is_dir():
            QMessageBox.warning(
                self,
                "Ungültiger Pfad",
                f"Der Steamapps-Pfad ist kein gültiger Ordner:\n{neuer_pfad}",
            )
            return

        abgeleiteter_spielordner = (
            neuer_pfad / "common" / SKYRIM_ORDNERNAME
        )
        if not abgeleiteter_spielordner.exists() or not abgeleiteter_spielordner.is_dir():
            QMessageBox.warning(
                self,
                "Skyrim nicht gefunden",
                (
                    "Unter dem Steamapps-Pfad wurde kein Skyrim-SE-Ordner gefunden:\n"
                    f"{abgeleiteter_spielordner}"
                ),
            )
            return

        self.umgebung.steamapps_ordner = neuer_pfad
        self.aktualisiere_pfad_labels()
        self.status_label.setText("Steamapps-Pfad aktualisiert.")

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

        for eintrag in mods:
            self.liste.addItem(
                ModItem(
                    eintrag.name,
                    eintrag.aktiviert,
                    ist_ueberfluessig=eintrag.ist_ueberfluessig,
                )
            )

        self.liste.blockSignals(False)
        self.speichere_status()
        self.status_label.setText(f"{len(mods)} Mods gefunden.")

    def deploy_aktive_variante(self) -> None:
        aktive_mods = self.liste.ausgewaehlte_mods_in_reihenfolge()
        if not aktive_mods:
            QMessageBox.information(
                self,
                "Keine Mods gewählt",
                "Es wurden keine Mods ausgewählt.",
            )
            return

        self.speichere_status()
        self.vernichte_manifest_methode(stumm=True)
        deployment_map, plugins, konflikte = self.modpack.berechne_deployment(
            aktive_mods
        )

        if self.modding_variante == "kopie":
            ergebnis = self.kopie_verwalter.deploy_kopien(
                aktive_mods,
                deployment_map,
                plugins,
                konflikte,
            )
        else:
            ergebnis = self.symlink_verwalter.deploy_symlinks(
                aktive_mods,
                deployment_map,
                plugins,
                konflikte,
            )

        self.status_label.setText(ergebnis.status_text)
        QMessageBox.information(self, "Deploy abgeschlossen", ergebnis.detail_text)

    def undeploy_aktive_variante(self, stumm: bool = False) -> None:
        ergebnis = self.vernichte_manifest_methode(stumm=stumm)

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

    def vernichte_manifest_methode(self, stumm: bool = False):
        try:
            manifest = self.status_speicher.lade_manifest()
        except Exception as exc:
            return SimpleNamespace(
                manifest_vorhanden=True,
                manifest_fehler=str(exc),
                status_text="",
                detail_text="",
            )

        if manifest is None:
            return SimpleNamespace(
                manifest_vorhanden=False,
                manifest_fehler=None,
                status_text="",
                detail_text="",
            )

        methode = manifest.get("methode", "symlink")
        if methode == "kopie":
            return self.kopie_verwalter.undeploy_kopien(stumm=stumm)
        return self.symlink_verwalter.undeploy_symlinks(stumm=stumm)

    def setze_modding_variante(self, variante: str, checked: bool = True) -> None:
        if not checked or variante == self.modding_variante:
            return

        self.vernichte_manifest_methode(stumm=True)
        self.modding_variante = variante
        self.aktualisiere_varianten_ui()
        self.status_label.setText(f"Modding-Variante aktiv: {variante}.")

    def aktualisiere_varianten_ui(self) -> None:
        if self.modding_variante == "kopie":
            self.action_kopie.setChecked(True)
            self.button_erzeuge.setText("Erzeuge Modkopien!")
            self.button_vernichte.setText("Vernichte Modkopien!")
            return

        self.action_symlinks.setChecked(True)
        self.button_erzeuge.setText("Erzeuge symbolische Modlinks!")
        self.button_vernichte.setText("Vernichte symbolische Modlinks!")

    def json_aufraeumen(self) -> None:
        try:
            behalten, entfernt = self.modpack.bereinige_status_json()
        except FileNotFoundError:
            QMessageBox.warning(
                self,
                "Ordner fehlt",
                f"Der Mods-Ordner wurde nicht gefunden:\n{self.umgebung.mod_ordner}",
            )
            return
        except Exception as exc:
            QMessageBox.warning(
                self,
                "JSON defekt",
                f"Die Status-JSON konnte nicht bereinigt werden:\n{exc}",
            )
            return

        self.aktualisieren()
        self.status_label.setText(
            f"Status-JSON bereinigt: {entfernt} Einträge entfernt."
        )
        QMessageBox.information(
            self,
            "JSON aufgeräumt",
            (
                f"{entfernt} überflüssige Einträge entfernt.\n"
                f"{behalten} Einträge bleiben erhalten."
            ),
        )

    def closeEvent(self, event) -> None:
        self.speichere_status()
        self.undeploy_aktive_variante(stumm=True)
        event.accept()
