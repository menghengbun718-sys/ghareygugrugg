import json
import os

try:
    import msvcrt
except ImportError:  # Linux / Ubuntu
    msvcrt = None

try:
    import fcntl
except ImportError:  # Windows
    fcntl = None

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ChatMemberHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# =========================
# SETTINGS
# =========================

BOT_TOKEN = "Your Bot token"

# Teacher Telegram User ID
ADMIN_IDS = [123456789]
TEACHER_PASSWORD = "1234"
TEACHER_AUTH = set()
ANSWER_VIEWER_NAMES = {"muy lyly", "heng"}
CHECK_ACCESS = set()

SCORES_FILE = "scores.json"
USERS_FILE = "users.json"
CHECK_ACCESS_FILE = "check_access.json"
EXERCISES_FILE = "exercises.json"

# =========================
# =========================
# /start       - ចាប់ផ្ដើម
# /score       - មើលពិន្ទុសិស្សទាំងអស់
# /top         - មើល Top Scores
# /clear       - លុបពិន្ទុទាំងអស់
# /students    - ចំនួនសិស្សដែលបានប្រឡង
# /help        - ជំនួយ

# =========================
# SAVE / LOAD SCORES
# =========================

def load_scores():
    if os.path.exists(SCORES_FILE):
        with open(SCORES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_score(name, score):
    scores = load_scores()

    scores.append({
        "name": name,
        "score": score
    })

    with open(SCORES_FILE, "w", encoding="utf-8") as f:
        json.dump(scores, f, ensure_ascii=False, indent=4)


# =========================
# SAVE / LOAD USERS
# =========================

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Convert string keys back to integers
            return {int(k): v for k, v in data.items()}
    return {}


def save_users():
    # Convert integer keys to strings for JSON compatibility
    users_to_save = {str(k): v for k, v in users.items()}
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users_to_save, f, ensure_ascii=False, indent=4)


def load_check_access():
    if os.path.exists(CHECK_ACCESS_FILE):
        with open(CHECK_ACCESS_FILE, "r", encoding="utf-8") as f:
            return {int(user_id) for user_id in json.load(f)}
    return set()


def save_check_access():
    with open(CHECK_ACCESS_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(CHECK_ACCESS), f, indent=4)


# =========================
# QUIZ QUESTIONS
# =========================
# Message to send: សូមស្វាគមន៍ {session.name}!
# Please do these exercises.
# ចាប់ផ្ដើមធ្វើតេស្តឥឡូវនេះ 👇

