from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config.settings import settings

# 동기 MariaDB 엔진 (마이그레이션용)
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.DEBUG
)

# 동기 세션 팩토리
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 비동기 엔진 생성
async_engine = create_async_engine(
    settings.ASYNC_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.DEBUG,
    pool_size=20,
    max_overflow=0
)

# 비동기 세션 팩토리
AsyncSessionLocal = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Base 클래스 (모든 모델의 부모)
Base = declarative_base()


async def get_async_db():
    """
    비동기 데이터베이스 세션 의존성
    FastAPI 엔드포인트에서 사용
    """
    async with AsyncSessionLocal() as session:
        yield session


def get_db():
    """
    동기 데이터베이스 세션 의존성 (레거시)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
