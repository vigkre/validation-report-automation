from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Replace the placeholders with your actual MySQL credentials
DATABASE_URL = "mysql://vira:vira_1234@10.168.2.129/vira"

# SQLAlchemy Engine
engine = create_engine(DATABASE_URL)

# SQLAlchemy SessionLocal to manage session lifecycle
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for creating ORM models
Base = declarative_base()


# Dependency to get the DB session for request lifecycle
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
