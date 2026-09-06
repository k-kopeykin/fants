import uuid
import shutil
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

ALLOWED_EXTENSIONS = {
    "gif": "image",
    "png": "image",
    "jpg": "image",
    "jpeg": "image",
    "mp4": "video"
}

MAX_FILE_SIZE_IMAGE = 10 * 1024 * 1024  # 10 MB
MAX_FILE_SIZE_VIDEO = 5 * 1024 * 1024   # 5 MB

def allowed_file(filename: str):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_type(filename: str):
    ext = filename.rsplit(".", 1)[1].lower()
    return ALLOWED_EXTENSIONS.get(ext)

@app.get("/")
def index(request: Request, db: Session = Depends(get_db)):
    fantasies = crud.get_fantasies(db)
    return templates.TemplateResponse(request, "index.html", {"fantasies": fantasies})

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
    db: Session = Depends(get_db)
):
    media_filename = None
    final_media_type = "text"
    
    # Если файл загружен — определяем тип автоматически
    if media and media.filename and media.filename.strip():
        if not allowed_file(media.filename):
            raise HTTPException(
                status_code=400, 
                detail="Недопустимый формат. Разрешены: GIF, PNG, JPEG, MP4"
            )
        
        content = await media.read()
        file_size = len(content)
        media.file.seek(0)
        
        ext = media.filename.rsplit(".", 1)[1].lower()
        
        if ext in ["gif", "png", "jpg", "jpeg"]:
            if file_size > MAX_FILE_SIZE_IMAGE:
                raise HTTPException(status_code=400, detail=f"Файл слишком большой. Максимум 10MB")
        elif ext == "mp4":
            if file_size > MAX_FILE_SIZE_VIDEO:
                raise HTTPException(status_code=400, detail=f"Видео слишком большое. Максимум 5MB")
        
        final_media_type = get_file_type(media.filename)
        media_filename = f"{uuid.uuid4()}.{ext}"
        file_path = UPLOAD_DIR / media_filename
        
        with open(file_path, "wb") as buffer:
            buffer.write(content)
    
    # Если таймер выключен — сохраняем 0
    final_timer = timer_seconds if timer_enabled == "yes" else 0
    
    new_fantasy = crud.create_fantasy(
        db, 
        description=description, 
        media_filename=media_filename,
        media_type=final_media_type,
        category=category,
        temperature=temperature,
        target_gender=target_gender,
        timer_seconds=final_timer
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
    fantasies = crud.get_latest_fantasies(db, limit=20)
    return templates.TemplateResponse(request, "new.html", {"fantasies": fantasies})

@app.post("/fantasy/{fantasy_id}/delete")
def delete_fantasy_route(
    fantasy_id: int,
    db: Session = Depends(get_db)
):
    success = crud.delete_fantasy(db, fantasy_id, UPLOAD_DIR)
    if success:
        return RedirectResponse(url="/", status_code=303)
    raise HTTPException(status_code=404, detail="Фант не найден")