import asyncio
import calendar as calendar_module
import logging
import re
import urllib.parse
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)

import config
import database as db

logging.basicConfig(level=logging.INFO)

bot = Bot(token=config.TOKEN)
dp = Dispatcher()

user_state = {}              # user_id -> holat
user_selected_restoran = {}  # user_id -> tanlangan restoran nomi
pending_review = {}          # user_id -> to'ldirilayotgan izoh ma'lumotlari

hisob_savat = {}              # user_id -> {"restoran": str, "items": {taom_id: {"taom","narx","miqdor"}}}
hisob_miqdor_kutilayotgan = {}  # user_id -> {"taom_id": int, "rejim": "qoshish" | "tahrirlash"}


# ===================== YORDAMCHI FUNKSIYALAR =====================

def narxni_formatlash(narx: int) -> str:
    if not narx:
        return "Narxi kelishiladi"
    return f"{narx:,}".replace(",", " ") + " so'm"


def manzil_matni(restoran: str) -> str:
    manzil = db.get_restaurant_info(restoran)["manzil"]
    if not manzil:
        return "Manzil: ko'rsatilmagan"
    return f"Manzil: {manzil}"


def google_maps_havolasi(restoran: str) -> str:
    """Bazada aniq Google Maps havolasi bo'lsa o'shani, bo'lmasa manzil bo'yicha
    qidiruv havolasini qaytaradi."""
    info = db.get_restaurant_info(restoran)
    if info.get("xarita_havolasi"):
        return info["xarita_havolasi"]
    manzil = info.get("manzil")
    soz = f"{restoran} {manzil}" if manzil else restoran
    return "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(soz)


def manzil_xarita_keyboard(restoran: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📍 Xaritada ko'rish / Yo'l ko'rsatish", url=google_maps_havolasi(restoran))]
    ])


def usluga_matni(restoran: str) -> str:
    foiz = db.get_restaurant_info(restoran)["usluga_foiz"]
    if foiz is None:
        return "Xizmat haqi (usluga): ko'rsatilmagan"
    return f"Xizmat haqi (usluga): {foiz}%"


def reyting_matni(taom_id: int) -> str:
    xulosa = db.rating_summary(taom_id)
    if xulosa["soni"] == 0:
        return "Hali baholanmagan"
    return f"⭐ {xulosa['ortacha']} ({xulosa['soni']} ta baho)"


def taom_card_matni(item: dict) -> str:
    izohlar_soni = db.reviews_count(item["id"])
    return (
        f"🍽 <b>{item['taom']}</b>\n"
        f"🏠 {item['restoran']}\n"
        f"📂 {item['turkum']}\n"
        f"💰 {narxni_formatlash(item['narx'])}\n"
        f"{reyting_matni(item['id'])} · 💬 {izohlar_soni} ta izoh"
    )


def taom_inline_keyboard(item: dict) -> InlineKeyboardMarkup:
    taom_id = item["id"]
    izohlar_soni = db.reviews_count(taom_id)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐️ Baholash", callback_data=f"baho|{taom_id}")],
        [InlineKeyboardButton(text="💬 Izoh qoldirish", callback_data=f"izoh|{taom_id}")],
        [InlineKeyboardButton(text=f"👁 Izohlarni ko'rish ({izohlar_soni})", callback_data=f"korish|{taom_id}")],
    ])


def yulduz_keyboard(taom_id: int) -> InlineKeyboardMarkup:
    tugmalar = [InlineKeyboardButton(text="⭐" * i, callback_data=f"star|{taom_id}|{i}") for i in range(1, 6)]
    return InlineKeyboardMarkup(inline_keyboard=[[t] for t in tugmalar])


def ovoz_taklif_keyboard(taom_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎤 Ovozli fikr qoldirish", callback_data=f"ovoz_kut|{taom_id}")],
        [InlineKeyboardButton(text="⏭ Kerak emas", callback_data=f"ovoz_yoq|{taom_id}")],
    ])


def skip_media_keyboard(taom_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭ O'tkazib yuborish", callback_data=f"media_otkazish|{taom_id}")]
    ])


def izoh_tasdiq_keyboard(taom_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Saqlash", callback_data=f"izoh_saqlash|{taom_id}")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"izoh_bekor|{taom_id}")],
    ])


def admin_panel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🕘 Kirish/chiqish tarixi", callback_data="admin|history")],
        [InlineKeyboardButton(text="📈 Yangi foydalanuvchilar", callback_data="admin|newusers")],
    ])


def newusers_filter_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📅 Haftalik", callback_data="newusers|week"),
            InlineKeyboardButton(text="🗓 Oylik", callback_data="newusers|month"),
        ],
    ])


def foydalanuvchi_belgisi(username: str, full_name: str, telegram_id: str) -> str:
    if username:
        return f"@{username}"
    if full_name:
        return full_name
    return f"ID {telegram_id}"


# Bazadagi vaqtlar UTC (butun dunyo standarti) bo'yicha saqlanadi.
# Admin panelda ko'rsatilganda Toshkent vaqtiga (UTC+5) o'giramiz.
TOSHKENT_FARQI = timedelta(hours=5)


def mahalliy_vaqt(dt: datetime) -> str:
    return (dt + TOSHKENT_FARQI).strftime("%d.%m.%Y %H:%M")


# ----- Sana/vaqt tanlash uchun taqvim klaviaturasi -----

UZ_OYLAR = ["Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
            "Iyul", "Avgust", "Sentabr", "Oktabr", "Noyabr", "Dekabr"]
UZ_KUNLAR = ["Du", "Se", "Ch", "Pa", "Ju", "Sh", "Ya"]


