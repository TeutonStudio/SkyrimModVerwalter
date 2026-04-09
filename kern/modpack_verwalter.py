from dataclasses import dataclass
from pathlib import Path

from kern.status_speicher import StatusSpeicher
from kern.umgebung_verwalter import Umgebung


PLUGIN_ENDUNGEN = {".esp", ".esm", ".esl"}


@dataclass
class ModListenEintrag:
    name: str
    aktiviert: bool
    ist_ueberfluessig: bool = False


class ModPackVerwalter:
    def __init__(self, umgebung: Umgebung, status_speicher: StatusSpeicher):
        self.umgebung = umgebung
        self.status_speicher = status_speicher

    def ermittle_vorhandene_mods(self) -> list[str]:
        if not self.umgebung.mod_ordner.exists():
            raise FileNotFoundError(str(self.umgebung.mod_ordner))

        return sorted(
            [
                ordner.name
                for ordner in self.umgebung.mod_ordner.iterdir()
                if ordner.is_dir()
            ],
            key=lambda name: name.lower(),
        )

    def lade_modliste(self) -> list[ModListenEintrag]:
        alter_status = self.status_speicher.lade_mod_status()
        bekannte_mods = alter_status.get("mods", [])
        vorhandene_mods = self.ermittle_vorhandene_mods()
        vorhandene_mods_set = set(vorhandene_mods)
        bereits_zugeordnet: set[str] = set()
        finale_eintraege: list[ModListenEintrag] = []

        for eintrag in bekannte_mods:
            mod_name = eintrag["name"]
            aktiviert = bool(eintrag.get("aktiv", False))
            ordner_existiert = mod_name in vorhandene_mods_set
            ordner_bereits_zugeordnet = mod_name in bereits_zugeordnet
            ist_ueberfluessig = (not ordner_existiert) or ordner_bereits_zugeordnet

            finale_eintraege.append(
                ModListenEintrag(
                    name=mod_name,
                    aktiviert=aktiviert and not ist_ueberfluessig,
                    ist_ueberfluessig=ist_ueberfluessig,
                )
            )

            if ordner_existiert and not ordner_bereits_zugeordnet:
                bereits_zugeordnet.add(mod_name)

        for mod_name in vorhandene_mods:
            if mod_name not in bereits_zugeordnet:
                finale_eintraege.append(ModListenEintrag(name=mod_name, aktiviert=False))

        return finale_eintraege

    def bereinige_status_json(self) -> tuple[int, int]:
        daten = self.status_speicher.lade_mod_status_strikt()
        bekannte_mods = daten.get("mods", [])
        vorhandene_mods = set(self.ermittle_vorhandene_mods())
        bereinigt: list[dict] = []
        bereits_zugeordnet: set[str] = set()
        entfernt = 0

        for eintrag in bekannte_mods:
            mod_name = eintrag["name"]
            ordner_existiert = mod_name in vorhandene_mods
            ordner_bereits_zugeordnet = mod_name in bereits_zugeordnet

            if not ordner_existiert or ordner_bereits_zugeordnet:
                entfernt += 1
                continue

            bereinigt.append(eintrag)
            bereits_zugeordnet.add(mod_name)

        daten["mods"] = bereinigt
        self.status_speicher.speichere_mod_status_roh(daten)
        return len(bereinigt), entfernt

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
