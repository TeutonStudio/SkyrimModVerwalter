from pathlib import Path

from kern.status_speicher import StatusSpeicher
from kern.umgebung_verwalter import Umgebung


PLUGIN_ENDUNGEN = {".esp", ".esm", ".esl"}


class ModPackVerwalter:
    def __init__(self, umgebung: Umgebung, status_speicher: StatusSpeicher):
        self.umgebung = umgebung
        self.status_speicher = status_speicher

    def lade_modliste(self) -> list[tuple[str, bool]]:
        alter_status = self.status_speicher.lade_mod_status()
        bekannte_mods = alter_status.get("mods", [])

        bekannte_reihenfolge = [eintrag["name"] for eintrag in bekannte_mods]
        bekannte_aktiv = {
            eintrag["name"]: bool(eintrag.get("aktiv", False))
            for eintrag in bekannte_mods
        }

        if not self.umgebung.mod_ordner.exists():
            raise FileNotFoundError(str(self.umgebung.mod_ordner))

        vorhandene_mods = sorted(
            [
                ordner.name
                for ordner in self.umgebung.mod_ordner.iterdir()
                if ordner.is_dir()
            ],
            key=lambda name: name.lower(),
        )

        finale_reihenfolge: list[str] = []

        for mod_name in bekannte_reihenfolge:
            if mod_name in vorhandene_mods:
                finale_reihenfolge.append(mod_name)

        for mod_name in vorhandene_mods:
            if mod_name not in finale_reihenfolge:
                finale_reihenfolge.append(mod_name)

        return [
            (mod_name, bekannte_aktiv.get(mod_name, False))
            for mod_name in finale_reihenfolge
        ]

    def sammle_dateien_eines_mods(self, mod_name: str) -> list[Path]:
        mod_pfad = self.umgebung.mod_ordner / mod_name
        return sorted(
            [pfad for pfad in mod_pfad.rglob("*") if pfad.is_file()],
            key=lambda pfad: str(pfad.relative_to(mod_pfad)).lower(),
        )

    def berechne_deployment(
        self,
        aktive_mods: list[str],
    ) -> tuple[dict[str, str], list[str], list[str]]:
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
                    if plugin_name in plugins:
                        plugins.remove(plugin_name)
                    plugins.append(plugin_name)

        return deployment_map, plugins, konflikte
