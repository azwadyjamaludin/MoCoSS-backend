"""
database.py - Database Connection & Session Configuration
"""
import os
import urllib.parse
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import declarative_base, sessionmaker

# Database Credentials
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "4z14zW@dy") # os.getenv = Handle special characters in password
DB_NAME = os.getenv("DB_NAME", "mocoss_db")
SOCKET_PATH = "/Volumes/MicroSD/mysql.sock"

# Encode socket path and build URL safely using URL.create
DATABASE_URL = URL.create(
    drivername="mysql+pymysql",
    username=DB_USER,
    password=DB_PASS,
    host="localhost",
    database=DB_NAME,
    query={"unix_socket": SOCKET_PATH}
)

# Engine and Session Factory
engine = create_engine(DATABASE_URL, echo=True, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#if connection fails, try starting MySQL server