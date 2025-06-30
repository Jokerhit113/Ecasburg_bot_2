from sqlalchemy import Column, Integer, String, select, ForeignKey
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship, selectinload

engie = create_async_engine("sqlite+aiosqlite:///data_base/db_all/bot_test2.db")
async_session = async_sessionmaker(engie, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String, primary_key=False)
    user_id = Column(Integer, unique=True)
    departament = Column(String, primary_key = False)


async def init_users_db():
    async with engie.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)