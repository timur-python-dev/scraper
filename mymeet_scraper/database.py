import aiosqlite
import logging
from typing import List
from . import config

async def init_db():
    """Инициализирует базу данных и создает таблицу, если она не существует."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS scraped_images (
                url TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                filename TEXT,
                retries INTEGER DEFAULT 0,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()
    logging.info(f"База данных инициализирована: {config.DB_PATH}")

async def add_urls_to_queue(urls: List[str]):
    """Добавляет новые URL в БД со статусом 'pending'. Игнорирует дубликаты."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.executemany(
            "INSERT OR IGNORE INTO scraped_images (url, status) VALUES (?, 'pending')",
            [(url,) for url in urls]
        )
        await db.commit()
    logging.info(f"Добавлено/обновлено {len(urls)} URL в очередь на скачивание.")

async def get_pending_urls() -> List[str]:
    """Возвращает список URL, которые еще не были скачаны."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        cursor = await db.execute("SELECT url FROM scraped_images WHERE status = 'pending'")
        rows = await cursor.fetchall()
        return [row[0] for row in rows]

async def update_status(url: str, status: str, filename: str | None = None):
    """Обновляет статус URL (например, 'completed' или 'failed')."""
    async with aiosqlite.connect(config.DB_PATH) as db:
        await db.execute(
            "UPDATE scraped_images SET status = ?, filename = ?, timestamp = CURRENT_TIMESTAMP WHERE url = ?",
            (status, filename, url)
        )
        await db.commit()