-- Issue #5: run in Supabase SQL Editor on the same project as SUPABASE_URL.
-- This migration only repairs deduplication; existing secrets stay untouched.
begin;
create table if not exists public.bot_updates (
  update_id bigint primary key,
  created_at timestamptz not null default now()
);
alter table public.bot_updates enable row level security;
revoke all on public.bot_updates from public, anon, authenticated;
revoke select (update_id, created_at), insert (update_id, created_at)
  on public.bot_updates from public, anon, authenticated;
grant usage on schema public to anon;
grant insert (update_id) on public.bot_updates to anon;
drop policy if exists bot_public_updates_insert on public.bot_updates;
create policy bot_public_updates_insert on public.bot_updates for insert to anon
  with check (true);
notify pgrst, 'reload schema';
commit;
