"""
Umumiy sozlamalar. Bot ham, API (backend) ham shu fayldan foydalanadi,
shunday qilib ikkalasi bir xil bazaga ulanadi.

Barcha qiymatlarni environment variable orqali ham berish mumkin,
shunda kodni o'zgartirmasdan serverda sozlash oson bo'ladi.
"""

import os

# ----- Telegram bot -----
TOKEN = os.environ.get("BOT_TOKEN", "SIZNING_TOKENINGIZ")

# Faqat shu Telegram ID (raqamli) uchun "Admin panel" ko'rinadi -
# kirish/chiqish tarixi va yangi foydalanuvchilar statistikasi shu yerdan kuzatiladi.
# Bir nechta admin kerak bo'lsa, vergul bilan ajratib yozing: "340525338,111111111"
ADMIN_IDS = [
    int(x.strip()) for x in os.environ.get("ADMIN_IDS", "340525338").split(",") if x.strip()
]

# Mini App (veb-ilova) qaysi manzilda joylashganini shu yerga yozing.
# Masalan: https://tanla-app.example.com
# Bo'sh qoldirsangiz, botdagi "Ilovada ochish" tugmasi ko'rsatilmaydi.
WEBAPP_URL = os.environ.get("WEBAPP_URL", "")

# ----- Baza (Database) -----
# Ikkalasi (bot.py va api.py) ham AYNAN shu faylga ulanishi kerak,
# aks holda ma'lumotlar bo'linib qoladi.
DATABASE_PATH = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "tanla.db"))
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# ----- API (backend) -----
# Mini App shu manzil orqali ma'lumot oladi/yuboradi.
API_HOST = os.environ.get("API_HOST", "0.0.0.0")
API_PORT = int(os.environ.get("API_PORT", "8000"))

# Ishlab chiqish paytida barcha manzillarga ruxsat beramiz (*),
# lekin serverga chiqarganda faqat Mini App domenini yozing, masalan:
# CORS_ORIGINS = ["https://tanla-app.example.com"]
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*").split(",")
