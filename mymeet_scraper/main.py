import asyncio
import logging
import aiohttp
import aiofiles
from . import config, database, scraper, downloader

async def main():
    """Главная функция, управляющая всем процессом."""
    logging.info("--- Запуск Production-Ready скраппера ---")
    
    config.OUTPUT_DIR.mkdir(exist_ok=True)
    (config.OUTPUT_DIR / "images").mkdir(exist_ok=True)
    (config.OUTPUT_DIR / "text").mkdir(exist_ok=True)
    await database.init_db()

    async with aiohttp.ClientSession(headers=config.HEADERS) as session:
        html = await scraper.fetch_main_page(session)
        if not html:
            return # Завершаем, если не удалось получить страницу

        text, image_urls = scraper.extract_content(html)
        
        text_path = config.OUTPUT_DIR / "text" / "content.txt"
        async with aiofiles.open(text_path, 'w', encoding='utf-8') as f:
            await f.write(text)
        logging.info(f"Текст сохранен в {text_path}")

        await database.add_urls_to_queue(list(image_urls))
        pending_urls = await database.get_pending_urls()
        
        if not pending_urls:
            logging.info("Нет новых изображений для скачивания.")
            return

        logging.info(f"Начинаем скачивание {len(pending_urls)} изображений...")
        download_queue = asyncio.Queue()
        for url in pending_urls:
            await download_queue.put(url)

        tasks = []
        for i in range(config.MAX_CONCURRENT_DOWNLOADS):
            task = asyncio.create_task(
                downloader.download_worker(f"Worker-{i+1}", download_queue, session)
            )
            tasks.append(task)
        
        await download_queue.join()

        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    logging.info("--- Работа скраппера успешно завершена ---")

def run():
    """Настраивает логирование и запускает главный асинхронный процесс."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    asyncio.run(main())

if __name__ == '__main__':
    run()