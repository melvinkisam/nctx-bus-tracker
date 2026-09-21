from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Resolve the SQLite DB relative to this file so it works from any working directory.
BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = (BASE_DIR / "data" / "stops.db").resolve()
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"

# connects app to the database, checks all threads and not only the one that created it
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

# creates a session to interact with the db
session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class, inheriting class is made into a table in the db
Base = declarative_base()