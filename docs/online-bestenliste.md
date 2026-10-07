# Online-Funktionen einrichten (Supabase, kostenlos)

Ein Supabase-Projekt schaltet zwei Dinge frei: die **weltweite Bestenliste** und das **Live-Duell**
(zwei Spieler fahren gleichzeitig dieselbe Strecke). Das Live-Duell braucht keine Tabelle, nur Realtime,
das bei neuen Projekten schon eingeschaltet ist.

Das Spiel kann Ergebnisse in einer gemeinsamen Online-Liste speichern. Dafür braucht es ein kostenloses
Supabase-Projekt. Die Liste funktioniert nur in der Web-App (GitHub Pages), nicht im Claude-Artifact-Link,
weil dort keine Verbindungen zu fremden Servern erlaubt sind.

## 1. Projekt anlegen

1. Auf https://supabase.com registrieren und **New project** anlegen (Region z. B. Frankfurt).
2. Links **SQL Editor** öffnen, diesen Code einfügen und **Run** drücken:

```sql
create table public.scores (
  id bigint generated always as identity primary key,
  name text not null check (char_length(name) between 1 and 14),
  score integer not null check (score between 0 and 10000000),
  dist integer not null check (dist between 0 and 1000000),
  created_at timestamptz not null default now()
);

alter table public.scores enable row level security;

create policy "Bestenliste lesen" on public.scores
  for select to anon using (true);

create policy "Ergebnis eintragen" on public.scores
  for insert to anon with check (true);
```

## 2. Zugangsdaten eintragen

Unter **Project Settings → API** (bzw. **API Keys**) stehen die **Project URL** und der **anon public** Key
(oder der neue **Publishable key**, beginnt mit `sb_publishable_`; beide funktionieren).
Beide in `index.html` eintragen:

```js
const ONLINE = { url: 'https://DEINPROJEKT.supabase.co', key: 'DEIN-ANON-KEY' };
```

Der anon-Key ist für die Nutzung im Browser gedacht und darf öffentlich sein. Die Regeln oben erlauben nur
Lesen und neue Einträge, kein Ändern oder Löschen.

## Hinweis

Die Liste hat keinen Schutz gegen Schummeln: Wer sich auskennt, kann erfundene Punktzahlen eintragen.
Für ein privates Spiel unter Freunden reicht das in der Regel.

## Tagesrennen (Tages-Bestenliste)

Für das Tagesrennen braucht es eine zweite Tabelle. Im **SQL Editor** einfügen und **Run** drücken:

```sql
create table public.daily (
  id bigint generated always as identity primary key,
  day date not null,
  name text not null check (char_length(name) between 1 and 14),
  dist integer not null check (dist between 0 and 1000000),
  score integer not null check (score between 0 and 100000000),
  created_at timestamptz not null default now()
);
alter table public.daily enable row level security;
create policy "Tagesrennen lesen" on public.daily for select to anon using (true);
create policy "Tagesrennen eintragen" on public.daily for insert to anon
  with check (day between current_date - 1 and current_date + 1);
grant select, insert on public.daily to anon;
```

Die Strecke des Tages wird aus dem Datum berechnet: alle Spieler fahren am selben Tag dieselbe Strecke am selben Ort.
