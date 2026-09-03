import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

# Формат для psycopg3: postgresql+psycopg://user:password@host:port/dbname
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/fanty_db")

engine = create_engine(DATABASE_URL, echo=False) # echo=True можно включить для отладки SQL-запросов
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Зависимость для получения сессии БД в роутах FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()