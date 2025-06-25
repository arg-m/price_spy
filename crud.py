# crud.py
from datetime import datetime
from fastapi import HTTPException
from database import database
from models import products, competitors, price_records
from schemas import ProductCreate, Product, CompetitorCreate, Competitor, PriceRecordCreate, PriceRecord


# ----------------------------
# CRUD для Products
# ----------------------------

async def create_product(prod_in: ProductCreate) -> Product:
    query = products.insert().values(**prod_in.model_dump())
    product_id = await database.execute(query)
    row = await database.fetch_one(products.select().where(products.c.id == product_id))
    return Product(**row)


async def get_product(product_id: int) -> Product:
    row = await database.fetch_one(products.select().where(products.c.id == product_id))
    if not row:
        raise HTTPException(status_code=404, detail="Product not found")
    return Product(**row)


async def get_products(skip: int = 0, limit: int = 100) -> list[Product]:
    rows = await database.fetch_all(products.select().offset(skip).limit(limit))
    return [Product(**r) for r in rows]


# ----------------------------
# CRUD для Competitors
# ----------------------------

async def create_competitor(comp_in: CompetitorCreate) -> Competitor:
    query = competitors.insert().values(**comp_in.model_dump())
    competitor_id = await database.execute(query)
    row = await database.fetch_one(competitors.select().where(competitors.c.id == competitor_id))
    return Competitor(**row)


async def get_competitor(competitor_id: int) -> Competitor:
    row = await database.fetch_one(competitors.select().where(competitors.c.id == competitor_id))
    if not row:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return Competitor(**row)


async def get_competitors(skip: int = 0, limit: int = 100) -> list[Competitor]:
    rows = await database.fetch_all(competitors.select().offset(skip).limit(limit))
    return [Competitor(**r) for r in rows]


# ----------------------------
# CRUD для PriceRecords
# ----------------------------

async def create_price_record(record_in: PriceRecordCreate) -> PriceRecord:
    # Проверяем существование товара и конкурента
    await get_product(record_in.product_id)
    await get_competitor(record_in.competitor_id)

    query = price_records.insert().values(**record_in.model_dump())
    record_id = await database.execute(query)
    row = await database.fetch_one(price_records.select().where(price_records.c.id == record_id))
    return PriceRecord(**row)


async def get_price_record(record_id: int) -> PriceRecord:
    row = await database.fetch_one(price_records.select().where(price_records.c.id == record_id))
    if not row:
        raise HTTPException(status_code=404, detail="Price record not found")
    return PriceRecord(**row)


async def get_price_records_by_product(product_id: int) -> list[PriceRecord]:
    rows = await database.fetch_all(price_records.select().where(price_records.c.product_id == product_id))
    return [PriceRecord(**r) for r in rows]


# ----------------------------
# Интеграция с Ozon
# ----------------------------

def search_product_urls(query):
    from parsers.ozon_parser import init_driver, search_and_get_links
    driver = init_driver()
    try:
        result = search_and_get_links(driver, query)
        driver.quit()
        return result
    except Exception as e:
        driver.quit()
        raise e


def parse_ozon_product(url: str):
    from parsers.ozon_parser import init_driver, parse_product
    driver = init_driver()
    try:
        result = parse_product(driver, url)
        driver.quit()
        return result
    except Exception as e:
        driver.quit()
        raise e


async def create_price_record_from_ozon(product_id: int) -> PriceRecord:
    # Получаем товар
    prod = await database.fetch_one(products.select().where(products.c.id == product_id))
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")

    name = prod["name"]

    # Поиск ссылок на Ozon
    urls = search_product_urls(name)
    if not urls:
        raise HTTPException(status_code=500, detail="Ozon: item not found")

    # Парсим первый результат
    info = parse_ozon_product(urls[0])
    if not info or len(info) < 7:
        raise HTTPException(status_code=500, detail="Ozon: parsing failed")

    sku, _, _, price_str, _, _, _ = info

    # Получаем ID конкурента Ozon
    comp = await database.fetch_one(competitors.select().where(competitors.c.name == "Ozon"))
    if not comp:
        raise HTTPException(status_code=500, detail="Competitor 'Ozon' missing")

    # Парсим цену
    try:
        # Оставляем только цифры и точку
        clean_price = ''.join(c for c in price_str if c.isdigit() or c == '.')
        if not clean_price:
            raise ValueError(f"Не удалось очистить цену: {price_str}")
        price = float(clean_price)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ozon: invalid price format → {e}")

    # Создаем запись о цене
    rec_in = PriceRecordCreate(
        product_id=product_id,
        competitor_id=comp["id"],
        price=price,
        date=datetime.now().date()
    )

    query = price_records.insert().values(**rec_in.model_dump())
    record_id = await database.execute(query)

    return PriceRecord(id=record_id, **rec_in.model_dump())


async def fetch_all_ozon_prices() -> list[PriceRecord]:
    prods = await database.fetch_all(products.select())
    return [await create_price_record_from_ozon(p["id"]) for p in prods]