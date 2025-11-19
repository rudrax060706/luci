from database.db import DB_PATH
import sqlite3

global_message_count = 0
current_round = 1

async def handle_message(bot, event):
    from config import GROUP_ID, TOTAL_MESSAGES_FOR_ROUND
    global global_message_count, current_round

    if event.is_private:
        return
    if event.chat_id != GROUP_ID:
        await bot.leave_chat(event.chat_id)
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    user_id = event.sender_id
    cur.execute("SELECT 1 FROM ignored WHERE user_id=?", (user_id,))
    if cur.fetchone():
        conn.close()
        return

    cur.execute("INSERT OR IGNORE INTO users(user_id, message_count, last_round) VALUES(?, 0, ?)", (user_id, current_round))
    cur.execute("UPDATE users SET message_count = message_count + 1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

    global_message_count += 1
    if global_message_count >= TOTAL_MESSAGES_FOR_ROUND:
        current_round += 1
        global_message_count = 0
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("UPDATE users SET message_count=0, last_round=?", (current_round,))
        conn.commit()
        conn.close()
        from utils.logger import log_event
        log_event(f"Round reset to {current_round}")
