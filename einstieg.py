import json
import sys
from pathlib import Path

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
# from PyQt6.QtWidgets import QDialogButtonBox.StandardButton


PLUGIN_ENDUNGEN = {".esp", ".esm", ".esl"}


class Umgebung:
    def __init__(self):
        self.spiel_ordner = Path(
            "/home/alex/.var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps/common/Skyrim Special Edition"
        )
        self.mod_ordner = Path("/home/alex/Games/MO2/Modpack1/mods")
        self.plugins_txt = Path(
            "/home/alex/.var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps/compatdata/489830/pfx/"
            "drive_c/users/steamuser/AppData/Local/Skyrim Special Edition/plugins.txt"
        )

    @property
    def data_ordner(self) -> Path:
        return self.spiel_ordner / "Data"

    @property
    def status_datei(self) -> Path:
        return self.mod_ordner / "modliste_status.json"

    @property
    def manifest_datei(self) -> Path:
        return self.mod_ordner / "deploy_manifest.json"


class PfadDialog(QDialog):
    def __init__(self, titel: str, aktueller_pfad: Path, parent=None):
        super().__init__(parent)
        self.setWindowTitle(titel)
        self.resize(700, 120)

        self.eingabe = QLineEdit(str(aktueller_pfad))
        self.button_durchsuchen = QPushButton("Durchsuchen...")

        self.button_durchsuchen.clicked.connect(self.ordner_waehlen)

        layout = QFormLayout()
        zeile = QHBoxLayout()
        zeile.addWidget(self.eingabe)
        zeile.addWidget(self.button_durchsuchen)

        layout.addRow("Pfad:", zeile)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        haupt = QVBoxLayout()
        haupt.addLayout(layout)
        haupt.addWidget(buttons)
        self.setLayout(haupt)

    def ordner_waehlen(self):
        ordner = QFileDialog.getExistingDirectory(
            self,
            "Ordner wählen",
            self.eingabe.text(),
        )
        if ordner:
            self.eingabe.setText(ordner)

    def pfad(self) -> Path:
        return Path(self.eingabe.text()).expanduser()


class ModListe(QListWidget):
    reihenfolge_geaendert = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setAlternatingRowColors(True)
        self.setDropIndicatorShown(True)

        model = self.model()
        if model is not None:
            model.rowsMoved.connect(self._emit_reihenfolge_geaendert)

    def _emit_reihenfolge_geaendert(self, *args):
        self.reihenfolge_geaendert.emit()

    def dragMoveEvent(self, event):
        # Direktes Droppen "auf" einen Eintrag verhindern.
        # Erlaubt bleiben nur Positionen oberhalb/unterhalb.
        index = self.indexAt(event.position().toPoint())
        if index.isValid():
            rect = self.visualRect(index)
            pos_y = event.position().toPoint().y()
            obere_zone = rect.top() + 6
            untere_zone = rect.bottom() - 6

            if obere_zone < pos_y < untere_zone:
                event.ignore()
                return

        super().dragMoveEvent(event)

    def dropEvent(self, event):
        super().dropEvent(event)
        self.reihenfolge_geaendert.emit()

    def ausgewaehlte_mods_in_reihenfolge(self) -> list[str]:
        mods = []
        for index in range(self.count()):
            item = self.item(index)
            if item.checkState() == Qt.CheckState.Checked:
                mods.append(item.text())
        return mods

    def alle_mods_in_reihenfolge(self) -> list[tuple[str, bool]]:
        mods = []
        for index in range(self.count()):
            item = self.item(index)
            aktiviert = item.checkState() == Qt.CheckState.Checked
            mods.append((item.text(), aktiviert))
        return mods


