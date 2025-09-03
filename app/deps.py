import os
from dotenv import load_dotenv
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")

# Sync SQLAlchemy (recommended for now with LINE SDK)
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=3600, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Settings:
    CHANNEL_ACCESS_TOKEN: str = os.environ["CHANNEL_ACCESS_TOKEN"]
    CHANNEL_SECRET: str = os.environ["CHANNEL_SECRET"]

settings = Settings()
