import telebot
import urllib.request
import json
import time
from collections import defaultdict
from datetime import datetime

TELEGRAM_TOKEN = "8737861854:AAFP_Z5_HNkEfBb-TvbJdxMY7jUOu5t7bBQ"
MY_ID = 1620880381

tavily_key = "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"
gemini_keys = [ "AIzaSyAu4mJmPiMxMcobycOYwfr5oXjxKTpY_Qo", "AIzaSyALRvL5CpGEVM2MJLXAATSPiRa6BUBi3B0",  'AIzaSyCDmeyzJAk51Pf5uQ_M0lnuZ2NE3sc6Pmc' ]

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Память, статистика, антиспам, режимы
memory = defaultdict(list)
users = {}
last_request = {}
user_modes = {}

GLADIATOR_PERSONALITY = """Ты — Гладиатор, мощный AI ассистент. 
Говоришь уверенно, коротко и по делу. 
Иногда используешь боевые метафоры типа "На арене фактов...", "Противник повержен — вот ответ:".
Никогда не говоришь что ты AI или Gemini. Ты — Гладиатор и только."""

def ask_gemini(user_id, question, context):
    mode = user_modes.get(user_id, "normal")
    if mode == "short":
        style = "Отвечай очень кратко, максимум 2-3 предложения."
    elif mode == "detail":
        style = "Отвечай подробно и развёрнуто."
    else:
        style = "Отвечай чётко и по делу."

    # Добавляем память
    history = memory[user_id][-6:]
    history_text = "\n".join([f"{m['role']}: {m['text']}" for m in history])

    prompt = f"""{GLADIATOR_PERSONALITY}

История разговора:
{history_text}

Данные из интернета: {context}

Вопрос: {question}

{style} Отвечай на русском."""

    for key in gemini_keys:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}"
            body = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.7, "maxOutputTokens": 1000}
            }
            data = json.dumps(body).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result["candidates"][0]["content"]["parts"][0]["text"].strip()
        except:
            continue
    return "Арена временно закрыта... Все силы на исходе 😔 Попробуй позже!"

def search_tavily(question):
    try:
        tavily_url = "https://api.tavily.com/search"
        payload = {"api_key": tavily_key, "query": question, "search_depth": "basic", "max_results": 5}
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(tavily_url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            results = json.loads(resp.read().decode("utf-8")).get("results", [])
            return "\n\n".join(r.get("content", "") for r in results[:3]) or "Ничего не найдено"
    except Exception as e:
        return f"Ошибка поиска: {e}"

def is_spam(user_id):
    now = time.time()
    if user_id in last_request:
        if now - last_request[user_id] < 3:
            return True
    last_request[user_id] = now
    return False

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.first_name or "Воин"
    users[user_id] = {"name": username, "count": users.get(user_id, {}).get("count", 0)}
    bot.reply_to(message, f"⚔️ Приветствую тебя, {username}!\n\nЯ — Гладиатор. Задавай любой вопрос — я найду ответ на арене знаний!\n\nНапиши /help чтобы узнать мои команды.")

@bot.message_handler(commands=['help'])
def help_cmd(message):
    text = """⚔️ *Команды Гладиатора:*

/start — Начать
/help — Список команд
/режим краткий — Короткие ответы
/режим подробный — Развёрнутые ответы
/режим обычный — Обычный режим
/stats — Статистика (только для админа)

*В группе:* напиши "Гладиатор, [вопрос]" и я отвечу!

⚔️ Просто задай любой вопрос — я найду ответ!"""
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['stats'])
def stats_cmd(message):
    if message.from_user.id != MY_ID:
        bot.reply_to(message, "⚔️ Эта команда только для моего создателя!")
        return
    total = len(users)
    bot.reply_to(message, f"⚔️ *Статистика Гладиатора:*\n\nВсего воинов: {total}", parse_mode="Markdown")

@bot.message_handler(commands=['режим'])
def mode_cmd(message):
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "Напиши: /режим краткий, /режим подробный или /режим обычный")
        return
    mode = parts[1].lower()
    if mode == "краткий":
        user_modes[message.from_user.id] = "short"
        bot.reply_to(message, "⚔️ Режим: Краткий удар!")
    elif mode == "подробный":
        user_modes[message.from_user.id] = "detail"
        bot.reply_to(message, "⚔️ Режим: Полная битва!")
    else:
        user_modes[message.from_user.id] = "normal"
        bot.reply_to(message, "⚔️ Режим: Обычный бой!")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    text = message.text.strip()

    # В группе отвечаем только на "Гладиатор,"
    if message.chat.type in ["group", "supergroup"]:
        if not text.lower().startswith("гладиатор,"):
            return
        text = text[10:].strip()

    # Антиспам
    if is_spam(user_id):
        bot.reply_to(message, "⚔️ Не так быстро, воин! Подожди пару секунд.")
        return

    # Считаем пользователя
    if user_id not in users:
        users[user_id] = {"name": message.from_user.first_name or "Воин", "count": 0}
    users[user_id]["count"] = users[user_id].get("count", 0) + 1

    # Отправляем "ищу" и потом удаляем
    searching_msg = bot.reply_to(message, "⚔️ Гладиатор выходит на арену знаний...")

    # Ищем в интернете
    context = search_tavily(text)

    # Получаем ответ
    answer = ask_gemini(user_id, text, context)

    # Сохраняем в память
    memory[user_id].append({"role": "user", "text": text})
    memory[user_id].append({"role": "Гладиатор", "text": answer})
    if len(memory[user_id]) > 20:
        memory[user_id] = memory[user_id][-20:]

    # Удаляем "ищу" сообщение
    try:
        bot.delete_message(message.chat.id, searching_msg.message_id)
    except:
        pass

    bot.reply_to(message, answer)

print("⚔️ Гладиатор на арене!")
bot.infinity_polling()