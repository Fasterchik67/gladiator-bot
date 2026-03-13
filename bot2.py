import telebot
import urllib.request
import json

TELEGRAM_TOKEN = "8737861854:AAFP_Z5_HNkEfBb-TvbJdxMY7jUOu5t7bBQ"

tavily_key = "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"
gemini_keys = [ "AIzaSyAu4mJmPiMxMcobycOYwfr5oXjxKTpY_Qo", "AIzaSyALRvL5CpGEVM2MJLXAATSPiRa6BUBi3B0",  'AIzaSyCDmeyzJAk51Pf5uQ_M0lnuZ2NE3sc6Pmc' ]

bot = telebot.TeleBot(TELEGRAM_TOKEN)

def ask_gemini(question, context):
    for key in gemini_keys:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
            body = {
                "contents": [{"parts": [{"text": f"Вопрос: {question}\nДанные: {context}\nОтвечай на русском."}]}],
                "generationConfig": {"temperature": 0.4, "maxOutputTokens": 5000}
            }
            data = json.dumps(body).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result["candidates"][0]["content"]["parts"][0]["text"].strip()
        except:
            continue
    return "Все ключи на лимите, попробуй позже 😔"

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Дарова! Задавай любой вопрос — я поищу в интернете и отвечу.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    question = message.text.strip()
    bot.reply_to(message, "Ищу информацию...")

    tavily_url = "https://api.tavily.com/search"
    payload = {"api_key": tavily_key, "query": question, "search_depth": "basic", "max_results": 5}
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(tavily_url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            results = json.loads(resp.read().decode("utf-8")).get("results", [])
            context = "\n\n".join(r.get("content", "") for r in results[:3]) or "Ничего не найдено"
    except Exception as e:
        context = f"Ошибка поиска: {e}"

    answer = ask_gemini(question, context)
    bot.reply_to(message, answer)

print("Бот запущен...")
bot.infinity_polling()