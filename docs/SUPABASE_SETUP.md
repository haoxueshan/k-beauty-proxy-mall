# Supabase Setup

## 1. Create a project

Create a Supabase cloud project and keep these values ready:

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`

## 2. Create backend environment variables

Copy [backend/.env.example](C:/Users/Administrator/Desktop/demo/backend/.env.example) to `backend/.env` and fill in your project values.

Required for the backend:

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`

The backend now also accepts `NEXT_PUBLIC_SUPABASE_URL` as a fallback for the URL, but it still needs `SUPABASE_SERVICE_ROLE_KEY` for server-side writes.
Do not put a value starting with `sb_publishable_` into `SUPABASE_SERVICE_ROLE_KEY`.

## 2.1 Create frontend environment variables

Copy [frontend/.env.local.example](C:/Users/Administrator/Desktop/demo/frontend/.env.local.example) to `frontend/.env.local`.

Required for the frontend:

- `NEXT_PUBLIC_API_BASE_URL`
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`

## 3. Run the schema in Supabase SQL Editor

Execute [db/schema.sql](C:/Users/Administrator/Desktop/demo/db/schema.sql) inside the Supabase SQL Editor.

If you already created the older scaffold tables before this change, also run:

- [db/supabase_migration_auth.sql](C:/Users/Administrator/Desktop/demo/db/supabase_migration_auth.sql)
- [db/supabase_migration_admin_orders_roles.sql](C:/Users/Administrator/Desktop/demo/db/supabase_migration_admin_orders_roles.sql)

## 4. Current cloud-backed tables

The backend now stores these flows in Supabase:

- `users`
- `auth_sessions`
- `cart_items`
- `orders`
- `order_items`

## 5. Current scope

- Product search/detail now uses backend crawler responses, with homepage sync and live search paths available.
- Auth, cart insert, and order persistence now use Supabase cloud tables.
- The current backend write path cannot run with only a publishable key; it still requires a service role key or a future RLS-based redesign.
