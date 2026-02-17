import asyncio
import aiohttp
import os
import config
import state
from worker import worker

async def main():
    os.makedirs(config.FILE_SAVE_DIRECTORY, exist_ok=True)

    # Read seed URLs
    try:
        with open(config.SEED_FILE, 'r') as f:
            seeds = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Error: Seed file '{config.SEED_FILE}' not found.")
        return
    except Exception as e:
        print(f"Error reading seed file: {e}")
        return

    if not seeds:
        print("No seed URLs found in the file.")
        return

    print(f"Loaded {len(seeds)} seed URLs from '{config.SEED_FILE}'.")
    print(f"Using {config.NUM_WORKERS} workers.")

    queue = asyncio.Queue()
    for url in seeds:
        await queue.put(url)
        async with state.seen_lock:
            state.seen_urls.add(url)

    semaphore = asyncio.Semaphore(config.MAX_CONCURRENT_REQUESTS)

    connector = aiohttp.TCPConnector(limit=0)
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(
        connector=connector,
        timeout=timeout,
        headers={'User-Agent': config.USER_AGENT}
    ) as session:

        workers = [asyncio.create_task(worker(i, session, queue, semaphore))
                   for i in range(config.NUM_WORKERS)]

        await queue.join()

        for _ in workers:
            await queue.put(None)
        await asyncio.gather(*workers, return_exceptions=True)

    print("\nCrawling finished.")
    print(f"Checked URLs: {len(state.checked_urls)}")