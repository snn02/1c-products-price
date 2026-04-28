from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

PRICE_URL: str = os.getenv("PRICE_URL", "https://1c.ru/ftp/pub/pricelst/price_1c.zip")
DB_PATH: Path = Path(os.getenv("DB_PATH", "data/prices.db"))
AUTO_UPDATE_DAYS: int = int(os.getenv("AUTO_UPDATE_DAYS", "1"))
