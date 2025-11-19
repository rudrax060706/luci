from telethon import events, types
from config import OWNER_ID, GROUP_ID, WELCOME_MESSAGE, LOG_GROUP_ID
from database.db import DB_PATH
from utils.logger import log_event
import sqlite3
import os
from datetime import datetime


def register_commands(bot):

    # ==============================
    # 🎬 /start COMMAND (Instant Telegram send)
    # ==============================
    @bot.on(events.NewMessage(pattern=r'^/start$'))
    async def start_cmd(event):
        sender = await event.get_sender()
        name = sender.first_name or "there"
        user_id = sender.id
        username = f"@{sender.username}" if sender.username else "N/A"
        time_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        message = WELCOME_MESSAGE.format(name=name)

        try:
            # ✅ Use saved Telegram file directly for instant send
            input_document = types.InputDocument(
                id=6059744618914782252,  # 🆔 File ID
                access_hash=8348114473456465796,  # 🔑 Access Hash
                file_reference=bytes.fromhex("030000005569024a6100302828d34a3532b658819b4d137c25")  # 📦 File Reference
            )

            await bot.send_file(event.chat_id, input_document, caption=message)

            # Log to group
            log_text = (
                f"🆕 **User Started Bot**\n\n"
                f"👤 Name: {name}\n"
                f"🆔 User ID: `{user_id}`\n"
                f"💬 Username: {username}\n"
                f"🕒 Time: {time_now}\n"
                f"📍 Chat ID: {event.chat_id}"
            )
            await log_event(bot, log_text)

        except Exception as e:
            await event.reply("⚠️ Something went wrong while sending the welcome message.")
            await log_event(bot, f"❌ Error in /start: {e}")

    # ==============================
    # 👑 /ignore COMMAND (Owner only)
    # ==============================
    @bot.on(events.NewMessage(pattern=r'^/ignore (\d+)$'))
    async def ignore_cmd(event):
        if event.sender_id != OWNER_ID:
            return

        user_id = int(event.pattern_match.group(1))
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("INSERT OR IGNORE INTO ignored(user_id) VALUES(?)", (user_id,))
        conn.commit()
        conn.close()

        msg = f"✅ User `{user_id}` added to ignore list."
        await event.reply(msg)
        await log_event(bot, f"👑 Owner ignored user `{user_id}`")

    # ==============================
    # 👑 /unignore COMMAND (Owner only)
    # ==============================
    @bot.on(events.NewMessage(pattern=r'^/unignore (\d+)$'))
    async def unignore_cmd(event):
        if event.sender_id != OWNER_ID:
            return

        user_id = int(event.pattern_match.group(1))
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("DELETE FROM ignored WHERE user_id=?", (user_id,))
        conn.commit()
        conn.close()

        msg = f"❎ User `{user_id}` removed from ignore list."
        await event.reply(msg)
        await log_event(bot, f"👑 Owner unignored user `{user_id}`")

    # ==============================
    # 📜 /ignored COMMAND (Show ignored list)
    # ==============================
    @bot.on(events.NewMessage(pattern=r'^/ignored$'))
    async def ignored_cmd(event):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM ignored")
        ignored = cur.fetchall()
        conn.close()

        ignored_list = ', '.join(str(u[0]) for u in ignored) or "None"
        await event.reply(f"🚫 Ignored users: {ignored_list}")

    # ==============================
    # ℹ️ /help COMMAND
    # ==============================
    @bot.on(events.NewMessage(pattern=r'^/help$'))
    async def help_cmd(event):
        help_text = (
            "**🤖 Bot Command List**\n\n"
            "📍 General:\n"
            "/start — Show welcome message\n"
            "/help — Show this help message\n"
            "/ignored — Show ignored users list\n\n"
            "👑 Owner Only:\n"
            "/ignore <user_id> — Add user to ignore list\n"
            "/unignore <user_id> — Remove user from ignore list\n"
        )

        await event.reply(help_text)