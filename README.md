# Trading Therapist

AI Trading Therapist + Behavioral Analytics.  
**Automatic trade data first** — traders cannot lie about what they actually did.

## Features

- **MT5** — Expert Advisor webhook → auto trades + behavioral events  
- **IBKR** — Webhook + Flex Query CSV upload  
- **Trading Plan** — max trades/day, risk, symbols → plan-deviation detection  
- **AI Therapist** — OpenAI when keyed, CBT-style fallback otherwise  
- **JWT auth** + per-connection API tokens for EAs/scripts  

## Quick start (local)

### Backend

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
mkdir -p data
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
echo 'NEXT_PUBLIC_API_URL=http://127.0.0.1:8000/api/v1' > .env.local
npm run dev
```

## Deploy

See [docs/DEPLOY.md](docs/DEPLOY.md) for **GitHub → Supabase → Railway/Render (backend) → Vercel (frontend)**.

```bash
cp .env.example .env
docker compose up -d --build
```

## Philosophy

Trade data from brokers is the source of truth. Manual logging is a fallback. Coaching is grounded in what you actually did.
