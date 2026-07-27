# Tanla — bot + ilova, umumiy baza

Bu loyihada Telegram bot va veb-ilova (Telegram Mini App) **bitta umumiy bazadan**
(`tanla.db`, SQLite) foydalanadi. Kimdir botda taomga baho bersa yoki izoh qoldirsa,
xuddi shu baho/izoh ilovada ham darhol ko'rinadi — va aksincha.

## Fayllar tuzilishi

```
tanla/
├── config.py        # sozlamalar (token, baza yo'li, API manzili)
├── seed_data.py      # boshlang'ich menyu (faqat 1-marta bazaga yozish uchun)
├── database.py       # UMUMIY baza qatlami — bot ham, API ham shundan foydalanadi
├── bot.py             # Telegram bot (bazaga to'g'ridan-to'g'ri ulanadi)
├── api.py             # FastAPI backend (Mini App shu orqali bazaga ulanadi)
├── webapp/
│   └── index.html    # Mini App (veb-ilova) — bitta HTML fayl
├── requirements.txt
└── tanla.db           # birinchi ishga tushirishda avtomatik yaratiladi
```

## 1-qadam: kutubxonalarni o'rnatish

```bash
pip install -r requirements.txt --break-system-packages
```

## 2-qadam: sozlash

`config.py` faylida yoki muhit o'zgaruvchilari (environment variables) orqali:

- `BOT_TOKEN` — BotFather'dan olingan token
- `WEBAPP_URL` — Mini App joylashgan manzil (masalan `https://sizning-domen.uz`).
  Buni keyingi qadamda to'ldirasiz.

```bash
export BOT_TOKEN="123456:AA...."
```

## 3-qadam: botni ishga tushirish

```bash
python3 bot.py
```

Birinchi ishga tushishda `tanla.db` avtomatik yaratiladi va `seed_data.py`
dagi menyu bilan to'ldiriladi. Bot hoziroq to'liq ishlaydi — ilova shart emas.

## 4-qadam: veb-ilova (Mini App) uchun backend'ni ishga tushirish

```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```

Bu bot bilan **bir xil** `tanla.db` fayliga ulanadi (bir xil papkada ishga
tushirilsa, avtomatik shunday bo'ladi).

## 5-qadam: Mini App'ni joylashtirish (hosting)

`webapp/index.html` — bu oddiy statik HTML fayl. Uni istalgan bepul statik
hosting'ga joylashtirish mumkin (masalan GitHub Pages, Netlify, Vercel, yoki
o'z serveringiz). Muhim shart: **HTTPS bo'lishi shart** (Telegram Mini App
faqat https manzillarni qabul qiladi).

Joylashtirgach:
1. `webapp/index.html` faylining boshidagi `API_BASE` o'zgaruvchisiga
   backend manzilini yozing (masalan `"https://tanla-api.example.com"`).
2. `config.py` dagi `WEBAPP_URL` ga Mini App manzilini yozing
   (masalan `"https://sizning-username.github.io/tanla"`).
3. Botni qayta ishga tushiring — asosiy menyuda "🌐 Ilovada ochish" tugmasi
   paydo bo'ladi.

Ixtiyoriy: @BotFather orqali `/mybots` → botingiz → **Bot Settings** →
**Menu Button** bo'limida ham shu havolani ko'rsatsangiz, foydalanuvchilar
Mini App'ni bot chatining pastki chap tugmasidan ham ocha oladi.

## Admin panel — kirish/chiqish tarixi va yangi foydalanuvchilar statistikasi

Botga `config.py` (yoki `ADMIN_IDS` muhit o'zgaruvchisi) orqali kiritilgan
Telegram ID uchun asosiy menyuda qo'shimcha **"🔐 Admin panel"** tugmasi
paydo bo'ladi. Boshqa hech bir foydalanuvchi bu tugmani ko'rmaydi.

Admin panelda:

- **🕘 Kirish/chiqish tarixi** — kim qachon botni ishga tushirgani (/start)
  va kim qachon botni bloklab, undan chiqib ketgani (so'nggi 30 ta hodisa,
  vaqti bilan).
- **📈 Yangi foydalanuvchilar** — **Haftalik** (so'nggi 7 kun) yoki
  **Oylik** (so'nggi 30 kun) filtr bilan, shu davrda birinchi marta botga
  kirgan foydalanuvchilar soni va ro'yxati.

Bir nechta administrator kerak bo'lsa:

```bash
export ADMIN_IDS="340525338,111111111"
```

## Ma'lumotlarni ko'chirish haqida eslatma

Eski `malumotlar.json` (agar bo'lsa) avtomatik ko'chirilmaydi — yangi tizim
nol nuqtadan boshlanadi. Agar eski reyting/izohlarni saqlab qolish kerak
bo'lsa, ayting — buning uchun alohida bir martalik ko'chirish (migratsiya)
skripti yozib beraman.

## Kelajakda kengaytirish

- Foydalanuvchi ko'payib, SQLite yetarli bo'lmay qolsa: `config.py` dagi
  `DATABASE_URL` ni PostgreSQL manziliga almashtirish kifoya — `database.py`
  dagi kod o'zgarishsiz ishlayveradi.
- Alohida mobil ilova (Android/iOS) kerak bo'lsa, u ham xuddi shu `api.py`
  backend'iga ulanadi — hech narsa qayta yozilmaydi.