DEFAULT_QUESTIONS = [
    {
        "question": "១. នៅក្នុងត្រីកោណកែង តើអនុគមន៍ស៊ីនុស (Sin) នៃមុំស្រួចមួយស្មើនឹងផលធៀបអ្វី?",
        "options": ["ក. ជ្រុងឈម និង ជ្រុងជាប់", "ខ. ជ្រុងឈម និង អ៊ីប៉ូតេនុស", "គ. ជ្រុងជាប់ និង អ៊ីប៉ូតេនុស"],
        "answer": 1
    },
    {
        "question": "២. ត្រីកោណកែងមួយមានជ្រុងឈមមុំ A ប្រវែង 3cm និងអ៊ីប៉ូតេនុសប្រវែង 5cm។ តើ Sin(A) មានតម្លៃប៉ុន្មាន?",
        "options": ["ក. 3/5", "ខ. 4/5", "គ. 3/4"],
        "answer": 0
    },
    {
        "question": "៣. នៅក្នុងត្រីកោណកែង តើអនុគមន៍កូស៊ីនុស (Cos) នៃមុំស្រួចមួយស្មើនឹងផលធៀបអ្វី?",
        "options": ["ក. ជ្រុងឈម និង អ៊ីប៉ូតេនុស", "ខ. ជ្រុងជាប់ និង អ៊ីប៉ូតេនុស", "គ. ជ្រុងឈម និង ជ្រុងជាប់"],
        "answer": 1
    },
    {
        "question": "៤. ត្រីកោណកែងមួយមានជ្រុងឈមមុំ B ប្រវែង 4cm និងជ្រុងជាប់ប្រវែង 3cm។ តើ Tan(B) មានតម្លៃប៉ុន្មាន?",
        "options": ["ក. 3/4", "ខ. 4/5", "គ. 4/3"],
        "answer": 2
    },
    {
        "question": "៥. បើមុំ C ជាមុំស្រួចនៃត្រីកោណកែង ហើយ Sin(C) = 1/2 នោះតើមុំ C មានរង្វាស់ប៉ុន្មានដឺក្រេ?",
        "options": ["ក. 30°", "ខ. 45°", "គ. 60°"],
        "answer": 0
    },
    {
        "question": "៦. នៅក្នុងត្រីកោណកែង តើអនុគមន៍តង់សង់ (Tan) នៃមុំស្រួចមួយស្មើនឹងផលធៀបអ្វី?",
        "options": ["ក. ជ្រុងជាប់ និង ជ្រុងឈម", "ខ. ជ្រុងឈម និង ជ្រុងជាប់", "គ. ជ្រុងឈម និង អ៊ីប៉ូតេនុស"],
        "answer": 1
    },
    {
        "question": "៧. បើមុំ A ជាមុំស្រួចនៃត្រីកោណកែង ហើយ Cos(A) = 1/2 នោះតើមុំ A មានរង្វាស់ប៉ុន្មានដឺក្រេ?",
        "options": ["ក. 30°", "ខ. 45°", "គ. 60°"],
        "answer": 2
    },
    {
        "question": "៨. ត្រីកោណកែងមួយមានជ្រុងជាប់មុំ C ប្រវែង 6cm និងអ៊ីប៉ូតេនុសប្រវែង 10cm។ តើ Cos(C) មានតម្លៃប៉ុន្មាន?",
        "options": ["ក. 6/10 ឬ 3/5", "ខ. 8/10 ឬ 4/5", "គ. 10/6 ឬ 5/3"],
        "answer": 0
    },
    {
        "question": "៩. តម្លៃនៃ Tan(45°) គឺស្មើនឹងប៉ុន្មាន?",
        "options": ["ក. 0", "ខ. 1", "គ. មិនអាចកំណត់បាន"],
        "answer": 1
    },
    {
        "question": "១០. តាមទ្រឹស្តីបទពីតាក័រ នៅក្នុងត្រីកោណកែង បើ a និង b ជាជ្រុងជាប់មុំកែង និង c ជាអ៊ីប៉ូតេនុស តើរូបមន្តមួយណាត្រឹមត្រូវ?",
        "options": ["ក. c² = a² + b²", "ខ. a² = b² + c²", "គ. c = a + b"],
        "answer": 0
    }
]


def load_questions():
    if os.path.exists(EXERCISES_FILE):
        with open(EXERCISES_FILE, "r", encoding="utf-8") as f:
            loaded_questions = json.load(f)
        if not isinstance(loaded_questions, list):
            return DEFAULT_QUESTIONS.copy()
        return [
            item
            for item in loaded_questions
            if (
                isinstance(item, dict)
                and isinstance(item.get("question"), str)
                and item["question"].strip()
                and isinstance(item.get("options"), list)
                and len(item["options"]) >= 2
                and isinstance(item.get("answer"), int)
                and 0 <= item["answer"] < len(item["options"])
                and ("photo" not in item or isinstance(item["photo"], str))
            )
        ]
    return DEFAULT_QUESTIONS.copy()


def save_questions():
    with open(EXERCISES_FILE, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=4)


questions = load_questions()

# =========================
# USER DATA
# =========================

users = load_users()  # Load users data at startup
CHECK_ACCESS = load_check_access()


def has_staff_access(user_id):
    user = users.get(user_id, {})
    return (
        user_id in ADMIN_IDS
        or user_id in TEACHER_AUTH
        or user.get("role") in {"teacher", "dev"}
    )


# =========================
# ROLE / LOGIN FLOW
# =========================

def get_user_data(user_id):
    if user_id not in users:
        users[user_id] = {
            "name": "",
            "score": 0,
            "question": 0,
            "role": None
        }
        save_users()  # Save users data when new user is created
    return users[user_id]


def build_role_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👨‍🏫 Teacher", callback_data="role:teacher"),
            InlineKeyboardButton("👨‍🎓 Student", callback_data="role:student"),
            InlineKeyboardButton(" Developer", callback_data="role:dev")
        ]
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user_data(user_id)
    user["name"] = update.effective_user.full_name
    user["score"] = 0
    user["question"] = 0
    user["role"] = None

    context.user_data["state"] = "waiting_name"
    await update.message.reply_text("Please enter your name")


async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_id = update.effective_user.id
    user = get_user_data(user_id)
    name = update.message.text.strip()

    if not name:
        await update.message.reply_text("Name is not valid. Please enter your name again")
        return

    user["name"] = name
    save_users()  # Save after name change
    context.user_data["state"] = "waiting_role"
    await update.message.reply_text(
        "1. Choose your role",
        reply_markup=build_role_keyboard()
    )


