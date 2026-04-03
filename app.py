from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from groq import Groq
import os

app = Flask(__name__)

# 🔐 API key
API_KEY = os.environ.get("GROQ_API_KEY")

# 🌍 Language detection (simple)
def detect_language(text):
    text = text.lower()
    if any(word in text for word in ["kya", "hai", "namaste", "kaise"]):
        return "Hindi"
    return "English"

# 🌦 Weather (simple dynamic style)
def weather_advice():
    return "🌦 Weather looks suitable for spraying today. Avoid spraying during strong sunlight."

# 📍 Shop
def nearby_shop():
    return "📍 https://www.google.com/maps/search/pesticide+shop"

# 💬 AI Chat (TEXT)
def ai_chat(user_text):
    try:
        if not API_KEY:
            return "❌ API key missing"

        client = Groq(api_key=API_KEY)
        language = detect_language(user_text)

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": f"""
You are an expert agriculture assistant.

Always respond in {language}.

Give answers in this format:
1. Problem
2. Natural Solution
3. Chemical Solution
4. Prevention
Keep it simple for farmers.
"""
                },
                {"role": "user", "content": user_text}
            ]
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"⚠️ AI Error: {str(e)}"

# 📸 Image Disease Detection (AI BASED)
def predict_disease(image_url):
    try:
        client = Groq(api_key=API_KEY)

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": """
You are a plant disease expert.

From the image, identify:
1. Disease name
2. Natural treatment
3. Chemical treatment
4. Prevention

Keep it simple for farmers.
"""
                },
                {
                    "role": "user",
                    "content": f"Analyze this crop image: {image_url}"
                }
            ]
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"⚠️ Detection Error: {str(e)}"

# 🏠 Home
@app.route("/")
def home():
    return "✅ AI Crop Doctor LIVE"

# 🚀 MAIN BOT
@app.route("/webhook", methods=["POST"])
def whatsapp_bot():
    incoming_msg = request.values.get('Body', '').strip()
    num_media = int(request.values.get('NumMedia', 0))

    resp = MessagingResponse()
    msg = resp.message()

    # 📸 IMAGE CASE
    if num_media > 0:
        media_url = request.values.get('MediaUrl0')

        result = predict_disease(media_url)

        msg.body(f"""
📸 Crop Analysis:

{result}

{weather_advice()}

{nearby_shop()}
""")
        return str(resp)

    # 👋 GREETING
    if incoming_msg.lower() in ["hi", "hello", "hey"]:
        msg.body(
            "👋 Welcome to AI Crop Doctor 🌾\n\n"
            "Send crop image 📸 OR ask any farming question."
        )
        return str(resp)

    # 💬 TEXT CHAT
    ai_reply = ai_chat(incoming_msg)

    msg.body(f"""
{ai_reply}

{weather_advice()}
{nearby_shop()}
""")

    return str(resp)

# 🚀 RUN
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
