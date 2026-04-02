from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import numpy as np
import tensorflow as tf
from PIL import Image
import requests
from io import BytesIO
from groq import Groq

app = Flask(__name__)

# 🔑 Groq API
client = Groq(api_key="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")

# Load model
model = tf.keras.models.load_model("keras_model.h5", compile=False)

with open("labels.txt", "r") as f:
    labels = [line.strip() for line in f.readlines()]

# 🧠 IMAGE AI
def predict_disease(image_url):
    try:
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content)).convert("RGB")

        img = img.resize((224, 224))
        img_array = np.array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)

        prediction = model.predict(img_array)
        return labels[np.argmax(prediction)]
    except:
        return "Unknown disease"

# 💬 GROQ CHAT (MAIN BRAIN)
def ai_chat(user_text):
    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert agriculture assistant. Help farmers with crops, diseases, fertilizers, weather, and solutions. Keep answers simple and practical."
                },
                {"role": "user", "content": user_text}
            ]
        )
        return response.choices[0].message.content
    except:
        return "⚠️ Sorry, try again."

# 🌦 Weather (simple)
def weather_advice():
    return "🌦 Weather looks suitable for spraying today."

# 📍 Nearby
def nearby_shop():
    return "📍 https://www.google.com/maps/search/pesticide+shop"

@app.route("/")
def home():
    return "AI Crop Doctor Running"

# 🚀 MAIN BOT (NO MENU — PURE AI CHAT)
@app.route("/webhook", methods=["POST"])
def whatsapp_bot():
    incoming_msg = request.values.get('Body', '').strip()
    media_url = request.values.get('MediaUrl0')

    resp = MessagingResponse()
    msg = resp.message()

    # 📸 IMAGE CASE
    if media_url:
        disease = predict_disease(media_url)

        reply = f"""
📸 Image received!

🧠 Detected: {disease}

🧪 Advisory:
• Use Mancozeb spray
• Neem oil recommended

{weather_advice()}

{nearby_shop()}

💬 You can ask more about this disease!
"""
        msg.body(reply)
        return str(resp)

    # 👋 GREETING
    if incoming_msg.lower() in ["hi", "hello", "hey"]:
        msg.body(
            "👋 Welcome to AI Crop Doctor 🌾\n\n"
            "Ask anything about crops, diseases, fertilizers.\n"
            "Or send a crop image 📸"
        )
        return str(resp)

    # 💬 NORMAL AI CHAT
    ai_reply = ai_chat(incoming_msg)

    final_reply = f"""
{ai_reply}

📘 Need full advisory? Type: advisory
{weather_advice()}
{nearby_shop()}
"""

    msg.body(final_reply)
    return str(resp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
