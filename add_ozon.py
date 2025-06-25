# add_ozon.py
import asyncio
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData
from databases import Database

# Подключение к БД
DATABASE_URL = "sqlite:///./db.sqlite3"
database = Database(DATABASE_URL)
engine = create_engine(DATABASE_URL)
metadata = MetaData()

# Определим таблицу competitors (если не определена в другом месте)
competitors = Table(
    "competitors", metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, nullable=False, unique=True),
)

async def add_ozon_to_competitors():
    await database.connect()
    
    # Проверим, есть ли уже Ozon
    query = competitors.select().where(competitors.c.name == "Ozon")
    result = await database.fetch_one(query)
    
    if not result:
        # Добавляем Ozon
        query = competitors.insert().values(name="Ozon")
        await database.execute(query)
        print("✅ Конкурент 'Ozon' успешно добавлен в базу данных.")
    else:
        print("ℹ️ Конкурент 'Ozon' уже существует.")

    await database.disconnect()

if __name__ == "__main__":
    asyncio.run(add_ozon_to_competitors())