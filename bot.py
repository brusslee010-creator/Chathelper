import os
import sqlite3
import logging
from datetime import datetime, timedelta, timezone

from telegram import Update, ChatPermissions
from telegram.constants import ChatMemberStatus
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ChatMemberHandler,
    ContextTypes, filters
)

TOKEN = os.getenv("BOT_TOKEN", "").strip()
FOUNDER_ID = int(os.getenv("FOUNDER_ID", "0"))

if not TOKEN or not FOUNDER_ID:
    raise RuntimeError("Set BOT_TOKEN and FOUNDER_ID in Railway Variables.")

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("group-helper")

DB = "bot.db"
db = sqlite3.connect(DB, check_same_thread=False)
db.row_factory = sqlite3.Row
cur = db.cursor()

cur.executescript("""
CREATE TABLE IF NOT EXISTS admins (
    chat_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    added_by INTEGER NOT NULL,
    PRIMARY KEY(chat_id, user_id)
);
CREATE TABLE IF NOT EXISTS warns (
    chat_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    count INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY(chat_id, user_id)
);
CREATE TABLE IF NOT EXISTS settings (
    chat_id INTEGER PRIMARY KEY,
    welcome_enabled INTEGER NOT NULL DEFAULT 1,
    filter_enabled INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS banned_words (
    chat_id INTEGER NOT NULL,
    word TEXT NOT NULL,
    PRIMARY KEY(chat_id, word)
);
""")
db.commit()

DEFAULT_RULES = """📜 ԽՄԲԻ ԿԱՆՈՆՆԵՐ

1. 🤝 Հարգիր բոլոր մասնակիցներին․ հայհոյանքը, վիրավորանքը և նվաստացումը արգելվում են։
2. 🚫 Արգելվում է spam-ը և նույն հաղորդագրությունների անընդհատ կրկնությունը։
3. 📢 Արգելվում է գովազդը առանց ադմինիստրացիայի թույլտվության։
4. 🔗 Արգելվում է այլ չատերի, խմբերի կամ ալիքների գովազդային հղումների տարածումը։
5. 🔞 Արգելվում է արգելված կամ անօրինական բովանդակության տարածումը։
6. 🔐 Մի տարածիր ուրիշ մասնակիցների անձնական տվյալները և մի փորձիր խաբել կամ վնասել նրանց։
7. ⚠️ Հետևիր ադմինիստրացիայի ցուցումներին։ Կանոնների խախտումը կարող է հանգեցնել warn, mute, kick կամ ban-ի։

ℹ️ Կանոնները կարող են լրացվել կամ փոփոխվել հիմնադրի կողմից։
"""

def is_founder(user_id: int) -> bool:
    return user_id == FOUNDER_ID

def is_admin(chat_id: int, user_id: int) -> bool:
    if is_founder(user_id):
        return True
    row = cur.execute(
        "SELECT 1 FROM admins WHERE chat_id=? AND user_id=?",
        (chat_id, user_id)
    ).fetchone()
    return bool(row)

def ensure_settings(chat_id: int):
    cur.execute("INSERT OR IGNORE INTO settings(chat_id) VALUES(?)", (chat_id,))
    db.commit()

async def bot_can_restrict(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    member = await context.bot.get_chat_member(update.effective_chat.id, context.bot.id)
    return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)

async def deny(update: Update, text="❌ Դու այս գործողության իրավունքը չունես։"):
    await update.effective_message.reply_text(text)

async def target_from_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Target can be replied-to user or first argument @username / numeric ID."""
    msg = update.effective_message
    if msg.reply_to_message:
        return msg.reply_to_message.from_user

    if not context.args:
        return None

    raw = context.args[0].strip()
    if raw.startswith("@"):
        try:
            member = await context.bot.get_chat_member(
                update.effective_chat.id, raw
            )
            return member.user
        except Exception:
            return None

    try:
        uid = int(raw)
        member = await context.bot.get_chat_member(update.effective_chat.id, uid)
        return member.user
    except Exception:
        return None

async def protected_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = await target_from_update(update, context)
    if not target:
        await update.effective_message.reply_text(
            "ℹ️ Պատասխանիր օգտատիրոջ հաղորդագրությանը կամ գրիր @username / ID։"
        )
        return None

    actor = update.effective_user
    if target.id == FOUNDER_ID:
        await update.effective_message.reply_text(
            "🛡️ Հիմնադրի վրա այս բոտը ոչ մի moderation գործողություն թույլ չի տալիս։"
        )
        return None

    # Admins cannot act on other admins.
    if is_admin(update.effective_chat.id, target.id) and not is_founder(actor.id):
        await update.effective_message.reply_text(
            "🛡️ Ադմինը չի կարող moderation գործողություն կատարել ուրիշ ադմինի վրա։"
        )
        return None

    return target

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "🤖 Chat Helper Bot\n\n"
        "Խմբերի կառավարման և moderation բոտ։\n"
        "Օգտագործիր /help՝ հրամանների ցանկը տեսնելու համար։"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """🤖 ԲՈՏԻ ՀՐԱՄԱՆՆԵՐ

