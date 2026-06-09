create table if not exists profiles (
  id uuid primary key,
  email text not null,
  role text not null default 'user',
  created_at timestamptz default now()
);

alter table if exists profiles
  drop constraint if exists profiles_role_check;

alter table if exists profiles
  add constraint profiles_role_check check (role in ('user', 'admin', 'super_admin'));

create index if not exists idx_profiles_role on profiles(role);

alter table if exists users
  add column if not exists role text not null default 'user';

alter table if exists users
  add column if not exists is_admin boolean not null default false;

update users
set role = case
  when role in ('user', 'admin', 'super_admin') then role
  when coalesce(is_admin, false) then 'admin'
  else 'user'
end;

alter table if exists users
  drop constraint if exists users_role_check;

alter table if exists users
  add constraint users_role_check check (role in ('user', 'admin', 'super_admin'));

update users
set is_admin = role in ('admin', 'super_admin')
where is_admin is distinct from (role in ('admin', 'super_admin'));

insert into profiles (id, email, role, created_at)
select id, email, role, coalesce(created_at, now())
from users
on conflict (id) do update
set email = excluded.email,
    role = excluded.role;

alter table if exists orders
  add column if not exists status text default 'pending';

alter table if exists orders
  add column if not exists admin_note text;

alter table if exists orders
  add column if not exists updated_at timestamptz default now();

update orders
set status = case
  when status in ('pending', 'quoted', 'processing', 'completed', 'cancelled') then status
  when status = 'pending_quote' then 'pending'
  when status = 'quoted' then 'quoted'
  when status in (
    'pending_payment',
    'paid',
    'pending_purchase',
    'purchasing',
    'purchased',
    'warehouse_received',
    'shipping',
    'china_delivery'
  ) then 'processing'
  when status in ('delivered', 'completed') then 'completed'
  when status = 'cancelled' then 'cancelled'
  else 'pending'
end;

alter table if exists orders
  alter column status set default 'pending';

alter table if exists orders
  drop constraint if exists orders_status_check;

alter table if exists orders
  add constraint orders_status_check check (status in ('pending', 'quoted', 'processing', 'completed', 'cancelled'));

update orders
set updated_at = coalesce(updated_at, created_at, now())
where updated_at is null;

create index if not exists idx_orders_status on orders(status);

insert into users (
  id,
  email,
  password_salt,
  password_hash,
  name,
  phone,
  role,
  is_admin,
  created_at,
  updated_at
)
values (
  gen_random_uuid(),
  'haoxueshan5@gmail.com',
  'admin-demo-salt',
  'ff3de8ffb98d1c1f9cb478e3cb4000a2d67fe165f92774055773b1d67ba7b53d',
  'admin',
  null,
  'super_admin',
  true,
  now(),
  now()
)
on conflict (email) do update
set password_salt = excluded.password_salt,
    password_hash = excluded.password_hash,
    name = excluded.name,
    role = 'super_admin',
    is_admin = true,
    updated_at = now();

insert into profiles (id, email, role, created_at)
select id, email, role, created_at
from users
where email = 'haoxueshan5@gmail.com'
on conflict (id) do update
set email = excluded.email,
    role = excluded.role;
