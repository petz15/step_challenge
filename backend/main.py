from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from alembic.config import Config
from alembic import command
import os
import sys
import traceback

from routers import auth, activities, leaderboards, settings, garmin, stats


def run_migrations():
    alembic_cfg = Config(os.path.join(os.path.dirname(__file__), "alembic.ini"))
    alembic_cfg.set_main_option("script_location", os.path.join(os.path.dirname(__file__), "alembic"))
    command.upgrade(alembic_cfg, "head")


def run_seed():
    import seed as seed_module
    seed_module.seed(reset=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Running database migrations…", flush=True)
    try:
        run_migrations()
    except Exception:
        print("ERROR: database migration failed:", flush=True)
        traceback.print_exc()
        sys.exit(1)

    print("Seeding default data…", flush=True)
    try:
        run_seed()
    except Exception:
        print("ERROR: seeding failed:", flush=True)
        traceback.print_exc()
        sys.exit(1)

    print("Ready.", flush=True)
    yield


app = FastAPI(title="Step Challenge API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(activities.router)
app.include_router(leaderboards.router)
app.include_router(settings.router)
app.include_router(garmin.router)
app.include_router(stats.router)


@app.get("/health")
def health():
    return {"status": "ok"}
