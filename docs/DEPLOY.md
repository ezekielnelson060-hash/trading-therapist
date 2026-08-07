# Deploy Guide: GitHub → Supabase → Vercel

## 1. GitHub
Repo: `ezekielnelson060-hash/trading-therapist`

## 2. Supabase (Postgres)

1. Create project at https://supabase.com
2. Settings → Database → copy Connection string (URI)
3. Convert to async SQLAlchemy:

```
postgresql+asyncpg://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
```

4. Backend env:
```
DATABASE_URL=postgresql+asyncpg://...
SECRET_KEY=<openssl rand -hex 32>
OPENAI_API_KEY=sk-...   # optional
```

5. `pip install asyncpg`

Tables auto-create on startup via SQLAlchemy `create_all`.

## 3. Backend host (not Vercel)

Use **Railway**, **Render**, or **Fly.io** for FastAPI.

Railway example:
- Deploy from GitHub, root `backend/`
- Env: DATABASE_URL, SECRET_KEY, OPENAI_API_KEY
- Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

## 4. Vercel (frontend only)

1. Import repo on vercel.com
2. Root Directory: `frontend`
3. Env: `NEXT_PUBLIC_API_URL=https://YOUR-BACKEND-URL/api/v1`
4. Deploy

## 5. CORS

Add your Vercel domain to `allow_origins` in `backend/app/main.py`.

## Checklist

- [ ] Supabase + DATABASE_URL
- [ ] Backend deployed
- [ ] CORS allows Vercel
- [ ] Vercel NEXT_PUBLIC_API_URL set
- [ ] Test register → brokers → import
