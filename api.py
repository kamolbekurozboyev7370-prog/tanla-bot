"""
BACKEND API
===========
Mini App (webapp/index.html) shu API orqali umumiy bazaga (tanla.db) ulanadi.
Bot (bot.py) bazaga to'g'ridan-to'g'ri (database.py orqali) ulanadi, API'ga
muhtoj emas - shuning uchun bot ishlashi uchun bu serverni ishga tushirish
SHART EMAS, faqat Mini App'ni ishlatish uchun kerak.

Ishga tushirish:
    uvicorn api:app --host 0.0.0.0 --port 8000
"""

from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import config
import database as db

app = FastAPI(title="Tanla API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    db.init_db()
    db.seed_menu_if_empty()
    db.sync_restaurant_info()


# ===================== SXEMALAR =====================

class RatingIn(BaseModel):
    stars: int = Field(ge=1, le=5)
    user_id: Optional[str] = None


class ReviewIn(BaseModel):
    matn: str
    sana: Optional[str] = None
    username: Optional[str] = None
    user_id: Optional[str] = None


# ===================== RESTORANLAR =====================

@app.get("/api/restaurants")
def list_restaurants():
    natija = []
    for nom in db.get_restaurant_names():
        info = db.get_restaurant_info(nom)
        xulosa = db.restaurant_rating_summary(nom)
        natija.append({
            "name": nom,
            "manzil": info["manzil"],
            "usluga_foiz": info["usluga_foiz"],
            "xarita_havolasi": info.get("xarita_havolasi"),
            "ortacha_baho": xulosa["ortacha"],
            "baholar_soni": xulosa["soni"],
            "categories": db.get_restaurant_categories(nom),
        })
    return natija


# ===================== MENYU =====================

def _enrich(item: dict) -> dict:
    xulosa = db.rating_summary(item["id"])
    item = dict(item)
    item["ortacha_baho"] = xulosa["ortacha"]
    item["baholar_soni"] = xulosa["soni"]
    item["izohlar_soni"] = db.reviews_count(item["id"])
    return item


@app.get("/api/menu")
def list_menu(restoran: Optional[str] = None, turkum: Optional[str] = None):
    items = db.get_menu_items(restoran=restoran, turkum=turkum)
    return [_enrich(i) for i in items]


@app.get("/api/menu/{item_id}")
def get_menu_item(item_id: int):
    item = db.menu_item_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Taom topilmadi")
    return _enrich(item)


@app.get("/api/search")
def search(q: str):
    items = db.search_menu(q)
    return [_enrich(i) for i in items]


# ===================== REYTING =====================

@app.post("/api/menu/{item_id}/rating")
def add_rating(item_id: int, body: RatingIn):
    item = db.menu_item_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Taom topilmadi")
    db.add_rating(item_id, body.stars, user_id=body.user_id, source="webapp")
    return {"ok": True, "xulosa": db.rating_summary(item_id)}


# ===================== IZOHLAR =====================

@app.get("/api/menu/{item_id}/reviews")
def list_reviews(item_id: int):
    item = db.menu_item_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Taom topilmadi")
    # media_file_id ni chiqarib tashlaymiz - bu faqat Telegram ichida ishlaydi
    return [
        {k: v for k, v in r.items() if k not in ("media_file_id",)}
        for r in db.get_reviews(item_id)
    ]


@app.post("/api/menu/{item_id}/reviews")
def add_review(item_id: int, body: ReviewIn):
    item = db.menu_item_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Taom topilmadi")
    if len(body.matn.strip()) < 3:
        raise HTTPException(status_code=400, detail="Izoh juda qisqa")
    review = db.add_review(
        item_id=item_id,
        matn=body.matn,
        sana=body.sana,
        username=body.username or "Foydalanuvchi",
        user_id=body.user_id,
        source="webapp",
    )
    review.pop("media_file_id", None)
    return {"ok": True, "review": review}
