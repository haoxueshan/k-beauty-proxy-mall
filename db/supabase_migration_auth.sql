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

create table if not exists admin_users (
  id uuid primary key default gen_random_uuid(),
  email text unique not null,
  password_salt text not null,
  password_hash text not null,
  name text not null,
  phone text,
  role text not null default 'admin' check (role in ('admin', 'super_admin')),
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists admin_auth_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references admin_users(id) on delete cascade,
  token text unique not null,
  created_at timestamptz default now()
);

alter table if exists cart_items
  alter column product_id type text using product_id::text;

alter table if exists cart_items
  add column if not exists source_url text;

alter table if exists cart_items
  add column if not exists title_zh text;

alter table if exists cart_items
  add column if not exists title_ko text;

alter table if exists cart_items
  add column if not exists image_url text;

alter table if exists cart_items
  add column if not exists sale_price_krw integer;

alter table if exists cart_items
  add column if not exists price_cny numeric;

alter table if exists cart_items
  add column if not exists brand_ko text;

alter table if exists orders
  alter column user_id type uuid using user_id::uuid;

alter table if exists order_items
  alter column product_id type text using product_id::text;

alter table if exists order_items
  add column if not exists source_url text;

alter table if exists order_items
  add column if not exists note text;
