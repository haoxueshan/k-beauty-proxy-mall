alter table if exists users
  add column if not exists password_salt text;

alter table if exists auth_sessions
  add column if not exists id uuid default gen_random_uuid();

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conname = 'auth_sessions_pkey'
  ) then
    alter table auth_sessions add constraint auth_sessions_pkey primary key (id);
  end if;
end $$;

alter table if exists auth_sessions
  alter column user_id type uuid using user_id::uuid;

alter table if exists cart_items
  alter column product_id type text using product_id::text;

alter table if exists orders
  alter column user_id type uuid using user_id::uuid;

alter table if exists order_items
  alter column product_id type text using product_id::text;