class HauptFenster(QMainWindow):
    def __init__(self):
        super().__init__()
        self.umgebung = Umgebung()

        self.setWindowTitle("Skyrim Mod Verwalter")
        self.resize(QSize(900, 600))

        self.liste = ModListe()
        self.status_label = QLabel("Bereit.")
        self.label_mod_ordner = QLabel()
        self.label_data_ordner = QLabel()

        self.button_aktualisieren = QPushButton("Modliste neu laden")
        self.button_erzeuge = QPushButton("Erzeuge symbolische Modlinks!")
        self.button_vernichte = QPushButton("Vernichte symbolische Modlinks!")

        self.button_aktualisieren.clicked.connect(self.modliste_laden)
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
        self.modliste_laden()

    def _baue_menue(self):
        menueleiste = self.menuBar()
        menue_umgebung = menueleiste.addMenu("Umgebung")

        action_spielpfad = QAction("Spielpfad", self)
        action_modpfad = QAction("Modpfad", self)

        action_spielpfad.triggered.connect(self.dialog_spielpfad)
        action_modpfad.triggered.connect(self.dialog_modpfad)

        menue_umgebung.addAction(action_spielpfad)
        menue_umgebung.addAction(action_modpfad)

    def aktualisiere_pfad_labels(self):
        self.label_mod_ordner.setText(f"Mods-Ordner: {self.umgebung.mod_ordner}")
        self.label_data_ordner.setText(f"Data-Ordner: {self.umgebung.data_ordner}")

    def dialog_spielpfad(self):
        dialog = PfadDialog("Spielpfad ändern", self.umgebung.spiel_ordner, self)
        if dialog.exec():
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

    def dialog_modpfad(self):
        dialog = PfadDialog("Modpfad ändern", self.umgebung.mod_ordner, self)
        if dialog.exec():
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
            self.modliste_laden()
            self.status_label.setText("Modpfad aktualisiert.")

    def lade_status(self) -> dict:
        status_datei = self.umgebung.status_datei
        if not status_datei.exists():
            return {"mods": []}

        try:
            return json.loads(status_datei.read_text(encoding="utf-8"))
        except Exception:
            return {"mods": []}

    def speichere_status(self):
        try:
            self.umgebung.mod_ordner.mkdir(parents=True, exist_ok=True)
            daten = {
                "mods": [
                    {"name": name, "aktiv": aktiv}
                    for name, aktiv in self.liste.alle_mods_in_reihenfolge()
                ]
            }
            self.umgebung.status_datei.write_text(
                json.dumps(daten, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as exc:
            self.status_label.setText(f"Status konnte nicht gespeichert werden: {exc}")

    def modliste_laden(self):
        alter_status = self.lade_status()
        bekannte_mods = alter_status.get("mods", [])

        bekannte_reihenfolge = [eintrag["name"] for eintrag in bekannte_mods]
        bekannte_aktiv = {
            eintrag["name"]: bool(eintrag.get("aktiv", False))
            for eintrag in bekannte_mods
        }

        self.liste.blockSignals(True)
        self.liste.clear()

        if not self.umgebung.mod_ordner.exists():
            self.liste.blockSignals(False)
            self.status_label.setText("Mods-Ordner existiert nicht.")
            QMessageBox.warning(
                self,
                "Ordner fehlt",
                f"Der Mods-Ordner wurde nicht gefunden:\n{self.umgebung.mod_ordner}",
            )
            return

        vorhandene_mods = sorted(
            [ordner.name for ordner in self.umgebung.mod_ordner.iterdir() if ordner.is_dir()],
            key=lambda name: name.lower(),
        )

        if not vorhandene_mods:
            self.liste.blockSignals(False)
            self.status_label.setText("Keine Mod-Unterordner gefunden.")
            return

        finale_reihenfolge = []

        for mod_name in bekannte_reihenfolge:
            if mod_name in vorhandene_mods:
                finale_reihenfolge.append(mod_name)

        for mod_name in vorhandene_mods:
            if mod_name not in finale_reihenfolge:
                finale_reihenfolge.append(mod_name)

        for mod_name in finale_reihenfolge:
            item = QListWidgetItem(mod_name)
            item.setFlags(
                item.flags()
                | Qt.ItemFlag.ItemIsUserCheckable
                | Qt.ItemFlag.ItemIsDragEnabled
                | Qt.ItemFlag.ItemIsDropEnabled
                | Qt.ItemFlag.ItemIsSelectable
                | Qt.ItemFlag.ItemIsEnabled
            )
            item.setCheckState(
                Qt.CheckState.Checked
                if bekannte_aktiv.get(mod_name, False)
                else Qt.CheckState.Unchecked
            )
            self.liste.addItem(item)

        self.liste.blockSignals(False)
        self.speichere_status()
        self.status_label.setText(f"{len(finale_reihenfolge)} Mods gefunden.")

    def sammle_dateien_eines_mods(self, mod_name: str) -> list[Path]:
        mod_pfad = self.umgebung.mod_ordner / mod_name
        dateien = []
        for pfad in mod_pfad.rglob("*"):
            if pfad.is_file():
                # TODO if is meta.ini: continue
                dateien.append(pfad)
        return dateien

    def berechne_deployment(self, aktive_mods: list[str]) -> tuple[dict[str, str], list[str], list[str]]:
        deployment_map: dict[str, str] = {}
        plugins: list[str] = []
        konflikte: list[str] = []

        for mod_name in aktive_mods:
            mod_pfad = self.umgebung.mod_ordner / mod_name
            if not mod_pfad.is_dir():
                continue

            for quelle in self.sammle_dateien_eines_mods(mod_name):
                rel = quelle.relative_to(mod_pfad)
                ziel = self.umgebung.data_ordner / rel
                ziel_str = str(ziel)

                if ziel_str in deployment_map:
                    vorherige_quelle = deployment_map[ziel_str]
                    konflikte.append(
                        f"{ziel} wird überschrieben:\n"
                        f"  alt: {vorherige_quelle}\n"
                        f"  neu: {quelle}"
                    )

                deployment_map[ziel_str] = str(quelle)

                if quelle.suffix.lower() in PLUGIN_ENDUNGEN:
                    plugin_name = quelle.name
                    if plugin_name not in plugins:
                        plugins.append(plugin_name)

        return deployment_map, plugins, konflikte

    def schreibe_plugins_txt(self, plugins: list[str]):
        self.umgebung.plugins_txt.parent.mkdir(parents=True, exist_ok=True)
        zeilen = [f"*{plugin}" for plugin in plugins]
        self.umgebung.plugins_txt.write_text(
            "\n".join(zeilen) + ("\n" if zeilen else ""),
            encoding="utf-8",
        )

    def deploy_symlinks(self):
        aktive_mods = self.liste.ausgewaehlte_mods_in_reihenfolge()

        if not aktive_mods:
            QMessageBox.information(
                self,
                "Keine Mods gewählt",
                "Es wurden keine Mods ausgewählt.",
            )
            return

        self.speichere_status()
        self.undeploy_symlinks(stumm=True)

        deployment_map, plugins, konflikte = self.berechne_deployment(aktive_mods)

        erstellt = []
        fehler = []

        for ziel_str, quelle_str in deployment_map.items():
            ziel = Path(ziel_str)
            quelle = Path(quelle_str)

            try:
                ziel.parent.mkdir(parents=True, exist_ok=True)

                if ziel.exists() or ziel.is_symlink():
                    if ziel.is_symlink():
                        ziel.unlink()
                    else:
                        fehler.append(
                            f"Ziel existiert bereits und ist kein Symlink:\n{ziel}"
                        )
                        continue

                ziel.symlink_to(quelle)
                erstellt.append(ziel_str)
            except Exception as exc:
                fehler.append(f"{ziel} -> {quelle}\n{exc}")

        try:
            self.schreibe_plugins_txt(plugins)
        except Exception as exc:
            fehler.append(f"plugins.txt konnte nicht geschrieben werden:\n{exc}")

        manifest = {
            "mods_ordner": str(self.umgebung.mod_ordner),
            "spiel_ordner": str(self.umgebung.spiel_ordner),
            "data_ordner": str(self.umgebung.data_ordner),
            "aktive_mods_reihenfolge": aktive_mods,
            "symlinks": deployment_map,
            "erstellte_symlinks": erstellt,
            "plugins": plugins,
            "konflikte": konflikte,
        }

        self.umgebung.manifest_datei.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        meldung = [
            "Deploy abgeschlossen.",
            f"Aktive Mods: {len(aktive_mods)}",
            f"Erstellte Symlinks: {len(erstellt)}",
            f"Plugins: {len(plugins)}",
            f"Konflikte: {len(konflikte)}",
            f"Fehler: {len(fehler)}",
        ]

        self.status_label.setText(
            f"Deploy fertig: {len(erstellt)} Symlinks, {len(plugins)} Plugins."
        )

        detail_text = "\n".join(meldung)

        if konflikte:
            detail_text += "\n\nKonflikte wurden nach Reihenfolge aufgelöst:"
            detail_text += "\nSpäter in der Liste gewinnt.\n"
            detail_text += "\n".join(konflikte[:20])
            if len(konflikte) > 20:
                detail_text += f"\n... und {len(konflikte) - 20} weitere"

        if fehler:
            detail_text += "\n\nFehler:\n" + "\n".join(fehler[:20])
            if len(fehler) > 20:
                detail_text += f"\n... und {len(fehler) - 20} weitere"

        QMessageBox.information(self, "Deploy abgeschlossen", detail_text)

    def undeploy_symlinks(self, stumm: bool = False):
        manifest_datei = self.umgebung.manifest_datei

        if not manifest_datei.exists():
            if not stumm:
                QMessageBox.information(
                    self,
                    "Nichts zu tun",
                    "Kein Manifest vorhanden.",
                )
            return

        try:
            manifest = json.loads(manifest_datei.read_text(encoding="utf-8"))
        except Exception as exc:
            if not stumm:
                QMessageBox.warning(
                    self,
                    "Manifest defekt",
                    f"Manifest konnte nicht gelesen werden:\n{exc}",
                )
            return

        entfernte = 0
        fehler = []

        for ziel_str in manifest.get("erstellte_symlinks", []):
            ziel = Path(ziel_str)
            try:
                if ziel.is_symlink():
                    ziel.unlink()
                    entfernte += 1
            except Exception as exc:
                fehler.append(f"{ziel}\n{exc}")

        self.raeume_leere_ordner_auf(self.umgebung.data_ordner)

        try:
            self.schreibe_plugins_txt([])
        except Exception as exc:
            fehler.append(f"plugins.txt konnte nicht geleert werden:\n{exc}")

        try:
            manifest_datei.unlink()
        except Exception as exc:
            fehler.append(f"Manifest konnte nicht gelöscht werden:\n{exc}")

        self.status_label.setText(f"Undeploy fertig: {entfernte} Symlinks entfernt.")

        if not stumm:
            text = f"{entfernte} Symlinks entfernt."
            if fehler:
                text += "\n\nFehler:\n" + "\n".join(fehler[:20])
                if len(fehler) > 20:
                    text += f"\n... und {len(fehler) - 20} weitere"

            QMessageBox.information(self, "Undeploy abgeschlossen", text)

    def raeume_leere_ordner_auf(self, wurzel: Path):
        if not wurzel.exists():
            return

        ordner_liste = [pfad for pfad in wurzel.rglob("*") if pfad.is_dir()]
        ordner_liste.sort(key=lambda p: len(p.parts), reverse=True)

        for ordner in ordner_liste:
            try:
                if ordner == wurzel:
                    continue
                if not any(ordner.iterdir()):
                    ordner.rmdir()
            except Exception:
                pass

    def closeEvent(self, event):
        self.speichere_status()
        self.undeploy_symlinks(stumm=True)
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    fenster = HauptFenster()
    fenster.show()
    sys.exit(app.exec())