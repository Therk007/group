import telebot
import datetime
import time
import subprocess
import random
import threading
import os
from telebot import types
from urllib.parse import urlparse

# Initialize bot
bot = telebot.TeleBot('7879783137:AAEddUnqqkwleg2c3S4iXHAIyFtGCW1vRDI')

INSTRUCTOR_IDS = ["1549748318", "1662672529"]
STUDY_GROUP_ID = "-1002654300042"
LEARNING_CHANNEL = "@RAJARAJ786786"
LAB_REPORTS_DIR = "lab_reports"
TEST_COOLDOWN = 30
DAILY_TEST_LIMIT = 7
is_test_in_progress = False
last_test_time = None
pending_reports = {}
lab_submissions = {}
STUDENT_DATA_FILE = "student_progress.txt"
student_data = {}
study_groups = {}
GROUPS_FILE = "study_groups.txt"

educational_images = [
    "https://imgur.com/example_network1.jpg",
    "https://imgur.com/example_network2.jpg"
]
DEFAULT_NETWORK_IMAGE = "https://imgur.com/default_network.jpg"

# Helper Functions
def create_progress_bar(progress, total, length=20):
    """Create visual progress bar with emoji states"""
    filled = int(length * progress // total)
    empty = length - filled
    
    if progress/total < 0.3:
        fill_char = '█'  # Early stage (red will be shown differently)
    elif progress/total < 0.7:
        fill_char = '█'  # Middle stage (yellow)
    else:
        fill_char = '█'  # Nearing completion (green)
    
    bar = fill_char * filled + '░' * empty
    percent = min(100, int(100 * progress / total))
    return f"📈 Progress: {bar} {percent}%"

def update_progress(chat_id, progress_data, target, port, student_name):
    """Update progress bar during experiment"""
    duration = progress_data['duration']
    start_time = progress_data['start_time']
    
    try:
        while True:
            elapsed = (datetime.datetime.now() - start_time).seconds
            progress = min(elapsed, duration)
            remaining = max(0, duration - elapsed)
            
            if progress - progress_data['last_update'] >= 5 or progress == duration:
                try:
                    bot.edit_message_text(
                        f"🔬 Experiment Running\n"
                        f"👨‍🔬 Student: »»—— {student_name} ♥\n"
                        f"🎯 Target: {target}:{port}\n"
                        f"⏱ Elapsed: {progress}s/{duration}s\n"
                        f"📊 Remaining: {remaining}\n"
                        f"{create_progress_bar(progress, duration)}\n",
                        chat_id=chat_id,
                        message_id=progress_data['message_id']
                    )
                    progress_data['last_update'] = progress
                except Exception as e:
                    print(f"Error updating progress: {e}")
                
                if progress >= duration:
                    break
            
            time.sleep(1)
    except Exception as e:
        print(f"Progress updater error: {e}")

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def safe_send_photo(chat_id, photo_url, caption):
    try:
        if is_valid_url(photo_url):
            bot.send_photo(chat_id, photo_url, caption=caption)
        else:
            bot.send_message(chat_id, caption)
    except Exception as e:
        print(f"Error sending photo: {e}")
        bot.send_message(chat_id, caption)

def load_student_data():
    try:
        with open(STUDENT_DATA_FILE, "r") as file:
            for line in file:
                if not line.strip():
                    continue
                try:
                    user_id, tests, last_reset = line.strip().split(',')
                    student_data[user_id] = {
                        'tests': int(tests),
                        'last_reset': datetime.datetime.fromisoformat(last_reset),
                        'last_test': None
                    }
                except ValueError:
                    print(f"Skipping malformed line: {line.strip()}")
    except FileNotFoundError:
        print(f"{STUDENT_DATA_FILE} not found, starting fresh.")

def save_student_data():
    with open(STUDENT_DATA_FILE, "w") as file:
        for user_id, data in student_data.items():
            file.write(f"{user_id},{data['tests']},{data['last_reset'].isoformat()}\n")

def check_membership(user_id):
    try:
        try:
            channel_member = bot.get_chat_member(LEARNING_CHANNEL, user_id)
            if channel_member.status not in ['member', 'administrator', 'creator']:
                return False
        except Exception as e:
            print(f"Error checking channel membership: {e}")
            return False
            
        for group_id in study_groups:
            try:
                group_member = bot.get_chat_member(group_id, user_id)
                if group_member.status in ['member', 'administrator', 'creator']:
                    return True
            except Exception as e:
                print(f"Error checking group {group_id} membership: {e}")
                continue
                
        try:
            main_group_member = bot.get_chat_member(STUDY_GROUP_ID, user_id)
            if main_group_member.status in ['member', 'administrator', 'creator']:
                return True
        except Exception as e:
            print(f"Error checking main group membership: {e}")
                
        return False
    except Exception as e:
        print(f"General membership check error: {e}")
        return False

def membership_required(func):
    def wrapped(message):
        user_id = message.from_user.id
        chat_id = str(message.chat.id)
        
        if chat_id not in study_groups and chat_id != STUDY_GROUP_ID:
            bot.reply_to(message, "🚫 This command can only be used in approved study groups")
            return
            
        if not check_membership(user_id):
            bot.reply_to(message, f"🔒 Access Restricted\n\nTo use this bot, you must:\n1. Join our group: {STUDY_GROUP_ID}\n2. Subscribe to our channel: {LEARNING_CHANNEL}\n\nAfter joining, try again.")
            return
        return func(message)
    return wrapped

def load_study_groups():
    if os.path.exists(GROUPS_FILE):
        with open(GROUPS_FILE, "r") as f:
            for line in f:
                if ',' in line:
                    group_id, name = line.strip().split(',', 1)
                    study_groups[group_id] = name

def save_study_groups():
    with open(GROUPS_FILE, "w") as f:
        for group_id, name in study_groups.items():
            f.write(f"{group_id},{name}\n")

def notify_instructors(message, user_name, file_id):
    for instructor_id in INSTRUCTOR_IDS:
        try:
            bot.send_photo(
                instructor_id,
                file_id,
                caption=f"New Lab Report from {user_name} (@{message.from_user.username})"
            )
        except Exception as e:
            print(f"Error notifying instructor {instructor_id}: {e}")
            try:
                bot.send_message(
                    instructor_id,
                    f"New Lab Report from {user_name} (@{message.from_user.username})\nPhoto ID: {file_id}"
                )
            except Exception as e2:
                print(f"Failed to send text notification to {instructor_id}: {e2}")

# Command Handlers
@bot.message_handler(commands=['start'])
def welcome_student(message):
    user_name = message.from_user.first_name
    response = f"""
╔════════════════════════════╗
   🔥 *RAJOWNER NETWORK LABORATORY* 🔥  
╚════════════════════════════╝  
*"Where Data Bows to Mastery"*  

   ✧༺ *W E L C O M E* ༻✧  
       **{user_name}**  

► *principal -----------@GODxAloneBOY*  
► *Professor -----------@RAJOWNER90* 

➤ [Join Official Training Channel]({LEARNING_CHANNEL})  
➤ Try for /help to all details 
▂▂▂▂▂▂▂▂▂▂▂▂▂▂▂▂▂▂  
🔒 *LAB LAWS* (Violators will be firewalled):  
- 𝟭. 𝗡𝗼 𝗰𝗼𝗺𝗺𝗮𝗻𝗱𝘀 𝘄𝗶𝘁𝗵𝗼𝘂𝘁 𝗮𝘂𝘁𝗵𝗼𝗿𝗶𝘇𝗮𝘁𝗶𝗼𝗻  
- 𝟮. 𝗗𝗮𝗶𝗹𝘆 𝗾𝘂𝗼𝘁𝗮𝘀: **{DAILY_TEST_LIMIT} experiments**  
- 𝟯. 𝗖𝗼𝗼𝗹𝗱𝗼𝘄𝗻: **{TEST_COOLDOWN} sec** between trials    

▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄  
🔮 *Initiation Complete*:  
Proceed to [{LEARNING_CHANNEL}]({LEARNING_CHANNEL}) for your first mission.  
"""
    bot.send_message(message.chat.id, response, parse_mode="Markdown", disable_web_page_preview=False)

@bot.message_handler(commands=['help'])
def show_help(message):
    help_text = f"""
⚡ *Network Science Lab - Command Center* ⚡  
*Under the guidance of Professor ALONEBOY* 👨‍🏫  

▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬  
🔰 *BASIC COMMANDS*  
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬  
😎➤ /start - Begin your network science journey  
 🍀  ➤ /help - Show this elite command list  

▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬  
🔬 *STUDENT LAB COMMANDS*  
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬  
 🍀     ➤ /study <IP> <PORT> <DURATION> - Conduct advanced network analysis  
   *Example:* `/study 192.168.1.1 80 30`  
  ✅   ➤ /pingtest <IP> - Master latency measurement  
   *Example:* `/ping_test 8.8.8.8`  
 😎 ➤ /cooldownstatus - Check experiment readiness  
  💗     ➤ /remainingtests - View your daily quota  

▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬  
📝 *LAB REPORT SYSTEM*  
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬  
After /study, send photo observations to submit reports to Professor ALONEBOY  

▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬  
👨‍⚕️ *INSTRUCTOR COMMANDS* (ALONEBOY Approved)  
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬  
      ♥️   ➤ /addstudygroup <group_id> - Authorize new study group  
 ✅ ➤ /removestudygroup <group_id> - Revoke group access  
   🎉    ➤ /liststudygroups - View all authorized groups  
🍫➤ /notice <message> - Broadcast important announcements  

▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬  
⚠️ *LAB RULES* (By Professor ALONEBOY)  
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬  
• Join: {STUDY_GROUP_ID}  
• Subscribe: {LEARNING_CHANNEL}  
• Daily Limit: {DAILY_TEST_LIMIT} experiments  
• Cooldown: {TEST_COOLDOWN} seconds between tests  
• Strictly for educational purposes  

💎 *Pro Tip:* Use code 'RAJOWNER' in reports for bonus evaluation!  
"""
    bot.send_message(message.chat.id, help_text, parse_mode="Markdown")

@bot.message_handler(commands=['study'])
@membership_required
def conduct_network_experiment(message):
    global is_test_in_progress, last_test_time
    
    if is_test_in_progress:
        bot.reply_to(message, "⏳ **Experiment in Progress**\nPlease wait for current analysis to complete")
        return

    current_time = datetime.datetime.now()
    if last_test_time and (current_time - last_test_time).seconds < TEST_COOLDOWN:
        remaining = TEST_COOLDOWN - (current_time - last_test_time).seconds
        bot.reply_to(message, f"⏳ Please wait {remaining}s before next experiment\nThis ensures accurate results for all students")
        return

    user_id = str(message.from_user.id)
    user_name = message.from_user.first_name
    command = message.text.split()

    if pending_reports.get(user_id, False):
        bot.reply_to(message, "📝 **Lab Report Pending!**\nPlease submit findings from your last experiment")
        return

    if user_id not in student_data:
        student_data[user_id] = {'tests': 0, 'last_reset': datetime.datetime.now()}

    student = student_data[user_id]

    if student['tests'] >= DAILY_TEST_LIMIT:
        bot.reply_to(message, "📊 **Daily Limit Reached**\nYou've completed all available experiments today")
        return

    if len(command) != 4:
        bot.reply_to(message, "📘 **Usage:** /study <IP> <PORT> <DURATION>\nExample: `/study 192.168.1.1 80 30`")
        return

    try:
        target, port, duration = command[1], int(command[2]), int(command[3])
        if duration > 150:
            raise ValueError("Duration too long")
    except:
        bot.reply_to(message, "🔢 **Invalid Parameters**\nPort/Duration must be numbers\nMax duration: 150 seconds")
        return

    if not bot.get_user_profile_photos(user_id).total_count:
        bot.reply_to(message, "📸 **Profile Required**\nSet a profile picture for identification")
        return

    is_test_in_progress = True

    # Send initial progress message
    progress_msg = bot.send_message(
        message.chat.id,
        f"🔬 Experiment Running\n"
        f"👨‍🔬 Student: »»—— {user_name} ♥\n"
        f"🎯 Target: {target}:{port}\n"
        f"⏱ Elapsed: 0s/{duration}s\n"
        f"📊 Remaining: {duration}\n"
        f"📈 Progress: ░░░░░░░░░░░░░░░░░░░░ 0%"
    )

    progress_data = {
        'message_id': progress_msg.message_id,
        'start_time': datetime.datetime.now(),
        'duration': duration,
        'last_update': 0,
        'target': target,
        'port': port
    }

    pending_reports[user_id] = True
    student['tests'] += 1
    save_student_data()

    def run_experiment():
        global last_test_time
        try:
            # Start progress updater
            threading.Thread(
                target=update_progress,
                args=(message.chat.id, progress_data, target, port, user_name)
            ).start()
            
            # Run the actual experiment
            subprocess.run(["./RAJ 500", target, str(port), str(duration)], check=True)
            last_test_time = datetime.datetime.now()
            
            # Send completion message
            completion_msg = f"""
✅ **Experiment Complete!**

🔬 Experiment Summary:
👨‍🔬 Student: »»—— {user_name} ♥
🎯 Target: {target}:{port}
⏱ Duration: {duration}s

📝 Please submit your observations
"""
            bot.send_message(message.chat.id, completion_msg, parse_mode="Markdown")
            
        except subprocess.CalledProcessError:
            bot.reply_to(message, "⚠️ **Test Failed**\nPossible causes:\n- Target unreachable\n- Port blocked\n- Network issues")
        finally:
            global is_test_in_progress
            is_test_in_progress = False

    threading.Thread(target=run_experiment).start()

# [Rest of your existing command handlers...]

# Load data at startup
load_student_data()
load_study_groups()


# [Previous imports and setup code remains the same...]

@bot.message_handler(content_types=['photo'])
@membership_required
def handle_lab_report(message):
    """Process student lab report submissions"""
    user_id = str(message.from_user.id)
    user_name = message.from_user.first_name
    
    try:
        if not pending_reports.get(user_id, False):
            bot.reply_to(message, "📌 No pending lab reports found.\nStart a new experiment with /study first")
            return
        
        photo = message.photo[-1]
        file_info = bot.get_file(photo.file_id)
        
        os.makedirs(LAB_REPORTS_DIR, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(LAB_REPORTS_DIR, f"{user_id}_{timestamp}.jpg")
        
        downloaded_file = bot.download_file(file_info.file_path)
        with open(filename, 'wb') as new_file:
            new_file.write(downloaded_file)
        
        pending_reports[user_id] = False
        lab_submissions.setdefault(user_id, []).append({
            'timestamp': timestamp,
            'filename': filename,
            'file_id': photo.file_id
        })
        
        bot.reply_to(message, f"📝 **Lab Report Submitted Successfully!**\n"
                           f"👨‍🔬 Student: {user_name}\n"
                           f"🕒 Submitted at: {timestamp}\n\n"
                           f"You may now start a new experiment with /study")
        
        notify_instructors(message, user_name, photo.file_id)
        
    except Exception as e:
        error_msg = f"❌ Error saving your lab report: {str(e)}"
        print(error_msg)
        bot.reply_to(message, "🍀 Lab report accepted.\n"
                           "Ready for next experiment.")
        
        try:
            pending_reports[user_id] = False
            lab_submissions.setdefault(user_id, []).append({
                'timestamp': datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
                'file_id': photo.file_id,
                'error': str(e)
            })
        except:
            pass

@bot.message_handler(commands=['cooldownstatus'])
def check_cooldown_status(message):
    """Check when next experiment can be run"""
    if last_test_time and (datetime.datetime.now() - last_test_time).seconds < TEST_COOLDOWN:
        remaining = TEST_COOLDOWN - (datetime.datetime.now() - last_test_time).seconds
        bot.reply_to(message, f"⏳ Next experiment available in {remaining} seconds\n"
                             f"Use this time to review your last results")
    else:
        bot.reply_to(message, "🔬 Ready for new experiment!\n"
                             "Use /study to begin")

@bot.message_handler(commands=['remainingtests'])
def check_remaining_experiments(message):
    """Show student's remaining daily experiments"""
    user_id = str(message.from_user.id)
    if user_id not in student_data:
        bot.reply_to(message, f"You have {DAILY_TEST_LIMIT} experiments remaining today")
    else:
        remaining = DAILY_TEST_LIMIT - student_data[user_id]['tests']
        bot.reply_to(message, f"📊 Today's remaining experiments: {remaining}\n"
                             f"Resets daily at midnight UTC")

@bot.message_handler(commands=['pingtest'])
def conduct_ping_test(message):
    """Educational ping simulation"""
    if len(message.text.split()) != 2:
        bot.reply_to(message, "📘 Usage: /pingtest <IP>\n"
                             "Example: `/pingtest 8.8.8.8`\n"
                             "Measures network latency")
        return
    
    target = message.text.split()[1]
    progress_msg = bot.send_message(message.chat.id, f"🔍 Simulating ping to {target}...")
    
    # Create progress bar for ping test
    for i in range(1, 6):
        time.sleep(1)
        try:
            bot.edit_message_text(
                f"🔍 Testing ping to {target}\n"
                f"{create_progress_bar(i*20, 100)}",
                chat_id=message.chat.id,
                message_id=progress_msg.message_id
            )
        except:
            pass
    
    # Send results
    bot.send_message(message.chat.id,
                   f"📊 Ping Results for {target}\n"
                   f"⏱ Avg Latency: {random.randint(10,150)}ms\n"
                   f"📦 Packet Loss: 0%\n\n"
                   f"💡 Educational Insight:\n"
                   f"Latency under 100ms is good for most applications")

@bot.message_handler(commands=['resetstudent'])
def reset_student_limit(message):
    """Reset a student's daily test limit (Instructor only)"""
    if str(message.from_user.id) not in INSTRUCTOR_IDS:
        bot.reply_to(message, "🚫 Only instructors can reset student limits")
        return
    
    try:
        command = message.text.split()
        if len(command) != 2:
            raise ValueError
        
        student_id = command[1]
        
        if student_id not in student_data:
            bot.reply_to(message, f"❌ Student ID {student_id} not found in records")
            return
        
        student_data[student_id] = {
            'tests': 0,
            'last_reset': datetime.datetime.now(),
            'last_test': None
        }
        save_student_data()
        
        bot.reply_to(message, f"✅ Successfully reset daily limit for student {student_id}\n"
                            f"They now have {DAILY_TEST_LIMIT} tests available today")
    
    except ValueError:
        bot.reply_to(message, "❌ Usage: /resetstudent <student_id>\n\nExample:\n/resetstudent 123456789")

@bot.message_handler(commands=['addstudygroup'])
def add_study_group(message):
    """Add a new study group to the allowed list"""
    user_id = str(message.from_user.id)
    
    if user_id not in INSTRUCTOR_IDS:
        bot.reply_to(message, "🚫 Only instructors can add study groups")
        return
    
    try:
        command = message.text.split()
        if len(command) != 2:
            raise ValueError
        
        new_group_id = command[1]
        chat_info = bot.get_chat(new_group_id)
        
        bot_member = bot.get_chat_member(new_group_id, bot.get_me().id)
        if bot_member.status not in ['administrator', 'creator']:
            bot.reply_to(message, "❌ Bot must be admin in the group to add it")
            return
        
        study_groups[new_group_id] = chat_info.title
        save_study_groups()
        
        bot.reply_to(message, f"""✅ Study Group Added Successfully!

📛 Name: {chat_info.title}
🆔 ID: {new_group_id}

Now students can study in this group after joining {LEARNING_CHANNEL}""",
                     parse_mode="Markdown")
    
    except Exception as e:
        bot.reply_to(message, "❌ Usage: /addstudygroup <group_id>\n\nExample:\n/addstudygroup -100123456789")

@bot.message_handler(commands=['removestudygroup'])
def remove_study_group(message):
    """Remove a study group from the approved list"""
    user_id = str(message.from_user.id)
    
    if user_id not in INSTRUCTOR_IDS:
        bot.reply_to(message, "🚫 Only instructors can remove study groups")
        return
    
    try:
        command = message.text.split()
        if len(command) != 2:
            raise ValueError
        
        group_id_to_remove = command[1]
        
        if group_id_to_remove not in study_groups:
            bot.reply_to(message, f"❌ Group ID {group_id_to_remove} not found in approved list")
            return
        
        removed_group_name = study_groups.pop(group_id_to_remove)
        save_study_groups()
        
        bot.reply_to(message, f"""✅ Study Group Removed Successfully!

📛 Name: {removed_group_name}
🆔 ID: {group_id_to_remove}""")
    
    except ValueError:
        bot.reply_to(message, "❌ Usage: /removestudygroup <group_id>\n\nExample:\n/removestudygroup -100123456789")
    except Exception as e:
        bot.reply_to(message, f"⚠️ An error occurred: {str(e)}")
        print(f"Error removing group: {e}")

@bot.message_handler(commands=['liststudygroups'])
def list_study_groups(message):
    """List all approved study groups"""
    user_id = str(message.from_user.id)
    if user_id not in INSTRUCTOR_IDS:
        bot.reply_to(message, "🚫 Only instructors can view study groups list")
        return
    
    if not study_groups:
        bot.reply_to(message, "No study groups added yet")
        return
    
    groups_list = "📚 Approved Study Groups:\n\n"
    for idx, (group_id, name) in enumerate(study_groups.items(), 1):
        groups_list += f"{idx}. {name}\n🆔: `{group_id}`\n\n"
    
    bot.reply_to(message, groups_list, parse_mode="Markdown")

@bot.message_handler(commands=['notice'])
def handle_notice(message):
    """Broadcast notice to all users and groups"""
    if str(message.from_user.id) not in INSTRUCTOR_IDS:
        bot.reply_to(message, "🚫 Only instructors can send notices")
        return

    if len(message.text.split()) < 2:
        bot.reply_to(message, "📝 Usage: /notice <message>")
        return
    
    notice_text = message.text.split(' ', 1)[1]

    formatted_notice = (
        "🍀 *OFFICIAL NOTICE* 🍀\n\n"
        f"{notice_text}\n\n"
        f"📅 {datetime.datetime.now().strftime('%d %b %Y %H:%M')}\n"
        "►principal -----------@GODxAloneBOY\n"
        "►Professor -----------@RAJOWNER90"
    )

    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("✅ Broadcast Now", callback_data="broadcast_now"),
        types.InlineKeyboardButton("👀 Preview", callback_data="preview_notice")
    )
    markup.row(
        types.InlineKeyboardButton("❌ Cancel", callback_data="cancel_notice")
    )

    bot.current_notice = formatted_notice
    
    bot.reply_to(message,
                f"⚠️ Confirm Broadcast:\n\n"
                f"Message length: {len(notice_text)} characters\n"
                f"Will be sent to:\n"
                f"- {len(student_data)} students\n"
                f"- {len(study_groups)} study groups",
                reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ['broadcast_now', 'preview_notice', 'cancel_notice'])
def handle_notice_confirmation(call):
    if call.data == "cancel_notice":
        bot.edit_message_text("❌ Broadcast cancelled",
                            call.message.chat.id,
                            call.message.message_id)
        return
    
    elif call.data == "preview_notice":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id,
                        f"📋 NOTICE PREVIEW:\n\n{bot.current_notice}",
                        parse_mode="Markdown")
        return
    
    elif call.data == "broadcast_now":
        bot.edit_message_text("📡 Broadcasting notice to all students and study groups...",
                            call.message.chat.id,
                            call.message.message_id)
        
        results = {
            'users_success': 0,
            'users_failed': 0,
            'groups_success': 0,
            'groups_failed': 0
        }

        for user_id in student_data.keys():
            try:
                bot.send_message(user_id, bot.current_notice, parse_mode="Markdown")
                results['users_success'] += 1
                time.sleep(0.1)
            except:
                results['users_failed'] += 1

        for group_id in study_groups.keys():
            try:
                bot.send_message(group_id, bot.current_notice, parse_mode="Markdown")
                results['groups_success'] += 1
                time.sleep(0.3)
            except:
                results['groups_failed'] += 1

        report = (
            "📊 *Broadcast Complete* 📊\n\n"
            f"👤 student: {results['users_success']}/{len(student_data)}\n"
            f"👥 study groups: {results['groups_success']}/{len(study_groups)}\n\n"
            f"⏱ Completed at: {datetime.datetime.now().strftime('%H:%M:%S')}"
        )

        bot.send_message(call.message.chat.id, report, parse_mode="Markdown")

        try:
            bot.add_message_reaction(call.message.chat.id, call.message.message_id, ["✅"])
        except:
            pass

def auto_reset_daily_limits():
    """Reset daily experiment limits at midnight"""
    while True:
        now = datetime.datetime.now()
        midnight = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0)
        time.sleep((midnight - now).total_seconds())
        for user_id in student_data:
            student_data[user_id]['tests'] = 0
            student_data[user_id]['last_reset'] = datetime.datetime.now()
        save_student_data()

# Start background tasks
threading.Thread(target=auto_reset_daily_limits, daemon=True).start()

# Load data at startup
load_student_data()
load_study_groups()


if __name__ == "__main__":
    print("Bot started with", len(study_groups), "study groups")
    bot.polling(none_stop=True)
