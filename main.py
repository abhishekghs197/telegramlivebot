import os
import telebot
from flask import Flask, request
from openai import OpenAI

# 1. Fetch environment variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
HF_TOKEN = os.environ.get("HF_TOKEN")

# Check if tokens are set
if not BOT_TOKEN or not HF_TOKEN:
    raise ValueError("Missing BOT_TOKEN or HF_TOKEN in environment variables.")

# 2. Initialize Telegram Bot and Flask App
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# 3. Initialize OpenAI Client (Pointed to Hugging Face Router)
hf_client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
)

# --- TELEGRAM BOT LOGIC ---

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Hello! I am a problem-solving chatbot. Made me a CoderAbhi. Send me a message and I'll reply!")

@bot.message_handler(func=lambda message: True)
def handle_chat(message):
    try:
        # User-এর মেসেজ ছোট হাতের অক্ষরে (lowercase) কনভার্ট করে নিচ্ছি মেলানোর সুবিধার জন্য
        user_text = message.text.strip().lower()
        
        # কাস্টম প্রশ্নের উত্তর (Custom Question Answer)
        if "what is your name" in user_text or "whats your name" in user_text:
            bot.reply_to(message, "AD")
            return  # উত্তর দিয়ে দেওয়া হয়েছে, তাই AI-কে আর কল করবে না

        # Show "typing..." status in Telegram while the AI generates a response
        bot.send_chat_action(message.chat.id, 'typing')
        
        # Call the Hugging Face / DeepSeek model
        response = hf_client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1:novita",
            messages=[
                {
                    "role": "user",
                    "content": message.text,
                }
            ],
        )
        
        # Extract the reply and send it back to the user
        reply = response.choices[0].message.content
        bot.reply_to(message, reply)

    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, "Sorry, I encountered an error while thinking. Please try again later.")


# --- FLASK WEBHOOK LOGIC ---

# This route handles incoming updates from Telegram securely
@app.route('/' + BOT_TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

# This acts as a health check route for Render
@app.route("/")
def webhook():
    return "Bot is running perfectly!", 200

if __name__ == "__main__":
    # Remove any existing webhooks before setting a new one
    bot.remove_webhook()
    
    # Render.com automatically provides the RENDER_EXTERNAL_URL environment variable
    # e.g., https://your-app-name.onrender.com
    webhook_url = os.environ.get("RENDER_EXTERNAL_URL")
    
    if webhook_url:
        # Connect Telegram to the Render URL
        bot.set_webhook(url=f"{webhook_url}/{BOT_TOKEN}")
        print(f"Webhook set to: {webhook_url}")
    else:
        print("Warning: RENDER_EXTERNAL_URL not found. Webhook not set.")

    # Render automatically assigns a PORT. Default to 5000 for local testing.
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
