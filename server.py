from fastapi import FastAPI
import asyncio
import aiohttp
import zeep
import requests
import os
import base64

app = FastAPI()

# ✅ Добавляем обработчик для главной страницы
@app.get("/")
def home():
    return {"message": "API is running! Use /docs to test"}

# Загружаем переменные окружения (API-ключи хранятся в Render)
ROSSKO_WSDL = "http://api.rossko.ru/service/v2.1/GetSearch?wsdl"
ROSSKO_KEY1 = os.getenv("ROSSKO_KEY1")
ROSSKO_KEY2 = os.getenv("ROSSKO_KEY2")
ROSSKO_DELIVERY_ID = "000000002"
ROSSKO_ADDRESS_ID = 207262

BERG_API_KEY = os.getenv("BERG_API_KEY")
BERG_URL = "https://api.berg.ru/ordering/get_stock.json"

AUTOSOYUZ_API_HOST = "https://api.xn--80aep1aarf3h.xn--p1ai"
AUTOSOYUZ_USERNAME = os.getenv("AUTOSOYUZ_USERNAME")
AUTOSOYUZ_PASSWORD = os.getenv("AUTOSOYUZ_PASSWORD")

# Авторизация для Автосоюза
auth_string = f"{AUTOSOYUZ_USERNAME}:{AUTOSOYUZ_PASSWORD}"
auth_encoded = base64.b64encode(auth_string.encode()).decode()
AUTOSOYUZ_HEADERS = {
    "Authorization": f"Basic {auth_encoded}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# Клиент для Rossko API
rossko_client = zeep.Client(wsdl=ROSSKO_WSDL)

async def fetch_rossko(part_number):
    """Получение данных о запчастях из Rossko API"""
    try:
        response = rossko_client.service.GetSearch(
            KEY1=ROSSKO_KEY1,
            KEY2=ROSSKO_KEY2,
            text=part_number,
            delivery_id=ROSSKO_DELIVERY_ID,
            address_id=ROSSKO_ADDRESS_ID
        )
        if not hasattr(response, "PartsList") or not response.PartsList:
            return []
        parts = response.PartsList.Part if hasattr(response.PartsList, "Part") else []
        return [{"source": "Rossko", "brand": part.brand, "part_number": part.partnumber,
                 "name": part.name, "price": float(part.stocks.stock[0].price) if part.stocks and part.stocks.stock else None,
                 "availability": int(part.stocks.stock[0].count) if part.stocks and part.stocks.stock else 0} for part in parts]
    except Exception as e:
        return {"error": f"Ошибка Rossko: {e}"}

async def fetch_berg(session, part_number):
    """Получение данных из Berg API"""
    try:
        url = f"{BERG_URL}?items[0][resource_article]={part_number}&key={BERG_API_KEY}"
        async with session.get(url) as response:
            return await response.json()
    except Exception as e:
        return {"error": f"Ошибка Berg: {e}"}

async def fetch_autosoyuz(session, part_number):
    """Получение данных из Автосоюз API"""
    try:
        url = f"{AUTOSOYUZ_API_HOST}/SearchService/GetBrands?article={part_number}"
        async with session.get(url, headers=AUTOSOYUZ_HEADERS) as response:
            return await response.json()
    except Exception as e:
        return {"error": f"Ошибка Автосоюз: {e}"}

@app.get("/get_parts_info")
async def get_parts_info(part_number: str):
    """Основной эндпоинт API, который запрашивает данные с 3 источников"""
    async with aiohttp.ClientSession() as session:
        rossko_task = fetch_rossko(part_number)
        berg_task = fetch_berg(session, part_number)
        autosoyuz_task = fetch_autosoyuz(session, part_number)
        rossko_data, berg_data, autosoyuz_data = await asyncio.gather(rossko_task, berg_task, autosoyuz_task)

    return {"rossko": rossko_data, "berg": berg_data, "autosoyuz": autosoyuz_data}

