# Telegram Group Helper Bot

Railway-ready Telegram group moderation bot.

## Required Railway Variables

Set these two variables:

BOT_TOKEN=YOUR_BOT_TOKEN
FOUNDER_ID=YOUR_TELEGRAM_USER_ID

Do NOT put the real token inside bot.py or upload it to GitHub.

## Important Telegram permissions

Add the bot to your group as an Administrator.

For moderation features, give it the permissions needed to:
- Delete messages
- Ban/restrict users
- Invite users (optional)
- Manage chat as needed

For new-member welcome events, Telegram privacy/admin settings should allow the bot to receive chat member updates.

## Founder / Admin hierarchy

Founder:
- Can manage admins.
- Can moderate members and admins.
- Cannot be moderated by anyone through this bot.

Admin:
- Can moderate normal members.
- Cannot moderate another admin.
- Cannot moderate the Founder.
- Cannot add/remove admins unless the user is Founder.

Member:
- Cannot use moderation commands.

## Main commands

/help
/rules
/admins
/warn
/unwarn
/warns
/mute
/unmute
/ban
/unban
/kick

Founder:
/addadmin
/deladmin
/setwelcome
/setrules
/stats
/broadcast

## Targeting users

Reply to a user's message:

/warn
/mute 10m
/ban
/kick

Or use:

/warn @username
/mute @username 1h
/ban @username
/kick @username

For unban, use the numeric Telegram ID when possible:

/unban 123456789

## Railway deployment

1. Create a new Railway project.
2. Deploy this folder/repository.
3. Add BOT_TOKEN.
4. Add FOUNDER_ID.
5. Start the service.

The SQLite database is created automatically as bot.db.

NOTE: SQLite stored on Railway's normal ephemeral filesystem can be lost when the service is redeployed/recreated. For permanent production data, attach a Railway Volume and store the database on that mounted path in a later version.
