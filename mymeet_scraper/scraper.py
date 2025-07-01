import logging
from bs4 import Tag
from typing import Tuple, Set
from urllib.parse import urljoin
import aiohttp
from bs4 import BeautifulSoup
from . import config

async def fetch_main_page(session: aiohttp.ClientSession) -> str | None:
    """Загружает HTML главной страницы."""
    logging.info(f"Запрашиваем главную страницу: {config.BASE_URL}")
    try:
        timeout = aiohttp.ClientTimeout(total=config.REQUEST_TIMEOUT)
        async with session.get(config.BASE_URL, timeout=timeout) as response:
            response.raise_for_status()
            return await response.text()
    except aiohttp.ClientError as e:
        logging.critical(f"Не удалось получить главную страницу: {e}")
        return None

def extract_content(html: str) -> Tuple[str, Set[str]]:
    """Извлекает текст и уникальные URL изображений из HTML."""
    logging.info("Начинаем парсинг HTML...")
    soup = BeautifulSoup(html, 'lxml')

    for element in soup(['script', 'style']):
        element.decompose()
    page_text = soup.body.get_text(separator='\n', strip=True) if soup.body else ""
    logging.info(f"Извлечено ~{len(page_text)} символов текста.")

    image_urls: Set[str] = set()
    for img_tag in soup.find_all('img'):
        if not isinstance(img_tag, Tag):
            continue

        src = img_tag.get('src') or img_tag.get('data-src')
        
        if not isinstance(src, str):
            continue

        if src.startswith('data:image'):
            continue
        
        absolute_url = urljoin(config.BASE_URL, src)
        image_urls.add(absolute_url)
    
    logging.info(f"Найдено {len(image_urls)} уникальных URL изображений.")
    return page_text, image_urls