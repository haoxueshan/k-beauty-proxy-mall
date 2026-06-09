alter table users
  add column if not exists is_admin boolean not null default false;

create index if not exists idx_users_is_admin on users(is_admin);

-- Promote the real administrator account after running this migration.
-- Replace the email before executing:
-- update users set is_admin = true where email = 'admin@example.com';
