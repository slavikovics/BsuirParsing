import asyncio

checked_urls = set()
seen_urls = set()
seen_lock = asyncio.Lock()