"""
UMUMIY BAZA QATLAMI
====================
Bot (bot.py) ham, veb-ilova backend (api.py) ham FAQAT shu fayl orqali
ma'lumotlarni o'qiydi/yozadi. Shu tufayli ikkalasi bitta fizik bazaga
(tanla.db) ulanadi va bir joyda kiritilgan reyting/izoh darhol ikkalasida
ham ko'rinadi.

Diqqat: bu yerdagi funksiyalar SODDA sinxron (blocking) funksiyalar.
SQLite juda tez ishlaydigan yengil baza bo'lgani uchun kichik-o'rta
yuklama (bir nechta restoran, bir necha yuz-ming foydalanuvchi) uchun
bu yetarli. Foydalanuvchi ko'payib ketsa, DATABASE_URL ni PostgreSQL'ga
almashtirish kifoya - qolgan kod o'zgarmaydi (SQLAlchemy shuning uchun
ishlatilgan).
"""

from datetime import datetime, timedelta

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    func,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

import config
import seed_data

engine = create_engine(config.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


# ===================== MODELLAR =====================

class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    manzil = Column(String, nullable=True)
    usluga_foiz = Column(Integer, nullable=True)
    xarita_havolasi = Column(String, nullable=True)  # Google Maps'dagi aniq joylashuv havolasi

    menu_items = relationship("MenuItem", back_populates="restoran", cascade="all, delete-orphan")


class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    turkum = Column(String, nullable=False)
    taom = Column(String, nullable=False)
    narx = Column(Integer, nullable=False)

    restoran = relationship("Restaurant", back_populates="menu_items")
    ratings = relationship("Rating", back_populates="menu_item", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="menu_item", cascade="all, delete-orphan")
    voices = relationship("Voice", back_populates="menu_item", cascade="all, delete-orphan")


class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True)
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"), nullable=False)
    user_id = Column(String, nullable=True)
    source = Column(String, default="bot")  # "bot" yoki "webapp" - qayerdan kelgani
    stars = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    menu_item = relationship("MenuItem", back_populates="ratings")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True)
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"), nullable=False)
    user_id = Column(String, nullable=True)
    username = Column(String, nullable=True)
    source = Column(String, default="bot")
    sana = Column(String, nullable=True)  # tashrif sanasi/vaqti (matn ko'rinishida)
    matn = Column(Text, nullable=True)
    media_file_id = Column(String, nullable=True)  # faqat botdan kelgan izohlarda bo'ladi
    media_type = Column(String, nullable=True)  # "photo" | "video" | None
    created_at = Column(DateTime, default=datetime.utcnow)

    menu_item = relationship("MenuItem", back_populates="reviews")


class Voice(Base):
    __tablename__ = "voices"

    id = Column(Integer, primary_key=True)
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"), nullable=False)
    user_id = Column(String, nullable=True)
    username = Column(String, nullable=True)
    file_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    menu_item = relationship("MenuItem", back_populates="voices")


class BotUser(Base):
    """Botdan foydalangan har bir shaxs haqida joriy holat (hozir faolmi yoki botni bloklaganmi)."""
    __tablename__ = "bot_users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True, nullable=False)
    username = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    first_joined_at = Column(DateTime, default=datetime.utcnow)  # birinchi marta /start bosgan vaqti
    last_joined_at = Column(DateTime, default=datetime.utcnow)   # oxirgi marta kirgan (yoki qayta kirgan) vaqti
    left_at = Column(DateTime, nullable=True)                    # botni oxirgi bloklagan/chiqib ketgan vaqti
    is_active = Column(Boolean, default=True)                    # hozir bot bilan aloqasi bormi


class UserEvent(Base):
    """Har bir kirish ('join') va chiqish ('leave') hodisasi - to'liq tarix uchun."""
    __tablename__ = "user_events"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, nullable=False)
    username = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    event_type = Column(String, nullable=False)  # "join" | "leave"
    created_at = Column(DateTime, default=datetime.utcnow)


# ===================== INIT / SEED =====================

def init_db():
    Base.metadata.create_all(engine)
    _migrate_yangi_ustunlar()


