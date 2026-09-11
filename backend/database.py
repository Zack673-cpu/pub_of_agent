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
        logging.StreamHandler(), #终端
        logging.FileHandler(Path(__file__).parent/"app.log",encoding="utf-8"), #文件
    ]
)

logger=logging.getLogger(__name__)



db_connection=os.getenv("DB_CONNECTION")
if db_connection==None:
    logger.error("  数据库链接失败，检查.env")
    sys.exit()


engine = create_engine(db_connection, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, future=True)
def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


db_name="textbook_agent"


