from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DB_PATH = Path(__file__).resolve().parent.parent / "db" / "web_signin.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


class Base(DeclarativeBase):
    pass


def get_engine():
    url = f"sqlite:///{DB_PATH}"
    engine = create_engine(url, echo=False, connect_args={"check_same_thread": False})
    return engine


def get_session_factory(engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    初始化数据库引擎和会话工厂，并创建所有表。
    具体表结构在 models.py 中定义。
    """
    from . import models  # noqa: F401  # 导入以注册模型

    engine = get_engine()
    models.Base.metadata.create_all(bind=engine)
    SessionLocal = get_session_factory(engine)
    return engine, SessionLocal

