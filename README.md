# Olive Young Proxy Shopping Platform

MVP scaffold for a Chinese-language Olive Young proxy shopping platform.

## What is included

- `docs/PRD.md`: distilled product requirements from the provided PRD
- `frontend/`: Next.js App Router scaffold with key user and admin pages
- `backend/`: FastAPI scaffold with mock product, cart, order, and crawler APIs
- `db/schema.sql`: Supabase/PostgreSQL schema based on the PRD

## MVP scope

- Chinese keyword product search
- Product listing and detail pages
- Proxy cart and order submission flow
- Admin views for products, orders, crawler tasks, and logistics
- Olive Young homepage sync and pricing services
- GPT-based translation module with local fallback rules

## Run locally

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Supabase cloud database

1. Create a Supabase project
2. Copy `backend/.env.example` to `backend/.env`
3. Copy `frontend/.env.local.example` to `frontend/.env.local`
4. Fill frontend `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`
5. Fill backend `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`
6. Optional: fill backend `OPENAI_API_KEY` to enable GPT translation
7. Run `db/schema.sql` in the Supabase SQL editor

Detailed setup notes: `docs/SUPABASE_SETUP.md`

## Translation module

- Backend translation service: [backend/services/llm_translate_service.py](C:/Users/Administrator/Desktop/demo/backend/services/llm_translate_service.py)
- Product title translation now prefers OpenAI and falls back to local rules when no API key is configured
- Direct translation API: `POST /api/translate`

Example request:

```json
{
  "texts": ["라운드랩 자작나무 수분 선크림 50ml"],
  "source_language": "Korean",
  "target_language": "Simplified Chinese"
}
```

## Notes

- The crawler code is intentionally stubbed and only models public-data syncing flows.
- Auth, cart, and order persistence now target Supabase cloud tables.
- Product search/detail uses synced Olive Young homepage data when crawling succeeds.
