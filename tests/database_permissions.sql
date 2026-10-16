-- CI only: exercise PostgreSQL grants and RLS without real Supabase credentials.
begin;
insert into public.secret (id, "API_KEY", "API_SECRET") values (2, 'unchanged', 'unchanged');
set local role anon;
do $$
declare
  changed bigint;
  target bigint;
begin
  update public.secret set "API_KEY" = 'test-key', "API_SECRET" = 'test-secret'
    where id = 1 returning id into target;
  get diagnostics changed = row_count;
  if changed <> 1 or target <> 1 then
    raise exception 'Anonymous scoped update must return exactly one id';
  end if;
  insert into public.bot_updates (update_id) values (123);
  begin
    insert into public.bot_updates (update_id) values (123);
    raise exception 'Duplicate update must fail';
  exception when unique_violation then null;
  end;
  begin
    perform "API_KEY", "API_SECRET" from public.secret;
    raise exception 'Secret values must not be readable';
  exception when insufficient_privilege then null;
  end;
  begin
    perform update_id from public.bot_updates;
    raise exception 'Update IDs must not be readable';
  exception when insufficient_privilege then null;
  end;
  begin
    delete from public.secret where id = 1;
    raise exception 'Secrets must not be deletable';
  exception when insufficient_privilege then null;
  end;
  begin
    update public.secret set id = 3 where id = 1;
    raise exception 'Primary keys must not be editable';
  exception when insufficient_privilege then null;
  end;
  begin
    insert into public.secret (id) values (3);
    raise exception 'Secret rows must not be insertable';
  exception when insufficient_privilege then null;
  end;
end $$;
reset role;
do $$
begin
  if not exists (select 1 from public.secret where id = 1 and "API_KEY" = 'test-key'
                 and "API_SECRET" = 'test-secret') then
    raise exception 'Target values were not updated';
  end if;
  if not exists (select 1 from public.secret where id = 2 and "API_KEY" = 'unchanged'
                 and "API_SECRET" = 'unchanged') then
    raise exception 'Another row was unexpectedly changed';
  end if;
end $$;
rollback;