👑 Հիմնադիր
/admins
/addadmin
/deladmin
/broadcast
/stats
/setrules
/setwelcome
/filter

🛡️ Admin / Founder
/warn
/unwarn
/warns
/mute
/unmute
/ban
/unban
/kick

👥 Բոլորը
/rules
/help

💡 Թիրախավորման համար կարող ես պատասխանել տվյալ օգտատիրոջ հաղորդագրությանը կամ օգտագործել @username / ID։
"""
    await update.effective_message.reply_text(text)

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(DEFAULT_RULES)

async def admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    rows = cur.execute("SELECT user_id FROM admins WHERE chat_id=?", (chat_id,)).fetchall()
    lines = [f"👑 Founder: {FOUNDER_ID}"]
    if rows:
        lines.append("\n🛡️ Admins:")
        for r in rows:
            try:
                m = await context.bot.get_chat_member(chat_id, r["user_id"])
                lines.append(f"• {m.user.full_name} — {m.user.id}")
            except Exception:
                lines.append(f"• ID {r['user_id']}")
    else:
        lines.append("\n🛡️ Ավելացված admin-ներ չկան։")
    await update.effective_message.reply_text("\n".join(lines))

async def addadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_founder(update.effective_user.id):
        return await deny(update)
    target = await target_from_update(update, context)
    if not target:
        return await update.effective_message.reply_text(
            "Օգտագործիր /addadmin @username կամ պատասխանիր օգտատիրոջ հաղորդագրությանը։"
        )
    if target.id == FOUNDER_ID:
        return await update.effective_message.reply_text("👑 Նա արդեն հիմնադիրն է։")
    cur.execute(
        "INSERT OR REPLACE INTO admins(chat_id,user_id,added_by) VALUES(?,?,?)",
        (update.effective_chat.id, target.id, update.effective_user.id)
    )
    db.commit()
    await update.effective_message.reply_text(
        f"🛡️ {target.full_name} նշանակվեց admin։"
    )

async def deladmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_founder(update.effective_user.id):
        return await deny(update)
    target = await target_from_update(update, context)
    if not target:
        return await update.effective_message.reply_text(
            "Օգտագործիր /deladmin @username կամ պատասխանիր հաղորդագրությանը։"
        )
    if target.id == FOUNDER_ID:
        return await update.effective_message.reply_text("❌ Հիմնադրին հնարավոր չէ հեռացնել։")
    cur.execute(
        "DELETE FROM admins WHERE chat_id=? AND user_id=?",
        (update.effective_chat.id, target.id)
    )
    db.commit()
    await update.effective_message.reply_text(
        f"✅ {target.full_name}-ը այլևս admin չէ։"
    )

async def warn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_chat.id, update.effective_user.id):
        return await deny(update)
    target = await protected_target(update, context)
    if not target:
        return
    chat_id = update.effective_chat.id
    row = cur.execute(
        "SELECT count FROM warns WHERE chat_id=? AND user_id=?",
        (chat_id, target.id)
    ).fetchone()
    count = (row["count"] if row else 0) + 1
    cur.execute(
        "INSERT OR REPLACE INTO warns(chat_id,user_id,count) VALUES(?,?,?)",
        (chat_id, target.id, count)
    )
    db.commit()

    if count >= 3:
        try:
            await context.bot.restrict_chat_member(
                chat_id, target.id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=datetime.now(timezone.utc) + timedelta(hours=1)
            )
            action = "\n🔇 3 warn-ի պատճառով՝ 1 ժամ mute։"
        except Exception:
            action = "\n⚠️ Mute-ը չհաջողվեց․ ստուգիր բոտի admin permissions-ը։"
    else:
        action = ""
    await update.effective_message.reply_text(
        f"⚠️ {target.full_name}-ը ստացել է warn։\n"
        f"📊 Warn-եր՝ {count}/3{action}"
    )

async def unwarn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_chat.id, update.effective_user.id):
        return await deny(update)
    target = await protected_target(update, context)
    if not target:
        return
    chat_id = update.effective_chat.id
    row = cur.execute(
        "SELECT count FROM warns WHERE chat_id=? AND user_id=?",
        (chat_id, target.id)
    ).fetchone()
    count = max(0, (row["count"] if row else 0) - 1)
    cur.execute(
        "INSERT OR REPLACE INTO warns(chat_id,user_id,count) VALUES(?,?,?)",
        (chat_id, target.id, count)
    )
    db.commit()
    await update.effective_message.reply_text(
        f"✅ {target.full_name}-ի warn-երը նվազեցվեցին։ Այժմ՝ {count}"
    )

async def warns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = await target_from_update(update, context)
    if not target:
        return await update.effective_message.reply_text(
            "Պատասխանիր օգտատիրոջ հաղորդագրությանը կամ գրիր @username / ID։"
        )
    row = cur.execute(
        "SELECT count FROM warns WHERE chat_id=? AND user_id=?",
        (update.effective_chat.id, target.id)
    ).fetchone()
    await update.effective_message.reply_text(
        f"⚠️ {target.full_name} — {row['count'] if row else 0} warn"
    )

def parse_duration(value: str):
    try:
        unit = value[-1].lower()
        number = int(value[:-1])
        seconds = {"m": 60, "h": 3600, "d": 86400}[unit] * number
        if number <= 0 or seconds > 30 * 86400:
            return None
        return seconds
    except Exception:
        return None

async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_chat.id, update.effective_user.id):
        return await deny(update)
    target = await protected_target(update, context)
    if not target:
        return
    duration = "10m"
    if update.message and context.args and not update.message.reply_to_message:
        if len(context.args) >= 2:
            duration = context.args[1]
    elif context.args and update.message and update.message.reply_to_message:
        duration = context.args[0]

    seconds = parse_duration(duration)
    if not seconds:
        return await update.effective_message.reply_text(
            "Օրինակ՝ /mute 10m, /mute 1h կամ /mute 1d։"
        )
    until = datetime.now(timezone.utc) + timedelta(seconds=seconds)
    try:
        await context.bot.restrict_chat_member(
            update.effective_chat.id, target.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until
        )
        await update.effective_message.reply_text(
            f"🔇 {target.full_name} muted է {duration}։"
        )
    except Exception as e:
        log.warning("mute failed: %s", e)
        await update.effective_message.reply_text(
            "⚠️ Mute-ը չհաջողվեց։ Համոզվիր, որ բոտը admin է և ունի սահմանափակելու իրավունք։"
        )

async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_chat.id, update.effective_user.id):
        return await deny(update)
    target = await protected_target(update, context)
    if not target:
        return
    try:
        await context.bot.restrict_chat_member(
            update.effective_chat.id, target.id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_audios=True,
                can_send_documents=True,
                can_send_photos=True,
                can_send_videos=True,
                can_send_video_notes=True,
                can_send_voice_notes=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_change_info=False,
                can_invite_users=True,
                can_pin_messages=False,
            )
        )
        await update.effective_message.reply_text(f"🔊 {target.full_name} unmuted է։")
    except Exception:
        await update.effective_message.reply_text("⚠️ Unmute-ը չհաջողվեց։")

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_chat.id, update.effective_user.id):
        return await deny(update)
    target = await protected_target(update, context)
    if not target:
        return
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, target.id)
        await update.effective_message.reply_text(f"🚫 {target.full_name} banned է։")
    except Exception:
        await update.effective_message.reply_text("⚠️ Ban-ը չհաջողվեց։ Ստուգիր բոտի իրավունքները։")

async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_chat.id, update.effective_user.id):
        return await deny(update)
    target = await target_from_update(update, context)
    if not target:
        return await update.effective_message.reply_text(
            "Օգտագործիր /unban ID կամ @username։"
        )
    try:
        await context.bot.unban_chat_member(
            update.effective_chat.id, target.id, only_if_banned=True
        )
        await update.effective_message.reply_text(f"✅ {target.full_name} unbanned է։")
    except Exception:
        await update.effective_message.reply_text("⚠️ Unban-ը չհաջողվեց։")

async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_chat.id, update.effective_user.id):
        return await deny(update)
    target = await protected_target(update, context)
    if not target:
        return
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, target.id)
        await context.bot.unban_chat_member(update.effective_chat.id, target.id)
        await update.effective_message.reply_text(f"👢 {target.full_name} հեռացվեց խմբից։")
    except Exception:
        await update.effective_message.reply_text("⚠️ Kick-ը չհաջողվեց։")

async def setwelcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_founder(update.effective_user.id):
        return await deny(update)
    ensure_settings(update.effective_chat.id)
    value = 1 if not context.args or context.args[0].lower() == "on" else 0
    cur.execute(
        "UPDATE settings SET welcome_enabled=? WHERE chat_id=?",
        (value, update.effective_chat.id)
    )
    db.commit()
    await update.effective_message.reply_text(
        f"👋 Welcome՝ {'միացված' if value else 'անջատված'}։"
    )

async def setrules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_founder(update.effective_user.id):
        return await deny(update)
    await update.effective_message.reply_text(
        "ℹ️ Այս տարբերակում կանոնները պահված են bot.py-ում։\n"
        "Ցանկության դեպքում հաջորդ տարբերակում կարող ենք դարձնել ամբողջությամբ խմբից կառավարվող։"
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_chat.id, update.effective_user.id):
        return await deny(update)
    chat_id = update.effective_chat.id
    admin_count = cur.execute(
        "SELECT COUNT(*) c FROM admins WHERE chat_id=?", (chat_id,)
    ).fetchone()["c"]
    warn_count = cur.execute(
        "SELECT COALESCE(SUM(count),0) c FROM warns WHERE chat_id=?", (chat_id,)
    ).fetchone()["c"]
    try:
        members = await context.bot.get_chat_member_count(chat_id)
    except Exception:
        members = "անհասանելի"
    await update.effective_message.reply_text(
        f"📊 Խմբի վիճակագրություն\n\n"
        f"👥 Members: {members}\n"
        f"🛡️ Admins (բոտի համակարգում): {admin_count}\n"
        f"⚠️ Ընդհանուր warn-եր: {warn_count}"
    )

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_founder(update.effective_user.id):
        return await deny(update)
    await update.effective_message.reply_text(
        "📢 Broadcast ֆունկցիայի համար բոտին պետք է ունենալ առանձին persistent member registry։ "
        "Այս տարբերակում broadcast-ը միացված չէ, որպեսզի չուղարկի չպահված/ոչ նպատակային օգտատերերի։"
    )

async def new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    ensure_settings(chat_id)
    row = cur.execute(
        "SELECT welcome_enabled FROM settings WHERE chat_id=?", (chat_id,)
    ).fetchone()
    if row and not row["welcome_enabled"]:
        return

    for member in update.chat_member.new_chat_members:
        username = f"@{member.username}" if member.username else "չկա"
        text = (
            f"👋 Բարի գալուստ, {member.full_name}!\n\n"
            f"👤 Name: {member.full_name}\n"
            f"🆔 ID: {member.id}\n"
            f"🔗 Username: {username}\n\n"
            "🎉 Ուրախ ենք քեզ տեսնել մեր համայնքում։\n"
            "Խնդրում ենք հարգել մյուս մասնակիցներին և պահպանել խմբի կանոնները։\n\n"
            "📜 Խնդրում ենք անպայման կարդալ խմբի կանոնները՝ /rules"
        )
        await context.bot.send_message(chat_id, text)

async def message_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    chat = update.effective_chat
    if chat.type not in ("group", "supergroup"):
        return

    # Founder and registered admins are never auto-filtered.
    if is_admin(chat.id, update.effective_user.id):
        return

    text = update.message.text.lower()
    # Conservative built-in filter. Add/remove words in the code if desired.
    blocked = ["http://", "https://", "t.me/"]
    if any(x in text for x in blocked):
        try:
            await update.message.delete()
            await update.message.reply_text(
                f"🚫 {update.effective_user.full_name}, գովազդային/արտաքին հղումներ այստեղ չեն թույլատրվում։"
            )
        except Exception:
            pass

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    log.exception("Unhandled error", exc_info=context.error)

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("rules", rules))
    app.add_handler(CommandHandler("admins", admins))

    app.add_handler(CommandHandler("addadmin", addadmin))
    app.add_handler(CommandHandler("deladmin", deladmin))

    app.add_handler(CommandHandler("warn", warn))
    app.add_handler(CommandHandler("unwarn", unwarn))
    app.add_handler(CommandHandler("warns", warns))
    app.add_handler(CommandHandler("mute", mute))
    app.add_handler(CommandHandler("unmute", unmute))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(CommandHandler("kick", kick))

    app.add_handler(CommandHandler("setwelcome", setwelcome))
    app.add_handler(CommandHandler("setrules", setrules))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("broadcast", broadcast))

    app.add_handler(ChatMemberHandler(new_member, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_filter))
    app.add_error_handler(error_handler)

    log.info("Bot started.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
