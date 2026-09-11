from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
from backend.models import Base
import logging
from pathlib import Path
import sys

load_dotenv()




db_name="textbook_agent"


