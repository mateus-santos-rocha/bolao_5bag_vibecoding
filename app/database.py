from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .config import DB_PARAMS, DB_PASSWORD

DB_URL = f"postgresql+psycopg2://{DB_PARAMS['user']}:{DB_PASSWORD}@{DB_PARAMS['host']}:{DB_PARAMS['port']}/{DB_PARAMS['database']}"
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
