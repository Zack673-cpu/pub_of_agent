from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
from backend.models import Base
import logging
from pathlib import Path
import sys

load_dotenv()


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),           # 终端
        logging.FileHandler(Path(__file__).parent/"app.log", encoding="utf-8"),  # 文件
    ]
)
logger = logging.getLogger(__name__)



password=os.getenv("DB_PASSWORD")
if password is None:
    logger.error("    DB_PASSWORD 为空，检查 .env 文件")
    sys.exit()




db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': password,  # 若无密码则留空 ''
    'port': 3306,
    'charset': 'utf8mb4'
}

db_name="textbook_agent"


