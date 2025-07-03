from sqlalchemy import Column, Integer, String, select, ForeignKey
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship, selectinload

engie = create_async_engine("sqlite+aiosqlite:///data_base/db_all/users.db")
async_session = async_sessionmaker(engie, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)  # ТОЛЬКО этот столбец должен быть primary_key
    name = Column(String)                   # Убрать primary_key=False (оно по умолчанию)
    user_id = Column(Integer, unique=True)   # Оставить unique, но не primary_key
    departament = Column(String)

async def init_users_db():
    async with engie.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)