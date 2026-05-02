import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Railway 환경에서는 환경변수 DATABASE_URL 제공. 로컬 테스트시에는 sqlite 활용 등 고려
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

# Railway의 DATABASE_URL이 postgres:// 로 시작하는 경우 sqlalchemy 호환을 위해 postgresql:// 로 변경
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLite의 경우 체크 동일 스레드 옵션 비활성화 필요
engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
