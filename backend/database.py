from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from urllib.parse import quote
from dotenv import load_dotenv
import os

load_dotenv()

host = os.environ["POSTGRES_HOST"]
port = os.getenv("POSTGRES_PORT", "5432")
db   = os.environ["POSTGRES_DB"]
user = os.environ["POSTGRES_USER"]
password = quote(os.environ["POSTGRES_PASSWORD"], safe="")

DATABASE_URL = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()
