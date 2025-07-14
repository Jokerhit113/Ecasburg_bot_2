from sqlalchemy import Column, Integer, String, select, ForeignKey, JSON
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import DeclarativeBase, relationship, selectinload

engie = create_async_engine("sqlite+aiosqlite:///data_base/db_all/deals.db")
deals_session = async_sessionmaker(engie, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Deals(Base):
    __tablename__ = "deals"
    # Сделка
    id = Column(Integer, primary_key=True)  # ТОЛЬКО этот столбец должен быть primary_key
    deal_id = Column(Integer, unique=True) # Номер сделки
    buy_user = Column(String) # Назначеный покупатель администратором
    march_model = Column(String) # Марка, модель автомобиля
    vin_code = Column(String) # Вин код автомобиля
    car_photo_id = Column(String) # Фото автомобиля
    provider_id = Column(Integer) # Назначенный поставщик
    broker_id = Column(Integer) # Назначенный брокер
    buyer_id = Column(Integer) # ID покупателя
    carrier_id = Column(Integer) # ID Перевозчика


    # Данные от Покупателя
    payment_photo_id = Column(String) # Фото оплаты автомобиля покупателем
    payment_document_id = Column(String) # Документ оплаты автомобиля покупателем
    passport_photos = Column(MutableList.as_mutable(JSON), default=list) # Фотографии паспорта
    passport_documents = Column(MutableList.as_mutable(JSON), default=list) # Документы / файлы паспорта
    foreign_currency_account_statement_photo = Column(MutableList.as_mutable(JSON), default=list) # Фото Выписки по валютному счёту
    foreign_currency_account_statement_docs = Column(MutableList.as_mutable(JSON), default=list)  # Документы Выписки по валютному счёту
    cash_flow_statement_photos = Column(MutableList.as_mutable(JSON), default=list)# Фото Выписки движения денег по валютному счёту
    cash_flow_statement_docs = Column(MutableList.as_mutable(JSON), default=list)# Документы Выписки движения денег по валютному счёту
    snils_buyer_photos = Column(MutableList.as_mutable(JSON), default=list)# СНИЛС фото Покупателя
    snils_buyer_docs = Column(MutableList.as_mutable(JSON), default=list)# СНИЛС документ Покупателя
    buyer_phone_number = Column(String) # Номер телефона покупателя
    buyer_actual_address_of_residence = Column(String) # Фактический адрес проживания
    buyer_email_address = Column(String) # E-mail
    buyer_driver_license = Column(String) # Водительское удостоверение
    buyer_imported_yes_no = Column(String) # Был ли ввоз автомобиля из-за границы за последние 3 года
    buyer_have_car = Column(String) # Есть ли автомобиль в пользовании в данный момент
    elpts_registration_photo = Column(String) # Фото регистрации в ЭПТС

    # Данные от Поставщика
    payment_confirmation_yes_no = Column(String) # Подтверждение получения денег от покупателя
    buy_car_provider_photo_id = Column(MutableList.as_mutable(JSON), default=list) # Фото выкупа автомобиля поставщиком
    buy_car_provider_video_id = Column(MutableList.as_mutable(JSON), default=list) # Видео выкупа автомобиля поставщиком
    provider_photo_car_before_border_id = Column(MutableList.as_mutable(JSON), default=list)  # Фото автомобиля до отправки на границу от поставщика
    provider_video_car_before_border_id = Column(MutableList.as_mutable(JSON), default=list)  # Видео автомобиля до отправки на границу от поставщика
    provider_photo_car_border_id = Column(MutableList.as_mutable(JSON), default=list) # Фото автомобиля на границе от поставщика
    provider_video_car_border_id = Column(MutableList.as_mutable(JSON), default=list) # Видео автомобиля на границе от поставщика
    document_docs_car_provider_id = Column(MutableList.as_mutable(JSON), default=list) # Документы по автомобилю от поставщика
    photo_docs_car_provider_id = Column(MutableList.as_mutable(JSON), default=list) # Фото документы по автомобилю от поставщика

    # Данные от Брокера
    confirmation_of_acceptance_of_documents_from_suppliers = Column(String) # Подтверждение получения документов от поставщика
    confirmation_of_acceptance_of_documents_from_buyer = Column(String) # Подтверждение получения документов от Покупателя
    document_doc_broker_id = Column(MutableList.as_mutable(JSON), default=list) # Документы по автомобилю от поставщика
    photo_docs_broker_id = Column(MutableList.as_mutable(JSON), default=list) # Фото документы по автомобилю от поставщика

async def init_deals_db():
    async with engie.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)