# Step Challenge — Runbook

PostgreSQL runs standalone on the dev machine (serving other databases).  
Docker Compose runs only the **backend** and **frontend** containers.

---

## One-time setup on the dev machine

### 1. Create the database

Connect to the existing PostgreSQL instance and create the app database:

```sql
CREATE DATABASE step_challenge;
```

### 2. Configure environment variables

```bash
cp app.env.example app.env
```

Fill in your actual Postgres credentials — passwords with `$` or other special characters are fine as-is, no escaping needed:

```dotenv
POSTGRES_HOST=host.docker.internal
POSTGRES_PORT=5432
POSTGRES_DB=step_challenge
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your$password!asis

JWT_SECRET=some-long-random-string
```

`host.docker.internal` resolves to the host machine from inside a Docker container.  
The `docker-compose.yml` maps it automatically via `extra_hosts` — no manual config needed.

### 3. First start

```bash
docker compose up --build
```

This builds both images and starts the containers. On first boot the backend will:
1. Run `alembic upgrade head` — creates all tables in `step_challenge`
2. Seed two user accounts and the default conversion rules (only if empty)

Wait for this line before opening the browser:

```
backend-1  | Ready.
```

Open **http://localhost:3000** and log in:

| User  | Email                     | Password |
|-------|---------------------------|----------|
| Peter | peter@stepchallenge.local | peter123 |
| Anine | anine@stepchallenge.local | anine123 |

---

## Daily startup

```bash
docker compose up -d
```

(`-d` runs in the background. Omit it to tail logs in the terminal.)

## Stop

```bash
docker compose down
```

---

## After changing code

Rebuild only the service you changed:

```bash
# Backend change (Python files)
docker compose up --build backend

# Frontend change (TypeScript/CSS)
docker compose up --build frontend
```

---

## Reset the database

```bash
# Inside the running backend container:
docker compose exec backend python seed.py --reset
```

This drops and recreates all tables (via Alembic), then re-seeds the two default users and conversion rules.

---

## Access from phone / other devices on the LAN

1. Find the dev machine's LAN IP:
   ```bash
   ip a   # look for 192.168.x.x under your network interface
   ```
2. Set it in `.env`:
   ```dotenv
   DEV_MACHINE_IP=192.168.1.x
   ```
3. Rebuild the frontend (the IP is baked in at build time):
   ```bash
   docker compose up --build frontend
   ```
4. Open `http://192.168.1.x:3000` on your phone. Make sure the firewall allows ports 3000 and 8000 from the LAN.

---

## View logs

```bash
docker compose logs -f           # all services
docker compose logs -f backend   # backend only
docker compose logs -f frontend  # frontend only
```

---

## Useful one-liners

```bash
# Check container status
docker compose ps

# Open a Python shell in the backend container
docker compose exec backend python

# Connect to the database directly (from the dev machine, not Docker)
psql -U postgres -d step_challenge
```

---

## Ports

| Service  | URL                        |
|----------|----------------------------|
| Frontend | http://localhost:3000      |
| Backend  | http://localhost:8000      |
| API docs | http://localhost:8000/docs |

---

## Troubleshooting

**Backend can't connect to PostgreSQL**  
Check that the `DATABASE_URL` in `.env` uses `host.docker.internal` as the hostname and matches your Postgres credentials. Also verify PostgreSQL is listening on `0.0.0.0` (not just `127.0.0.1`) — check `listen_addresses` in `postgresql.conf`.

**Port already in use**  
Another process is using 8000 or 3000. Either stop it or change the host-side port in `docker-compose.yml` (e.g. `"8001:8000"`).

**Frontend shows "fetch failed" after login**  
The browser calls the backend at `http://localhost:8000` directly (not via Docker networking), so the backend port must be reachable from the browser. Confirm the backend container is up with `docker compose ps`.