async def handle_role_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    user = get_user_data(user_id)
    choice = query.data.split(":", 1)[1] if query.data else ""

    if choice == "teacher":
        user["role"] = "teacher"
        context.user_data["state"] = "waiting_teacher_password"
        await query.edit_message_text(
            f"👤 Name: {user['name']}\n\nPlease enter the teacher password"
        )
        return

    if choice == "student":
        user["role"] = "student"
        save_users()  # Save after role selection
        context.user_data["state"] = "none"
        await query.edit_message_text(f"✅ Name: {user['name']}\nRole: Student")
        await send_question(update, context)
        return

    if choice == "dev":
        context.user_data["state"] = "waiting_dev_password"
        await query.edit_message_text(
            f"👤 Name: {user['name']}\n\nPlease enter the developer password"
        )
        return

    await query.edit_message_text("❌ Invalid selection")


async def handle_teacher_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_id = update.effective_user.id
    user = get_user_data(user_id)
    entered_password = update.message.text.strip()

    if entered_password == TEACHER_PASSWORD:
        user["role"] = "teacher"
        save_users()  # Save after role change
        TEACHER_AUTH.add(user_id)
        context.user_data["state"] = "none"
        await update.message.reply_text(
            f"✅ Teacher {user['name']} verified successfully\n\n"
            "Teacher can use these commands:\n\n"
            "/start - ចាប់ផ្ដើម\n"
            "/score - មើលពិន្ទុសិស្សទាំងអស់\n"
            "/top - មើល Top Scores\n"
            "/clear - លុបពិន្ទុទាំងអស់\n"
            "/students - ចំនួនសិស្សដែលបានប្រឡង\n"
            "/addexercise - Add a new exercise\n"
            "/editexercise - Edit an existing exercise\n"
            "/deleteexercise - Delete an exercise\n"
            "/check - View the correct answers\n"
            "/help - ជំនួយ"
        )
        return

    await update.message.reply_text(
        "❌ Incorrect password. Please enter the teacher password again"
    )


async def handle_dev_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_id = update.effective_user.id
    user = get_user_data(user_id)
    entered_password = update.message.text.strip()

    if entered_password == TEACHER_PASSWORD:
        user["role"] = "dev"
        save_users()
        context.user_data["state"] = "none"
        await update.message.reply_text(
            f"✅ Developer {user['name']} verified successfully"
        )
        await send_question(update, context)
        return

    await update.message.reply_text(
        "❌ Incorrect password. Please enter the developer password again"
    )


# =========================
# SEND QUESTION
# =========================

async def send_question(update, context):
    user_id = update.effective_user.id
    user = users[user_id]

    if not user.get("role"):
        return

    if not questions:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="សូមរងចាំលោកគ្រូបង្កើតលំហាត់។"
        )
        return

    if user["question"] >= len(questions):
        await finish_quiz(update, context)
        return

    # Send welcome message before first question
    if user["question"] == 0:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"សូមស្វាគមន៍ {user['name']}!\n\n"
            "Please do these exercises.\n\n"
            "ចាប់ផ្ដើមធ្វើតេស្តឥឡូវនេះ 👇"
        )

    q = questions[user["question"]]

    keyboard = []

    for i, option in enumerate(q["options"]):
        keyboard.append([
            InlineKeyboardButton(
                option,
                callback_data=f"quiz:{user['question']}:{i}"
            )
        ])

    reply_markup = InlineKeyboardMarkup(keyboard)
    if q.get("photo"):
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=q["photo"],
            caption=q["question"],
            reply_markup=reply_markup
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=q["question"],
            reply_markup=reply_markup
        )


async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user_data(user_id)

    if not user.get("role"):
        await update.message.reply_text("Please use /start first to register for the quiz.")
        return

    user["score"] = 0
    user["question"] = 0
    save_users()
    await send_question(update, context)


# =========================
# ANSWER
# =========================

async def answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not query.data or not query.data.startswith("quiz:"):
        return

    try:
        _, q_index, choice = query.data.split(":")
        q_index = int(q_index)
        choice = int(choice)
    except ValueError:
        await query.edit_message_text("❌ Invalid answer")
        return

    user_id = query.from_user.id
    user = users.get(user_id)
    if not user or q_index != user["question"]:
        await query.edit_message_text("⚠️ សំណួរនេះមិនសកម្មទៀតទេ។ សូមប្រើ /start ដើម្បីចាប់ផ្ដើមថ្មី។")
        return

    if q_index < 0 or q_index >= len(questions) or choice < 0 or choice >= len(questions[q_index]["options"]):
        await query.edit_message_text("❌ Invalid answer")
        return

    if choice == questions[q_index]["answer"]:
        user["score"] += 10

    # Track which answer number (1, 2, 3, etc.)
    answer_number = user["question"] + 1

    user["question"] += 1
    save_users()  # Save after each answer

    await query.edit_message_text(f"✅ ចម្លើយទី {answer_number} ត្រូវបានកត់ត្រា។")

    await send_question(update, context)


