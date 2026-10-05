# Weltweite Bestenliste einrichten (Supabase, kostenlos)

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

Unter **Project Settings → API** stehen die **Project URL** und der **anon public** Key.
Beide in `index.html` eintragen:

```js
const ONLINE = { url: 'https://DEINPROJEKT.supabase.co', key: 'DEIN-ANON-KEY' };
```

Der anon-Key ist für die Nutzung im Browser gedacht und darf öffentlich sein. Die Regeln oben erlauben nur
Lesen und neue Einträge, kein Ändern oder Löschen.

## Hinweis

Die Liste hat keinen Schutz gegen Schummeln: Wer sich auskennt, kann erfundene Punktzahlen eintragen.
Für ein privates Spiel unter Freunden reicht das in der Regel.
