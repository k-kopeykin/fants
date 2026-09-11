from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from .models import Fantasy, GameSession
import json
import random

def create_fantasy(db: Session, description: str, media_filename: str, media_type: str,
                   category: str, temperature: str, target_gender: str, timer_seconds: int,
                   boldness: int = 50):
    new_fantasy = Fantasy(
        description=description, media_filename=media_filename, media_type=media_type,
        category=category, temperature=temperature, target_gender=target_gender,
        timer_seconds=timer_seconds, boldness=boldness
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
    return db.query(Fantasy).order_by(desc(Fantasy.created_at)).limit(limit).all()

def delete_fantasy(db: Session, fantasy_id: int, upload_dir) -> bool:
    import os
    fantasy = db.query(Fantasy).filter_by(id=fantasy_id).first()
    if not fantasy:
        return False
    file_path = upload_dir / fantasy.media_filename
    if file_path.exists():
        os.remove(file_path)
    db.delete(fantasy)
    db.commit()
    return True


# === ЛОГИКА ИГРЫ ===

LEVELS_ORDER = ["flirt", "prelude", "intimacy"]
TEMP_ORDER = ["warm", "hot", "fire"]

def get_next_temperature(current: str) -> str:
    idx = TEMP_ORDER.index(current)
    return TEMP_ORDER[min(idx + 1, len(TEMP_ORDER) - 1)]

def get_next_level(current: str) -> str:
    idx = LEVELS_ORDER.index(current)
    return LEVELS_ORDER[min(idx + 1, len(LEVELS_ORDER) - 1)]


def get_active_session(db: Session) -> GameSession:
    return db.query(GameSession).filter_by(is_active=1).order_by(desc(GameSession.started_at)).first()

def stop_session(db: Session, session_id: int):
    session = db.query(GameSession).filter_by(id=session_id).first()
    if session:
        session.is_active = 0
        db.commit()

def pick_next_fantasy(db: Session, session: GameSession) -> Fantasy:
    """Выбирает следующий фант по правилам игры"""
    shown_ids = json.loads(session.fantasies_shown or "[]")
    
    # Температура: берём текущую и все ниже (чтобы не прыгать сразу на огонь)
    temp_idx = TEMP_ORDER.index(session.current_temperature)
    allowed_temps = TEMP_ORDER[:temp_idx + 1]
    
    query = db.query(Fantasy).filter(
        Fantasy.category == session.current_level,
        Fantasy.temperature.in_(allowed_temps),
        Fantasy.target_gender.in_([session.current_turn, "both"]),
        Fantasy.boldness <= session.slider_value,
        ~Fantasy.id.in_(shown_ids) if shown_ids else True
    )
    
    fantasy = query.order_by(func.random()).first()
    
    # Если не нашли — расширяем поиск (убираем фильтр по показанным)
    if not fantasy and shown_ids:
        fantasy = db.query(Fantasy).filter(
            Fantasy.category == session.current_level,
            Fantasy.temperature.in_(allowed_temps),
            Fantasy.target_gender.in_([session.current_turn, "both"]),
            Fantasy.boldness <= session.slider_value
        ).order_by(func.random()).first()
    
    
    
    return fantasy

def advance_turn(db: Session, session: GameSession, fantasy_id: int):
    """После выполнения фанта — переключаем ход и запоминаем ID"""
    shown = json.loads(session.fantasies_shown or "[]")
    shown.append(fantasy_id)
    session.fantasies_shown = json.dumps(shown)
    
    # Переключаем ход
    session.current_turn = "f" if session.current_turn == "m" else "m"
    db.commit()



def create_session(db: Session, slider_value: int = 50) -> GameSession:
    session = GameSession(
        current_level="flirt",
        current_temperature="warm",
        current_turn=random.choice(["m", "f"]),  # случайный старт
        slider_value=slider_value,
        fantasies_shown="[]"
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

def set_temperature(db: Session, session: GameSession, temperature: str) -> bool:
    """Установить конкретную температуру (warm/hot/fire)"""
    if temperature in TEMP_ORDER:
        session.current_temperature = temperature
        db.commit()
        return True
    return False

def get_random_fantasy(db: Session):
    return db.query(Fantasy).order_by(func.random()).first()