def _migrate_yangi_ustunlar():
    """Eski bazada mavjud bo'lmagan yangi ustunlarni qo'shib qo'yadi
    (bazani o'chirib qayta yaratmasdan, mavjud ma'lumotlar saqlanadi).
    Faqat SQLite uchun; PostgreSQL'ga o'tilsa, ustunlar allaqachon
    to'g'ri sxema bilan yaratiladi (create_all orqali)."""
    if engine.dialect.name != "sqlite":
        return
    with engine.connect() as conn:
        mavjud_ustunlar = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(restaurants)")}
        if "xarita_havolasi" not in mavjud_ustunlar:
            conn.exec_driver_sql("ALTER TABLE restaurants ADD COLUMN xarita_havolasi VARCHAR")
            conn.commit()


def sync_restaurant_info():
    """seed_data.py dagi manzil/usluga/xarita ma'lumotlarini mavjud restoranlarga
    har ishga tushganda yangilaydi - restoranlar allaqachon bazada bo'lsa ham ishlaydi."""
    with SessionLocal() as db:
        for r in db.query(Restaurant).all():
            nom = r.name
            if nom in seed_data.RESTORAN_MANZIL:
                r.manzil = seed_data.RESTORAN_MANZIL[nom]
            if nom in seed_data.RESTORAN_USLUGA:
                r.usluga_foiz = seed_data.RESTORAN_USLUGA[nom]
            if nom in getattr(seed_data, "RESTORAN_XARITA", {}):
                r.xarita_havolasi = seed_data.RESTORAN_XARITA[nom]
        db.commit()


def seed_menu_if_empty():
    """Baza bo'sh bo'lsa, seed_data.py dagi boshlang'ich menyuni bazaga yozadi."""
    with SessionLocal() as db:
        if db.query(Restaurant).count() > 0:
            return

        restaurants = {}
        nomlar = list(dict.fromkeys(item["restoran"] for item in seed_data.MENU))
        for nom in nomlar:
            r = Restaurant(
                name=nom,
                manzil=seed_data.RESTORAN_MANZIL.get(nom),
                usluga_foiz=seed_data.RESTORAN_USLUGA.get(nom),
                xarita_havolasi=getattr(seed_data, "RESTORAN_XARITA", {}).get(nom),
            )
            db.add(r)
            db.flush()
            restaurants[nom] = r

        for item in seed_data.MENU:
            db.add(MenuItem(
                restaurant_id=restaurants[item["restoran"]].id,
                turkum=item["turkum"],
                taom=item["taom"],
                narx=item["narx"],
            ))
        db.commit()


# ===================== YORDAMCHI FUNKSIYALAR =====================
# Bular MENU-dict ko'rinishidagi natija qaytaradi (asl bot.py bilan mos kelishi uchun):
# {"id", "restoran", "turkum", "taom", "narx"}

def _mi_to_dict(mi: MenuItem) -> dict:
    return {
        "id": mi.id,
        "restoran": mi.restoran.name,
        "turkum": mi.turkum,
        "taom": mi.taom,
        "narx": mi.narx,
    }


def get_restaurant_names() -> list:
    with SessionLocal() as db:
        rows = db.query(Restaurant.name).order_by(Restaurant.id).all()
        return [r[0] for r in rows]


def get_restaurant_info(restoran: str) -> dict:
    with SessionLocal() as db:
        r = db.query(Restaurant).filter(Restaurant.name == restoran).first()
        if not r:
            return {"manzil": None, "usluga_foiz": None, "xarita_havolasi": None}
        return {"manzil": r.manzil, "usluga_foiz": r.usluga_foiz, "xarita_havolasi": r.xarita_havolasi}


def get_categories() -> list:
    """Barcha restoranlar bo'yicha noyob turkumlar (tartib saqlangan)."""
    with SessionLocal() as db:
        rows = db.query(MenuItem.turkum, MenuItem.id).order_by(MenuItem.id).all()
        return list(dict.fromkeys(r[0] for r in rows))


def get_restaurant_categories(restoran: str) -> list:
    with SessionLocal() as db:
        rows = (
            db.query(MenuItem.turkum, MenuItem.id)
            .join(Restaurant)
            .filter(Restaurant.name == restoran)
            .order_by(MenuItem.id)
            .all()
        )
        return list(dict.fromkeys(r[0] for r in rows))


def get_menu_items(restoran: str = None, turkum: str = None) -> list:
    with SessionLocal() as db:
        q = db.query(MenuItem)
        if restoran:
            q = q.join(Restaurant).filter(Restaurant.name == restoran)
        if turkum:
            q = q.filter(MenuItem.turkum == turkum)
        return [_mi_to_dict(mi) for mi in q.order_by(MenuItem.id).all()]


