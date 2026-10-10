# Eigene 3D-Modelle mit KI (meshy.ai, kostenlos)

**Gratis-Version:**
- 100 Credits im Monat; ein Modell kostet 20, also etwa 5 Versuche.
- 10 Downloads im Monat, aber **nur von Modellen mit „Meshy 6 Lite“**.
- Lizenz CC BY 4.0: Du darfst die Modelle auch in der Verkaufs-App benutzen, musst aber „Meshy“ nennen.
  Ich trage das in `assets/MODELS-CREDITS.md` ein.

## Schritt für Schritt (etwa 10 Minuten pro Modell)

1. **meshy.ai** öffnen → „Sign up“ → mit dem Google-Konto anmelden.
2. Links **„Text to 3D“** wählen.
3. Bei Modell **„Meshy 6 Lite“** einstellen (sonst ist der Download nicht gratis).
4. Falls angeboten: **„Low Poly“** bzw. **„Smart Topology“** einschalten.
5. Einen dieser Sätze ins Textfeld kopieren:

   | Was | Satz |
   |---|---|
   | Tanne | `stylized snowy pine tree, snow on the branches, low poly game asset, single tree, no ground` |
   | Felsen | `stylized mountain rock with snow on top, low poly game asset, no ground` |
   | Baumstamm | `fallen tree log with snow on top, stylized, low poly game asset, no ground` |
   | Schneemann | `cute snowman with top hat and red scarf, stylized, low poly game asset` |
   | Pistenraupe | `red snow groomer vehicle, stylized, low poly game asset` |

6. **„Generate“** tippen, etwa 1 Minute warten, den schönsten Vorschlag anklicken (mit dem Finger drehen zum Ansehen).
   Gefällt keiner: nochmal „Generate“ (kostet wieder Credits).
7. **„Download“** → Format **GLB** → die Datei im Chat an Claude schicken.

Claude macht den Rest: Größe, Schnee, weniger Flächen fürs Handy (`tools/models.py`), Einbau und Bilder aus dem Spiel
zur Abnahme. Für den Wald reichen 3 Tannen; sie werden verschieden gedreht und skaliert.

## Ganz kostenlos: TRELLIS (Microsoft) auf Hugging Face

Keine Credits, MIT-Lizenz (auch für die Verkaufs-App, ohne Namensnennung), Download als GLB. Läuft im Browser.

1. **huggingface.co/spaces/gokaygokay/Flux-TRELLIS** öffnen (kein Konto nötig).
2. Satz eintippen, z. B. `grey mountain boulder with snow on top, stylized game asset` oder
   `cute snowman with black top hat, carrot nose, red scarf, stylized game asset`.
3. **„Generate“** → 1–3 Minuten warten (bei viel Andrang Warteschlange).
4. **„Extract GLB“** → **„Download GLB“** → per Google Drive („Jeder mit dem Link“) an Claude schicken.

Mit Bild statt Text: **huggingface.co/spaces/trellis-community/TRELLIS** (Foto hochladen).

**Nicht verwenden:** Hunyuan3D (Tencent) – die Lizenz gilt nicht in der EU.
