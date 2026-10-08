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

Ohne den Schutz unten (Abschnitt „Schutz gegen Schummeln“) kann jeder, der sich auskennt, erfundene Punktzahlen eintragen.

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

## Schutz gegen Schummeln (für die Store-Version)

Das Spiel schickt seit Version 30 eine anonyme Spieler-ID mit und trägt unrealistische Läufe gar nicht erst ein.
Dieser Code sorgt dafür, dass die Datenbank das ebenfalls prüft. Im **SQL Editor** einfügen und **Run** drücken
(einmalig, die bestehenden Einträge bleiben erhalten):

```sql
-- anonyme Spieler-ID (das Spiel funktioniert auch ohne diese Spalte)
alter table public.scores add column if not exists player_id uuid;
alter table public.daily  add column if not exists player_id uuid;

-- Punkte passen zur Strecke (dieselbe Grenze wie im Spiel), Strecke nicht absurd
alter table public.scores add constraint scores_plausible check (dist <= 200000 and score <= dist * 60 + 5000) not valid;
alter table public.daily  add constraint daily_plausible  check (dist <= 200000 and score <= dist * 60 + 5000) not valid;

-- höchstens ein Eintrag alle 20 Sekunden pro Spieler-ID und Tabelle
create or replace function public.rate_limit_entries() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  if new.player_id is not null then
    if tg_table_name = 'scores' and exists (select 1 from public.scores where player_id = new.player_id and created_at > now() - interval '20 seconds')
    or tg_table_name = 'daily'  and exists (select 1 from public.daily  where player_id = new.player_id and created_at > now() - interval '20 seconds') then
      raise exception 'too many entries';
    end if;
  end if;
  new.created_at := now();
  return new;
end $$;

drop trigger if exists scores_rate_limit on public.scores;
create trigger scores_rate_limit before insert on public.scores for each row execute function public.rate_limit_entries();
drop trigger if exists daily_rate_limit on public.daily;
create trigger daily_rate_limit before insert on public.daily for each row execute function public.rate_limit_entries();

create index if not exists scores_player_idx on public.scores (player_id, created_at);
create index if not exists daily_player_idx  on public.daily  (player_id, created_at);
```

Namen mit Schimpfwörtern (in allen 10 Sprachen) filtert das Spiel selbst: beim Eintragen und beim Anzeigen.
Einen einzelnen Eintrag löschst du im **Table Editor** (Zeile anklicken → Delete).