def taqvim_keyboard(yil: int, oy: int) -> InlineKeyboardMarkup:
    kal = calendar_module.Calendar(firstweekday=0)
    oy_kunlari = kal.monthdayscalendar(yil, oy)

    keyboard = [
        [
            InlineKeyboardButton(text="◀", callback_data=f"cal_nav|{yil}-{oy:02d}|prev"),
            InlineKeyboardButton(text=f"{UZ_OYLAR[oy - 1]} {yil}", callback_data="cal_ignore"),
            InlineKeyboardButton(text="▶", callback_data=f"cal_nav|{yil}-{oy:02d}|next"),
        ],
        [InlineKeyboardButton(text=kun, callback_data="cal_ignore") for kun in UZ_KUNLAR],
    ]

    for hafta in oy_kunlari:
        qator = []
        for kun in hafta:
            if kun == 0:
                qator.append(InlineKeyboardButton(text=" ", callback_data="cal_ignore"))
            else:
                sana_str = f"{yil}-{oy:02d}-{kun:02d}"
                qator.append(InlineKeyboardButton(text=str(kun), callback_data=f"cal_day|{sana_str}"))
        keyboard.append(qator)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def soat_keyboard(sana_str: str) -> InlineKeyboardMarkup:
    soatlar = list(range(9, 24))  # 09:00 dan 23:00 gacha
    keyboard = []
    qator = []
    for i, soat in enumerate(soatlar, start=1):
        qator.append(InlineKeyboardButton(text=f"{soat:02d}:00", callback_data=f"vaqt_soat|{sana_str}|{soat:02d}"))
        if i % 4 == 0:
            keyboard.append(qator)
            qator = []
    if qator:
        keyboard.append(qator)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def daqiqa_keyboard(sana_str: str, soat: str) -> InlineKeyboardMarkup:
    daqiqalar = ["00", "15", "30", "45"]
    qator = [
        InlineKeyboardButton(text=f"{soat}:{d}", callback_data=f"vaqt_daqiqa|{sana_str}|{soat}|{d}")
        for d in daqiqalar
    ]
    return InlineKeyboardMarkup(inline_keyboard=[qator])


# ----- Izoh matnini tekshirish -----

def izoh_matni_yaroqlimi(matn: str) -> bool:
    """Kamida 2 ta har xil, 2 harfdan uzunroq so'z talab qilinadi."""
    sozlar = re.findall(r"[^\W\d_]{2,}", matn, flags=re.UNICODE)
    noyob_sozlar = set(s.lower() for s in sozlar)
    return len(sozlar) >= 2 and len(noyob_sozlar) >= 2


def foydalanuvchi_nomi(user: types.User) -> str:
    if user.username:
        return user.username
    return user.full_name or "Foydalanuvchi"


# ===================== KLAVIATURALAR =====================

def is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS


def asosiy_menu(user_id: int = None) -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="⭐️ Restoranlar reytingi"), KeyboardButton(text="🍽 Taomlar reytingi")],
        [KeyboardButton(text="🍲 Nima yemoqchisiz?"), KeyboardButton(text="🏠 Restoranlar")],
        [KeyboardButton(text="🔍 Taom nomini qidirish"), KeyboardButton(text="🧮 Taxminiy hisob-kitob")],
        [KeyboardButton(text="📞 Biz bilan bog'lanish"), KeyboardButton(text="ℹ️ Bot haqida")],
    ]
    if config.WEBAPP_URL:
        keyboard.append([KeyboardButton(text="🌐 Ilovada ochish", web_app=WebAppInfo(url=config.WEBAPP_URL))])
    if user_id is not None and is_admin(user_id):
        keyboard.append([KeyboardButton(text="🔐 Admin panel")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def orqaga_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="0️⃣ Orqaga")]], resize_keyboard=True)


def turkumlar_menu() -> ReplyKeyboardMarkup:
    tugmalar = [[KeyboardButton(text=t)] for t in db.get_categories()]
    tugmalar.append([KeyboardButton(text="0️⃣ Orqaga")])
    return ReplyKeyboardMarkup(keyboard=tugmalar, resize_keyboard=True)


def restoranlar_menu() -> ReplyKeyboardMarkup:
    tugmalar = [[KeyboardButton(text=r)] for r in db.get_restaurant_names()]
    tugmalar.append([KeyboardButton(text="0️⃣ Orqaga")])
    return ReplyKeyboardMarkup(keyboard=tugmalar, resize_keyboard=True)


def restoran_turkumlar_menu(restoran: str) -> ReplyKeyboardMarkup:
    tugmalar = [[KeyboardButton(text=t)] for t in db.get_restaurant_categories(restoran)]
    tugmalar.append([KeyboardButton(text="0️⃣ Orqaga")])
    return ReplyKeyboardMarkup(keyboard=tugmalar, resize_keyboard=True)


# ----- Taxminiy hisob-kitob (mijoz uchun) -----

def hisob_restoranlar_menu() -> ReplyKeyboardMarkup:
    tugmalar = [[KeyboardButton(text=r)] for r in db.get_restaurant_names()]
    tugmalar.append([KeyboardButton(text="0️⃣ Bekor qilish")])
    return ReplyKeyboardMarkup(keyboard=tugmalar, resize_keyboard=True)


def hisob_taomlar_keyboard(taomlar: list) -> InlineKeyboardMarkup:
    """Barcha taomlarni bitta ro'yxatda, har birining oldida ➕ tugmasi bilan ko'rsatadi."""
    qatorlar = []
    joriy_turkum = None
    for item in taomlar:
        if item["turkum"] != joriy_turkum:
            joriy_turkum = item["turkum"]
            qatorlar.append([InlineKeyboardButton(text=f"— {joriy_turkum} —", callback_data="hs_ignore")])
        qatorlar.append([InlineKeyboardButton(
            text=f"➕ {item['taom']} — {narxni_formatlash(item['narx'])}",
            callback_data=f"hs_add|{item['id']}"
        )])
    qatorlar.append([InlineKeyboardButton(text="🧮 Taxminiy hisobni hisoblash", callback_data="hs_hisobla")])
    qatorlar.append([InlineKeyboardButton(text="✏️ Savatni tahrirlash", callback_data="hs_tahrir")])
    qatorlar.append([InlineKeyboardButton(text="🗑 Savatni bekor qilish", callback_data="hs_bekor")])
    return InlineKeyboardMarkup(inline_keyboard=qatorlar)


