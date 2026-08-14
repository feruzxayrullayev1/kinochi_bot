from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
import re

from database import (
    add_user, is_premium, get_channels, get_video,
    increment_video_view
)
from keyboards import (
    main_reply_kb, menu_inline, channels_keyboard,
    premium_plans, admin_activate_kb
)
from config import ADMIN_IDS, PREMIUM_PRICES, PAYMENT_CHANNEL

router = Router()


async def check_subscriptions(bot: Bot, user_id: int) -> bool:
    """Foydalanuvchi majburiy kanallarga obuna bo‘lganini tekshiradi"""
    if await is_premium(user_id):
        return True

    channels = await get_channels()
    if not channels:
        return True

    for ch_id, _, _ in channels:
        try:
            member = await bot.get_chat_member(chat_id=ch_id, user_id=user_id)
            if member.status in ("left", "kicked"):
                return False
        except Exception:
            return False
    return True


@router.message(CommandStart())
async def start_handler(message: Message, bot: Bot):
    user = message.from_user
    await add_user(user.id, user.username, user.full_name)

    # Admin bo‘lsa — Admin panel
    if user.id in ADMIN_IDS:
        from keyboards import admin_menu
        await message.answer(
            "🛠 <b>Admin panel</b>\n\nKerakli bo‘limni tanlang:",
            reply_markup=admin_menu(),
            parse_mode="HTML"
        )
        return

    # Oddiy foydalanuvchi
    if await check_subscriptions(bot, user.id):
        await message.answer(
            f"👋 Assalomu alaykum, <b>{user.full_name}</b>!\n\n"
            "🎬 Kodni yozing va filmni oling.\n"
            "Menyu uchun pastdagi <b>📋 Menyu</b> tugmasini bosing.",
            reply_markup=main_reply_kb(),
            parse_mode="HTML"
        )
    else:
        channels = await get_channels()
        await message.answer(
            "⚠️ Botdan foydalanish uchun quyidagi kanallarga obuna bo‘ling:",
            reply_markup=channels_keyboard(channels)
        )


@router.callback_query(F.data == "check_subs")
async def check_subs_handler(callback: CallbackQuery, bot: Bot):
    if await check_subscriptions(bot, callback.from_user.id):
        try:
            await callback.message.delete()
        except:
            pass
        await callback.message.answer(
            "✅ Obuna tasdiqlandi!\n\nKodni yozing yoki «📋 Menyu» tugmasini bosing.",
            reply_markup=main_reply_kb()
        )
    else:
        await callback.answer("❌ Hali barcha kanallarga obuna bo‘lmadingiz!", show_alert=True)


@router.message(F.text == "📋 Menyu")
async def open_menu(message: Message):
    prem = await is_premium(message.from_user.id)
    await message.answer("📋 <b>Menyu</b>:", reply_markup=menu_inline(prem), parse_mode="HTML")


@router.message(F.text.regexp(r"^#?\d+$"))
async def process_code(message: Message, bot: Bot):
    """Foydalanuvchi kod yuborganda ishlaydi"""
    code = re.sub(r"[^\d]", "", message.text.strip())

    # Majburiy obuna tekshiruvi
    if not await check_subscriptions(bot, message.from_user.id):
        channels = await get_channels()
        await message.answer(
            "⚠️ Avval kanallarga obuna bo‘ling:",
            reply_markup=channels_keyboard(channels)
        )
        return

    user_is_prem = await is_premium(message.from_user.id)

    # Bazadan qidiramiz
    video = await get_video(code)

    if not video:
        await message.answer("❌ Bunday kod topilmadi.")
        return

    file_id, caption, is_prem_video = video

    # Premium tekshiruvi
    if is_prem_video and not user_is_prem:
        await message.answer(
            "⭐ Bu film faqat <b>Premium</b> obunachilar uchun!\n\n"
            "Premium olish uchun «📋 Menyu» → «⭐ Premium olish» ni bosing.",
            parse_mode="HTML"
        )
        return

    # Videoni yuborish
    try:
        await bot.send_video(
            chat_id=message.chat.id,
            video=file_id,
            caption=caption or f"🎬 Kod: {code}"
        )
        await increment_video_view(code)
    except Exception as e:
        await message.answer("❌ Videoni yuborishda xatolik yuz berdi.")
        print(f"Send video error: {e}")


@router.callback_query(F.data == "buy_premium")
async def buy_premium(callback: CallbackQuery):
    text = (
        "⭐ <b>Premium obuna</b>\n\n"
        "1️⃣ 1 oylik — <b>30.000 so‘m</b>\n"
        "2️⃣ 2 oylik — <b>50.000 so‘m</b>\n"
        "3️⃣ 3 oylik — <b>70.000 so‘m</b>\n\n"
        "Afzalliklari:\n"
        "• Kanallarga obuna bo‘lish shart emas\n"
        "• Maxsus kodli filmlar\n"
        "• Tezroq xizmat"
    )
    await callback.message.edit_text(text, reply_markup=premium_plans(), parse_mode="HTML")


@router.callback_query(F.data.startswith("premium_"))
async def select_premium(callback: CallbackQuery, bot: Bot):
    months = int(callback.data.split("_")[1])
    price = PREMIUM_PRICES[months]
    user = callback.from_user

    await callback.message.edit_text(
        f"✅ Siz <b>{months} oylik</b> tarifni tanladingiz ({price:,} so‘m).\n\n"
        f"To‘lov uchun kanal:\n{PAYMENT_CHANNEL}\n\n"
        "To‘lov qilgandan so‘ng admin tez orada faollashtiradi.",
        parse_mode="HTML"
    )

    username = f"@{user.username}" if user.username else "Yo‘q"
    admin_text = (
        f"🔔 <b>Yangi Premium so‘rovi</b>\n\n"
        f"👤 {user.full_name}\n"
        f"🆔 <code>{user.id}</code>\n"
        f"🔗 {username}\n"
        f"📅 {months} oylik\n"
        f"💰 {price:,} so‘m"
    )

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                admin_text,
                reply_markup=admin_activate_kb(user.id, months),
                parse_mode="HTML"
            )
        except:
            pass


@router.callback_query(F.data == "back_menu")
async def back_menu(callback: CallbackQuery):
    prem = await is_premium(callback.from_user.id)
    await callback.message.edit_text("📋 <b>Menyu</b>:", reply_markup=menu_inline(prem), parse_mode="HTML")


@router.callback_query(F.data == "my_stats")
async def my_stats(callback: CallbackQuery):
    prem = await is_premium(callback.from_user.id)
    status = "⭐ Premium obunachi" if prem else "Oddiy foydalanuvchi"
    await callback.message.answer(f"📊 Holatingiz: <b>{status}</b>", parse_mode="HTML")


@router.callback_query(F.data == "help")
async def help_handler(callback: CallbackQuery):
    await callback.message.answer(
        "ℹ️ <b>Yordam</b>\n\n"
        "• Kodni to‘g‘ridan-to‘g‘ri yozing (masalan: <code>123</code>)\n"
        "• Menyu orqali Premium olishingiz mumkin\n"
        "• Premium bo‘lsangiz maxsus filmlarni ham olasiz",
        parse_mode="HTML"
    )