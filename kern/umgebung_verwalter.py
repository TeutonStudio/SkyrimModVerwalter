from pathlib import Path


DEFAULT_SPIEL_ORDNER = Path(
    "/home/alex/.var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps/common/Skyrim Special Edition"
)
DEFAULT_MOD_ORDNER = Path("/home/alex/Games/MO2/Modpack1/mods")
DEFAULT_PLUGINS_TXT = Path(
    "/home/alex/.var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps/compatdata/489830/pfx/"
    "drive_c/users/steamuser/AppData/Local/Skyrim Special Edition/plugins.txt"
)


class Umgebung:
    def __init__(
        self,
        spiel_ordner: Path | None = None,
        mod_ordner: Path | None = None,
        plugins_txt: Path | None = None,
    ):
        self.spiel_ordner = spiel_ordner or DEFAULT_SPIEL_ORDNER
        self.mod_ordner = mod_ordner or DEFAULT_MOD_ORDNER
        self.plugins_txt = plugins_txt or DEFAULT_PLUGINS_TXT

    @property
    def data_ordner(self) -> Path:
        return self.spiel_ordner / "Data"

    @property
    def status_datei(self) -> Path:
        return self.mod_ordner / "modliste_status.json"

    @property
    def manifest_datei(self) -> Path:
        return self.mod_ordner / "deploy_manifest.json"
