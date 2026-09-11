import uuid
import shutil
import json
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, Depends, Request, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from .database import engine, get_db, Base
from . import crud

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Fanty App")

UPLOAD_DIR = Path(__file__).parent / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

ALLOWED_EXTENSIONS = {"gif": "image", "png": "image", "jpg": "image", "jpeg": "image", "mp4": "video"}
MAX_FILE_SIZE_IMAGE = 10 * 1024 * 1024
MAX_FILE_SIZE_VIDEO = 5 * 1024 * 1024

def allowed_file(filename: str):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_type(filename: str):
    return ALLOWED_EXTENSIONS.get(filename.rsplit(".", 1)[1].lower())


# === СТАРЫЕ РОУТЫ (создание, удаление, new) ===

@app.get("/")
def index(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(request, "index.html", {"fantasies": crud.get_fantasies(db)})

@app.get("/create")
def create_page(request: Request):
    return templates.TemplateResponse(request, "create.html")

@app.post("/create")
async def create_fantasy(
    request: Request,
    description: str = Form(...),
    media: UploadFile = File(None),
    category: str = Form("prelude"),
    temperature: str = Form("warm"),
    target_gender: str = Form("both"),
    timer_enabled: str = Form("no"),
    timer_seconds: int = Form(0),
    boldness: int = Form(50),
    db: Session = Depends(get_db)
):
    media_filename = None
    final_media_type = "text"
    
    if media and media.filename and media.filename.strip():
        if not allowed_file(media.filename):
            raise HTTPException(status_code=400, detail="Недопустимый формат")
        content = await media.read()
        file_size = len(content)
        media.file.seek(0)
        ext = media.filename.rsplit(".", 1)[1].lower()
        
        if ext in ["gif", "png", "jpg", "jpeg"] and file_size > MAX_FILE_SIZE_IMAGE:
            raise HTTPException(status_code=400, detail="Файл слишком большой (макс. 10MB)")
        if ext == "mp4" and file_size > MAX_FILE_SIZE_VIDEO:
            raise HTTPException(status_code=400, detail="Видео слишком большое (макс. 5MB)")
        
        final_media_type = get_file_type(media.filename)
        media_filename = f"{uuid.uuid4()}.{ext}"
        with open(UPLOAD_DIR / media_filename, "wb") as buffer:
            buffer.write(content)
    
    final_timer = timer_seconds if timer_enabled == "yes" else 0
    
    new_fantasy = crud.create_fantasy(
        db, description=description, media_filename=media_filename,
        media_type=final_media_type, category=category, temperature=temperature,
        target_gender=target_gender, timer_seconds=final_timer, boldness=boldness
    )
    return templates.TemplateResponse(request, "fantasy.html", {"fantasy": new_fantasy})

@app.get("/fantasy/{fantasy_id}")
def get_fantasy_page(request: Request, fantasy_id: int, db: Session = Depends(get_db)):
    fantasy = crud.get_fantasy(db, fantasy_id)
    if not fantasy:
        raise HTTPException(status_code=404, detail="Фант не найден")
    return templates.TemplateResponse(request, "fantasy.html", {"fantasy": fantasy})

@app.get("/random")
def random_fantasy_page(request: Request, db: Session = Depends(get_db)):
    fantasy = crud.get_random_fantasy(db)
    if not fantasy:
        return templates.TemplateResponse(request, "index.html", {"fantasies": []})
    return templates.TemplateResponse(request, "fantasy.html", {"fantasy": fantasy})

@app.get("/new")
def latest_fantasies_page(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(request, "new.html", {"fantasies": crud.get_latest_fantasies(db, 20)})

@app.post("/fantasy/{fantasy_id}/delete")
def delete_fantasy_route(fantasy_id: int, db: Session = Depends(get_db)):
    if crud.delete_fantasy(db, fantasy_id, UPLOAD_DIR):
        return RedirectResponse(url="/new", status_code=303)
    raise HTTPException(status_code=404, detail="Фант не найден")


# === НОВЫЕ РОУТЫ ИГРЫ ===

@app.get("/game/start")
def start_game(request: Request, slider: int = 50, db: Session = Depends(get_db)):
    """Начинаем новую сессию"""
    # Деактивируем старые сессии
    old = crud.get_active_session(db)
    if old:
        crud.stop_session(db, old.id)
    
    session = crud.create_session(db, slider_value=slider)
    return RedirectResponse(url=f"/game/{session.id}", status_code=303)

@app.get("/game/{session_id}")
def game_screen(request: Request, session_id: int, db: Session = Depends(get_db)):
    """Экран игры — показывает текущий фант"""
    session = db.query(crud.GameSession).filter_by(id=session_id, is_active=1).first()
    if not session:
        return RedirectResponse(url="/", status_code=303)
    
    # Если фант ещё не выбран для этого хода — выбираем
    current_fantasy = None
    if not hasattr(session, '_current_fantasy'):
        current_fantasy = crud.pick_next_fantasy(db, session)
    
    if not current_fantasy:
        # Нет подходящих фантов — предлагаем повысить уровень/температуру
        return templates.TemplateResponse(request, "game_empty.html", {
            "session": session,
            "levels": crud.LEVELS_ORDER,
            "temps": crud.TEMP_ORDER
        })
    
    return templates.TemplateResponse(request, "game.html", {
        "session": session,
        "fantasy": current_fantasy,
        "levels": crud.LEVELS_ORDER,
        "temps": crud.TEMP_ORDER
    })

@app.post("/game/{session_id}/done")
def mark_done(request: Request, session_id: int, fantasy_id: int, db: Session = Depends(get_db)):
    """Фант выполнен — переключаем ход и показываем следующий"""
    session = db.query(crud.GameSession).filter_by(id=session_id, is_active=1).first()
    if not session:
        return RedirectResponse(url="/", status_code=303)
    
    crud.advance_turn(db, session, fantasy_id)
    return RedirectResponse(url=f"/game/{session_id}", status_code=303)

@app.post("/game/{session_id}/skip")
def skip_fantasy(request: Request, session_id: int, db: Session = Depends(get_db)):
    """Пропустить фант — просто выбираем другой (без пометки выполнения)"""
    session = db.query(crud.GameSession).filter_by(id=session_id, is_active=1).first()
    if not session:
        return RedirectResponse(url="/", status_code=303)
    
    return RedirectResponse(url=f"/game/{session_id}", status_code=303)

@app.post("/game/{session_id}/level-up")
def level_up(request: Request, session_id: int, db: Session = Depends(get_db)):
    """Переход на следующий уровень"""
    session = db.query(crud.GameSession).filter_by(id=session_id, is_active=1).first()
    if not session:
        return RedirectResponse(url="/", status_code=303)
    
    next_level = crud.get_next_level(session.current_level)
    if next_level != session.current_level:
        session.current_level = next_level
        session.current_temperature = "warm"  # сбрасываем температуру на новом уровне
        db.commit()
    return RedirectResponse(url=f"/game/{session_id}", status_code=303)

@app.post("/game/{session_id}/temp-up")
def temperature_up(request: Request, session_id: int, db: Session = Depends(get_db)):
    """Повысить температуру"""
    session = db.query(crud.GameSession).filter_by(id=session_id, is_active=1).first()
    if not session:
        return RedirectResponse(url="/", status_code=303)
    
    next_temp = crud.get_next_temperature(session.current_temperature)
    if next_temp != session.current_temperature:
        session.current_temperature = next_temp
        db.commit()
    return RedirectResponse(url=f"/game/{session_id}", status_code=303)

@app.post("/game/{session_id}/stop")
def stop_game(request: Request, session_id: int, db: Session = Depends(get_db)):
    """Остановить игру"""
    crud.stop_session(db, session_id)
    return RedirectResponse(url="/", status_code=303)

@app.post("/game/{session_id}/set-temp/{temperature}")
def set_temperature_route(request: Request, session_id: int, temperature: str, db: Session = Depends(get_db)):
    """Установить температуру по клику на огонёк"""
    session = db.query(crud.GameSession).filter_by(id=session_id, is_active=1).first()
    if not session:
        return RedirectResponse(url="/", status_code=303)
    
    if crud.set_temperature(db, session, temperature):
        return RedirectResponse(url=f"/game/{session_id}", status_code=303)
    raise HTTPException(status_code=400, detail="Недопустимая температура")