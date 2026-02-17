import os
from dotenv import load_dotenv

load_dotenv()

SEED_FILE = os.getenv('SEED_FILE', 'seeds.txt')
NUM_WORKERS = int(os.getenv('NUM_WORKERS', '5'))
MAX_CONCURRENT_REQUESTS = int(os.getenv('MAX_CONCURRENT_REQUESTS', '10'))
FILE_SAVE_DIRECTORY = os.getenv('FILE_SAVE_DIRECTORY', 'parsed_content')
USER_AGENT = "Mozilla/5.0 (compatible; AsyncCrawler/1.0)"