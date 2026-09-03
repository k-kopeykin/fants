import uuid
import shutil
from pathlib import Path

from fastapi import FastAPI, Depends, Request, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .database import engine, get_db, Base
from . import crud

# 1. Создаем таблицы в БД при запуске
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Fanty App")

# 2. Настройка папки для загрузки GIF
UPLOAD_DIR = Path(__file__).parent / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 3. Подключаем статику и шаблоны
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


# === МАРШРУТЫ ===

@app.get("/")
def index(request: Request, db: Session = Depends(get_db)):
    fantasies = crud.get_fantasies(db)
    # ИСПРАВЛЕНО: request теперь первый аргумент
    return templates.TemplateResponse(
        request, 
        "index.html", 
        {"fantasies": fantasies}
    )

@app.get("/create")
def create_page(request: Request):
    return templates.TemplateResponse(
        request, 
        "create.html"
    )

@app.post("/create")
async def create_fantasy(
    request: Request,
    description: str = Form(...),
    gif: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Генерируем уникальное имя файла
    ext = gif.filename.split(".")[-1] if "." in gif.filename else "gif"
    filename = f"{uuid.uuid4()}.{ext}"
    file_path = UPLOAD_DIR / filename

    # Сохраняем файл на диск
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(gif.file, buffer)

    # Сохраняем запись в БД
    new_fantasy = crud.create_fantasy(db, description=description, gif_filename=filename)

    # Показываем созданный фант
    return templates.TemplateResponse(
        request, 
        "fantasy.html", 
        {"fantasy": new_fantasy}
    )

@app.get("/fantasy/{fantasy_id}")
def get_fantasy_page(request: Request, fantasy_id: int, db: Session = Depends(get_db)):
    fantasy = crud.get_fantasy(db, fantasy_id)
    if not fantasy:
        raise HTTPException(status_code=404, detail="Фант не найден")
    
    return templates.TemplateResponse(
        request, 
        "fantasy.html", 
        {"fantasy": fantasy}
    )

@app.get("/random")
def random_fantasy_page(request: Request, db: Session = Depends(get_db)):
    fantasy = crud.get_random_fantasy(db)
    if not fantasy:
        return templates.TemplateResponse(
            request, 
            "index.html", 
            {"fantasies": [], "empty_message": "Пока нет ни одного фанта. Давай создадим первый!"}
        )
    
    return templates.TemplateResponse(
        request, 
        "fantasy.html", 
        {"fantasy": fantasy}
    )