def hisob_tahrirlash_keyboard(user_id: int) -> InlineKeyboardMarkup:
    savat = hisob_savat.get(user_id, {}).get("items", {})
    qatorlar = []
    for taom_id, item in savat.items():
        qatorlar.append([InlineKeyboardButton(
            text=f"{item['taom']} — {item['miqdor']} dona",
            callback_data=f"hs_item|{taom_id}"
        )])
    qatorlar.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="hs_royxatga_qaytish")])
    return InlineKeyboardMarkup(inline_keyboard=qatorlar)


def hisob_item_amal_keyboard(taom_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Miqdorini o'zgartirish", callback_data=f"hs_item_tahrir|{taom_id}")],
        [InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"hs_item_ochir|{taom_id}")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="hs_tahrir")],
    ])


def hisob_savat_matni(user_id: int) -> str:
    savat = hisob_savat.get(user_id)
    if not savat or not savat["items"]:
        return "Savat hozircha bo'sh."
    qismlar = [f"🧾 <b>{savat['restoran']}</b> — savat\n"]
    jami = 0
    for item in savat["items"].values():
        summa = item["narx"] * item["miqdor"]
        jami += summa
        qismlar.append(f"• {item['taom']} — {item['miqdor']} dona × {narxni_formatlash(item['narx'])} = {narxni_formatlash(summa)}")
    qismlar.append(f"\nOraliq summa: {narxni_formatlash(jami)}")
    return "\n".join(qismlar)


def miqdorni_ayirish(matn: str):
    """Matnni musbat songa aylantiradi. (muvaffaqiyat, qiymat_yoki_xato_matni)"""
    matn = matn.strip().replace(",", ".")
    try:
        qiymat = float(matn)
    except ValueError:
        return False, "Iltimos, faqat son kiriting (masalan: 2 yoki 1.5)."
    if qiymat <= 0:
        return False, "Miqdor musbat son bo'lishi kerak."
    return True, qiymat


HISOB_OGOHLANTIRISH = (
    "\n\n⚠️ <b>Diqqat:</b> Siz barcha ma'lumotlarni to'liq va to'g'ri kiritgan bo'lsangiz ham, "
    "ushbu summa restoran taqdim etadigan haqiqiy chekdan farq qilishi mumkin — taomlar yoki "
    "ichimliklar narxi o'zgargan bo'lishi mumkin, yoki siz alohida xona/kabinada o'tirgan "
    "bo'lsangiz, u yerda xizmat haqi (usluga) boshqacha bo'lishi mumkin. "
    "Ushbu xizmat sizga faqat <b>taxminiy</b> hisobni hisoblab beradi, xolos."
)


# ===================== MATNLAR =====================

BOT_HAQIDA_TEXT = (
    "ℹ️ <b>Tanla</b> boti haqida\n\n"
    "Tanla — tumandagi restoran va ovqatlanish maskanlarining menyusi, narxlari va "
    "ularni sinab ko'rgan odamlarning fikrlarini bir joyga jamlovchi bot.\n\n"
    "Har bir taomni baholashingiz, izoh qoldirishingiz va boshqalarning fikrlarini "
    "o'qib, o'zingiz uchun eng to'g'ri tanlovni qilishingiz mumkin.\n\n"
    "Shu bot bilan bir xil ma'lumotlarni veb-ilovada ham ko'rishingiz mumkin — "
    "qaysi birida baho/izoh qoldirsangiz, ikkalasida ham darhol ko'rinadi."
)

BOGLANISH_TEXT = (
    "📞 Biz bilan bog'lanish\n\n"
    "Savol, taklif yoki restoranlaringizni bot bazasiga qo'shish uchun murojaat qiling:\n"
    "Telegram: @sizning_username\n"
    "Telefon: +998 90 000 00 00"
)


# ===================== ASOSIY BUYRUQLAR =====================

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_state[message.from_user.id] = "main"
    db.track_join(
        message.from_user.id,
        username=foydalanuvchi_nomi(message.from_user),
        full_name=message.from_user.full_name,
    )
    await message.answer(
        "Assalomu alaykum! Men <b>Tanla</b> botiman 🍽\n\n"
        "Tumandagi restoran va ovqatlanish maskanlarining <b>menyusi</b>, <b>narxlari</b> "
        "va <b>haqiqiy mijozlar fikri</b> asosida sizga eng qulay tanlovni topishga "
        "yordam beraman.\n\n"
        "Quyidagi bo'limlardan birini tanlang 👇",
        reply_markup=asosiy_menu(message.from_user.id),
        parse_mode="HTML"
    )


# ===================== BOT BLOKLANSA/QAYTA OCHILSA (kirish-chiqish kuzatuvi) =====================

@dp.my_chat_member()
async def on_bot_membership_changed(update: types.ChatMemberUpdated):
    """Foydalanuvchi botni bloklasa yoki chatni o'chirsa - 'chiqib ketdi' deb yoziladi.
    Bloklashni bekor qilib qayta yozsa - 'kirdi' deb qayta yoziladi."""
    yangi_holat = update.new_chat_member.status
    user = update.from_user
    if yangi_holat in ("kicked", "left"):
        db.track_leave(user.id, username=foydalanuvchi_nomi(user), full_name=user.full_name)
    elif yangi_holat in ("member",):
        db.track_join(user.id, username=foydalanuvchi_nomi(user), full_name=user.full_name)


# ===================== OVOZLI XABARLAR =====================

@dp.message(F.voice)
async def voice_handler(message: types.Message):
    user_id = message.from_user.id
    state = user_state.get(user_id, "")
    if state.startswith("ovoz_kutilmoqda:"):
        taom_id = int(state.split(":")[1])
        db.add_voice(
            taom_id,
            file_id=message.voice.file_id,
            username=foydalanuvchi_nomi(message.from_user),
            user_id=user_id,
            source="bot",
        )
        user_state[user_id] = "main"
        await message.answer("Ovozli fikringiz uchun rahmat! 🙏", reply_markup=asosiy_menu(user_id))
    else:
        await message.answer("Hozircha ovozli xabar kutilmayapti.")


# ===================== RASM / VIDEO XABARLAR =====================

