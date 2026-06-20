from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from alembic.config import Config
from alembic import command
import os

from routers import auth, activities, leaderboards, settings


def run_migrations():
    """Run alembic upgrade head to ensure DB schema is current."""
    alembic_cfg = Config(os.path.join(os.path.dirname(__file__), "alembic.ini"))
    alembic_cfg.set_main_option("script_location", os.path.join(os.path.dirname(__file__), "alembic"))
    command.upgrade(alembic_cfg, "head")


def run_seed():
    """Seed default data (users + conversion rules) if tables are empty."""
    import seed as seed_module
    seed_module.seed(reset=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Running database migrations…")
    run_migrations()
    print("Seeding default data…")
    run_seed()
    print("Ready.")
    yield


app = FastAPI(title="Step Challenge API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(activities.router)
app.include_router(leaderboards.router)
app.include_router(settings.router)


@app.get("/health")
def health():
    return {"status": "ok"}
