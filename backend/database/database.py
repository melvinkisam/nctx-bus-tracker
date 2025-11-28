from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Initializing database location (SQLite, can switch to PostgreSQL)
SQLALCHEMY_DATABASE_URL = "sqlite:///./data/stops.db"

# connects app to the database, checks all threads and not only the one that created it
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

# creates a session to interact with the db
session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class, inheriting class is made into a table in the db
Base = declarative_base()