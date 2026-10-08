# Mountain Ride in den App Store und zu Google Play bringen

Das Spiel ist fertig für die Stores vorbereitet: App-Hülle (Capacitor) für Android und iOS, Werbung (AdMob),
Käufe (RevenueCat), Datenschutz/Impressum, Store-Texte und Screenshots in 10 Sprachen.
Was jetzt noch fehlt, sind **deine Konten, deine IDs und das Hochladen**. Diese Anleitung geht Schritt für Schritt durch.

Wo was liegt:
- `store/listing/<sprache>.json` – Name, Untertitel, Beschreibungen, Keywords, „Neu in dieser Version“
- `store/screenshots/<sprache>/ios-1…6.jpg` (1290 × 2796, iPhone 6,9") und `android-1…6.jpg` (1080 × 1920)
- `store/feature-graphic.png` – Google-Play-Grafik 1024 × 500
- `store/products.md` – In-App-Produkte mit IDs und Preisen
- `store/privacy-answers.md` – Antworten für App-Datenschutz, Datensicherheit, Altersfreigabe
- `resources/icon.png` – App-Icon 1024 × 1024 (für App Store Connect)

---

## 1. Konten anlegen (einmalig)

1. **Apple Developer Program** – https://developer.apple.com/programs/ (99 $ pro Jahr). Als Einzelperson anmelden.
2. **Google Play Console** – https://play.google.com/console (25 $ einmalig). Identität bestätigen.
3. **AdMob** – https://admob.google.com (kostenlos, mit demselben Google-Konto).
4. **RevenueCat** – https://app.revenuecat.com (kostenlos bis 2.500 $ Umsatz im Monat).
5. Bei Apple (App Store Connect → Business) und Google (Zahlungsprofil) **Steuer- und Bankdaten** eintragen –
   ohne das gibt es keine Käufe und keine Auszahlungen.

## 2. Impressum und Datenschutz ✔

Erledigt, wie bei deinen anderen Apps: Josef Gallab (Einzelunternehmen), österreichisches Impressum (§ 5 ECG, § 25 MedienG,
GISA 39801937), Kontakt kontakt@wellbooked.at (in `assets/lib/legal.js` bei `CONTACT` änderbar). Die Seiten:
- https://almaz6380.github.io/Mountain-Ride/privacy.html
- https://almaz6380.github.io/Mountain-Ride/imprint.html

## 3. AdMob einrichten

1. In AdMob **zwei Apps** anlegen: „Mountain Ride“ für Android und für iOS (noch nicht im Store → „Nein“ wählen).
2. Pro App **zwei Anzeigenblöcke** anlegen: „Belohnt“ (Rewarded) und „Interstitial“.
3. Unter **Datenschutz und Mitteilungen** eine **DSGVO-Mitteilung** (Einwilligung) erstellen und veröffentlichen,
   bei iOS zusätzlich die **IDFA-Erklärung**. Das ist der Dialog, den das Spiel beim Start zeigt.
4. Mir die IDs schicken (oder selbst eintragen):
   - App-IDs (`ca-app-pub-…~…`): Android → `android/app/src/main/res/values/strings.xml` (`admob_app_id`),
     iOS → `ios/App/App/Info.plist` (`GADApplicationIdentifier`)
   - Anzeigenblock-IDs (`ca-app-pub-…/…`): in `index.html` bei `MONEY.adUnits`, und dort `adsTesting: false` setzen.
5. Bis dahin zeigt das Spiel **Google-Testanzeigen** – damit kannst du alles gefahrlos ausprobieren.

## 4. Käufe einrichten

1. In App Store Connect (App → Monetarisierung → In-App-Käufe) und in der Play Console (Monetarisieren → Produkte →
   In-App-Produkte) die fünf Produkte aus `store/products.md` anlegen – **IDs exakt übernehmen**.
2. In RevenueCat ein Projekt anlegen, beide Apps verbinden (Anleitungen im RevenueCat-Dashboard: App-Store-Connect-API-Key
   bzw. Google-Service-Account), die fünf Produkte importieren.
3. Die zwei **öffentlichen SDK-Keys** (`appl_…` und `goog_…`) in `index.html` bei `MONEY.revenueCatKey` eintragen.
   Solange die Keys leer sind, blendet das Spiel den Kauf-Bereich einfach aus.

## 5. App bauen

Einmalig auf dem Mac: **Node.js** (https://nodejs.org, LTS), **Xcode** (App Store), **Android Studio**
(https://developer.android.com/studio). Dann im Terminal:

```bash
git clone https://github.com/almaz6380/Mountain-Ride.git
cd Mountain-Ride
npm install
npm run sync          # baut www/ aus dem Spiel und kopiert es in beide App-Projekte
```

Nach jeder Änderung am Spiel wieder `npm run sync`.

### Android (Google Play)

1. `npm run android` – öffnet Android Studio. Beim ersten Mal lädt es eine Weile.
2. Zum Testen: Handy per USB anschließen (Entwickleroptionen + USB-Debugging an) → grüner Play-Knopf.
3. Für den Store: **Build → Generate Signed App Bundle** → „Android App Bundle“ → neuen Schlüssel anlegen
   (Datei und Passwörter **gut aufbewahren**, ohne sie gibt es keine Updates) → `release`.
   Ergebnis: `android/app/release/app-release.aab`.
4. Bei jedem Update in `android/app/build.gradle` `versionCode` um 1 erhöhen (und `versionName`, z. B. "1.1").

### iOS (App Store)

1. `npm run ios` – öffnet Xcode.
2. Links „App“ anklicken → Reiter **Signing & Capabilities** → Team: dein Apple-Developer-Konto.
   Die Bundle-ID ist `com.almaz6380.mountainride`.
3. Unter **+ Capability** „In-App Purchase“ hinzufügen.
4. Zum Testen: iPhone anschließen, oben als Ziel wählen → ▶︎.
5. Für den Store: oben als Ziel „Any iOS Device“ → **Product → Archive** → im Fenster „Distribute App“ →
   „App Store Connect“ → Upload. Nach ein paar Minuten erscheint der Build in App Store Connect unter **TestFlight**.
6. Bei jedem Update in Xcode unter „General“ **Build** um 1 erhöhen.

## 6. Store-Einträge anlegen

**Entwickler-Website in beiden Stores:** https://almaz6380.github.io/ – dort liegt schon `app-ads.txt` mit deinem
AdMob-Konto (pub-8860791993288062). AdMob prüft die Datei auf der Website, die im Store-Eintrag steht.
Support-E-Mail: kontakt@wellbooked.at.

**App Store Connect** (https://appstoreconnect.apple.com → Meine Apps → +):
- Name, Untertitel, Werbetext, Beschreibung, Keywords, „Neu“: aus `store/listing/<sprache>.json`
  (Sprachen links unter „Lokalisierungen“ hinzufügen: Deutsch, Englisch (USA), Spanisch (Spanien),
  Portugiesisch (Brasilien), Französisch, Italienisch, Russisch, Chinesisch (vereinfacht), Japanisch, Arabisch).
- Screenshots: `store/screenshots/<sprache>/ios-*.jpg` in das Feld **iPhone 6,9"**.
- Datenschutz-URL, App-Datenschutz, Altersfreigabe: siehe `store/privacy-answers.md`.
- Kategorie: Spiele → Action (zweite: Sport). Preis: kostenlos.

**Google Play Console** (App erstellen → Spiel, kostenlos):
- Store-Eintrag: App-Name = `name`, Kurzbeschreibung = `shortDescription`, Vollständige Beschreibung = `description`
  (Übersetzungen unter „Übersetzungen verwalten“ hinzufügen).
- Grafiken: Symbol 512 × 512 (`assets/icon-512.png`), Feature-Grafik `store/feature-graphic.png`,
  Smartphone-Screenshots `store/screenshots/<sprache>/android-*.jpg`.
- App-Inhalte (Datenschutzerklärung, Werbung, Datensicherheit, Zielgruppe, Altersfreigabe): siehe `store/privacy-answers.md`.

## 7. Testen und Einreichen

**Google – Pflichttest:** Neue private Entwicklerkonten müssen vor dem Start einen **geschlossenen Test mit mindestens
12 Testern über 14 Tage** machen (Play Console → Test → Geschlossener Test → Tester per E-Mail-Liste einladen,
`.aab` hochladen). Danach „Zugriff auf Produktion beantragen“.

**Apple – TestFlight:** Build in TestFlight freigeben, mit dem eigenen iPhone testen. Käufe mit einem
**Sandbox-Konto** (App Store Connect → Benutzer und Zugriff → Sandbox) ausprobieren.

Checkliste vor dem Einreichen:
- [ ] Einwilligungsdialog erscheint beim ersten Start (in der EU), auf dem iPhone danach die Tracking-Frage
- [ ] Belohntes Video „Weiterfahren“ und „Münzen ×2“ funktionieren, Zwischenwerbung kommt nach jeder 4. Runde
- [ ] Münzpaket kaufen → Münzen kommen an; „Werbefrei“ kaufen → keine Zwischenwerbung mehr
- [ ] App löschen, neu installieren → „Käufe wiederherstellen“ bringt „Werbefrei“ zurück
- [ ] Spielstand bleibt nach dem Schließen der App erhalten
- [ ] Einstellungen → Datenschutz / Impressum öffnen die Seiten mit deinen Daten
- [ ] Echte AdMob-IDs und RevenueCat-Keys eingetragen, `adsTesting: false`

Dann: App Store Connect → Version → **Zur Prüfung einreichen**; Play Console → Produktion → **Release erstellen**.
Die Prüfung dauert meist 1–3 Tage. Rückfragen der Prüfer beantworten wir zusammen.
