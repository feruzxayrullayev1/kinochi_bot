from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import re

from database import (
    add_channel, remove_channel, get_channels,
    set_storage_channel, get_storage_channel,
    add_video, set_premium, add_payment, get_stats, get_all_users
)
from keyboards import admin_menu, cancel_kb, add_video_type_kb
from config import ADMIN_IDS, PREMIUM_PRICES

router = Router()


class AdminStates(StatesGroup):
    add_channel = State()
    remove_channel = State()
    set_public_storage = State()
    set_premium_storage = State()
    add_video_file = State()
    add_video_code = State()
    broadcast = State()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


@router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🛠 <b>Admin panel</b>",
        reply_markup=admin_menu(),
        parse_mode="HTML"
    )


# ==================== MAJBURIY KANAL ====================

@router.callback_query(F.data == "admin_add_channel")
async def admin_add_channel(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.add_channel)
    await callback.message.answer(
        "Majburiy kanal username yoki ID sini yuboring:\n"
        "<code>@kanalim</code> yoki <code>-1001234567890</code>\n\n"
        "⚠️ Bot kanalda <b>admin</b> bo‘lishi shart!",
        reply_markup=cancel_kb(),
        parse_mode="HTML"
    )


@router.message(AdminStates.add_channel)
async def process_add_channel(message: Message, state: FSMContext, bot: Bot):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_menu())
        return

    try:
        chat = await bot.get_chat(message.text.strip())
        ch_id = str(chat.id)
        title = chat.title or str(chat.id)

        try:
            link = await bot.export_chat_invite_link(ch_id)
        except Exception:
            link = f"https://t.me/{chat.username}" if chat.username else ""

        await add_channel(ch_id, title, link)
        await message.answer(
            f"✅ Qo‘shildi: <b>{title}</b>\nID: <code>{ch_id}</code>",
            reply_markup=admin_menu(),
            parse_mode="HTML"
        )
        await state.clear()
    except Exception as e:
        await message.answer(f"❌ Xato: {e}\nBot admin ekanligini tekshiring.")


