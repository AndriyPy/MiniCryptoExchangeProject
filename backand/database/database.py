from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

DB_URL = "sqlite:///crypto_db.db"
engine = create_engine(DB_URL, echo=True)

Session = sessionmaker(bind=engine)

def create_db_and_tables():
	Base.metadata.create_all(engine)