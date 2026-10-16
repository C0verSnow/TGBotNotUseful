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
-- No anonymous/authenticated policies. Only backend service_role accesses these tables.
revoke all on public.secret, public.bot_updates from anon, authenticated;
grant select, update on public.secret to service_role;
grant select, insert on public.bot_updates to service_role;
