import csv
import sys
import os

# Добавляем путь к папке app, чтобы импортировать наши модули
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine, Base
from app.models import Fantasy

# Убедимся, что таблицы существуют (на всякий случай)
Base.metadata.create_all(bind=engine)

def import_from_csv(file_path):
    db = SessionLocal()
    count = 0
    try:
        print(f"📂 Читаем файл {file_path}...")
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Создаем новый фант
                fantasy = Fantasy(
                    description=row['description'].strip(),
                    media_type="text", # По умолчанию текстовый фант
                    category=row.get('category', 'prelude').strip(),
                    temperature=row.get('temperature', 'warm').strip(),
                    target_gender=row.get('target_gender', 'both').strip(),
                    boldness=int(row.get('boldness', 50)),
                    timer_seconds=int(row.get('timer_seconds', 0))
                )
                db.add(fantasy)
                count += 1
            
            db.commit()
            print(f"✅ Успешно добавлено {count} фантов в базу!")
    except FileNotFoundError:
        print(f"❌ Ошибка: Файл {file_path} не найден. Положите его в корень проекта.")
    except Exception as e:
        db.rollback()
        print(f"❌ Ошибка при импорте: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    import_from_csv("fantasies.csv")