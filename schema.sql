-- Execute once using the Supabase SQL editor. Never put real credentials in this file.
create table if not exists public.secret (
  id bigint primary key,
  "API_KEY" text not null default '',
  "API_SECRET" text not null default ''
);
alter table public.secret enable row level security;
insert into public.secret (id) values (1) on conflict (id) do nothing;
create table if not exists public.bot_updates (
  update_id bigint primary key,
  created_at timestamptz not null default now()
);
alter table public.bot_updates enable row level security;
-- Public-key-only mode, explicitly requested in issue #3. Anyone with the
-- project URL and public key can update secrets and claim update IDs directly.
-- No anonymous reads of API_KEY/API_SECRET; PATCH returns only id.
revoke all on public.secret, public.bot_updates from public, anon, authenticated;
revoke select (id, "API_KEY", "API_SECRET"), update (id, "API_KEY", "API_SECRET")
  on public.secret from public, anon, authenticated;
revoke select (update_id, created_at), insert (update_id, created_at)
  on public.bot_updates from public, anon, authenticated;
grant usage on schema public to anon;
grant select (id), update ("API_KEY", "API_SECRET") on public.secret to anon;
grant insert (update_id) on public.bot_updates to anon;

drop policy if exists bot_public_secret_select on public.secret;
create policy bot_public_secret_select on public.secret for select to anon using (true);
drop policy if exists bot_public_secret_update on public.secret;
create policy bot_public_secret_update on public.secret for update to anon
  using (true) with check (true);
drop policy if exists bot_public_updates_insert on public.bot_updates;
create policy bot_public_updates_insert on public.bot_updates for insert to anon
  with check (true);

-- Make newly created tables visible to the REST API after commit.
notify pgrst, 'reload schema';
