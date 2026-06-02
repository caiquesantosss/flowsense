import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = "sqlite+aiosqlite:///./flowsense.db"

engine = create_async_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False},
    echo=False
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db():
    """Gerenciador de sessão para as rotas da API"""
    async with async_session() as session:
        yield session
        await session.commit()