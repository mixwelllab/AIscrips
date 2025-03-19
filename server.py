from fastapi import FastAPI
from fastapi.responses import JSONResponse
import aiohttp
import asyncio

app = FastAPI()

# 🔹 Функция для получения данных из Rossko
async def fetch_rossko(part_number: str):
    # Здесь твой код для работы с API Rossko
    return [
        {"brand": "NTP", "part_number": part_number, "name": None, "price": None, "availability": 0},
        {"brand": "Hyundai/Kia", "part_number": part_number, "name": "Колодки тормозные задние", "price": None, "availability": 0},
        {"brand": "SUFIX", "part_number": "SP-1187", "name": "Фильтр масляный (картридж)", "price": 247.0, "availability": 1},
        {"brand": "Sangsin", "part_number": part_number, "name": "Колодка дискового тормоза (задняя) (с пластиной)", "price": 1500.77, "availability": 23}
    ]

# 🔹 Функция для получения данных из Berg
async def fetch_berg(session, part_number: str):
    # Здесь твой код для работы с API Berg
    return {
        "resources": [
            {
                "article": "SP-1187",
                "brand": {"id": 1206540, "name": "SUFIX"},
                "name": "Фильтр масляный BMW 3(E46 / 90) 2.5D-3.0D...",
                "offers": [
                    {"warehouse": {"name": "BMS"}, "price": 247, "quantity": 1},
                    {"warehouse": {"name": "LNX"}, "price": 247, "quantity": 34}
                ]
            },
            {
                "article": "SP-1187",
                "brand": {"id": 1139185, "name": "ZEKKERT"},
                "name": "Зеркальный элемент правый выпуклый с подогревом BMW...",
                "offers": [{"warehouse": {"name": "RTZ"}, "price": 1495.29, "quantity": 1}]
            }
        ]
    }

# 🔹 Функция для получения данных из Автосоюза
async def fetch_autosoyuz(session, part_number: str):
    # Здесь твой код для работы с API Автосоюза
    return {"Error": "Недопустимое значение для параметров withouttransit."}

# ✅ Основной эндпоинт получения данных о запчастях
@app.get("/get_parts_info")
async def get_parts_info(part_number: str):
    async with aiohttp.ClientSession() as session:
        rossko_task = fetch_rossko(part_number)
        berg_task = fetch_berg(session, part_number)
        autosoyuz_task = fetch_autosoyuz(session, part_number)
        rossko_data, berg_data, autosoyuz_data = await asyncio.gather(rossko_task, berg_task, autosoyuz_task)

    response_data = {
        "rossko": [
            {"brand": item["brand"], "part_number": item["part_number"], "name": item["name"], "price": item["price"], "availability": item["availability"]}
            for item in rossko_data
        ],
        "berg": [
            {"brand": item["brand"]["name"], "part_number": item["article"], "name": item["name"], "price": item["offers"][0]["price"] if item["offers"] else None, "availability": sum(offer["quantity"] for offer in item["offers"]) if item["offers"] else 0}
            for item in berg_data["resources"]
        ],
        "autosoyuz": autosoyuz_data
    }
    
    return JSONResponse(content=response_data)

# ✅ Главная страница для проверки работоспособности API
@app.get("/")
def home():
    return {"message": "API is running! Use /docs to test"}
