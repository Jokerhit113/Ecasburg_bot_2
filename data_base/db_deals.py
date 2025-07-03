from sqlalchemy import Column, Integer, String, select, ForeignKey
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship, selectinload

engie = create_async_engine("sqlite+aiosqlite:///data_base/db_all/deals.db")
deals_session = async_sessionmaker(engie, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Deals(Base):
    __tablename__ = "deals"
    id = Column(Integer, primary_key=True)  # ТОЛЬКО этот столбец должен быть primary_key
    deal_id = Column(Integer, unique=True)
    buy_user = Column(String)
    march_model = Column(String)
    vin_code = Column(String)
    car_photo_id = Column(String)
    provider_id = Column(Integer, unique=True)
    broker_id = Column(Integer, unique=True)
    payment_photo_id = Column(String)
    payment_confirmation = Column(String)
    buy_car_photo_id = Column(String)
    buy_car_video_id = Column(String)
    provider_photo_car_border_id = Column(String)
    provider_video_car_border_id = Column(String)
    document_docs_car_provider_id = Column(String)
    photo_docs_car_provider_id = Column(String)



    user_id = Column(Integer, unique=True)
    departament = Column(String)

async def init_deals_db():
    async with engie.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)