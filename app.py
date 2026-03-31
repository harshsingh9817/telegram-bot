import requests
import re
import json
import os
import random
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ============= CONFIG =============
TELEGRAM_TOKEN = "PUT_YOUR_NEW_TOKEN_HERE"  # 🔥 DIRECT (no env problem)

OWNER_ID = "@itseagelrajput"
BOT_NAME = "DataHunter"
BOT_TAG = "by Harsh and DIGITAL PHANTOM"
ADMIN_IDS = [8210601443]

USERS_FILE = "users.json"
BANNED_FILE = "banned.json"

PLANS = {
    "weekly": {"price": 49, "days": 7, "tries": 500},
    "monthly": {"price": 149, "days": 30, "tries": 2500},
    "yearly": {"price": 499, "days": 365, "tries": 30000}
}

# ============= DATABASE =============
def load_json(file, default):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return default

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

def get_user(user_id):
    users = load_json(USERS_FILE, {})
    uid = str(user_id)
    if uid not in users:
        users[uid] = {
            "tries": 10,
            "premium": False,
            "expiry": None,
            "searches": 0,
            "ref_code": f"PH{random.randint(10000,99999)}",
            "ref_count": 0,
            "ref_by": None,
            "join_date": datetime.now().timestamp()
        }
        save_json(USERS_FILE, users)
    return users[uid]

def update_user(user_id, data):
    users = load_json(USERS_FILE, {})
    users[str(user_id)] = data
    save_json(USERS_FILE, users)

def is_banned(user_id):
    return str(user_id) in load_json(BANNED_FILE, [])

# ============= API =============
def search_number(number):
    try:
        url = f"https://dark-osint-number-api.vercel.app/?num={number}"
        data = requests.get(url, timeout=10).json()

        if data.get("phone_details", {}).get("success"):
            r = data["phone_details"]["result"]["results"][0]
            msg = f"""
📡 DataHunter Result

📱 {r.get('mobile')}
👤 {r.get('name')}
👨 {r.get('fname')}
📍 {r.get('address')}
📞 {r.get('alt')}
🔄 {r.get('circle')}
"""
            return msg, True
        return "❌ TARGET NOT FOUND", False
    except:
        return "❌ ERROR", False

# ============= BUTTONS =============
def main_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎯 START SCAN", callback_data="search")],
        [InlineKeyboardButton("👤 MY STATS", callback_data="profile")]
    ])

# ============= COMMANDS =============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if is_banned(user_id):
        await update.message.reply_text("🚫 BANNED")
        return

    user = get_user(user_id)

    await update.message.reply_text(
        f"👋 Welcome {update.effective_user.first_name}\n🎯 Scans: {user['tries']}",
        reply_markup=main_buttons()
    )

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "search":
        await query.edit_message_text("📩 Send number")
        context.user_data["wait"] = True

    elif query.data == "profile":
        user = get_user(query.from_user.id)
        await query.edit_message_text(f"🎯 {user['tries']} scans left")

async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("wait"):
        return

    user = get_user(update.effective_user.id)

    num = re.findall(r"\d{10}", update.message.text)
    if not num:
        await update.message.reply_text("❌ invalid number")
        return

    result, ok = search_number(num[0])

    if ok:
        user["tries"] -= 1
        user["searches"] += 1
        update_user(update.effective_user.id, user)

    await update.message.reply_text(result)
    context.user_data["wait"] = False

# ============= MAIN =============
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number))

    print("🔥 Bot Running on Koyeb 🔥")
    app.run_polling()

if __name__ == "__main__":
    main()
