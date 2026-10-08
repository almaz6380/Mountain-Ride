# In-App-Produkte

Diese Produkte legst du **genau mit diesen IDs** in App Store Connect und in der Google Play Console an.
Danach trägst du sie in RevenueCat ein (Products, ohne Entitlements nötig; das Spiel wertet die Käufe selbst aus).

| Produkt-ID      | Typ (Apple)            | Typ (Google)      | Preis (Vorschlag) | Inhalt                                          |
|-----------------|------------------------|-------------------|-------------------|-------------------------------------------------|
| `starter_pack`  | Nicht-Verbrauchsartikel | Einmalkauf        | 4,99 €            | Werbefrei + goldenes Board + 3.000 Münzen        |
| `no_ads`        | Nicht-Verbrauchsartikel | Einmalkauf        | 2,99 €            | Keine Zwischenwerbung mehr                      |
| `coins_small`   | Verbrauchsartikel      | Verbrauchsartikel | 0,99 €            | 1.000 Münzen                                    |
| `coins_medium`  | Verbrauchsartikel      | Verbrauchsartikel | 4,99 €            | 5.500 Münzen                                    |
| `coins_large`   | Verbrauchsartikel      | Verbrauchsartikel | 9,99 €            | 12.000 Münzen                                   |

Anzeigenamen und Beschreibungen pro Sprache stehen im Spiel (Schlüssel `iap.*` in `index.html` / `assets/lib/i18n.js`)
und können für die Store-Produktseiten übernommen werden.

## Wirtschaft im Spiel (zur Einordnung der Preise)

- Ein Lauf bringt die eingesammelten Münzen plus **1 Münze pro 50 m** (Streckenbonus). Ein normaler Lauf von 1–2 km bringt so etwa 50–100 Münzen.
- Missionen geben 80 / 150 / 250 / 400 Münzen.
- Power-up-Stufen kosten 150 / 300 / 500 / 800 / 1.200 Münzen, Boards 300–1.200, Orte 800–1.500.
- Damit kostet die erste Upgrade-Stufe 2–3 Läufe, die letzte etwa 15–20. Alles ist ohne Kauf erreichbar;
  Münzpakete sind eine Abkürzung, „Werbefrei“ der wichtigste Kauf.
- Belohnte Videos (freiwillig): „Weiterfahren“ (einmal pro Lauf) und „Münzen ×2“ am Rundenende.
  Zwischenwerbung höchstens nach jeder 4. Runde, nie in den ersten 3 Läufen, im Tutorial oder im Duell.
