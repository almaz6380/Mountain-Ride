# Mountain Ride

![Mountain Ride](assets/key-art.jpg)

Snowboard-Downhill im Browser, in 3D aus Sicht hinter dem Fahrer. Du fährst einen endlosen Hang frontal hinunter, und es wird mit jedem Meter schneller.

## Spielen

Über einen Webserver öffnen (z. B. `python3 -m http.server` im Ordner, dann http://localhost:8000). Direkt per Doppelklick lädt der Browser die Bilder nicht. Läuft auf Handy und Desktop.

## Web-App

Spielen und installieren: **https://almaz6380.github.io/Mountain-Ride/**
Auf dem Handy im Browser öffnen und „Zum Home-Bildschirm“ wählen, dann startet es wie eine App im Vollbild.

Neu bauen und veröffentlichen: `python3 tools/build-pages.py` erzeugt `dist/`, dessen Inhalt auf den Branch `gh-pages` kommt.

## Steuerung

Fünf Spuren, ein Wischer = eine Spur.

| Eingabe | Aktion |
| --- | --- |
| Wischen links/rechts · ← → | Eine Spur wechseln, auch im Sprung |
| Wischen hoch · Tippen · Leertaste · ↑ | Springen |
| Wischen runter · ↓ | Ducken (unter Bannern durch) |
| In der Luft: Tippen · Leertaste | 360°-Drehung |
| In der Luft: hoch wischen · ↑ | Backflip |
| In der Luft: runter wischen · ↓ | Grab |
| P · Esc | Pause |

## Inhalt

- 3D mit three.js (per CDN), 3D-Fahrer (`assets/rider.glb`, Skelett wird beim Laden erzeugt), Hindernisse als Low-Poly-Modelle mit echten Schatten
- Startbildschirm, Menü mit Orts-Auswahl: Alpen, Waldabfahrt, Fackel-Nacht, Gletscher (eigenes Licht, Deko und Musik)
- Endlose Piste in Etappen: Aufwärmen → Baumstämme → Banner → Zäune & Schneekugeln → Gletscherspalten → Profi
- Tricks und Kombos: 360°, Backflip, Grab; verschiedene Tricks und saubere Landungen hintereinander multiplizieren die Punkte
- Power-ups: Magnet, Schild, Turbo, ×2, Super-Sprung; Münzen, Missionen, Shop (Upgrades, Start-Items, Snowboards, Schneespur)
- Streckenabschnitte: Tiefschnee, Eisplatte, Schneetunnel, Steilhang
- Duell per Link (gleiche Strecke, Gegner als Geist), Live-Duell, Tagesrennen und weltweite Bestenliste über Supabase, siehe [docs/online-bestenliste.md](docs/online-bestenliste.md)
- Musik und Effekte live per Web Audio; Ton, Lautstärke, Grafik-Qualität und mehr in den Einstellungen
- Tutorial beim ersten Start, jederzeit über die Einstellungen wiederholbar
