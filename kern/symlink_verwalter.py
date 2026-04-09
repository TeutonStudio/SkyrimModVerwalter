from dataclasses import dataclass, field
from pathlib import Path

from kern.status_speicher import StatusSpeicher
from kern.umgebung_verwalter import Umgebung


@dataclass
class DeployErgebnis:
    aktive_mods: int
    erstellte_symlinks: int
    plugins: int
    konflikte: list[str] = field(default_factory=list)
    fehler: list[str] = field(default_factory=list)

    @property
    def status_text(self) -> str:
        return (
            f"Deploy fertig: {self.erstellte_symlinks} Symlinks, "
            f"{self.plugins} Plugins."
        )

    @property
    def detail_text(self) -> str:
        meldung = [
            "Deploy abgeschlossen.",
            f"Aktive Mods: {self.aktive_mods}",
            f"Erstellte Symlinks: {self.erstellte_symlinks}",
            f"Plugins: {self.plugins}",
            f"Konflikte: {len(self.konflikte)}",
            f"Fehler: {len(self.fehler)}",
        ]

        detail_text = "\n".join(meldung)

        if self.konflikte:
            detail_text += "\n\nKonflikte wurden nach Reihenfolge aufgelöst:"
            detail_text += "\nSpäter in der Liste gewinnt.\n"
            detail_text += "\n".join(self.konflikte[:20])
            if len(self.konflikte) > 20:
                detail_text += f"\n... und {len(self.konflikte) - 20} weitere"

        if self.fehler:
            detail_text += "\n\nFehler:\n" + "\n".join(self.fehler[:20])
            if len(self.fehler) > 20:
                detail_text += f"\n... und {len(self.fehler) - 20} weitere"

        return detail_text


@dataclass
class UndeployErgebnis:
    manifest_vorhanden: bool
    manifest_fehler: str | None = None
    entfernte_symlinks: int = 0
    fehler: list[str] = field(default_factory=list)

    @property
    def status_text(self) -> str:
        return f"Undeploy fertig: {self.entfernte_symlinks} Symlinks entfernt."

    @property
    def detail_text(self) -> str:
        text = f"{self.entfernte_symlinks} Symlinks entfernt."
        if self.fehler:
            text += "\n\nFehler:\n" + "\n".join(self.fehler[:20])
            if len(self.fehler) > 20:
                text += f"\n... und {len(self.fehler) - 20} weitere"
        return text


class SymlinkVerwalter:
    def __init__(self, umgebung: Umgebung, status_speicher: StatusSpeicher):
        self.umgebung = umgebung
        self.status_speicher = status_speicher

    def deploy_symlinks(
        self,
        aktive_mods: list[str],
        deployment_map: dict[str, str],
        plugins: list[str],
        konflikte: list[str],
    ) -> DeployErgebnis:
        self.undeploy_symlinks(stumm=True)

        erstellt: list[str] = []
        fehler: list[str] = []

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
            "steamapps_ordner": str(self.umgebung.steamapps_ordner),
            "spiel_ordner": str(self.umgebung.spiel_ordner),
            "data_ordner": str(self.umgebung.data_ordner),
            "plugins_txt": str(self.umgebung.plugins_txt),
            "aktive_mods_reihenfolge": aktive_mods,
            "symlinks": deployment_map,
            "erstellte_symlinks": erstellt,
            "plugins": plugins,
            "konflikte": konflikte,
        }
        self.status_speicher.speichere_manifest(manifest)

        return DeployErgebnis(
            aktive_mods=len(aktive_mods),
            erstellte_symlinks=len(erstellt),
            plugins=len(plugins),
            konflikte=konflikte,
            fehler=fehler,
        )

    def undeploy_symlinks(self, stumm: bool = False) -> UndeployErgebnis:
        del stumm

        try:
            manifest = self.status_speicher.lade_manifest()
        except Exception as exc:
            return UndeployErgebnis(
                manifest_vorhanden=True,
                manifest_fehler=str(exc),
            )

        if manifest is None:
            return UndeployErgebnis(manifest_vorhanden=False)

        entfernte = 0
        fehler: list[str] = []

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
            self.status_speicher.loesche_manifest()
        except FileNotFoundError:
            pass
        except Exception as exc:
            fehler.append(f"Manifest konnte nicht gelöscht werden:\n{exc}")

        return UndeployErgebnis(
            manifest_vorhanden=True,
            entfernte_symlinks=entfernte,
            fehler=fehler,
        )

    def schreibe_plugins_txt(self, plugins: list[str]) -> None:
        self.umgebung.plugins_txt.parent.mkdir(parents=True, exist_ok=True)
        zeilen = [f"*{plugin}" for plugin in plugins]
        self.umgebung.plugins_txt.write_text(
            "\n".join(zeilen) + ("\n" if zeilen else ""),
            encoding="utf-8",
        )

    def raeume_leere_ordner_auf(self, wurzel: Path) -> None:
        if not wurzel.exists():
            return

        ordner_liste = [pfad for pfad in wurzel.rglob("*") if pfad.is_dir()]
        ordner_liste.sort(key=lambda pfad: len(pfad.parts), reverse=True)

        for ordner in ordner_liste:
            try:
                if ordner == wurzel:
                    continue
                if not any(ordner.iterdir()):
                    ordner.rmdir()
            except Exception:
                pass
