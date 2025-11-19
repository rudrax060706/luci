import sqlite3
from telethon.tl.types import ChannelParticipantsAdmins
from utils.logger import log_event

DB_PATH = "database/data.db"

async def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY, 
            message_count INTEGER DEFAULT 0, 
            last_round INTEGER DEFAULT 0
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS mutes(
            user_id INTEGER PRIMARY KEY, 
            mute_end_timestamp INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ignored(
            user_id INTEGER PRIMARY KEY
        )
    """)
    conn.commit()
    conn.close()


async def add_ignored_admins(bot, group_id):
    """Automatically add all group admins to the ignored table."""
    try:
        admins = await bot.get_participants(group_id, filter=ChannelParticipantsAdmins())
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        for admin in admins:
            cur.execute("INSERT OR IGNORE INTO ignored(user_id) VALUES(?)", (admin.id,))

        conn.commit()
        conn.close()

        # ✅ FIXED: Added bot argument + await
        await log_event(bot, f"✅ Added {len(admins)} admins to ignored list automatically.")

    except Exception as e:
        # ✅ FIXED: Added bot argument + await
        await log_event(bot, f"⚠️ Error adding admins to ignored list: {e}")