@dp.message(F.photo | F.video)
async def media_handler(message: types.Message):
    user_id = message.from_user.id
    state = user_state.get(user_id, "")
    if state == "izoh_media_kutilmoqda":
        review = pending_review.get(user_id)
        if review is None:
            await message.answer("Xatolik yuz berdi, qaytadan boshlang.", reply_markup=asosiy_menu(user_id))
            user_state[user_id] = "main"
            return
        if message.photo:
            review["media_file_id"] = message.photo[-1].file_id
            review["media_type"] = "photo"
        elif message.video:
            review["media_file_id"] = message.video.file_id
            review["media_type"] = "video"
        user_state[user_id] = "izoh_matn_kutilmoqda"
        await message.answer(
            "✅ Fayl qabul qilindi.\n\n"
            "Endi taom haqida qisqacha yozing — aynan nimasi yoqdi yoki yoqmadi?"
        )
    else:
        await message.answer("Hozircha bu turdagi fayl kutilmayapti.")


# ===================== INLINE TUGMALAR (CALLBACK) =====================

@dp.callback_query(F.data.startswith("baho|"))
async def baho_callback(call: CallbackQuery):
    taom_id = int(call.data.split("|")[1])
    item = db.menu_item_by_id(taom_id)
    await call.message.answer(
        f"'{item['taom']}' uchun necha yulduz berasiz?",
        reply_markup=yulduz_keyboard(taom_id)
    )
    await call.answer()


@dp.callback_query(F.data.startswith("star|"))
async def star_callback(call: CallbackQuery):
    _, taom_id_str, yulduz_str = call.data.split("|")
    taom_id = int(taom_id_str)
    yulduz = int(yulduz_str)
    db.add_rating(taom_id, yulduz, user_id=call.from_user.id, source="bot")

    item = db.menu_item_by_id(taom_id)
    await call.message.edit_text(
        f"Rahmat! Siz '{item['taom']}' uchun {'⭐' * yulduz} baho berdingiz.\n"
        f"Hozirgi reyting: {reyting_matni(taom_id)}"
    )
    await call.message.answer(
        "Xohlasangiz, ovozli xabar orqali ham fikringizni bildirishingiz mumkin (ixtiyoriy):",
        reply_markup=ovoz_taklif_keyboard(taom_id)
    )
    await call.answer()


@dp.callback_query(F.data.startswith("ovoz_kut|"))
async def ovoz_kut_callback(call: CallbackQuery):
    taom_id = int(call.data.split("|")[1])
    user_state[call.from_user.id] = f"ovoz_kutilmoqda:{taom_id}"
    await call.message.answer("🎤 Ovozli xabaringizni yuboring:")
    await call.answer()


@dp.callback_query(F.data.startswith("ovoz_yoq|"))
async def ovoz_yoq_callback(call: CallbackQuery):
    await call.message.answer("Baho qabul qilindi, rahmat! 🙏", reply_markup=asosiy_menu())
    await call.answer()


@dp.callback_query(F.data.startswith("izoh|"))
async def izoh_start_callback(call: CallbackQuery):
    taom_id = int(call.data.split("|")[1])
    user_id = call.from_user.id
    pending_review[user_id] = {
        "taom_id": taom_id, "sana": None, "media_file_id": None, "media_type": None, "matn": None
    }
    user_state[user_id] = "izoh_sana_tanlanmoqda"
    hozir = datetime.now()
    await call.message.answer(
        "📅 Restoranga/kafega qaysi kuni borgan edingiz? Sanani tanlang:",
        reply_markup=taqvim_keyboard(hozir.year, hozir.month)
    )
    await call.answer()


@dp.callback_query(F.data == "cal_ignore")
async def cal_ignore_callback(call: CallbackQuery):
    await call.answer()


@dp.callback_query(F.data.startswith("cal_nav|"))
async def cal_nav_callback(call: CallbackQuery):
    _, ym, harakat = call.data.split("|")
    yil, oy = map(int, ym.split("-"))
    if harakat == "prev":
        oy -= 1
        if oy == 0:
            oy = 12
            yil -= 1
    else:
        oy += 1
        if oy == 13:
            oy = 1
            yil += 1
    await call.message.edit_reply_markup(reply_markup=taqvim_keyboard(yil, oy))
    await call.answer()


@dp.callback_query(F.data.startswith("cal_day|"))
async def cal_day_callback(call: CallbackQuery):
    sana_str = call.data.split("|")[1]
    user_id = call.from_user.id
    review = pending_review.get(user_id)
    if review is None:
        await call.answer()
        return
    await call.message.edit_text(
        f"📅 Tanlangan sana: {sana_str}\n\nEndi soatni tanlang:",
        reply_markup=soat_keyboard(sana_str)
    )
    await call.answer()


@dp.callback_query(F.data.startswith("vaqt_soat|"))
async def vaqt_soat_callback(call: CallbackQuery):
    _, sana_str, soat = call.data.split("|")
    await call.message.edit_text(
        f"📅 Sana: {sana_str}, soat: {soat}:00 atrofida\n\nAniqroq daqiqani tanlang:",
        reply_markup=daqiqa_keyboard(sana_str, soat)
    )
    await call.answer()


@dp.callback_query(F.data.startswith("vaqt_daqiqa|"))
async def vaqt_daqiqa_callback(call: CallbackQuery):
    _, sana_str, soat, daqiqa = call.data.split("|")
    user_id = call.from_user.id
    review = pending_review.get(user_id)
    if review is None:
        await call.answer()
        return
    sana_vaqt = f"{sana_str} {soat}:{daqiqa}"
    review["sana"] = sana_vaqt
    taom_id = review["taom_id"]
    user_state[user_id] = "izoh_media_kutilmoqda"
    await call.message.edit_text(f"📅 Tashrif vaqti tanlandi: {sana_vaqt}")
    await call.message.answer(
        "📷🎥 Taom haqida rasm yoki video yubormoqchimisiz? (ixtiyoriy)\n"
        "Agar kerak bo'lmasa, pastdagi tugmani bosing.",
        reply_markup=skip_media_keyboard(taom_id)
    )
    await call.answer()


@dp.callback_query(F.data.startswith("media_otkazish|"))
async def media_otkazish_callback(call: CallbackQuery):
    user_id = call.from_user.id
    user_state[user_id] = "izoh_matn_kutilmoqda"
    await call.message.answer("Taom haqida qisqacha yozing — aynan nimasi yoqdi yoki yoqmadi?")
    await call.answer()


