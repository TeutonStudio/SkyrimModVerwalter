import json

from kern.umgebung_verwalter import Umgebung


class StatusSpeicher:
    def __init__(self, umgebung: Umgebung):
        self.umgebung = umgebung

    def lade_mod_status(self) -> dict:
        status_datei = self.umgebung.status_datei
        if not status_datei.exists():
            return {"mods": []}

        try:
            return json.loads(status_datei.read_text(encoding="utf-8"))
        except Exception:
            return {"mods": []}

    def lade_mod_status_strikt(self) -> dict:
        status_datei = self.umgebung.status_datei
        if not status_datei.exists():
            return {"mods": []}
        return json.loads(status_datei.read_text(encoding="utf-8"))

    def speichere_mod_status(self, mods: list[tuple[str, bool]]) -> None:
        self.umgebung.mod_ordner.mkdir(parents=True, exist_ok=True)
        daten = {
            "mods": [
                {"name": name, "aktiv": aktiv}
                for name, aktiv in mods
            ]
        }
        self.umgebung.status_datei.write_text(
            json.dumps(daten, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def speichere_mod_status_roh(self, daten: dict) -> None:
        self.umgebung.mod_ordner.mkdir(parents=True, exist_ok=True)
        self.umgebung.status_datei.write_text(
            json.dumps(daten, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def lade_manifest(self) -> dict | None:
        manifest_datei = self.umgebung.manifest_datei
        if not manifest_datei.exists():
            return None
        return json.loads(manifest_datei.read_text(encoding="utf-8"))

    def speichere_manifest(self, manifest: dict) -> None:
        self.umgebung.mod_ordner.mkdir(parents=True, exist_ok=True)
        self.umgebung.manifest_datei.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def loesche_manifest(self) -> None:
        self.umgebung.manifest_datei.unlink()
