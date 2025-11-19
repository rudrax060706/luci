import sqlite3
from telethon import events, Button
from telethon.tl.functions.channels import GetParticipantRequest, EditBannedRequest
from telethon.tl.types import ChatBannedRights
from config import MIN_MESSAGES_REQUIRED, MUTE_DURATION, GROUP_ID, LOG_GROUP_ID
from utils.logger import log_event

# ✅ Helper: Check if user is admin
async def is_admin(bot, chat_id, user_id):
    try:
        participant = await bot(GetParticipantRequest(chat_id, user_id))
        p = participant.participant
        return bool(getattr(p, "admin_rights", None) or getattr(p, "rank", None))
    except Exception:
        return False


# ✅ Handle /grab or /secure command
async def handle_grab(bot, event):
    if event.chat_id != GROUP_ID:
        await bot.leave_chat(event.chat_id)
        return

    # Prevent double trigger
    if getattr(event, "handled", False):
        return
    event.handled = True

    user_id = event.sender_id
    sender = await event.get_sender()
    user_name = sender.first_name or "Unknown"

    conn = sqlite3.connect("database/data.db")
    cur = conn.cursor()

    # 🚫 Ignore users in ignored table
    cur.execute("SELECT 1 FROM ignored WHERE user_id=?", (user_id,))
    if cur.fetchone():
        conn.close()
        return

    # 📊 Check message count
    cur.execute("SELECT message_count FROM users WHERE user_id=?", (user_id,))
    result = cur.fetchone()
    conn.close()

    if result and result[0] < MIN_MESSAGES_REQUIRED:
        # 🔇 Define mute rights
        mute_rights = ChatBannedRights(
            until_date=None,
            send_messages=True
        )

        # Apply mute
        try:
            await bot(EditBannedRequest(GROUP_ID, user_id, ChatBannedRights(until_date=None, send_messages=True)))
        except Exception as e:
            await log_event(bot, f"❌ Failed to mute {user_name}: {e}")
            return

        # 📢 Announce in group with buttons
        await bot.send_message(
            GROUP_ID,
            f"🔇 **{user_name}** (`{user_id}`) has been muted for **{MUTE_DURATION // 60} minutes.**\n"
            f"Reason: Not enough messages before grabbing.",
            buttons=[
                [
                    Button.inline("✅ Unmute", data=f"unmute_{user_id}"),
                    Button.inline("❌ Decline", data=f"decline_{user_id}")
                ]
            ]
        )

        # 🪵 Log to log group
        await bot.send_message(
            LOG_GROUP_ID,
            f"🕒 **Mute Log:**\n"
            f"👤 User: {user_name} (`{user_id}`)\n"
            f"💬 Messages: {result[0] if result else 0}\n"
            f"⏱ Duration: {MUTE_DURATION // 60} minutes"
        )

        await log_event(bot, f"✅ Muted {user_name} ({user_id}) for low activity.")


# ✅ Handle button presses (Unmute / Decline)
@events.register(events.CallbackQuery)
async def button_handler(event):
    data = event.data.decode()
    chat_id = event.chat_id
    sender_id = event.sender_id

    # Only handle our buttons
    if not (data.startswith("unmute_") or data.startswith("decline_")):
        return

    target_id = int(data.split("_")[1])

    # 🛡️ Check if the person pressing is admin
    if not await is_admin(event.client, chat_id, sender_id):
        await event.answer("🚫 You are not authorized to use this.", alert=True)
        return

    # ✅ Handle Unmute
    if data.startswith("unmute_"):
        rights = ChatBannedRights(until_date=None, send_messages=False)
        await event.client(EditBannedRequest(chat_id, target_id, rights))
        await event.edit(f"✅ User `{target_id}` has been unmuted by admin `{sender_id}`.")
        await event.client.send_message(
            LOG_GROUP_ID,
            f"✅ **Unmute Action:** Admin `{sender_id}` unmuted user `{target_id}`"
        )

    # ❌ Handle Decline
    elif data.startswith("decline_"):
        await event.edit(f"❌ Unmute request for `{target_id}` declined by admin `{sender_id}`.")
        await event.client.send_message(
            LOG_GROUP_ID,
            f"❌ **Decline Action:** Admin `{sender_id}` declined unmute for `{target_id}`"
        )