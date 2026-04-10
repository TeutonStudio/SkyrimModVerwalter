# Skyrim Mod Verwalter

Ein einfacher PyQt6-basierter Mod-Manager fuer Skyrim Special Edition unter Linux.

Das Programm verwaltet Mods, die in einem separaten Mod-Ordner liegen, und bringt deren Dateien nach `Data`, ohne dass du deine Mods dauerhaft manuell in den Spielordner kopieren musst.

## Was das Programm macht

Jeder Mod liegt als eigener Unterordner im eingestellten Modpfad, zum Beispiel:

```text
mods/
  SkyUI/
    interface/...
    scripts/...
    SkyUI.esp
```

Beim Deploy werden nicht ganze Mod-Ordner verlinkt oder kopiert, sondern einzelne Dateien rekursiv nach `Skyrim Special Edition/Data` uebernommen:

```text
mods/SkyUI/interface/... -> Data/interface/...
mods/SkyUI/scripts/...   -> Data/scripts/...
mods/SkyUI/SkyUI.esp     -> Data/SkyUI.esp
```

Die Dateistruktur im Spiel bleibt damit so, wie Skyrim sie erwartet.

## Funktionen

- Aktivieren und Deaktivieren einzelner Mods per Checkbox
- Drag & Drop fuer die Mod-Reihenfolge
- Konfliktaufloesung nach Listenreihenfolge
- Deploy per `Symlinks` oder per `Kopie`
- Undeploy der zuvor erzeugten Dateien
- automatisches Schreiben von `plugins.txt`
- Speichern von Aktivierungsstatus und Reihenfolge im aktuellen Modpfad
- explizites Aufraeumen ueberfluessiger JSON-Eintraege

## Wichtige Hinweise

- Wenn mehrere aktive Mods dieselbe Datei liefern, gewinnt der Mod weiter unten in der Liste.
- `meta.ini` wird beim Deploy ignoriert.
- `plugins.txt` wird beim Deploy automatisch geschrieben und beim Undeploy wieder geleert.
- Beim Schliessen des Programms wird die aktive Methode derzeit automatisch wieder entfernt.

## Symlinks oder Kopie

Im Menue `Modding variante` kannst du zwischen zwei Methoden wechseln:

### Symlinks

Dateien werden als symbolische Links in `Data` angelegt.

Vorteile:

- schnell
- spart Speicherplatz
- Mods bleiben klar vom Spiel getrennt

Wichtiger Hinweis:

`Symlink` scheint mit der Flathub-Version von Steam aktuell nicht zuverlaessig zu funktionieren. Wenn Mods im Spiel trotz Deploy nicht erkannt werden, nutze die Variante `Kopie`.

### Kopie

Dateien werden physisch nach `Data` kopiert und beim Undeploy wieder entfernt.

Vorteile:

- robuster, wenn Symlinks von Steam oder der Umgebung nicht sauber verarbeitet werden

Nachteile:

- benoetigt mehr Speicherplatz
- Dateien muessen wirklich kopiert werden

Beim Wechsel der Methode entfernt das Programm automatisch zuerst die Dateien der vorher aktiven Methode.

## Voraussetzungen

- Linux
- Python 3
- PyQt6
- installierte Skyrim Special Edition
- Steam bzw. Steam-Flatpak/Flathub mit vorhandenem `steamapps`-Ordner

## Starten

Das Programm kann direkt ueber Python gestartet werden:

```bash
python einstieg.py
```

## Einrichtung

Im Menue `Umgebung` muessen zwei Pfade gesetzt werden:

### Steamapps-Pfad

Hier wird der `steamapps`-Ordner angegeben, zum Beispiel:

```text
/home/alex/.var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps
```

Daraus ermittelt das Programm automatisch:

- den Skyrim-Spielordner unter `common/Skyrim Special Edition`
- den `Data`-Ordner
- die `plugins.txt` unter `compatdata/489830/.../Skyrim Special Edition/plugins.txt`

### Modpfad

Hier wird der Ordner gesetzt, in dem deine Mods als einzelne Unterordner liegen.

Beispiel:

```text
/home/alex/Games/MO2/Modpack1/mods
```

## Bedienung

### Modliste neu laden

- liest den Modordner neu ein
- haengt neue Mods unten an die bestehende Reihenfolge an
- behaelt bekannte Reihenfolge und Aktivierungszustaende bei

### Erzeugen

Je nach gewaehlter Variante:

- `Erzeuge symbolische Modlinks!`
- `Erzeuge Modkopien!`

Dabei werden:

- alle aktiven Mods in Listenreihenfolge verarbeitet
- Konflikte nach Prioritaet aufgeloest
- Dateien in `Data` erzeugt
- Plugins in `plugins.txt` aktiviert
- ein Manifest fuer spaeteres Entfernen geschrieben

### Vernichten

Je nach gewaehlter Variante:

- `Vernichte symbolische Modlinks!`
- `Vernichte Modkopien!`

Dabei werden nur die vom Programm erzeugten Dateien anhand des Manifests entfernt. Anschliessend werden leere Unterordner unter `Data` aufgeraeumt.

## Gespeicherte Dateien

Im aktuellen Modpfad werden folgende Dateien abgelegt:

- `modliste_status.json`
- `deploy_manifest.json`

### modliste_status.json

Enthaelt:

- Reihenfolge der Mods
- Aktivierungszustand

### deploy_manifest.json

Enthaelt:

- die aktive Methode (`symlink` oder `kopie`)
- die erzeugten Dateien
- aktive Mods in Reihenfolge
- Pluginliste

## Menuepunkte

### Umgebung

- `Steamapps-Pfad`
- `Modpfad`

### Modpack

- `JSON aufräumen`

Entfernt ueberfluessige Eintraege aus `modliste_status.json`, wenn:

- ein Modordner nicht mehr existiert
- derselbe Mod mehrfach in der JSON steht

### Modding variante

- `Symlinks`
- `Kopie`

## Typische Probleme

### Mod wird doppelt angezeigt

Das kann passieren, wenn alte oder doppelte Eintraege in `modliste_status.json` vorhanden sind.

Loesung:

- Menue `Modpack -> JSON aufräumen`

### Mod wird im Spiel nicht erkannt

Pruefe:

- stimmt der `Steamapps-Pfad`
- ist der richtige `Modpfad` gesetzt
- ist die Mod aktiviert
- wurde erfolgreich deployt
- steht das Plugin in `plugins.txt`

Wenn du Steam aus Flathub nutzt:

- verwende nach Moeglichkeit `Kopie` statt `Symlinks`

## Projektstruktur

```text
einstieg.py
kern/
  umgebung_verwalter.py
  status_speicher.py
  modpack_verwalter.py
  symlink_verwalter.py
  kopie_verwalter.py
schnittstelle/
  verwalter_widget.py
  modliste_widget.py
  pfad_dialog.py
```

## Kurzfassung

Wenn du einfach loslegen willst:

1. Programm starten
2. `Umgebung -> Steamapps-Pfad` setzen
3. `Umgebung -> Modpfad` setzen
4. `Modding variante -> Kopie` waehlen, wenn du Steam aus Flathub nutzt
5. Mods aktivieren
6. `Erzeuge ...` klicken