@dp.callback_query(F.data.startswith("izoh_saqlash|"))
async def izoh_saqlash_callback(call: CallbackQuery):
    user_id = call.from_user.id
    review = pending_review.pop(user_id, None)
    if review:
        db.add_review(
            item_id=review["taom_id"],
            matn=review["matn"],
            sana=review["sana"],
            username=foydalanuvchi_nomi(call.from_user),
            user_id=user_id,
            media_file_id=review.get("media_file_id"),
            media_type=review.get("media_type"),
            source="bot",
        )
        user_state[user_id] = "main"
        await call.message.answer("✅ Izohingiz saqlandi. Rahmat! 🙏", reply_markup=asosiy_menu(user_id))
    await call.answer()


@dp.callback_query(F.data.startswith("izoh_bekor|"))
async def izoh_bekor_callback(call: CallbackQuery):
    user_id = call.from_user.id
    pending_review.pop(user_id, None)
    user_state[user_id] = "main"
    await call.message.answer("Izoh bekor qilindi.", reply_markup=asosiy_menu(user_id))
    await call.answer()


@dp.callback_query(F.data.startswith("korish|"))
async def korish_callback(call: CallbackQuery):
    taom_id = int(call.data.split("|")[1])
    izohlar = db.get_reviews(taom_id)
    if not izohlar:
        await call.message.answer("Bu taom uchun hali izohlar yo'q. Birinchi bo'lib siz yozing!")
    else:
        for r in izohlar:
            manba_belg = "" if r.get("source", "bot") == "bot" else " 🌐"
            caption = (
                f"👤 @{r['username']}{manba_belg}\n"
                f"📅 Tashrif: {r['sana']}\n"
                f"💬 {r['matn']}"
            )
            if r.get("media_type") == "photo" and r.get("media_file_id"):
                await call.message.answer_photo(r["media_file_id"], caption=caption)
            elif r.get("media_type") == "video" and r.get("media_file_id"):
                await call.message.answer_video(r["media_file_id"], caption=caption)
            else:
                await call.message.answer(caption)
    await call.answer()


# ===================== TAXMINIY HISOB-KITOB (CALLBACK) =====================

@dp.callback_query(F.data == "hs_ignore")
async def hs_ignore_callback(call: CallbackQuery):
    await call.answer()


@dp.callback_query(F.data.startswith("hs_add|"))
async def hs_add_callback(call: CallbackQuery):
    taom_id = int(call.data.split("|")[1])
    taom = db.menu_item_by_id(taom_id)
    user_id = call.from_user.id
    hisob_miqdor_kutilayotgan[user_id] = {"taom_id": taom_id, "rejim": "qoshish"}
    user_state[user_id] = "hisob_miqdor_kutilmoqda"
    await call.message.answer(
        f"{taom['taom']} — {narxni_formatlash(taom['narx'])}\nNecha dona/miqdor kiritasiz?"
    )
    await call.answer()


@dp.callback_query(F.data == "hs_tahrir")
async def hs_tahrir_callback(call: CallbackQuery):
    user_id = call.from_user.id
    savat = hisob_savat.get(user_id, {}).get("items", {})
    if not savat:
        await call.answer("Savat hozircha bo'sh.", show_alert=True)
        return
    await call.message.answer("Qaysi taomni tahrirlamoqchisiz?", reply_markup=hisob_tahrirlash_keyboard(user_id))
    await call.answer()


@dp.callback_query(F.data == "hs_royxatga_qaytish")
async def hs_royxatga_qaytish_callback(call: CallbackQuery):
    user_id = call.from_user.id
    savat = hisob_savat.get(user_id)
    if not savat:
        await call.answer()
        return
    taomlar = db.get_menu_items(restoran=savat["restoran"])
    await call.message.answer(
        hisob_savat_matni(user_id), parse_mode="HTML",
        reply_markup=hisob_taomlar_keyboard(taomlar)
    )
    await call.answer()


@dp.callback_query(F.data.startswith("hs_item|"))
async def hs_item_callback(call: CallbackQuery):
    taom_id = int(call.data.split("|")[1])
    user_id = call.from_user.id
    savat = hisob_savat.get(user_id, {}).get("items", {})
    item = savat.get(taom_id)
    if not item:
        await call.answer("Topilmadi.")
        return
    await call.message.answer(
        f"{item['taom']} — {item['miqdor']} dona\nNima qilamiz?",
        reply_markup=hisob_item_amal_keyboard(taom_id)
    )
    await call.answer()


@dp.callback_query(F.data.startswith("hs_item_tahrir|"))
async def hs_item_tahrir_callback(call: CallbackQuery):
    taom_id = int(call.data.split("|")[1])
    user_id = call.from_user.id
    hisob_miqdor_kutilayotgan[user_id] = {"taom_id": taom_id, "rejim": "tahrirlash"}
    user_state[user_id] = "hisob_miqdor_kutilmoqda"
    await call.message.answer("Yangi miqdorni kiriting:")
    await call.answer()


@dp.callback_query(F.data.startswith("hs_item_ochir|"))
async def hs_item_ochir_callback(call: CallbackQuery):
    taom_id = int(call.data.split("|")[1])
    user_id = call.from_user.id
    savat = hisob_savat.get(user_id, {}).get("items", {})
    savat.pop(taom_id, None)
    await call.message.answer("🗑 O'chirildi.\n\n" + hisob_savat_matni(user_id), parse_mode="HTML")
    if savat:
        await call.message.answer("Qaysi taomni tahrirlamoqchisiz?", reply_markup=hisob_tahrirlash_keyboard(user_id))
    await call.answer()