@router.callback_query(F.data == "admin_remove_channel")
async def admin_remove_channel(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return

    channels = await get_channels()
    if not channels:
        await callback.answer("Kanallar yo‘q", show_alert=True)
        return

    text = "O‘chirish uchun ID yuboring:\n\n"
    for ch_id, title, _ in channels:
        text += f"<code>{ch_id}</code> — {title}\n"

    await state.set_state(AdminStates.remove_channel)
    await callback.message.answer(text, reply_markup=cancel_kb(), parse_mode="HTML")


@router.message(AdminStates.remove_channel)
async def process_remove(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_menu())
        return

    await remove_channel(message.text.strip())
    await message.answer("✅ O‘chirildi!", reply_markup=admin_menu())
    await state.clear()


# ==================== STORAGE KANALLAR ====================

@router.callback_query(F.data == "admin_set_public_storage")
async def set_public_storage(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.set_public_storage)
    await callback.message.answer(
        "🌍 <b>Hamma uchun</b> kinolar saqlanadigan kanalni yuboring:\n"
        "<code>@kanal</code> yoki <code>-100...</code>\n\n"
        "Botni admin qiling!",
        reply_markup=cancel_kb(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_set_premium_storage")
async def set_premium_storage(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.set_premium_storage)
    await callback.message.answer(
        "💎 <b>Premium</b> kinolar saqlanadigan kanalni yuboring:\n"
        "<code>@kanal</code> yoki <code>-100...</code>\n\n"
        "Botni admin qiling!",
        reply_markup=cancel_kb(),
        parse_mode="HTML"
    )


@router.message(AdminStates.set_public_storage)
@router.message(AdminStates.set_premium_storage)
async def process_storage(message: Message, state: FSMContext, bot: Bot):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_menu())
        return

    current = await state.get_state()
    stype = "public" if "public" in str(current) else "premium"

    try:
        chat = await bot.get_chat(message.text.strip())
        await set_storage_channel(stype, str(chat.id), chat.title or str(chat.id))
        tip = "Hamma uchun" if stype == "public" else "Premium"
        await message.answer(
            f"✅ {tip} kanal saqlandi: <b>{chat.title}</b>\nID: <code>{chat.id}</code>",
            reply_markup=admin_menu(),
            parse_mode="HTML"
        )
        await state.clear()
    except Exception as e:
        await message.answer(f"❌ Xato: {e}")


# ==================== KINO QO‘SHISH (BOT ORQALI) ====================

@router.callback_query(F.data == "admin_add_video")
async def admin_add_video(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    await callback.message.edit_text(
        "Qaysi turdagi kino qo‘shmoqchisiz?",
        reply_markup=add_video_type_kb()
    )


@router.callback_query(F.data.in_({"add_video_public", "add_video_premium"}))
async def choose_video_type(callback: CallbackQuery, state: FSMContext):
    is_prem = 1 if callback.data == "add_video_premium" else 0
    await state.update_data(is_premium=is_prem)
    await state.set_state(AdminStates.add_video_file)
    await callback.message.answer("Videoni yuboring:", reply_markup=cancel_kb())


@router.message(AdminStates.add_video_file, F.video)
async def process_video_file(message: Message, state: FSMContext):
    await state.update_data(file_id=message.video.file_id)
    await state.set_state(AdminStates.add_video_code)
    await message.answer("Endi kodni yuboring (masalan: <code>123</code>):", parse_mode="HTML")


@router.message(AdminStates.add_video_code)
async def process_video_code(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_menu())
        return

    data = await state.get_data()
    code = message.text.strip().lstrip("#")

    await add_video(
        code=code,
        file_id=data["file_id"],
        is_premium=data.get("is_premium", 0)
    )

    tip = "Premium" if data.get("is_premium") else "Hamma uchun"
    await message.answer(
        f"✅ Saqlandi!\nKod: <code>{code}</code>\nTur: {tip}",
        reply_markup=admin_menu(),
        parse_mode="HTML"
    )
    await state.clear()


# ==================== PREMIUM FAOLLASHTIRISH ====================

@router.callback_query(F.data.startswith("activate_"))
async def activate_premium(callback: CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user.id):
        return

    parts = callback.data.split("_")
    user_id = int(parts[1])
    months = int(parts[2])
    days = months * 30
    price = PREMIUM_PRICES.get(months, 0)

    await set_premium(user_id, days)
    await add_payment(user_id, price, f"{months}_oy")

    try:
        await bot.send_message(
            user_id,
            f"🎉 <b>Premium faollashtirildi!</b>\n\n"
            f"Muddat: <b>{months} oy</b> ({days} kun)\n"
            f"Endi barcha maxsus filmlarni ko‘rishingiz mumkin.",
            parse_mode="HTML"
        )
    except Exception:
        pass

    await callback.message.edit_text(f"✅ {user_id} ga {months} oylik premium berildi.")
    await callback.answer("Muvaffaqiyatli!")


@router.callback_query(F.data.startswith("reject_"))
async def reject_premium(callback: CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user.id):
        return

    user_id = int(callback.data.split("_")[1])
    try:
        await bot.send_message(user_id, "❌ Premium so‘rovingiz rad etildi.")
    except Exception:
        pass

    await callback.message.edit_text("❌ Rad etildi.")


# ==================== OMMAVIY XABAR ====================

@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.broadcast)
    await callback.message.answer(
        "Ommaviy xabar yuboring (matn, rasm, video, audio, dokument — istalgan narsa):",
        reply_markup=cancel_kb()
    )


@router.message(AdminStates.broadcast)
async def process_broadcast(message: Message, state: FSMContext, bot: Bot):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_menu())
        return

    users = await get_all_users()
    success = 0

    for (uid,) in users:
        try:
            await message.copy_to(uid)
            success += 1
        except Exception:
            pass

    await message.answer(f"✅ {success} ta odamga yuborildi!", reply_markup=admin_menu())
    await state.clear()


# ==================== STATISTIKA ====================

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    stats = await get_stats()
    text = (
        "📊 <b>Statistika</b>\n\n"
        f"👥 Foydalanuvchilar: <b>{stats['users']}</b>\n"
        f"⭐ Premium: <b>{stats['premium']}</b>\n"
        f"🎥 Bazadagi videolar: <b>{stats['videos']}</b>\n"
        f"👁 Ko‘rishlar: <b>{stats['views']}</b>\n"
        f"💰 Daromad: <b>{stats['income']:,}</b> so‘m"
    )
    await callback.message.answer(text, parse_mode="HTML")


@router.callback_query(F.data == "admin_income")
async def admin_income(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return

    stats = await get_stats()
    await callback.message.answer(
        f"💰 Jami daromad: <b>{stats['income']:,} so‘m</b>",
        parse_mode="HTML"
    )


# ==================== YOPIQ KANALDAN AVTOMATIK SAQLASH ====================

@router.channel_post(F.video)
async def auto_save_from_channel(message: Message):
    """
    Yopiq kanalga video tashalganda avtomatik bazaga yozadi.
    Captionda #123 yoki 123 bo‘lishi shart.
    """
    if not message.video or not message.caption:
        return

    channel_id = str(message.chat.id)

    public_storage = await get_storage_channel("public")
    premium_storage = await get_storage_channel("premium")

    is_premium = None

    if premium_storage and channel_id == str(premium_storage[0]):
        is_premium = 1
    elif public_storage and channel_id == str(public_storage[0]):
        is_premium = 0
    else:
        return  # Bizning kanallarimiz emas

    # Captiondan kodni olish
    match = re.search(r"#?(\d+)", message.caption)
    if not match:
        return

    code = match.group(1)
    file_id = message.video.file_id
    caption = message.caption

    await add_video(
        code=code,
        file_id=file_id,
        caption=caption,
        is_premium=is_premium
    )
    print(f"✅ Avtomatik saqlandi → Kod: {code} | Premium: {bool(is_premium)}")