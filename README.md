# Step Challenge

A two-person step competition app with daily, weekly, and monthly leaderboards.

## Prerequisites

- PostgreSQL running locally (or remote) — set `DATABASE_URL` in `backend/.env`
- Python 3.11+
- Node.js 18+

## Quick Start

### 1. Backend

```bash
cd backend
pip install -r requirements.txt

# Copy and edit your database URL:
# backend/.env already has a default — update it if needed

# Start the server (runs migrations + seeds data automatically):
uvicorn main:app --reload
```

The server will:
1. Run `alembic upgrade head` — creates all tables
2. Seed two users and default conversion rules (if empty)
3. Start on http://localhost:8000

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Opens at http://localhost:3000

### Default Login Credentials

| User | Email | Password |
|------|-------|----------|
| Peter | peter@stepchallenge.local | peter123 |
| Anine   | anine@stepchallenge.local   | anine123    |

### Reset Database

```bash
cd backend
python seed.py --reset
```

## Features

- Log activities (Walking, Running, Hiking, Cycling, Climbing, Strength, Manual Steps)
- Auto-converts to step equivalents based on configurable rules
- Daily / Weekly / Monthly leaderboards (auto-refresh every 30s)
- Activity history with edit and delete
- Adjustable conversion rules — retroactively recalculates all activities
- Personal weekly/monthly step goals with progress bars
