from fastapi import FastAPI
import asyncio
import aiohttp
import zeep
import requests
import base64

app = FastAPI()

# API-ключи и настройки
ROSSKO_WSDL = "http://api.rossko.ru/service/v2.1/GetSearch?wsdl"
ROSSKO_KEY1 = "6564d3bfa97ebd83a412b1a808e30155"
ROSSKO_KEY2 = "710b787d8dd547ccc13e2e1ae8d145de"
ROSSKO_DELIVERY_ID = "000000002"
ROSSKO_ADDRESS_ID = 207262

BERG_API_KEY = "be39c9fd98e5aec101ee50901511f67fe30d0d0c97c25d1ff5fe2bf4ca832b0b"
BERG_URL = "https://api.berg.ru/ordering/get_stock.json"

AUTOSOYUZ_API_HOST = "https://api.xn--80aep1aarf3h.xn--p1ai"
AUTOSOYUZ_USERNAME = "m.belikov@vogueautocenter.ru"
AUTOSOYUZ_PASSWORD = "Vogue123654"

# Авторизация для Автосоюза
auth_string = f"{AUTOSOYUZ_USERNAME}:{AUTOSOYUZ_PASSWORD}"
auth_encoded = base64.b64encode(auth_string.encode()).decode()
AUTOSOYUZ_HEADERS = {
    "Authorization": f"Basic {auth_encoded}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

rossko_client = zeep.Client(wsdl=ROSSKO_WSDL)

async def fetch_rossko(part_number):
    try:
        response = rossko_client.service.GetSearch(
            KEY1=ROSSKO_KEY1, KEY2=ROSSKO_KEY2, text=part_number,
            delivery_id=ROSSKO_DELIVERY_ID, address_id=ROSSKO_ADDRESS_ID
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
    try:
        url = f"{BERG_URL}?items[0][resource_article]={part_number}&key={BERG_API_KEY}"
        async with session.get(url) as response:
            return await response.json()
    except Exception as e:
        return {"error": f"Ошибка Berg: {e}"}

async def fetch_autosoyuz(session, part_number):
    try:
        url = f"{AUTOSOYUZ_API_HOST}/SearchService/GetBrands?article={part_number}"
        async with session.get(url, headers=AUTOSOYUZ_HEADERS) as response:
            return await response.json()
    except Exception as e:
        return {"error": f"Ошибка Автосоюз: {e}"}

@app.get("/get_parts_info")
async def get_parts_info(part_number: str):
    async with aiohttp.ClientSession() as session:
        rossko_task = fetch_rossko(part_number)
        berg_task = fetch_berg(session, part_number)
        autosoyuz_task = fetch_autosoyuz(session, part_number)
        rossko_data, berg_data, autosoyuz_data = await asyncio.gather(rossko_task, berg_task, autosoyuz_task)

    return {"rossko": rossko_data, "berg": berg_data, "autosoyuz": autosoyuz_data}