def get_all_menu_items() -> list:
    with SessionLocal() as db:
        return [_mi_to_dict(mi) for mi in db.query(MenuItem).order_by(MenuItem.id).all()]


def menu_item_by_id(item_id: int) -> dict:
    with SessionLocal() as db:
        mi = db.get(MenuItem, item_id)
        return _mi_to_dict(mi) if mi else None


def search_menu(soz: str) -> list:
    soz = (soz or "").lower().strip()
    with SessionLocal() as db:
        rows = db.query(MenuItem).all()
        return [_mi_to_dict(mi) for mi in rows if soz in mi.taom.lower()]


# ----- Reyting -----

def add_rating(item_id: int, stars: int, user_id: str = None, source: str = "bot"):
    with SessionLocal() as db:
        db.add(Rating(menu_item_id=item_id, stars=stars, user_id=str(user_id) if user_id else None, source=source))
        db.commit()


def get_ratings(item_id: int) -> list:
    with SessionLocal() as db:
        rows = db.query(Rating.stars).filter(Rating.menu_item_id == item_id).all()
        return [r[0] for r in rows]


def rating_summary(item_id: int) -> dict:
    baholar = get_ratings(item_id)
    if not baholar:
        return {"ortacha": None, "soni": 0}
    return {"ortacha": round(sum(baholar) / len(baholar), 1), "soni": len(baholar)}


def restaurant_rating_summary(restoran: str) -> dict:
    with SessionLocal() as db:
        row = (
            db.query(func.avg(Rating.stars), func.count(Rating.stars))
            .join(MenuItem, MenuItem.id == Rating.menu_item_id)
            .join(Restaurant, Restaurant.id == MenuItem.restaurant_id)
            .filter(Restaurant.name == restoran)
            .first()
        )
        ortacha, soni = row[0], row[1] or 0
        return {"ortacha": round(ortacha, 1) if ortacha else None, "soni": soni}


# ----- Izohlar -----

def add_review(item_id: int, matn: str, sana: str = None, username: str = None,
                user_id: str = None, media_file_id: str = None, media_type: str = None,
                source: str = "bot") -> dict:
    with SessionLocal() as db:
        review = Review(
            menu_item_id=item_id,
            matn=matn,
            sana=sana,
            username=username,
            user_id=str(user_id) if user_id else None,
            media_file_id=media_file_id,
            media_type=media_type,
            source=source,
        )
        db.add(review)
        db.commit()
        db.refresh(review)
        return {
            "id": review.id,
            "username": review.username,
            "sana": review.sana,
            "matn": review.matn,
            "media_file_id": review.media_file_id,
            "media_type": review.media_type,
            "source": review.source,
        }


def get_reviews(item_id: int) -> list:
    with SessionLocal() as db:
        rows = (
            db.query(Review)
            .filter(Review.menu_item_id == item_id)
            .order_by(Review.created_at.desc())
            .all()
        )
        return [
            {
                "id": r.id,
                "username": r.username,
                "sana": r.sana,
                "matn": r.matn,
                "media_file_id": r.media_file_id,
                "media_type": r.media_type,
                "source": r.source,
            }
            for r in rows
        ]


def reviews_count(item_id: int) -> int:
    with SessionLocal() as db:
        return db.query(Review).filter(Review.menu_item_id == item_id).count()


# ----- Ovozli fikrlar -----

def add_voice(item_id: int, file_id: str, username: str = None, user_id: str = None, source: str = "bot"):
    with SessionLocal() as db:
        db.add(Voice(
            menu_item_id=item_id,
            file_id=file_id,
            username=username,
            user_id=str(user_id) if user_id else None,
            source=source,
        ))
        db.commit()


# ===================== FOYDALANUVCHILAR KIRISH/CHIQISH =====================
LOGIN_COOLDOWN_MINUTES = 30  # shu vaqt ichida qayta "kirdi" deb yozilmaydi


