create extension if not exists pgcrypto;

create table if not exists users (
  id uuid primary key default gen_random_uuid(),
  email text unique not null,
  password_salt text not null,
  password_hash text not null,
  name text not null,
  phone text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists auth_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  token text unique not null,
  created_at timestamptz default now()
);

create table if not exists products (
  id uuid primary key default gen_random_uuid(),
  source text not null default 'oliveyoung',
  goods_no text unique,
  source_url text not null,
  brand_ko text,
  brand_zh text,
  title_ko text,
  title_zh text,
  image_url text,
  original_price_krw integer,
  sale_price_krw integer,
  discount_rate integer,
  price_cny numeric,
  proxy_price_cny numeric,
  category_ko text,
  category_zh text,
  delivery_text text,
  stock_status text default 'unknown',
  ai_summary text,
  risk_tips jsonb,
  raw_data jsonb,
  source_updated_at timestamptz,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists search_logs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid,
  keyword_original text,
  keyword_ko text,
  keyword_en text,
  source text default 'oliveyoung',
  result_count integer,
  created_at timestamptz default now()
);

create table if not exists cart_items (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  product_id text not null,
  quantity integer default 1,
  selected_option text,
  note text,
  estimate_price_cny numeric,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists orders (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  order_no text unique not null,
  status text default 'pending_quote',
  product_total_cny numeric,
  service_fee_cny numeric,
  international_shipping_fee_cny numeric,
  package_fee_cny numeric,
  total_amount_cny numeric,
  paid_amount_cny numeric,
  receiver_name text,
  receiver_phone text,
  receiver_address text,
  user_note text,
  admin_note text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists order_items (
  id uuid primary key default gen_random_uuid(),
  order_id uuid not null references orders(id) on delete cascade,
  product_id text not null,
  source_url text,
  title_zh text,
  title_ko text,
  selected_option text,
  quantity integer,
  unit_price_cny numeric,
  subtotal_cny numeric,
  created_at timestamptz default now()
);

create table if not exists purchase_records (
  id uuid primary key default gen_random_uuid(),
  order_id uuid not null,
  purchase_site text default 'oliveyoung',
  purchase_account text,
  purchase_order_no text,
  purchase_price_krw integer,
  purchase_price_cny numeric,
  purchase_status text,
  proof_image_url text,
  purchased_at timestamptz,
  created_at timestamptz default now()
);

create table if not exists logistics (
  id uuid primary key default gen_random_uuid(),
  order_id uuid not null,
  stage text,
  carrier text,
  tracking_no text,
  status text,
  shipped_at timestamptz,
  delivered_at timestamptz,
  created_at timestamptz default now()
);

create table if not exists crawler_tasks (
  id uuid primary key default gen_random_uuid(),
  source text default 'oliveyoung',
  keyword text,
  status text default 'pending',
  total_count integer default 0,
  success_count integer default 0,
  fail_count integer default 0,
  error_message text,
  started_at timestamptz,
  finished_at timestamptz,
  created_at timestamptz default now()
);