@dp.callback_query(F.data == "hs_hisobla")
async def hs_hisobla_callback(call: CallbackQuery):
    user_id = call.from_user.id
    savat = hisob_savat.get(user_id)
    if not savat or not savat["items"]:
        await call.answer("Savat hozircha bo'sh.", show_alert=True)
        return

    restoran = savat["restoran"]
    info = db.get_restaurant_info(restoran)
    usluga_foiz = info["usluga_foiz"] or 0

    taomlar_summasi = sum(i["narx"] * i["miqdor"] for i in savat["items"].values())
    usluga_summasi = taomlar_summasi * usluga_foiz / 100
    umumiy = taomlar_summasi + usluga_summasi

    qismlar = [f"🧾 <b>{restoran}</b> — taxminiy hisob\n"]
    for item in savat["items"].values():
        summa = item["narx"] * item["miqdor"]
        qismlar.append(f"• {item['taom']} — {item['miqdor']} dona × {narxni_formatlash(item['narx'])} = {narxni_formatlash(summa)}")
    qismlar.append(f"\nTaomlar summasi: {narxni_formatlash(taomlar_summasi)}")
    qismlar.append(f"Usluga ({usluga_foiz}%): {narxni_formatlash(usluga_summasi)}")
    qismlar.append(f"<b>Taxminiy jami: {narxni_formatlash(umumiy)}</b>")
    qismlar.append(HISOB_OGOHLANTIRISH)

    await call.message.answer("\n".join(qismlar), parse_mode="HTML", reply_markup=asosiy_menu(user_id))
    await call.answer()


@dp.callback_query(F.data == "hs_bekor")
async def hs_bekor_callback(call: CallbackQuery):
    user_id = call.from_user.id
    hisob_savat.pop(user_id, None)
    hisob_miqdor_kutilayotgan.pop(user_id, None)
    user_state[user_id] = "main"
    await call.message.answer("Savat bekor qilindi.", reply_markup=asosiy_menu(user_id))
    await call.answer()


# ===================== ADMIN PANEL (faqat config.ADMIN_IDS uchun) =====================

