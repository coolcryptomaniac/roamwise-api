from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from app.core.config import get_settings

settings = get_settings()

# SQLite needs this connect_arg when used from multiple threads (FastAPI's
# default threadpool for sync endpoints); harmless for Postgres/MySQL URLs.
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args)
Base = declarative_base()
