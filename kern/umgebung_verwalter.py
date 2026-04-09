from pathlib import Path


DEFAULT_STEAMAPPS_ORDNER = Path(
    "/home/alex/.var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps"
)
DEFAULT_MOD_ORDNER = Path("/home/alex/Games/MO2/Modpack1/mods")
SKYRIM_ORDNERNAME = "Skyrim Special Edition"
SKYRIM_APP_ID = "489830"


class Umgebung:
    def __init__(
        self,
        steamapps_ordner: Path | None = None,
        mod_ordner: Path | None = None,
    ):
        self.steamapps_ordner = steamapps_ordner or DEFAULT_STEAMAPPS_ORDNER
        self.mod_ordner = mod_ordner or DEFAULT_MOD_ORDNER

    @property
    def spiel_ordner(self) -> Path:
        return self.steamapps_ordner / "common" / SKYRIM_ORDNERNAME

    @property
    def data_ordner(self) -> Path:
        return self.spiel_ordner / "Data"

    @property
    def plugins_txt(self) -> Path:
        return (
            self.steamapps_ordner
            / "compatdata"
            / SKYRIM_APP_ID
            / "pfx"
            / "drive_c"
            / "users"
            / "steamuser"
            / "AppData"
            / "Local"
            / SKYRIM_ORDNERNAME
            / "plugins.txt"
        )

    @property
    def status_datei(self) -> Path:
        return self.mod_ordner / "modliste_status.json"

    @property
    def manifest_datei(self) -> Path:
        return self.mod_ordner / "deploy_manifest.json"
