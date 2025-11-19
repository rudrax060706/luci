import asyncio
import time
import sqlite3
from datetime import datetime
from telethon import Button
from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import ChatBannedRights
from config import LOG_GROUP_ID, GROUP_ID
from utils.logger import log_event

DB_PATH = "database/data.db"


async def mute_user(bot, chat_id, user_id, duration):
    """Mute a user and announce with Unmute/Decline buttons"""
    rights = ChatBannedRights(until_date=time.time() + duration, send_messages=False)

    try:
        # ✅ Apply mute
        await bot(EditBannedRequest(chat_id, user_id, rights))

        # 🧠 Record mute in DB
        mute_end = int(time.time()) + duration
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO mutes(user_id, mute_end_timestamp) VALUES (?, ?)",
            (user_id, mute_end)
        )
        conn.commit()
        conn.close()

        # 🧾 Get user info
        user = await bot.get_entity(user_id)
        user_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "Unknown"

        # 📢 Announce mute in group
        message = (
            f"🔇 **{user_name}** (`{user_id}`) has been muted for "
            f"**{duration // 60} minutes.**\n"
            f"Reason: Not enough messages before grabbing."
        )

        buttons = [
            [
                Button.inline("✅ Unmute", data=f"unmute_{user_id}"),
                Button.inline("❌ Decline", data=f"decline_{user_id}")
            ]
        ]

        await bot.send_message(chat_id, message, buttons=buttons)

        # 🪵 Log to log group
        await bot.send_message(
            LOG_GROUP_ID,
            f"📋 **Mute Log**\n👤 User: {user_name} (`{user_id}`)\n"
            f"🕒 Duration: {duration // 60} minutes\n"
            f"🗓 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        # 🔐 Log locally as well
        await log_event(bot, f"Muted {user_name} ({user_id}) for {duration // 60} minutes.")

        # ⏳ Schedule automatic unmute
        asyncio.create_task(unmute_user(bot, chat_id, user_id, duration))

    except Exception as e:
        await log_event(bot, f"❌ Failed to mute {user_id}: {e}")
        await bot.send_message(LOG_GROUP_ID, f"❌ Failed to mute {user_id}: {e}")


async def unmute_user(bot, chat_id, user_id, duration):
    """Automatically unmute user after their mute duration ends"""
    await asyncio.sleep(duration)

    try:
        # ⏱ Verify mute duration expired
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT mute_end_timestamp FROM mutes WHERE user_id=?", (user_id,))
        data = cur.fetchone()
        conn.close()

        if not data or time.time() < data[0]:
            return  # still muted or no record found

        # 🔊 Remove mute
        rights = ChatBannedRights(until_date=None, send_messages=True)
        await bot(EditBannedRequest(chat_id, user_id, rights))

        # 🗑 Clean up from DB
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("DELETE FROM mutes WHERE user_id=?", (user_id,))
        conn.commit()
        conn.close()

        # 📢 Notify
        user = await bot.get_entity(user_id)
        user_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "Unknown"

        await bot.send_message(
            chat_id,
            f"🔊 **{user_name}** (`{user_id}`) has been automatically unmuted after their mute duration expired."
        )

        await bot.send_message(
            LOG_GROUP_ID,
            f"🕓 **Auto Unmute Log**\n👤 User: {user_name} (`{user_id}`)\n"
            f"🗓 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        await log_event(bot, f"Unmuted {user_name} ({user_id}) after duration.")

    except Exception as e:
        await log_event(bot, f"❌ Failed to unmute {user_id}: {e}")
        await bot.send_message(LOG_GROUP_ID, f"❌ Failed to unmute {user_id}: {e}")