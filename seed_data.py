"""
Boshlang'ich menyu ma'lumotlari.

MUHIM: Bu ro'yxat faqat baza BO'SH bo'lganda, birinchi marta ishga tushirilganda
bazaga yoziladi (database.py -> seed_menu_if_empty). Bot ishga tushgach, taomlarni
qo'shish/o'zgartirish/o'chirish endi shu faylni emas, balki bazani tahrirlash orqali
qilinadi (masalan admin panel yoki to'g'ridan-to'g'ri SQL orqali).
"""

MENU = [
    {"restoran": "Chayxona Davdon Baliq", "turkum": "Taomlar", "taom": "Shor kabob (1kg)", "narx": 200000},
    {"restoran": "Chayxona Davdon Baliq", "turkum": "Taomlar", "taom": "Sousga kabob(1kg)", "narx": 210000},
    {"restoran": "Chayxona Davdon Baliq", "turkum": "Taomlar", "taom": "Yurak bagr kabob(1kg)", "narx": 200000},
    {"restoran": "Chayxona Davdon Baliq", "turkum": "Taomlar", "taom": "Gosh say(1kg)", "narx": 200000},
    {"restoran": "Chayxona Davdon Baliq", "turkum": "Taomlar", "taom": "Dimlama baliq(1kg)", "narx": 120000},
    {"restoran": "Chayxona Davdon Baliq", "turkum": "Taomlar", "taom": "Xoroz chixambil", "narx": 300000},
    {"restoran": "Chayxona Davdon Baliq", "turkum": "Taomlar", "taom": "Qorin tuyoq shorva", "narx": 450000},
    {"restoran": "Chayxona Davdon Baliq", "turkum": "Taomlar", "taom": "Zigrik kabob(1kg)", "narx": 200000},

    {"restoran": "Chayxona Davdon Baliq", "turkum": "Baliqlar", "taom": "Qovurma sazan(1kg)", "narx": 90000},
    {"restoran": "Chayxona Davdon Baliq", "turkum": "Baliqlar", "taom": "Setka baliq(1kg)", "narx": 100000},
    {"restoran": "Chayxona Davdon Baliq", "turkum": "Baliqlar", "taom": "Laqqa baliq(1kg)", "narx": 200000},
    {"restoran": "Chayxona Davdon Baliq", "turkum": "Baliqlar", "taom": "Dimlama baliq(1kg)", "narx": 120000},
    {"restoran": "Chayxona Davdon Baliq", "turkum": "Baliqlar", "taom": "Piyostriy baliq(1kg)", "narx": 90000},
    {"restoran": "Chayxona Davdon Baliq", "turkum": "Baliqlar", "taom": "Sousga baliq(1kg)", "narx": 90000},
    {"restoran": "Chayxona Davdon Baliq", "turkum": "Baliqlar", "taom": "Unsiz baliq(1kg)", "narx": 90000},
    {"restoran": "Chayxona Davdon Baliq", "turkum": "Baliqlar", "taom": "Iqra", "narx": 70000},

    {"restoran": "Chayxona Davdon Baliq", "turkum": "Salatlar", "taom": "Achchuk chuchuk salat", "narx": 15000},
    {"restoran": "Chayxona Davdon Baliq", "turkum": "Salatlar", "taom": "Grubi salat", "narx": 15000},
    {"restoran": "Chayxona Davdon Baliq", "turkum": "Salatlar", "taom": "Salyoni salat", "narx": 15000},
    {"restoran": "Chayxona Davdon Baliq", "turkum": "Salatlar", "taom": "3 kunlik pomidor", "narx": 10000},

    {"restoran": "Chayxona Davdon Baliq", "turkum": "Nonlar", "taom": "Patir", "narx": 15000},
    {"restoran": "Chayxona Davdon Baliq", "turkum": "Nonlar", "taom": "Chorak", "narx": 10000},
    {"restoran": "Chayxona Davdon Baliq", "turkum": "Nonlar", "taom": "Buxonka", "narx": 5000},

    {"restoran": "Chayxona Davdon Baliq", "turkum": "Shashliklar", "taom": "G'ijduvon shashlik", "narx": 15000},
    {"restoran": "Chayxona Davdon Baliq", "turkum": "Shashliklar", "taom": "O'rdak shashlik", "narx": 20000},
    {"restoran": "Chayxona Davdon Baliq", "turkum": "Shashliklar", "taom": "Qusqovoy jiz shashlik", "narx": 25000},
    {"restoran": "Chayxona Davdon Baliq", "turkum": "Shashliklar", "taom": "Qanot shashlik", "narx": 20000},

    {"restoran": "Chayxona Davdon Baliq", "turkum": "Chay", "taom": "Limon chay", "narx": 15000},
    {"restoran": "Chayxona Davdon Baliq", "turkum": "Chay", "taom": "Ko'k chay", "narx": 5000},
    {"restoran": "Chayxona Davdon Baliq", "turkum": "Chay", "taom": "Qora chay", "narx": 5000},
    {"restoran": "Chayxona Davdon Baliq", "turkum": "Chay", "taom": "Mevali chay", "narx": 10000},

    {"restoran": "Chayxona Davdon Baliq", "turkum": "Ichimliklar", "taom": "Coca cola", "narx": 20000},
    {"restoran": "Chayxona Davdon Baliq", "turkum": "Ichimliklar", "taom": "Fanta", "narx": 20000},
    {"restoran": "Chayxona Davdon Baliq", "turkum": "Ichimliklar", "taom": "Sprite", "narx": 20000},
    {"restoran": "Chayxona Davdon Baliq", "turkum": "Ichimliklar", "taom": "Meva sharbati", "narx": 20000},
    {"restoran": "Chayxona Davdon Baliq", "turkum": "Ichimliklar", "taom": "Moxito", "narx": 20000},
    {"restoran": "Chayxona Davdon Baliq", "turkum": "Ichimliklar", "taom": "Flesh", "narx": 15000},
    {"restoran": "Chayxona Davdon Baliq", "turkum": "Ichimliklar", "taom": "Gorilla", "narx": 18000},
    {"restoran": "Chayxona Davdon Baliq", "turkum": "Ichimliklar", "taom": "Ayron", "narx": 15000},
    {"restoran": "Chayxona Davdon Baliq", "turkum": "Ichimliklar", "taom": "Toshkent suv", "narx": 10000},
    {"restoran": "Chayxona Davdon Baliq", "turkum": "Ichimliklar", "taom": "Gazli suv", "narx": 10000},
    {"restoran": "Chayxona Davdon Baliq", "turkum": "Ichimliklar", "taom": "Gazlanmagan suv", "narx": 10000},

    {"restoran": "Chayxona Davdon Baliq", "turkum": "Mevalar", "taom": "Meva asorti", "narx": 45000},

    # ===================== MALIKA MILLIY TAOMLARI =====================

    {"restoran": "Malika milliy taomlari", "turkum": "Baliq taomlar", "taom": "Qovurma baliq(1kg)", "narx": 100000},
    {"restoran": "Malika milliy taomlari", "turkum": "Baliq taomlar", "taom": "Dimlama baliq(1kg)", "narx": 100000},
    {"restoran": "Malika milliy taomlari", "turkum": "Baliq taomlar", "taom": "Setka baliq(1kg)", "narx": 110000},
    {"restoran": "Malika milliy taomlari", "turkum": "Baliq taomlar", "taom": "Falga baliq(1kg)", "narx": 110000},

    {"restoran": "Malika milliy taomlari", "turkum": "Mangal taomlar", "taom": "G'ijduvon shashlik", "narx": 18000},
    {"restoran": "Malika milliy taomlari", "turkum": "Mangal taomlar", "taom": "Mol kuskovoy shashlik", "narx": 26000},
    {"restoran": "Malika milliy taomlari", "turkum": "Mangal taomlar", "taom": "Quy kuskovoy shashlik", "narx": 26000},
    {"restoran": "Malika milliy taomlari", "turkum": "Mangal taomlar", "taom": "Mega kuskovoy shashlik", "narx": 120000},
    {"restoran": "Malika milliy taomlari", "turkum": "Mangal taomlar", "taom": "Setka kabob", "narx": 270000},
    {"restoran": "Malika milliy taomlari", "turkum": "Mangal taomlar", "taom": "Quy koreyka", "narx": 240000},
    {"restoran": "Malika milliy taomlari", "turkum": "Mangal taomlar", "taom": "Mega Gijduvon shashlik", "narx": 110000},
    {"restoran": "Malika milliy taomlari", "turkum": "Mangal taomlar", "taom": "Tovuq qanot shashlik", "narx": 25000},

    {"restoran": "Malika milliy taomlari", "turkum": "Salatlar", "taom": "Svejiy salat", "narx": 15000},
    {"restoran": "Malika milliy taomlari", "turkum": "Salatlar", "taom": "Fransuzskiy salat", "narx": 40000},
    {"restoran": "Malika milliy taomlari", "turkum": "Salatlar", "taom": "Achchiq-chuchuk salat", "narx": 15000},
    {"restoran": "Malika milliy taomlari", "turkum": "Salatlar", "taom": "Malika salat", "narx": 48000},
    {"restoran": "Malika milliy taomlari", "turkum": "Salatlar", "taom": "Mavsum salat", "narx": 30000},
    {"restoran": "Malika milliy taomlari", "turkum": "Salatlar", "taom": "Grekcheskiy salat", "narx": 40000},
    {"restoran": "Malika milliy taomlari", "turkum": "Salatlar", "taom": "Mujskoy kapriz salat", "narx": 42000},
    {"restoran": "Malika milliy taomlari", "turkum": "Salatlar", "taom": "Indeyka s gribami salat", "narx": 40000},
    {"restoran": "Malika milliy taomlari", "turkum": "Salatlar", "taom": "Dollar salat", "narx": 45000},
    {"restoran": "Malika milliy taomlari", "turkum": "Salatlar", "taom": "Shef salat", "narx": 35000},
    {"restoran": "Malika milliy taomlari", "turkum": "Salatlar", "taom": "Griby s myasom salat", "narx": 45000},
    {"restoran": "Malika milliy taomlari", "turkum": "Salatlar", "taom": "Gribnoy salat", "narx": 35000},
    {"restoran": "Malika milliy taomlari", "turkum": "Salatlar", "taom": "Ovoshnoy salat", "narx": 30000},
    {"restoran": "Malika milliy taomlari", "turkum": "Salatlar", "taom": "3 kunlik salat", "narx": 12000},
    {"restoran": "Malika milliy taomlari", "turkum": "Salatlar", "taom": "Yaponskiy salat", "narx": 45000},
    {"restoran": "Malika milliy taomlari", "turkum": "Salatlar", "taom": "Sezar salat", "narx": 42000},
    {"restoran": "Malika milliy taomlari", "turkum": "Salatlar", "taom": "Suzma", "narx": 15000},

    {"restoran": "Malika milliy taomlari", "turkum": "Xamirli taomlar", "taom": "Tuxum barak(1 porsiya)", "narx": 35000},
    {"restoran": "Malika milliy taomlari", "turkum": "Xamirli taomlar", "taom": "Qo'tir barak(1 porsiya)", "narx": 25000},
    {"restoran": "Malika milliy taomlari", "turkum": "Xamirli taomlar", "taom": "Kadi barak(1 porsiya)", "narx": 70000},
    {"restoran": "Malika milliy taomlari", "turkum": "Xamirli taomlar", "taom": "Kuk barak(1 porsiya)", "narx": 35000},
    {"restoran": "Malika milliy taomlari", "turkum": "Xamirli taomlar", "taom": "Barak assorti katta", "narx": 170000},
    {"restoran": "Malika milliy taomlari", "turkum": "Xamirli taomlar", "taom": "Barak assorti kichik", "narx": 85000},
    {"restoran": "Malika milliy taomlari", "turkum": "Xamirli taomlar", "taom": "Qapshirma", "narx": 13000},
    {"restoran": "Malika milliy taomlari", "turkum": "Xamirli taomlar", "taom": "Somsa", "narx": 15000},
    {"restoran": "Malika milliy taomlari", "turkum": "Xamirli taomlar", "taom": "Go'mma", "narx": 13000},
    {"restoran": "Malika milliy taomlari", "turkum": "Xamirli taomlar", "taom": "Besh barmoq", "narx": 360000},

    {"restoran": "Malika milliy taomlari", "turkum": "Assorti taomlar", "taom": "Mega assorti kichkina", "narx": 270000},
    {"restoran": "Malika milliy taomlari", "turkum": "Assorti taomlar", "taom": "Mega assorti katta", "narx": 370000},
    {"restoran": "Malika milliy taomlari", "turkum": "Assorti taomlar", "taom": "Malika assorti katta", "narx": 430000},
    {"restoran": "Malika milliy taomlari", "turkum": "Assorti taomlar", "taom": "Steyk assorti", "narx": 260000},
    {"restoran": "Malika milliy taomlari", "turkum": "Assorti taomlar", "taom": "Shashlik assorti katta", "narx": 430000},
    {"restoran": "Malika milliy taomlari", "turkum": "Assorti taomlar", "taom": "Shashlik assorti kichik", "narx": 220000},
    {"restoran": "Malika milliy taomlari", "turkum": "Assorti taomlar", "taom": "Malika assorti kichik", "narx": 330000},

    {"restoran": "Malika milliy taomlari", "turkum": "Go'shtli taomlar", "taom": "Tushonka(1kg)", "narx": 210000},
    {"restoran": "Malika milliy taomlari", "turkum": "Go'shtli taomlar", "taom": "Qaymoqa dil(1kg)", "narx": 230000},
    {"restoran": "Malika milliy taomlari", "turkum": "Go'shtli taomlar", "taom": "Sho'r kabob(1kg)", "narx": 220000},
    {"restoran": "Malika milliy taomlari", "turkum": "Go'shtli taomlar", "taom": "Sariyog'a dil(1kg)", "narx": 230000},
    {"restoran": "Malika milliy taomlari", "turkum": "Go'shtli taomlar", "taom": "Jigar kabob(1kg)", "narx": 220000},
    {"restoran": "Malika milliy taomlari", "turkum": "Go'shtli taomlar", "taom": "Zigirik(1kg)", "narx": 210000},
    {"restoran": "Malika milliy taomlari", "turkum": "Go'shtli taomlar", "taom": "Qozon kabob(1kg)", "narx": 220000},
    {"restoran": "Malika milliy taomlari", "turkum": "Go'shtli taomlar", "taom": "Qaymoqa kabob(1kg)", "narx": 230000},

    {"restoran": "Malika milliy taomlari", "turkum": "Issiq taomlar", "taom": "Sari yog'a tovuq(1 porsiya)", "narx": 80000},
    {"restoran": "Malika milliy taomlari", "turkum": "Issiq taomlar", "taom": "Qovurma lag'mon(1 porsiya)", "narx": 75000},
    {"restoran": "Malika milliy taomlari", "turkum": "Issiq taomlar", "taom": "Uyg'ur lag'mon(1 porsiya)", "narx": 70000},
    {"restoran": "Malika milliy taomlari", "turkum": "Issiq taomlar", "taom": "Go'sht say", "narx": 100000},
    {"restoran": "Malika milliy taomlari", "turkum": "Issiq taomlar", "taom": "Qaymoqa kabob (porsiya)", "narx": 80000},
    {"restoran": "Malika milliy taomlari", "turkum": "Issiq taomlar", "taom": "Tuya qush dimlama", "narx": 220000},
    {"restoran": "Malika milliy taomlari", "turkum": "Issiq taomlar", "taom": "Sho'r kabob (1 porsiya)", "narx": 75000},

    {"restoran": "Malika milliy taomlari", "turkum": "Suyuq taomlar", "taom": "Sho'rva barak(1 porsiya)", "narx": 35000},
    {"restoran": "Malika milliy taomlari", "turkum": "Suyuq taomlar", "taom": "Tiftel sho'rva(1 porsiya)", "narx": 35000},
    {"restoran": "Malika milliy taomlari", "turkum": "Suyuq taomlar", "taom": "Unoshi(1 porsiya)", "narx": 25000},
    {"restoran": "Malika milliy taomlari", "turkum": "Suyuq taomlar", "taom": "Mastava(1 porsiya)", "narx": 35000},
    {"restoran": "Malika milliy taomlari", "turkum": "Suyuq taomlar", "taom": "Osma shurva(1 porsiya)", "narx": 30000},
    {"restoran": "Malika milliy taomlari", "turkum": "Suyuq taomlar", "taom": "Bedana shurva(1 porsiya)", "narx": 45000},
]

# Har bir restoranda olinadigan xizmat haqi (usluga), foizda.
RESTORAN_USLUGA = {
    "Chayxona Davdon Baliq": 10,
    "Malika milliy taomlari": 10,
}

# Restoranlar manzili.
RESTORAN_MANZIL = {
    "Chayxona Davdon Baliq": "Qo'shko'pir tuman",
    "Malika milliy taomlari": "Qo'shko'pir tuman",
}

# Restoranning Google Maps'dagi aniq joylashuv havolasi (mavjud bo'lsa,
# botdagi "Xaritada ko'rish" tugmasi aynan shu havolaga olib boradi).
RESTORAN_XARITA = {
    "Chayxona Davdon Baliq": "https://maps.app.goo.gl/LrikePsK9yoSsDPw6",
    "Malika milliy taomlari": "https://maps.app.goo.gl/nJhxcmWJnFX555pf9",
}
