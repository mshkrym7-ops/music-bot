"""
🎵 ربات موزیک انگیزشی تلگرام
=====================================
راهنمای نصب:
1. pip install python-telegram-bot
2. توکن ربات رو از @BotFather بگیر
3. آیدی کانال انبارت رو وارد کن
4. python music_bot.py رو اجرا کن
"""

import random
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =====================
# تنظیمات - اینجا رو پر کن
# =====================
BOT_TOKEN = "TOKEN_خودت_رو_اینجا_بذار"
ADMIN_ID = 123456789  # آیدی عددی خودت (از @userinfobot بگیر)
STORAGE_FILE = "songs.json"  # فایل ذخیره آهنگ‌ها

# =====================
# تنظیمات Force Join
# =====================
# آیدی کانالت رو اینجا بذار — مثلاً: "@mychannel" یا -1001234567890
CHANNEL_ID = "@your_channel"
# لینک کانال برای نمایش به کاربر
CHANNEL_LINK = "https://t.me/your_channel"

# =====================
# دسته‌بندی‌ها
# =====================
CATEGORIES = {
    "rap": "🎤 رپ",
    "pop": "🎵 پاپ",
    "rock": "🎸 راک",
    "calm": "🌙 آروم",
    "hiphop": "🔥 هیپ‌هاپ",
    "persian": "🇮🇷 فارسی",
}

# =====================
# مدیریت دیتابیس ساده
# =====================
def load_songs():
    if os.path.exists(STORAGE_FILE):
        with open(STORAGE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {cat: [] for cat in CATEGORIES}

def save_songs(data):
    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# =====================
# بررسی عضویت در کانال
# =====================
async def is_member(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception:
        return False

def join_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 عضویت در کانال", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ عضو شدم!", callback_data="check_join")]
    ])

async def force_join_message(update_or_query, is_callback=False):
    text = (
        "⚠️ *برای استفاده از ربات باید عضو کانال ما بشی!*\n\n"
        "1️⃣ روی دکمه زیر کلیک کن و عضو کانال شو\n"
        "2️⃣ بعد از عضویت دکمه «عضو شدم» رو بزن ✅"
    )
    if is_callback:
        await update_or_query.edit_message_text(
            text, parse_mode="Markdown", reply_markup=join_keyboard()
        )
    else:
        await update_or_query.message.reply_text(
            text, parse_mode="Markdown", reply_markup=join_keyboard()
        )

