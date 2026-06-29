# Supabase Setup Guide for Willy's Wing Farm

## Step 1: Create a Supabase Account & Project
1. Go to https://supabase.com and create a free account
2. Create a new project (name it "Willy's Wing Farm" or similar)
3. Wait for your project to be ready (takes a few minutes)

## Step 2: Get Your API Credentials
1. In your Supabase dashboard, go to Project Settings > API
2. Copy your Project URL and `anon` public key
3. In `templates/index.html`, replace:
   - `YOUR_SUPABASE_URL` with your Project URL
   - `YOUR_SUPABASE_ANON_KEY` with your `anon` public key

## Step 3: Create Database Tables

### 1. products
```sql
create table products (
  id uuid default gen_random_uuid() primary key,
  name text not null,
  description text,
  price numeric,
  is_active boolean default true,
  image_url text,
  created_at timestamp default now()
);
```

### 2. orders
```sql
create table orders (
  id uuid default gen_random_uuid() primary key,
  client_name text not null,
  client_email text not null,
  client_phone text,
  location text,
  order_type text,
  quantity text,
  description text,
  delivery_option text,
  status text default 'Pending',
  client_id uuid,
  created_at timestamp default now()
);
```

### 3. gallery
```sql
create table gallery (
  id uuid default gen_random_uuid() primary key,
  url text not null,
  product text,
  description text,
  created_at timestamp default now()
);
```

### 4. pdfs
```sql
create table pdfs (
  id uuid default gen_random_uuid() primary key,
  title text not null,
  url text not null,
  description text,
  is_free boolean default true,
  price numeric default 0,
  created_at timestamp default now()
);
```

### 5. events
```sql
create table events (
  id uuid default gen_random_uuid() primary key,
  title text not null,
  date text not null,
  time text not null,
  location text not null,
  description text,
  price numeric default 0,
  image_url text,
  created_at timestamp default now()
);
```

### 6. clients
```sql
create table clients (
  id uuid default gen_random_uuid() primary key,
  name text not null,
  email text unique not null,
  password text not null,
  phone text,
  created_at timestamp default now()
);
```

### 7. contact_messages
```sql
create table contact_messages (
  id uuid default gen_random_uuid() primary key,
  name text not null,
  email text not null,
  phone text,
  subject text,
  message text,
  created_at timestamp default now()
);
```

### 8. egg_prices
```sql
create table egg_prices (
  id uuid default gen_random_uuid() primary key,
  bird_type text unique not null,
  price numeric default 0,
  unit text default 'dozen',
  updated_at timestamp default now()
);
```

## Step 4: Create Storage Bucket
1. In Supabase, go to Storage
2. Create a new bucket called `farm-files`
3. Set the bucket to public (we'll update RLS policies later if needed)

## Step 5: Set Up Row Level Security (RLS) Policies
For now, we'll set up basic policies. You may want to adjust these for production:
```sql
-- Enable RLS on all tables
alter table products enable row level security;
alter table orders enable row level security;
alter table gallery enable row level security;
alter table pdfs enable row level security;
alter table events enable row level security;
alter table clients enable row level security;
alter table contact_messages enable row level security;
alter table egg_prices enable row level security;

-- Allow everyone to read products, events, gallery, and egg_prices
create policy "Allow public read access" on products for select using (true);
create policy "Allow public read access" on events for select using (true);
create policy "Allow public read access" on gallery for select using (true);
create policy "Allow public read access" on egg_prices for select using (true);
create policy "Allow public read access" on pdfs for select using (true);

-- Allow everyone to insert into orders, contact_messages, and clients
create policy "Allow public insert" on orders for insert with check (true);
create policy "Allow public insert" on contact_messages for insert with check (true);
create policy "Allow public insert" on clients for insert with check (true);

-- For admin access, you'll need to add proper authentication later
```

## Step 6: Run the Application
1. Make sure your Python Flask backend is running (`python app.py`)
2. Open your browser and go to the application URL
