import asyncio
import hashlib
import logging
import magic
import aiohttp
import aiofiles
from . import config, database

async def get_file_extension(magic_bytes: bytes, response_headers) -> str:
    """Надежно определяет расширение файла."""
    # Приоритет №1: Magic-байты (самый надежный)
    mime_type = magic.from_buffer(magic_bytes, mime=True)
    if mime_type and mime_type.startswith('image'):
        return f".{mime_type.split('/')[1].split('+')[0]}"

    # Приоритет №2: Content-Type из заголовков
    content_type = response_headers.get('content-type')
    if content_type and content_type.startswith('image'):
        return f".{content_type.split('/')[1].split('+')[0]}"

    # Если ничего не помогло, возвращаем бинарное расширение
    return ".dat"

async def download_worker(name: str, queue: asyncio.Queue, session: aiohttp.ClientSession):
    """Воркер, который берет URL из очереди и скачивает файл."""
    while True:
        url = await queue.get()
        logging.info(f"[{name}] Взял в работу URL: {url}")
        
        try:
            timeout = aiohttp.ClientTimeout(total=config.REQUEST_TIMEOUT)
            async with session.get(url, timeout=timeout) as response:
                response.raise_for_status()
                
                content = await response.read()
                magic_bytes = content[:2048] # Magic-байты для определения типа

                ext = await get_file_extension(magic_bytes, response.headers)
                url_hash = hashlib.sha256(url.encode()).hexdigest()
                filename = f"{url_hash}{ext}"
                filepath = config.OUTPUT_DIR / "images" / filename
                
                async with aiofiles.open(filepath, 'wb') as f:
                    await f.write(content)
                
                await database.update_status(url, 'completed', filename)
                logging.info(f"[{name}] Успешно скачан и сохранен: {filename}")

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logging.error(f"[{name}] Ошибка сети при скачивании {url}: {e}")
            await database.update_status(url, 'failed')
        except IOError as e:
            logging.error(f"[{name}] Ошибка записи файла для {url}: {e}")
            await database.update_status(url, 'failed')
        except Exception as e:
            logging.critical(f"[{name}] Непредвиденная ошибка для {url}: {e}")
            await database.update_status(url, 'failed')
        finally:
            queue.task_done()