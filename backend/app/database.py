import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


load_dotenv()


POSTGRES_HOST = os.getenv(
    "POSTGRES_HOST",
    "localhost",
)

POSTGRES_PORT = os.getenv(
    "POSTGRES_PORT",
    "5432",
)

POSTGRES_DB = os.getenv(
    "POSTGRES_DB",
)

POSTGRES_USER = os.getenv(
    "POSTGRES_USER",
)

POSTGRES_PASSWORD = os.getenv(
    "POSTGRES_PASSWORD",
)


if not all(
    [
        POSTGRES_DB,
        POSTGRES_USER,
        POSTGRES_PASSWORD,
    ]
):
    raise RuntimeError(
        "PostgreSQL environment variables are not configured."
    )


DATABASE_URL = (
    f"postgresql+psycopg://"
    f"{POSTGRES_USER}:"
    f"{POSTGRES_PASSWORD}@"
    f"{POSTGRES_HOST}:"
    f"{POSTGRES_PORT}/"
    f"{POSTGRES_DB}"
)


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)