def track_activity(telegram_id, username: str = None, full_name: str = None):
    """Foydalanuvchi botga /start bosmasdan ham istalgan xabar yoki tugma orqali
    murojaat qilganda chaqiriladi. Agar oxirgi 'kirdi' yozuvidan beri
    LOGIN_COOLDOWN_MINUTES dan ko'p vaqt o'tgan bo'lsa, yangi 'kirdi' hodisasi yoziladi."""
    telegram_id = str(telegram_id)
    now = datetime.utcnow()
    with SessionLocal() as db:
        user = db.query(BotUser).filter(BotUser.telegram_id == telegram_id).first()
        last_event = (
            db.query(UserEvent)
            .filter(UserEvent.telegram_id == telegram_id, UserEvent.event_type == "join")
            .order_by(UserEvent.created_at.desc())
            .first()
        )
        should_log = (
            last_event is None
            or (now - last_event.created_at) > timedelta(minutes=LOGIN_COOLDOWN_MINUTES)
        )

        if user is None:
            user = BotUser(
                telegram_id=telegram_id,
                username=username,
                full_name=full_name,
                first_joined_at=now,
                last_joined_at=now,
                left_at=None,
                is_active=True,
            )
            db.add(user)
            should_log = True
        else:
            user.username = username or user.username
            user.full_name = full_name or user.full_name
            user.last_joined_at = now
            user.left_at = None
            user.is_active = True

        if should_log:
            db.add(UserEvent(
                telegram_id=telegram_id,
                username=username,
                full_name=full_name,
                event_type="join",
                created_at=now,
            ))
        db.commit()
def track_join(telegram_id, username: str = None, full_name: str = None):
    """Foydalanuvchi botni ishga tushirganda (/start) chaqiriladi. Yangi bo'lsa yaratadi,
    eski bo'lsa qayta faollashtiradi va 'join' hodisasini yozadi."""
    telegram_id = str(telegram_id)
    now = datetime.utcnow()
    with SessionLocal() as db:
        user = db.query(BotUser).filter(BotUser.telegram_id == telegram_id).first()
        if user is None:
            user = BotUser(
                telegram_id=telegram_id,
                username=username,
                full_name=full_name,
                first_joined_at=now,
                last_joined_at=now,
                left_at=None,
                is_active=True,
            )
            db.add(user)
        else:
            user.username = username or user.username
            user.full_name = full_name or user.full_name
            user.last_joined_at = now
            user.left_at = None
            user.is_active = True
        db.add(UserEvent(
            telegram_id=telegram_id,
            username=username,
            full_name=full_name,
            event_type="join",
            created_at=now,
        ))
        db.commit()


def track_leave(telegram_id, username: str = None, full_name: str = None):
    """Foydalanuvchi botni bloklaganda/chatni o'chirganda chaqiriladi."""
    telegram_id = str(telegram_id)
    now = datetime.utcnow()
    with SessionLocal() as db:
        user = db.query(BotUser).filter(BotUser.telegram_id == telegram_id).first()
        if user is not None:
            user.left_at = now
            user.is_active = False
            username = username or user.username
            full_name = full_name or user.full_name
        db.add(UserEvent(
            telegram_id=telegram_id,
            username=username,
            full_name=full_name,
            event_type="leave",
            created_at=now,
        ))
        db.commit()


def get_recent_events(limit: int = 30) -> list:
    """Eng oxirgi kirish/chiqish hodisalari (admin uchun tarix)."""
    with SessionLocal() as db:
        rows = (
            db.query(UserEvent)
            .order_by(UserEvent.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "telegram_id": r.telegram_id,
                "username": r.username,
                "full_name": r.full_name,
                "event_type": r.event_type,
                "created_at": r.created_at,
            }
            for r in rows
        ]


def get_active_users_count() -> int:
    with SessionLocal() as db:
        return db.query(BotUser).filter(BotUser.is_active == True).count()  # noqa: E712


def _period_kesim(period: str) -> datetime:
    now = datetime.utcnow()
    if period == "week":
        return now - timedelta(days=7)
    return now - timedelta(days=30)  # "month"


def get_new_users_stats(period: str = "week") -> dict:
    """period: 'week' yoki 'month'. Shu davrda birinchi marta kirgan foydalanuvchilar."""
    kesim = _period_kesim(period)
    with SessionLocal() as db:
        soni = db.query(BotUser).filter(BotUser.first_joined_at >= kesim).count()
        users = (
            db.query(BotUser)
            .filter(BotUser.first_joined_at >= kesim)
            .order_by(BotUser.first_joined_at.desc())
            .all()
        )
        return {
            "soni": soni,
            "users": [
                {
                    "telegram_id": u.telegram_id,
                    "username": u.username,
                    "full_name": u.full_name,
                    "first_joined_at": u.first_joined_at,
                }
                for u in users
            ],
        }


def get_total_users_count() -> int:
    with SessionLocal() as db:
        return db.query(BotUser).count()
