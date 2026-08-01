# 🥷 RoamWise Developer API

> AI-powered travel intelligence API for businesses. Built by [RoamWise](https://www.roamwise.co.in) from Almora, Uttarakhand.

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue?style=flat&logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## What It Does

Sell API access to travel businesses:
- **Itinerary Generation** — AI trip plans for any destination
- **Crowd Forecasting** — Crowd predictions + Shinobi dodge routes  
- **Budget Calculator** — Real budget breakdowns by tier
- **Smart Packing** — Climate-aware packing lists
- **Visa Guides** — Document checklists + rejection avoidance

## Quick Start

```bash
# 1. Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env

# 3. Init database + admin
python init_db.py

# 4. Run
uvicorn app.main:app --reload
```

API docs at `http://localhost:8000/docs`

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/v1/itinerary/generate` | POST | Generate AI trip itinerary |
| `/v1/crowd/forecast` | POST | Crowd predictions & Shinobi routes |
| `/v1/budget/calculate` | POST | Budget breakdown by tier |
| `/v1/packing/list` | POST | Smart packing lists |
| `/v1/visa/guide` | POST | Visa requirements & steps |
| `/v1/usage/stats` | GET | Monthly usage stats |
| `/v1/usage/breakdown` | GET | Per-endpoint analytics |
| `/v1/admin/customers` | POST | Create new API customer (admin) |

## Authentication

Pass your API key via header:
```bash
curl -X POST "http://localhost:8000/v1/itinerary/generate" \
  -H "X-API-Key: rw_live_xxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{"destination":"Manali","duration_days":5,"travelers":2}'
```

## Pricing Tiers

| Tier | Price | Quota | Rate Limit |
|---|---|---|---|
| Basic | ₹999/mo | 1,000 req | 20/min |
| Pro | ₹4,999/mo | 10,000 req | 100/min |
| Enterprise | ₹24,999/mo | 100,000 req | 500/min |

## Deployment

```bash
docker-compose up -d
```

Or deploy to Railway/Render/Fly.io.

## Tech Stack

- **FastAPI** — High-performance Python web framework
- **SQLAlchemy** — Database ORM
- **Pydantic v2** — Data validation
- **JWT** — Token-based auth
- **Rate Limiting** — Tier-based request throttling
- **Usage Logging** — Per-request analytics

## Built By

**Mohit Pandey** — Indie developer, author, creator from Almora, Uttarakhand.  
Building [RoamWise](https://www.roamwise.co.in) solo with an AI co-pilot.

## License

MIT
