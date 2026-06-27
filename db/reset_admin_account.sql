create extension if not exists pgcrypto;

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

insert into admin_users (
  id,
  email,
  password_salt,
  password_hash,
  name,
  phone,
  role,
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
  now(),
  now()
)
on conflict (email) do update
set password_salt = excluded.password_salt,
    password_hash = excluded.password_hash,
    name = excluded.name,
    role = 'super_admin',
    updated_at = now();

delete from admin_auth_sessions
where user_id in (
  select id
  from admin_users
  where email = 'haoxueshan5@gmail.com'
);
