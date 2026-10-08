# Antworten für die Store-Fragebögen

Datenschutzerklärung (für beide Stores): https://almaz6380.github.io/Mountain-Ride/privacy.html
Support-/Marketing-URL: https://almaz6380.github.io/Mountain-Ride/

Vorher in `assets/lib/legal.js` oben unter `CONTACT` deinen Namen, deine Anschrift und deine E-Mail eintragen
(Pflicht für Impressum und Datenschutzerklärung), dann neu veröffentlichen.

## Apple – App-Datenschutz (App Store Connect → App-Datenschutz)

„Werden Daten erfasst?“ → **Ja**. Folgende Datentypen anhaken:

| Datentyp (Apple) | Zweck | Mit Identität verknüpft? | Zum Tracking? | Wer |
|---|---|---|---|---|
| Kennungen → **Geräte-ID** | Werbung durch Drittanbieter | Nein | **Ja** | AdMob (Werbe-ID, nur nach ATT-Zustimmung) |
| Kennungen → **Nutzer-ID** | App-Funktionalität | Nein | Nein | Spielername + anonyme Spieler-ID in der Bestenliste, RevenueCat-ID |
| Standort → **Ungefährer Standort** | Werbung durch Drittanbieter | Nein | Ja | AdMob (aus der IP-Adresse) |
| Nutzungsdaten → **Produktinteraktion** | Werbung durch Drittanbieter, Analysen | Nein | Ja | AdMob |
| Nutzungsdaten → **Werbedaten** | Werbung durch Drittanbieter | Nein | Ja | AdMob |
| Diagnose → **Absturzdaten**, **Leistungsdaten** | App-Funktionalität | Nein | Nein | Google Mobile Ads SDK |
| Käufe → **Kaufhistorie** | App-Funktionalität | Nein | Nein | RevenueCat |
| Nutzerinhalte → **Gameplay-Inhalte** | App-Funktionalität | Nein | Nein | Punkte/Strecke in Bestenliste, Tagesrennen, Duell |

Nicht erfasst: Kontaktdaten, Gesundheit, Finanzinfos (Zahlungsdaten sieht nur Apple), genauer Standort,
sensible Daten, Kontakte, Browserverlauf, Suchverlauf.

Tracking: Ja (nur mit Zustimmung über die App-Tracking-Abfrage; das Spiel fragt beim ersten Start).

## Google Play – Datensicherheit (Play Console → App-Inhalte → Datensicherheit)

- Werden Daten erhoben oder geteilt? **Ja**
- Werden alle Daten bei der Übertragung verschlüsselt? **Ja** (HTTPS)
- Können Nutzer das Löschen ihrer Daten beantragen? **Ja** (per E-Mail, siehe Datenschutzerklärung)

| Datentyp (Google) | Erhoben | Geteilt | Zweck | Optional? |
|---|---|---|---|---|
| Standort → Ungefährer Standort | Ja | Ja (AdMob) | Werbung | Nein |
| App-Aktivitäten → App-Interaktionen | Ja | Ja (AdMob) | Werbung, Analysen | Nein |
| App-Aktivitäten → Sonstige nutzergenerierte Inhalte (Spielername, Punkte) | Ja | Nein | App-Funktionen | Ja (nur wer sich einträgt) |
| App-Info und -Leistung → Absturzprotokolle, Diagnosedaten | Ja | Ja (AdMob) | Werbung, App-Funktionen | Nein |
| Geräte- oder andere IDs | Ja | Ja (AdMob) | Werbung, Betrugsprävention | Nein |
| Finanzdaten → Kaufverlauf | Ja | Nein | App-Funktionen | Ja |

Werbe-ID: Ja, die App nutzt die Werbe-ID (Play Console → App-Inhalte → Werbe-ID → „Werbung oder Marketing“).

## Zielgruppe und Inhalte

- **Google Play → Zielgruppe:** 13–15, 16–17, 18 und älter (nicht unter 13 auswählen, sonst gelten die strengeren
  Familien-Regeln und normale AdMob-Werbung ist nicht erlaubt). „Spricht die App Kinder an?“ → Nein.
- **Apple:** nicht als „Für Kinder“ kennzeichnen.
- **Enthält Werbung:** Ja (beide Stores angeben).

## Altersfreigabe

**Apple (Altersfreigabe-Fragebogen):** überall „Keine“, außer:
- Zufallsgeneratoren/Glücksspiel: Nein · Wettbewerbe: Nein · Unbeschränkter Webzugriff: Nein
- Nutzergenerierte Inhalte / Interaktion mit anderen Nutzern: Ja, eingeschränkt – frei wählbare Spielernamen in
  Bestenlisten und im Live-Duell (ohne Chat, Namen werden auf Schimpfwörter gefiltert).
- In-App-Käufe: Ja. Werbung: Ja.
Erwartete Einstufung: 9+ (wegen nutzergenerierter Namen) bzw. 4+.

**Google Play (IARC-Fragebogen):** Kategorie „Spiel“. Gewalt: Nein (Stürze in den Schnee sind keine Gewalt),
Angst: Nein, Sex/Nacktheit: Nein, Sprache: Nein, Drogen: Nein, Glücksspiel: Nein.
Nutzer interagieren: Ja (Spielernamen in Bestenlisten, Live-Duell ohne Chat). Teilt Standort: Nein.
Digitale Käufe: Ja. Erwartete Einstufung: USK 0 / PEGI 3 / Everyone.

## Export-Compliance (Apple)

Verwendet die App Verschlüsselung? Nur Standard-HTTPS → in `Info.plist` ist `ITSAppUsesNonExemptEncryption = NO`
gesetzt, die Frage entfällt dann beim Hochladen.