@dp.callback_query(F.data == "admin|history")
async def admin_history_callback(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("Bu bo'lim faqat administrator uchun.", show_alert=True)
        return
    hodisalar = db.get_recent_events(limit=30)
    if not hodisalar:
        await call.message.answer("Hozircha hech qanday kirish/chiqish hodisasi qayd etilmagan.")
    else:
        qismlar = ["🕘 <b>Oxirgi kirish/chiqish hodisalari</b> (so'nggi 30 ta)\n"]
        for h in hodisalar:
            belgi = "🟢 Kirdi" if h["event_type"] == "join" else "🔴 Chiqdi (botni bloklagan)"
            ism = foydalanuvchi_belgisi(h["username"], h["full_name"], h["telegram_id"])
            vaqt = mahalliy_vaqt(h["created_at"])
            qismlar.append(f"{belgi}\n👤 {ism} · 🕒 {vaqt}")
        await call.message.answer("\n\n".join(qismlar), parse_mode="HTML")
    await call.answer()


@dp.callback_query(F.data == "admin|newusers")
async def admin_newusers_callback(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("Bu bo'lim faqat administrator uchun.", show_alert=True)
        return
    await call.message.answer(
        "📈 Yangi foydalanuvchilarni qaysi davr bo'yicha ko'rsataman?",
        reply_markup=newusers_filter_keyboard(),
    )
    await call.answer()


@dp.callback_query(F.data.startswith("newusers|"))
async def newusers_filter_callback(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("Bu bo'lim faqat administrator uchun.", show_alert=True)
        return
    period = call.data.split("|")[1]  # "week" | "month"
    natija = db.get_new_users_stats(period)
    davr_matni = "so'nggi 7 kun (haftalik)" if period == "week" else "so'nggi 30 kun (oylik)"

    sarlavha = (
        f"📈 <b>Yangi foydalanuvchilar</b> — {davr_matni}\n\n"
        f"👥 Jami yangi qo'shilganlar: <b>{natija['soni']}</b> ta"
    )

    if natija["soni"] == 0:
        await call.message.answer(sarlavha, parse_mode="HTML")
    else:
        qismlar = [sarlavha, ""]
        for u in natija["users"][:30]:
            ism = foydalanuvchi_belgisi(u["username"], u["full_name"], u["telegram_id"])
            vaqt = mahalliy_vaqt(u["first_joined_at"])
            qismlar.append(f"👤 {ism} — 🕒 {vaqt}")
        if natija["soni"] > 30:
            qismlar.append(f"\n… va yana {natija['soni'] - 30} ta foydalanuvchi.")
        await call.message.answer("\n".join(qismlar), parse_mode="HTML")
    await call.answer()


# ===================== ASOSIY MATNLI MENYU =====================

@dp.message()
async def menu_handler(message: types.Message):
    user_id = message.from_user.id
    state = user_state.get(user_id, "main")
    text = message.text or ""

    if state.startswith("ovoz_kutilmoqda"):
        await message.answer("Iltimos, ovozli xabar yuboring, yoki yuqoridagi 'Kerak emas' tugmasini bosing.")
        return

    # ---------- ASOSIY MENYU ----------
    if state == "main":
        if text == "⭐️ Restoranlar reytingi":
            qismlar = ["⭐️ <b>Restoranlar</b>\n"]
            for restoran in db.get_restaurant_names():
                dishes = db.get_menu_items(restoran=restoran)
                narxlar = [i["narx"] for i in dishes]
                xulosa = db.restaurant_rating_summary(restoran)
                if xulosa["soni"]:
                    reyting = f"⭐ {xulosa['ortacha']} ({xulosa['soni']} ta baho)"
                else:
                    reyting = "Hali baholanmagan"
                qismlar.append(
                    f"🏠 <b>{restoran}</b>\n"
                    f"🍽 {len(dishes)} ta taom | {reyting}\n"
                    f"💰 {narxni_formatlash(min(narxlar))} — {narxni_formatlash(max(narxlar))}\n"
                    f"🧾 {usluga_matni(restoran)}\n"
                    f"📍 {manzil_matni(restoran)}"
                )
            await message.answer("\n\n".join(qismlar), parse_mode="HTML", reply_markup=asosiy_menu(user_id))

        elif text == "🍽 Taomlar reytingi":
            barcha = db.get_all_menu_items()
            baholangan = [(item, db.get_ratings(item["id"])) for item in barcha]
            baholangan = [(item, b) for item, b in baholangan if b]
            if not baholangan:
                await message.answer(
                    "🍽 Hozircha hech qanday taom baholanmagan.\n"
                    "Taomlarni ko'rib, birinchi bo'lib baho bering!",
                    reply_markup=asosiy_menu(user_id)
                )
            else:
                baholangan.sort(key=lambda x: sum(x[1]) / len(x[1]), reverse=True)
                qismlar = ["🍽 <b>Eng yuqori baholangan taomlar</b>\n"]
                for item, baholar in baholangan[:10]:
                    ortacha = sum(baholar) / len(baholar)
                    qismlar.append(
                        f"🍽 <b>{item['taom']}</b> ({item['restoran']})\n"
                        f"⭐ {ortacha:.1f} ({len(baholar)} ta baho) · 💰 {narxni_formatlash(item['narx'])}"
                    )
                await message.answer("\n\n".join(qismlar), parse_mode="HTML", reply_markup=asosiy_menu(user_id))

        elif text == "🍲 Nima yemoqchisiz?":
            user_state[user_id] = "turkumlar"
            await message.answer("Qaysi turkum sizni qiziqtiradi?", reply_markup=turkumlar_menu())

        elif text == "🏠 Restoranlar":
            user_state[user_id] = "restoranlar"
            await message.answer("Qaysi restoran sizni qiziqtiradi?", reply_markup=restoranlar_menu())

        elif text == "🔍 Taom nomini qidirish":
            user_state[user_id] = "qidiruv"
            await message.answer("Taom nomini yozing (masalan: shashlik, baliq, chay):", reply_markup=orqaga_menu())

        elif text == "🧮 Taxminiy hisob-kitob":
            user_state[user_id] = "hisob_restoran_tanlash"
            await message.answer(
                "🧮 Taxminiy hisob-kitob\n\nQaysi restoran/ovqatlanish maskani uchun hisoblaymiz?",
                reply_markup=hisob_restoranlar_menu()
            )

        elif text == "📞 Biz bilan bog'lanish":
            await message.answer(BOGLANISH_TEXT, reply_markup=asosiy_menu(user_id))

        elif text == "ℹ️ Bot haqida":
            await message.answer(BOT_HAQIDA_TEXT, parse_mode="HTML", reply_markup=asosiy_menu(user_id))

        elif text == "🌐 Ilovada ochish":
            pass  # web_app tugmasi Telegram tomonidan avtomatik ochiladi

        elif text == "🔐 Admin panel":
            if not is_admin(user_id):
                await message.answer("Bu bo'lim faqat administrator uchun mavjud.", reply_markup=asosiy_menu(user_id))
            else:
                jami = db.get_total_users_count()
                faol = db.get_active_users_count()
                await message.answer(
                    f"🔐 <b>Admin panel</b>\n\n"
                    f"👥 Jami foydalanuvchilar: <b>{jami}</b>\n"
                    f"✅ Hozir faol (botni bloklamagan): <b>{faol}</b>\n\n"
                    f"Quyidagilardan birini tanlang:",
                    parse_mode="HTML",
                    reply_markup=admin_panel_keyboard(),
                )

        else:
            await message.answer("Iltimos, quyidagi tugmalardan birini tanlang 👇", reply_markup=asosiy_menu(user_id))

    # ---------- TURKUMLAR MENYUSI (barcha restoranlar bo'yicha) ----------
    elif state == "turkumlar":
        if text == "0️⃣ Orqaga":
            user_state[user_id] = "main"
            await message.answer("Asosiy menyu:", reply_markup=asosiy_menu(user_id))
        elif text in db.get_categories():
            taomlar = db.get_menu_items(turkum=text)
            await message.answer(f"📂 <b>{text}</b> bo'limidagi taomlar:", parse_mode="HTML", reply_markup=turkumlar_menu())
            for item in taomlar:
                await message.answer(taom_card_matni(item), parse_mode="HTML", reply_markup=taom_inline_keyboard(item))
        else:
            await message.answer("Iltimos, quyidagi turkumlardan birini tanlang 👇", reply_markup=turkumlar_menu())

    # ---------- RESTORANLAR RO'YXATI ----------
    elif state == "restoranlar":
        if text == "0️⃣ Orqaga":
            user_state[user_id] = "main"
            await message.answer("Asosiy menyu:", reply_markup=asosiy_menu(user_id))
        elif text in db.get_restaurant_names():
            user_selected_restoran[user_id] = text
            user_state[user_id] = "restoran_turkumlar"
            await message.answer(
                f"🏠 <b>{text}</b>\n"
                f"📍 {manzil_matni(text)}\n"
                f"🧾 {usluga_matni(text)}",
                parse_mode="HTML",
                reply_markup=manzil_xarita_keyboard(text)
            )
            await message.answer(
                "Qaysi turkumni ko'rmoqchisiz?",
                reply_markup=restoran_turkumlar_menu(text)
            )
        else:
            await message.answer("Iltimos, quyidagi restoranlardan birini tanlang 👇", reply_markup=restoranlar_menu())

    # ---------- TANLANGAN RESTORANNING TURKUMLARI ----------
    elif state == "restoran_turkumlar":
        restoran = user_selected_restoran.get(user_id)
        if text == "0️⃣ Orqaga":
            user_state[user_id] = "restoranlar"
            await message.answer("Qaysi restoran sizni qiziqtiradi?", reply_markup=restoranlar_menu())
        elif restoran and text in db.get_restaurant_categories(restoran):
            taomlar = db.get_menu_items(restoran=restoran, turkum=text)
            await message.answer(
                f"🏠 {restoran}\n📂 <b>{text}</b> bo'limidagi taomlar:",
                parse_mode="HTML",
                reply_markup=restoran_turkumlar_menu(restoran)
            )
            for item in taomlar:
                await message.answer(taom_card_matni(item), parse_mode="HTML", reply_markup=taom_inline_keyboard(item))
        else:
            markup = restoran_turkumlar_menu(restoran) if restoran else restoranlar_menu()
            await message.answer("Iltimos, quyidagi turkumlardan birini tanlang 👇", reply_markup=markup)

    # ---------- TAXMINIY HISOB: RESTORAN TANLASH ----------
    elif state == "hisob_restoran_tanlash":
        if text == "0️⃣ Bekor qilish":
            hisob_savat.pop(user_id, None)
            user_state[user_id] = "main"
            await message.answer("Asosiy menyu:", reply_markup=asosiy_menu(user_id))
        elif text in db.get_restaurant_names():
            hisob_savat[user_id] = {"restoran": text, "items": {}}
            user_state[user_id] = "hisob_faol"
            taomlar = db.get_menu_items(restoran=text)
            await message.answer(
                f"🏠 <b>{text}</b>\nTaomni tanlang (➕ tugmasini bosing):",
                parse_mode="HTML",
                reply_markup=hisob_taomlar_keyboard(taomlar)
            )
        else:
            await message.answer("Iltimos, ro'yxatdan restoran tanlang 👇", reply_markup=hisob_restoranlar_menu())

    # ---------- TAXMINIY HISOB: FAOL (inline tugmalar orqali boshqariladi) ----------
    elif state == "hisob_faol":
        await message.answer("Iltimos, yuqoridagi ➕ tugmalaridan foydalaning, yoki asosiy menyuga qayting.",
                              reply_markup=asosiy_menu(user_id))

    # ---------- TAXMINIY HISOB: MIQDOR KUTILMOQDA (qo'shish yoki tahrirlash) ----------
    elif state == "hisob_miqdor_kutilmoqda":
        kutilayotgan = hisob_miqdor_kutilayotgan.get(user_id)
        if not kutilayotgan:
            user_state[user_id] = "main"
            await message.answer("Xatolik yuz berdi, qaytadan urinib ko'ring.", reply_markup=asosiy_menu(user_id))
            return
        ok, natija = miqdorni_ayirish(text)
        if not ok:
            await message.answer(natija)
            return

        taom_id = kutilayotgan["taom_id"]
        taom = db.menu_item_by_id(taom_id)
        savat = hisob_savat.setdefault(user_id, {"restoran": taom["restoran"], "items": {}})

        if kutilayotgan["rejim"] == "tahrirlash":
            if taom_id in savat["items"]:
                savat["items"][taom_id]["miqdor"] = natija
        else:
            if taom_id in savat["items"]:
                savat["items"][taom_id]["miqdor"] += natija
            else:
                savat["items"][taom_id] = {"taom": taom["taom"], "narx": taom["narx"], "miqdor": natija}

        hisob_miqdor_kutilayotgan.pop(user_id, None)
        user_state[user_id] = "hisob_faol"
        taomlar = db.get_menu_items(restoran=savat["restoran"])
        await message.answer("✅ Qo'shildi!\n\n" + hisob_savat_matni(user_id), parse_mode="HTML")
        await message.answer("Yana taom qo'shasizmi?", reply_markup=hisob_taomlar_keyboard(taomlar))

    # ---------- QIDIRUV MENYUSI ----------
    elif state == "qidiruv":
        if text == "0️⃣ Orqaga":
            user_state[user_id] = "main"
            await message.answer("Asosiy menyu:", reply_markup=asosiy_menu(user_id))
        else:
            natijalar = db.search_menu(text)
            if not natijalar:
                await message.answer(
                    f"'{text}' bo'yicha hech narsa topilmadi 😔\n"
                    "Boshqa nom bilan qidirib ko'ring yoki «0️⃣ Orqaga» tugmasini bosing.",
                    reply_markup=orqaga_menu()
                )
            else:
                await message.answer(f"🔍 '{text}' bo'yicha {len(natijalar)} ta natija:", reply_markup=orqaga_menu())
                for item in natijalar:
                    await message.answer(taom_card_matni(item), parse_mode="HTML", reply_markup=taom_inline_keyboard(item))

    # ---------- IZOH: SANA TAQVIMDAN TANLANMOQDA ----------
    elif state == "izoh_sana_tanlanmoqda":
        await message.answer("Iltimos, yuqoridagi taqvimdan kunni tanlang (matn kiritish shart emas).")

    # ---------- IZOH: MEDIA KUTILMOQDA (matn yozsa eslatamiz) ----------
    elif state == "izoh_media_kutilmoqda":
        review = pending_review.get(user_id)
        taom_id = review["taom_id"] if review else None
        await message.answer(
            "Rasm yoki video yuboring, yoki yuqoridagi 'O'tkazib yuborish' tugmasini bosing.",
            reply_markup=skip_media_keyboard(taom_id) if taom_id else None
        )

    # ---------- IZOH: MATN KUTILMOQDA ----------
    elif state == "izoh_matn_kutilmoqda":
        review = pending_review.get(user_id)
        if review is None:
            user_state[user_id] = "main"
            await message.answer("Xatolik yuz berdi, qaytadan urinib ko'ring.", reply_markup=asosiy_menu(user_id))
            return
        if not izoh_matni_yaroqlimi(text):
            await message.answer(
                "Iltimos, kamida 2-3 ta ma'noli so'zdan iborat izoh yozing.\n"
                "Faqat raqam yoki bitta harfni takrorlash qabul qilinmaydi."
            )
            return
        review["matn"] = text
        taom_id = review["taom_id"]
        item = db.menu_item_by_id(taom_id)
        media_belg = "📎 Fayl biriktirilgan" if review["media_file_id"] else "Fayl biriktirilmagan"
        tasdiq_matni = (
            f"Quyidagi izohni saqlaymizmi?\n\n"
            f"🍽 {item['taom']}\n"
            f"📅 Tashrif: {review['sana']}\n"
            f"💬 {review['matn']}\n"
            f"{media_belg}"
        )
        user_state[user_id] = "izoh_tasdiq_kutilmoqda"
        await message.answer(tasdiq_matni, reply_markup=izoh_tasdiq_keyboard(taom_id))

    # ---------- IZOH: TASDIQ KUTILMOQDA ----------
    elif state == "izoh_tasdiq_kutilmoqda":
        await message.answer("Iltimos, yuqoridagi «✅ Saqlash» yoki «❌ Bekor qilish» tugmasini bosing.")

    else:
        user_state[user_id] = "main"
        await message.answer("Asosiy menyuga qaytdik:", reply_markup=asosiy_menu(user_id))


async def main():
    db.init_db()
    db.seed_menu_if_empty()
    db.sync_restaurant_info()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