# =========================
# FINISH QUIZ
# =========================

async def finish_quiz(update, context):
    user_id = update.effective_user.id
    user = users[user_id]

    save_score(user["name"], user["score"])

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            f"🏁 Quiz Finished\n\n"
            f"👤 Name: {user['name']}\n\n"
            f"The result has been saved successfully."
        )
    )


# =========================
# ADMIN VIEW SCORES
# =========================

async def score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not has_staff_access(user_id):
        await update.message.reply_text(
            "❌ Only teachers or Developers can view the scores."
        )
        return

    scores = load_scores()

    if not scores:
        await update.message.reply_text("No scores yet.")
        return

    msg = "📊 Student Scores\n\n"

    for item in scores:
        msg += f"👤 {item['name']} — {item['score']} points\n"

    await update.message.reply_text(msg)


# =========================
# TEACHER COMMANDS
# =========================

async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not has_staff_access(user_id):
        await update.message.reply_text(
            "❌ Only teachers or Developers can view the top scores."
        )
        return

    scores = load_scores()

    if not scores:
        await update.message.reply_text("No scores yet.")
        return

    # Sort by score descending and get top 5
    sorted_scores = sorted(scores, key=lambda x: x['score'], reverse=True)[:5]

    msg = "🏆 Top Scores\n\n"

    for i, item in enumerate(sorted_scores, 1):
        msg += f"{i}. 👤 {item['name']} — {item['score']} points\n"

    await update.message.reply_text(msg)


