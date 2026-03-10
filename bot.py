import telebot
import urllib.request
import json

# токен от BotFather
TELEGRAM_TOKEN = "8737861854:AAFsrfksAz4I-dyeNnhCzMmLHh8YQD4XoVo"  

tavily_key = "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"
gemini_key = "AIzaSyAu4mJmPiMxMcobycOYwfr5oXjxKTpY_Qo"

bot = telebot.TeleBot(TELEGRAM_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Дарова! Задавай любой вопрос — я поищу в интернете и отвечу вам.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    question = message.text.strip()
    bot.reply_to(message, "Ищу информацию...")

    # Tavily поиск ( код)
    tavily_url = "https://api.tavily.com/search"
    payload = {
        "api_key": tavily_key,
        "query": question,
        "search_depth": "basic",
        "max_results": 5
    }
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(tavily_url, data=data, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req) as resp:
            tavily_data = json.loads(resp.read().decode("utf-8"))
            results = tavily_data.get("results", [])
            context = "\n\n".join(r.get("content", "") for r in results[:3]) if results else "Ничего не найдено"
    except Exception as e:
        context = f"Ошибка поиска: {e}"

    # Gemini
    model = "gemini-2.5-flash"  
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"

    body = {
        "contents": [{
            "parts": [{
                "text": f"Вопрос: {question}\nДанные из интернета: {context}\nОтвечай ясно, но с полным предложением на русском. Не обрывай ответ."
            }]
        }],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 10000
        }
    }

    try:
        data2 = json.dumps(body).encode("utf-8")
        req2 = urllib.request.Request(url, data=data2, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req2) as resp2:
            result = json.loads(resp2.read().decode("utf-8"))
            answer = result["candidates"][0]["content"]["parts"][0]["text"].strip()
            bot.reply_to(message, answer)
    except Exception as e:
        bot.reply_to(message, f"Ошибка Gemini: {e}\nПопробуй позже или спроси проще.")

print("Бот запущен...")
bot.infinity_polling()