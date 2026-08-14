from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, KeyboardButtonRequestUser
from aiogram.utils.keyboard import InlineKeyboardBuilder

def main_reply_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Menyu")]
        ],
        resize_keyboard=True
    )

def menu_inline(is_premium: bool = False):
    kb = InlineKeyboardBuilder()
    if not is_premium:
        kb.button(text="⭐ Premium olish", callback_data="buy_premium")
    kb.button(text="📊 Mening holatim", callback_data="my_stats")
    kb.button(text="ℹ️ Yordam", callback_data="help")
    kb.adjust(1)
    return kb.as_markup()

def channels_keyboard(channels: list):
    kb = InlineKeyboardBuilder()
    for ch_id, title, link in channels:
        url = link if link else f"https://t.me/{str(ch_id).lstrip('@').lstrip('-100')}"
        kb.button(text=f"📢 {title}", url=url)
    kb.button(text="✅ Tekshirish", callback_data="check_subs")
    kb.adjust(1)
    return kb.as_markup()

def premium_plans():
    kb = InlineKeyboardBuilder()
    kb.button(text="1️⃣ 1 oylik — 30.000 so‘m", callback_data="premium_1")
    kb.button(text="2️⃣ 2 oylik — 50.000 so‘m", callback_data="premium_2")
    kb.button(text="3️⃣ 3 oylik — 70.000 so‘m", callback_data="premium_3")
    kb.button(text="🔙 Orqaga", callback_data="back_menu")
    kb.adjust(1)
    return kb.as_markup()

def admin_activate_kb(user_id: int, months: int):
    kb = InlineKeyboardBuilder()
    kb.button(text=f"✅ {months} oylik berish", callback_data=f"activate_{user_id}_{months}")
    kb.button(text="❌ Rad etish", callback_data=f"reject_{user_id}")
    kb.adjust(1)
    return kb.as_markup()

def admin_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Majburiy kanal", callback_data="admin_add_channel")
    kb.button(text="➖ Kanal o‘chirish", callback_data="admin_remove_channel")
    kb.button(text="📁 Hamma uchun kanal", callback_data="admin_set_public_storage")
    kb.button(text="💎 Premium kanal", callback_data="admin_set_premium_storage")
    kb.button(text="🎥 Kino qo‘shish", callback_data="admin_add_video")
    kb.button(text="📢 Ommaviy xabar", callback_data="admin_broadcast")
    kb.button(text="📊 Statistika", callback_data="admin_stats")
    kb.button(text="💰 Daromad", callback_data="admin_income")
    kb.adjust(2)
    return kb.as_markup()

def add_video_type_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="🌍 Hamma uchun", callback_data="add_video_public")
    kb.button(text="💎 Faqat Premium", callback_data="add_video_premium")
    kb.button(text="🔙 Orqaga", callback_data="admin_back")
    kb.adjust(1)
    return kb.as_markup()

def cancel_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
        resize_keyboard=True
    )