async def clear_scores(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not has_staff_access(user_id):
        await update.message.reply_text(
            "❌ Only teachers or Developers can clear scores."
        )
        return

    # Clear the scores file
    with open(SCORES_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=4)

    await update.message.reply_text("✅ All scores have been cleared.")


async def students_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not has_staff_access(user_id):
        await update.message.reply_text(
            "❌ Only teachers or Developers can view student count."
        )
        return

    scores = load_scores()
    count = len(scores)

    await update.message.reply_text(
        f"📚 Number of Students Tested\n\n"
        f"Total: {count} students"
    )


async def list_user_ids(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not has_staff_access(user_id):
        await update.message.reply_text(
            "❌ Only teachers or Developers can view user IDs."
        )
        return

    if not users:
        await update.message.reply_text("No registered users yet.")
        return

    msg = "👥 Registered User IDs\n\n"
    for registered_id, user in users.items():
        name = user.get("name") or "Unnamed"
        role = user.get("role") or "Not selected"
        msg += f"ID: {registered_id}\n user: {name}\nRole: {role}\n\n"

    await update.message.reply_text(msg)


def teacher_only(user_id):
    return has_staff_access(user_id)


async def add_exercise(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not teacher_only(update.effective_user.id):
        await update.message.reply_text("❌ Only teachers or Developers can add exercises.")
        return

    context.user_data["state"] = "exercise_add_question"
    await update.message.reply_text(
        "✏️ Send the new exercise question. Math symbols are supported, for example: "
        "√, ², ³, π, ×, ÷, ≤, ≥, ≠, ∑, ∫, or $x^2$.\n"
        "You can also send a photo with the question as its caption."
    )


async def edit_exercise(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not teacher_only(update.effective_user.id):
        await update.message.reply_text("❌ Only teachers or Developers can edit exercises.")
        return

    if not questions:
        await update.message.reply_text("There are no exercises to edit.")
        return

    keyboard = [
        [InlineKeyboardButton(f"{index + 1}. {item['question'][:40]}", callback_data=f"editq:{index}")]
        for index, item in enumerate(questions)
    ]
    await update.message.reply_text(
        "Choose an exercise to edit:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def exercise_edit_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not teacher_only(query.from_user.id):
        await query.edit_message_text("❌ Only teachers or Developers can edit exercises.")
        return

    exercise_index = int(query.data.split(":", 1)[1])
    if exercise_index < 0 or exercise_index >= len(questions):
        await query.edit_message_text("❌ Invalid exercise.")
        return

    context.user_data["exercise_index"] = exercise_index
    context.user_data["state"] = "exercise_edit_question"
    await query.edit_message_text(
        "Send the updated question, or send - to keep the current question. "
        "Math symbols are supported.\n\n"
        + questions[exercise_index]["question"]
    )


async def delete_exercise(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not teacher_only(update.effective_user.id):
        await update.message.reply_text("❌ Only teachers or Developers can delete exercises.")
        return

    if not questions:
        await update.message.reply_text("There are no exercises to delete.")
        return

    if context.args and context.args[0].casefold() == "all":
        context.user_data.pop("delete_exercise_index", None)
        context.user_data["delete_all_exercises"] = True
        keyboard = [[
            InlineKeyboardButton("✅ Yes, delete all", callback_data="confirmdelete:yes"),
            InlineKeyboardButton("❌ Cancel", callback_data="confirmdelete:no"),
        ]]
        await update.message.reply_text(
            f"Are you sure you want to delete all {len(questions)} exercises?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if context.args:
        try:
            exercise_index = int(context.args[0]) - 1
        except ValueError:
            exercise_index = -1
        if exercise_index < 0 or exercise_index >= len(questions):
            await update.message.reply_text(
                f"❌ Invalid exercise number. Choose a number from 1 to {len(questions)}."
            )
            return
        context.user_data.pop("delete_all_exercises", None)
        context.user_data["delete_exercise_index"] = exercise_index
        keyboard = [[
            InlineKeyboardButton("✅ Yes, delete", callback_data="confirmdelete:yes"),
            InlineKeyboardButton("❌ Cancel", callback_data="confirmdelete:no"),
        ]]
        await update.message.reply_text(
            "Are you sure you want to delete this exercise?\n\n"
            + questions[exercise_index]["question"],
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    keyboard = [
        [InlineKeyboardButton(f"{index + 1}. {item['question'][:40]}", callback_data=f"deleteq:{index}")]
        for index, item in enumerate(questions)
    ]
    keyboard.append([
        InlineKeyboardButton("🗑️ Delete all exercises", callback_data="deleteall:yes")
    ])
    await update.message.reply_text(
        "Choose an exercise to delete:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def exercise_delete_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not teacher_only(query.from_user.id):
        await query.edit_message_text("❌ Only teachers or Developers can delete exercises.")
        return

    if query.data.startswith("deleteall:"):
        context.user_data.pop("delete_exercise_index", None)
        context.user_data["delete_all_exercises"] = True
        keyboard = [[
            InlineKeyboardButton("✅ Yes, delete all", callback_data="confirmdelete:yes"),
            InlineKeyboardButton("❌ Cancel", callback_data="confirmdelete:no"),
        ]]
        await query.edit_message_text(
            f"Are you sure you want to delete all {len(questions)} exercises?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    try:
        exercise_index = int(query.data.split(":", 1)[1])
    except (ValueError, IndexError):
        await query.edit_message_text("❌ Invalid exercise.")
        return
    if exercise_index < 0 or exercise_index >= len(questions):
        await query.edit_message_text("❌ Invalid exercise.")
        return

    context.user_data.pop("delete_all_exercises", None)
    context.user_data["delete_exercise_index"] = exercise_index
    keyboard = [[
        InlineKeyboardButton("✅ Yes, delete", callback_data="confirmdelete:yes"),
        InlineKeyboardButton("❌ Cancel", callback_data="confirmdelete:no"),
    ]]
    await query.edit_message_text(
        "Are you sure you want to delete this exercise?\n\n"
        + questions[exercise_index]["question"],
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def confirm_delete_exercise(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not teacher_only(query.from_user.id):
        await query.edit_message_text("❌ Only teachers or Developers can delete exercises.")
        return

    if query.data.endswith(":no"):
        context.user_data.pop("delete_exercise_index", None)
        context.user_data.pop("delete_all_exercises", None)
        await query.edit_message_text("❎ Exercise deletion cancelled.")
        return

    if context.user_data.pop("delete_all_exercises", False):
        deleted_count = len(questions)
        questions.clear()
        save_questions()
        context.user_data.pop("delete_exercise_index", None)
        await query.edit_message_text(f"✅ Deleted all {deleted_count} exercises.")
        return

    exercise_index = context.user_data.pop("delete_exercise_index", None)
    if exercise_index is None or exercise_index < 0 or exercise_index >= len(questions):
        await query.edit_message_text("❌ This exercise is no longer available.")
        return

    questions.pop(exercise_index)
    save_questions()
    await query.edit_message_text(f"✅ Exercise {exercise_index + 1} was deleted.")


async def exercise_correct_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not teacher_only(query.from_user.id):
        await query.edit_message_text("❌ Only teachers or Developers can manage exercises.")
        return

    correct_answer = int(query.data.split(":", 1)[1])
    if query.data.startswith("addcorrect:"):
        questions.append({
            "question": context.user_data.pop("exercise_question"),
            "options": context.user_data.pop("exercise_options"),
            "answer": correct_answer,
        })
        photo = context.user_data.pop("exercise_photo", None)
        if photo:
            questions[-1]["photo"] = photo
        message = f"✅ Exercise {len(questions)} was added."
    else:
        exercise_index = context.user_data.pop("exercise_index")
        exercise = questions[exercise_index]
        exercise["question"] = context.user_data.pop("exercise_question", exercise["question"])
        exercise["options"] = context.user_data.pop("exercise_options", exercise["options"])
        exercise["answer"] = correct_answer
        photo = context.user_data.pop("exercise_photo", None)
        if photo:
            exercise["photo"] = photo
        message = f"✅ Exercise {exercise_index + 1} was updated."

    save_questions()
    context.user_data["state"] = "none"
    await query.edit_message_text(message)


def parse_options(text):
    options = [option.strip() for option in text.split("|") if option.strip()]
    return options if len(options) >= 2 else None


def answer_keyboard(prefix, options):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{index + 1}. {option}", callback_data=f"{prefix}:{index}")]
        for index, option in enumerate(options)
    ])


async def exercise_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get("state")
    text = update.message.text.strip()

    if state == "exercise_add_question":
        if not text:
            await update.message.reply_text("Question cannot be empty.")
            return
        context.user_data["exercise_question"] = text
        context.user_data["state"] = "exercise_add_options"
        await update.message.reply_text(
            "Send the choices separated by | (example: A | B | C). "
            "Math symbols such as √, ², π, ×, ÷ and fractions are allowed."
        )
        return

    if state == "exercise_add_options":
        options = parse_options(text)
        if not options:
            await update.message.reply_text("Please provide at least two choices separated by |.")
            return
        context.user_data["exercise_options"] = options
        context.user_data["state"] = "none"
        await update.message.reply_text(
            "Choose the correct answer:", reply_markup=answer_keyboard("addcorrect", options)
        )
        return

    if state == "exercise_edit_question":
        if text != "-":
            if not text:
                await update.message.reply_text("Question cannot be empty.")
                return
            context.user_data["exercise_question"] = text
        context.user_data["state"] = "exercise_edit_options"
        exercise = questions[context.user_data["exercise_index"]]
        await update.message.reply_text(
            "Send updated choices separated by |, or send - to keep them.\n\n" + " | ".join(exercise["options"])
        )
        return

    if state == "exercise_edit_options":
        if text != "-":
            options = parse_options(text)
            if not options:
                await update.message.reply_text("Please provide at least two choices separated by |.")
                return
            context.user_data["exercise_options"] = options
        context.user_data["state"] = "none"
        exercise = questions[context.user_data["exercise_index"]]
        options = context.user_data.get("exercise_options", exercise["options"])
        await update.message.reply_text("Choose the correct answer:", reply_markup=answer_keyboard("editcorrect", options))


async def exercise_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get("state")
    if state not in {"exercise_add_question", "exercise_edit_question"}:
        return

    if not teacher_only(update.effective_user.id):
        await update.message.reply_text("❌ Only teachers or Developers can manage exercises.")
        return

    photo = update.message.photo[-1]
    caption = (update.message.caption or "").strip()
    if state == "exercise_add_question" and not caption:
        await update.message.reply_text("Please send the photo with the exercise question as its caption.")
        return

    if state == "exercise_edit_question":
        if caption and caption != "-":
            context.user_data["exercise_question"] = caption
        context.user_data["exercise_photo"] = photo.file_id
        context.user_data["state"] = "exercise_edit_options"
        exercise = questions[context.user_data["exercise_index"]]
        await update.message.reply_text(
            "Photo saved. Send updated choices separated by |, or send - to keep them.\n\n"
            + " | ".join(exercise["options"])
        )
        return

    context.user_data["exercise_question"] = caption
    context.user_data["exercise_photo"] = photo.file_id
    context.user_data["state"] = "exercise_add_options"
    await update.message.reply_text(
        "Photo saved. Send the choices separated by | (example: A | B | C)."
    )


async def check_answers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    user = users.get(user_id, {})
    normalized_name = user.get("name", "").strip().casefold()
    is_named_answer_viewer = normalized_name in ANSWER_VIEWER_NAMES
    is_privileged_role = user.get("role") in {"teacher", "dev"}

    if (
        user_id not in ADMIN_IDS
        and user_id not in TEACHER_AUTH
        and user_id not in CHECK_ACCESS
        and not is_privileged_role
        and not is_named_answer_viewer
    ):
        await update.message.reply_text(
            "❌ Only teachers or approved answer viewers can view the answers."
        )
        return

    msg = "📋 Answer Key\n\n"

    for i, q in enumerate(questions, 1):
        correct_option = q["options"][q["answer"]]
        msg += f"{i}. {q['question']}\n"
        msg += f"   ✅ Answer: {correct_option}\n\n"

    await update.message.reply_text(msg)


async def give_access(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = users.get(user_id, {})
    normalized_name = user.get("name", "").strip().casefold()

    if normalized_name != "heng":
        await update.message.reply_text("❌ Only Heng can use /give.")
        return

    access_type = context.args[0].casefold() if context.args else ""
    if access_type not in {"check", "dev"}:
        await update.message.reply_text(
            "Usage: reply with /give check or /give dev\n"
            "or use /give check <telegram_user_id>\n"
            "or /give dev <telegram_user_id>"
        )
        return

    target_id = None
    if update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id
    elif len(context.args) > 1:
        try:
            target_id = int(context.args[1])
        except ValueError:
            target_id = None

    if target_id is None:
        await update.message.reply_text(
            "Usage: reply to a person's message with /give "
            f"{access_type}\nor use /give {access_type} <telegram_user_id>"
        )
        return

    if access_type == "check":
        CHECK_ACCESS.add(target_id)
        save_check_access()
        await update.message.reply_text(f"✅ User {target_id} can now use /check.")
        return

    target_user = get_user_data(target_id)
    target_user["role"] = "dev"
    save_users()
    await update.message.reply_text(
        f"✅ User {target_id} now has the Developer role and can use /check."
    )


async def send_server_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = users.get(user_id, {})

    if user_id not in ADMIN_IDS and user.get("role") != "dev":
        await update.message.reply_text("❌ Only Developers can send server time notices.")
        return

    arguments = context.args
    broadcast = bool(arguments) and arguments[0].casefold() == "all"
    target_id = None
    if broadcast and update.message.reply_to_message:
        await update.message.reply_text("❌ Use either 'all' or reply to one user, not both.")
        return
    if update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id
    elif arguments and not broadcast:
        try:
            target_id = int(arguments[0])
        except ValueError:
            target_id = None

    time_arguments = arguments[1:] if broadcast or (target_id is not None and not update.message.reply_to_message) else arguments
    if (not broadcast and target_id is None) or len(time_arguments) != 2:
        await update.message.reply_text(
            "Usage: /servertime <user_id> <off_time> <on_time>\n"
            "Or reply to a user message: /servertime <off_time> <on_time>\n"
            "To send everyone: /servertime all <off_time> <on_time>\n"
            "Example: /servertime all 22:00 06:00"
        )
        return

    off_time, on_time = time_arguments
    notice = (
        "🖥️ Server Schedule\n\n"
        f"Server OFF time: {off_time}\n"
        f"Server ON time: {on_time}\n\n"
        "Please plan your work accordingly."
    )

    if broadcast:
        sent_count = 0
        failed_count = 0
        for recipient_id in users:
            try:
                await context.bot.send_message(chat_id=recipient_id, text=notice)
                sent_count += 1
            except Exception:
                failed_count += 1
        await update.message.reply_text(
            f"✅ Server time notice sent to {sent_count} users.\n"
            f"❌ Failed: {failed_count} users."
        )
        return

    try:
        await context.bot.send_message(
            chat_id=target_id,
            text=notice
        )
    except Exception:
        await update.message.reply_text(
            "❌ Could not send the notice. Check the user ID and make sure the user started the bot."
        )
        return

    await update.message.reply_text(f"✅ Server time notice sent to user {target_id}.")


async def send_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not has_staff_access(user_id):
        await update.message.reply_text("❌ Only teachers or Developers can send messages to users.")
        return

    target_id = None
    message_parts = context.args

    if update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id
    elif message_parts:
        try:
            target_id = int(message_parts[0])
            message_parts = message_parts[1:]
        except ValueError:
            if update.effective_chat.type in {"group", "supergroup"}:
                target_id = update.effective_chat.id
            else:
                target_id = None
    elif update.effective_chat.type in {"group", "supergroup"}:
        target_id = update.effective_chat.id

    message_text = " ".join(message_parts).strip()
    if target_id is None or not message_text:
        await update.message.reply_text(
            "Usage: /message <user_id> <message>\n"
            "Or reply to a user's message: /message <message>"
        )
        return

    try:
        await context.bot.send_message(chat_id=target_id, text=message_text)
    except Exception:
        await update.message.reply_text(
            "❌ Could not send the message. Check the user ID and make sure the user started the bot."
        )
        return

    if update.effective_chat.type in {"group", "supergroup"} and target_id == update.effective_chat.id:
        await update.message.reply_text("✅ Message sent to this group.")
    else:
        await update.message.reply_text(f"✅ Message sent to user {target_id}.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
📋 Available Commands:

👨‍🎓 Student Commands:
/start   - ចាប់ផ្ដើមធ្វើតេស្ត
/quiz    - ចាប់ផ្ដើមធ្វើតេស្ត

👨‍🏫 Teacher Commands:
/score   - មើលពិន្ទុសិស្សទាំងអស់
/top     - មើល Top 5 Scores
/clear   - លុបពិន្ទុទាំងអស់
/students - ចំនួនសិស្សដែលបានប្រឡង
/id      - View registered user IDs
/check   - មើលចម្លើយត្រឹមត្រូវ
/message - Send a message to a student or the current group
/addexercise - Add an exercise(send a photo with the question as its caption if needed)
/editexercise - Edit an exercise
/deleteexercise [number] - Delete an exercise
/help - ជំនួយ
/message - Send a message to a student or the current group

Developer Commands:
/id      - View registered user ID
/give    - Grant access to /check or Developer role
/servertime - Send server OFF and ON times to a user or everyone
/message - Send a message to a student or the current group

"""
    await update.message.reply_text(help_text)


async def bot_added_to_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    change = update.my_chat_member
    old_status = change.old_chat_member.status
    new_status = change.new_chat_member.status

    if (
        change.chat.type in {"group", "supergroup"}
        and old_status in {"left", "kicked"}
        and new_status in {"member", "administrator"}
    ):
        await context.bot.send_message(
            chat_id=change.chat.id,
            text=f"✅ Bot added to this group.\nGroup ID: {change.chat.id}"
        )


# =========================
# ROUTER
# =========================

async def route_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get("state")

    if state == "waiting_name":
        await handle_name(update, context)
        return

    if state == "waiting_teacher_password":
        await handle_teacher_password(update, context)
        return

    if state == "waiting_dev_password":
        await handle_dev_password(update, context)
        return

    if state in {
        "exercise_add_question",
        "exercise_add_options",
        "exercise_edit_question",
        "exercise_edit_options",
    }:
        await exercise_text(update, context)


async def route_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await exercise_photo(update, context)


# =========================
# MAIN
# =========================

def main():
    lock_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".quiz_bot.lock")
    lock_file = open(lock_path, "a+")
    try:
        lock_file.seek(0)
        if os.name == "nt" and msvcrt is not None:
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
        elif fcntl is not None:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        else:
            raise OSError("No supported file locking backend is available.")
    except OSError:
        lock_file.close()
        print("Quiz Bot is already running. Stop the existing instance before starting another one.")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("quiz", quiz_command))
    app.add_handler(CommandHandler("score", score))
    app.add_handler(CommandHandler("top", top))
    app.add_handler(CommandHandler("clear", clear_scores))
    app.add_handler(CommandHandler("students", students_count))
    app.add_handler(CommandHandler("id", list_user_ids))
    app.add_handler(CommandHandler("check", check_answers))
    app.add_handler(CommandHandler("addexercise", add_exercise))
    app.add_handler(CommandHandler("editexercise", edit_exercise))
    app.add_handler(CommandHandler("deleteexercise", delete_exercise))
    app.add_handler(CommandHandler("give", give_access))
    app.add_handler(CommandHandler("message", send_user_message))
    app.add_handler(CommandHandler("servertime", send_server_time))
    app.add_handler(CommandHandler("muylyly", check_answers))
    app.add_handler(CommandHandler("heng", check_answers))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(ChatMemberHandler(bot_added_to_group, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(CallbackQueryHandler(handle_role_selection, pattern="^role:"))
    app.add_handler(CallbackQueryHandler(exercise_edit_selection, pattern="^editq:"))
    app.add_handler(CallbackQueryHandler(exercise_delete_selection, pattern="^deleteq:"))
    app.add_handler(CallbackQueryHandler(exercise_delete_selection, pattern="^deleteall:"))
    app.add_handler(CallbackQueryHandler(confirm_delete_exercise, pattern="^confirmdelete:"))
    app.add_handler(CallbackQueryHandler(exercise_correct_selection, pattern="^(addcorrect|editcorrect):"))
    app.add_handler(CallbackQueryHandler(answer, pattern="^quiz:"))
    app.add_handler(MessageHandler(filters.PHOTO, route_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, route_text))

    print("Quiz Bot Running...")

    try:
        app.run_polling(drop_pending_updates=True)
    finally:
        lock_file.close()


if __name__ == "__main__":
    main()
