import asyncio
import aiohttp
import state
import utils
import storage

async def worker(worker_id: int, session: aiohttp.ClientSession, queue: asyncio.Queue, semaphore: asyncio.Semaphore):
    print(f"Worker {worker_id} started")
    while True:
        url = await queue.get()
        if url is None:
            queue.task_done()
            break

        print(f"Worker {worker_id} processing {url}")

        async with semaphore:
            try:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        print(f"  Worker {worker_id}: {url} returned {resp.status}")
                        queue.task_done()
                        continue

                    content = await resp.read()
                    headers = resp.headers
                    final_url = str(resp.url)
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                print(f"  Worker {worker_id}: Error fetching {url}: {e}")
                queue.task_done()
                continue

        async with state.seen_lock:
            state.checked_urls.add(url)

        # Write content (CPU‑bound → thread)
        await asyncio.to_thread(storage.write_to_file_sync, content, headers, final_url)

        if 'text/html' in headers.get('Content-Type', ''):
            html_text = content.decode('utf-8', errors='ignore')
            new_links = await asyncio.to_thread(utils.find_all_links, html_text, final_url, True)

            for link in new_links:
                async with state.seen_lock:
                    if link not in state.seen_urls:
                        state.seen_urls.add(link)
                        await queue.put(link)

        queue.task_done()
        print(f"  Worker {worker_id}: finished {url}, queue size = {queue.qsize()}")