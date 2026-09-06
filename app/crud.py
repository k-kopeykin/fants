from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from .models import Fantasy

def create_fantasy(
    db: Session, 
    description: str, 
    media_filename: str,
    media_type: str,
    category: str,
    temperature: str,
    target_gender: str,
    timer_seconds: int
):
    new_fantasy = Fantasy(
        description=description, 
        media_filename=media_filename,
        media_type=media_type,
        category=category,
        temperature=temperature,
        target_gender=target_gender,
        timer_seconds=timer_seconds
    )
    db.add(new_fantasy)
    db.commit()
    db.refresh(new_fantasy)
    return new_fantasy

def get_fantasy(db: Session, fantasy_id: int):
    return db.query(Fantasy).filter_by(id=fantasy_id).first()

def get_fantasies(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Fantasy).offset(skip).limit(limit).all()

def get_latest_fantasies(db: Session, limit: int = 20):
    """Получить последние добавленные фанты (сортировка по дате)"""
    return db.query(Fantasy).order_by(desc(Fantasy.created_at)).limit(limit).all()

def get_random_fantasy(db: Session, target_gender: str = "any"):
    query = db.query(Fantasy)
    if target_gender != "any":
        query = query.filter((Fantasy.target_gender == target_gender) | (Fantasy.target_gender == "any"))
    return query.order_by(func.random()).first()