import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN topilmadi!")

ADMIN_IDS = [5467496016]          # O'zingizning Telegram ID

# Premium narxlari
PREMIUM_PRICES = {
    1: 30000,   # 1 oy
    2: 50000,   # 2 oy
    3: 70000    # 3 oy
}

# To'lov kanali
PAYMENT_CHANNEL = "https://t.me/MyWorkshub"