# =====================
# دستورات کاربر
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # ادمین نیازی به چک ندارد
    if user_id != ADMIN_ID and not await is_member(user_id, context):
        await force_join_message(update)
        return

    text = (
        "🎵 *به ربات موزیک انگیزشی خوش اومدی!*\n\n"
        "یه دسته‌بندی انتخاب کن تا یه آهنگ انگیزشی برات بفرستم 👇"
    )
    keyboard = build_category_keyboard()
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📖 *راهنما:*\n\n"
        "/start — شروع و انتخاب دسته‌بندی\n"
        "/random — آهنگ تصادفی از همه دسته‌ها\n"
        "/list — لیست تعداد آهنگ‌ها\n\n"
        "👮 *ادمین:*\n"
        "/add — اضافه کردن آهنگ جدید\n"
        "/remove — حذف آهنگ"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def random_song(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID and not await is_member(user_id, context):
        await force_join_message(update)
        return

    songs = load_songs()
    all_songs = []
    for cat, items in songs.items():
        for song in items:
            song["category"] = cat
            all_songs.append(song)

    if not all_songs:
        await update.message.reply_text("😕 هنوز آهنگی اضافه نشده!")
        return

    song = random.choice(all_songs)
    cat_name = CATEGORIES.get(song["category"], song["category"])
    caption = f"🎵 *{song.get('title', 'آهنگ انگیزشی')}*\n🏷 دسته: {cat_name}"
    await update.message.reply_audio(
        audio=song["file_id"],
        caption=caption,
        parse_mode="Markdown"
    )

async def list_songs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    songs = load_songs()
    text = "📊 *تعداد آهنگ‌ها:*\n\n"
    total = 0
    for cat, items in songs.items():
        count = len(items)
        total += count
        text += f"{CATEGORIES[cat]}: {count} آهنگ\n"
    text += f"\n🎵 مجموع: {total} آهنگ"
    await update.message.reply_text(text, parse_mode="Markdown")

# =====================
# انتخاب دسته و ارسال آهنگ
# =====================
def build_category_keyboard():
    buttons = []
    row = []
    for cat_id, cat_name in CATEGORIES.items():
        row.append(InlineKeyboardButton(cat_name, callback_data=f"cat_{cat_id}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("🎲 تصادفی از همه", callback_data="cat_random")])
    return InlineKeyboardMarkup(buttons)

async def category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    if user_id != ADMIN_ID and not await is_member(user_id, context):
        await force_join_message(query, is_callback=True)
        return

    data = query.data
    songs = load_songs()

    if data == "cat_random":
        all_songs = []
        for cat, items in songs.items():
            for s in items:
                s["category"] = cat
                all_songs.append(s)
        if not all_songs:
            await query.edit_message_text("😕 هنوز آهنگی اضافه نشده!")
            return
        song = random.choice(all_songs)
        cat_name = CATEGORIES.get(song["category"], "")
    else:
        cat_id = data.replace("cat_", "")
        cat_songs = songs.get(cat_id, [])
        if not cat_songs:
            await query.edit_message_text(
                f"😕 توی دسته {CATEGORIES.get(cat_id, '')} هنوز آهنگی نیست!\n\nدسته دیگه‌ای انتخاب کن:",
                reply_markup=build_category_keyboard()
            )
            return
        song = random.choice(cat_songs)
        song["category"] = cat_id
        cat_name = CATEGORIES.get(cat_id, "")

    caption = f"🎵 *{song.get('title', 'آهنگ انگیزشی')}*\n🏷 دسته: {cat_name}\n\n💪 امیدوارم انرژی بگیری!"
    await query.message.reply_audio(
        audio=song["file_id"],
        caption=caption,
        parse_mode="Markdown"
    )
    # دوباره کیبورد نشون بده
    await query.message.reply_text(
        "یه آهنگ دیگه می‌خوای؟ 👇",
        reply_markup=build_category_keyboard()
    )

async def check_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    if await is_member(user_id, context):
        await query.edit_message_text(
            "✅ *عضویت تأیید شد! خوش اومدی* 🎵\n\nحالا یه دسته‌بندی انتخاب کن:",
            parse_mode="Markdown",
            reply_markup=build_category_keyboard()
        )
    else:
        await query.answer("❌ هنوز عضو کانال نشدی!", show_alert=True)

# =====================
# پنل ادمین — اضافه کردن آهنگ
# =====================
async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ فقط ادمین می‌تونه آهنگ اضافه کنه!")
        return

    buttons = []
    row = []
    for cat_id, cat_name in CATEGORIES.items():
        row.append(InlineKeyboardButton(cat_name, callback_data=f"addcat_{cat_id}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    await update.message.reply_text(
        "➕ *اضافه کردن آهنگ*\n\nاول دسته‌بندی رو انتخاب کن:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def addcat_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    cat_id = query.data.replace("addcat_", "")
    context.user_data["adding_to_cat"] = cat_id
    cat_name = CATEGORIES.get(cat_id, cat_id)

    await query.edit_message_text(
        f"✅ دسته انتخاب شد: *{cat_name}*\n\n"
        "حالا فایل صوتی آهنگ رو بفرست 🎵\n"
        "(می‌تونی عنوان آهنگ رو هم توی caption بنویسی)",
        parse_mode="Markdown"
    )

async def receive_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    cat_id = context.user_data.get("adding_to_cat")
    if not cat_id:
        await update.message.reply_text(
            "ابتدا /add رو بزن و دسته‌بندی انتخاب کن!"
        )
        return

    audio = update.message.audio or update.message.voice
    if not audio:
        return

    file_id = audio.file_id
    title = (
        update.message.caption
        or getattr(audio, "title", None)
        or getattr(audio, "file_name", "آهنگ انگیزشی")
        or "آهنگ انگیزشی"
    )

    songs = load_songs()
    songs[cat_id].append({"file_id": file_id, "title": title})
    save_songs(songs)

    cat_name = CATEGORIES.get(cat_id, cat_id)
    await update.message.reply_text(
        f"✅ آهنگ *{title}* به دسته {cat_name} اضافه شد!\n\n"
        "آهنگ بعدی رو بفرست یا /add برای دسته جدید بزن.",
        parse_mode="Markdown"
    )

# =====================
# راه‌اندازی ربات
# =====================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # هندلرهای کاربر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("random", random_song))
    app.add_handler(CommandHandler("list", list_songs))

    # هندلرهای ادمین
    app.add_handler(CommandHandler("add", add_command))
    app.add_handler(MessageHandler(filters.AUDIO | filters.VOICE, receive_audio))

    # هندلرهای callback
    app.add_handler(CallbackQueryHandler(category_callback, pattern="^cat_"))
    app.add_handler(CallbackQueryHandler(addcat_callback, pattern="^addcat_"))
    app.add_handler(CallbackQueryHandler(check_join_callback, pattern="^check_join$"))

    print("🤖 ربات روشن شد...")
    app.run_polling()

if __name__ == "__main__":
    main()
