from sqlalchemy.orm import Session
from sqlalchemy import func
from .models import Fantasy

def create_fantasy(db: Session, description: str, gif_filename: str):
    new_fantasy = Fantasy(description=description, gif_filename=gif_filename)
    db.add(new_fantasy)
    db.commit()
    db.refresh(new_fantasy)
    return new_fantasy

def get_fantasy(db: Session, fantasy_id: int):
    return db.query(Fantasy).filter_by(id=fantasy_id).first()

def get_fantasies(db: Session, skip: int = 0, limit: int = 100):
    fantasies = db.query(Fantasy).offset(skip).limit(limit).all()
    return fantasies

def get_random_fantasy(db: Session):
    return db.query(Fantasy).order_by(func.random()).first()
    