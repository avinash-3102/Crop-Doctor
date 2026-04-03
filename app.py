from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import numpy as np
import tensorflow as tf
from PIL import Image
import requests
from io import BytesIO
from groq import Groq
import os

app = Flask(__name__)

# 🔐 Load API key from environment (Render will provide this)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found! Please set it in Render environment variables.")

client = Groq(api_key=GROQ_API_KEY)

# Load model
model = tf.keras.models.load_model("keras_model.h5", compile=False)

# Load labels
with open("labels.txt", "r") as f:
    labels = [line.strip() for line in f.readlines()]

# 📸 Image Prediction
def predict_disease(image_url):
    try:
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content)).convert("RGB")

        img = img.resize((224, 224))
        img_array = np.array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)

        prediction = model.predict(img_array)
        return labels[np.argmax(prediction)]

    except Exception as e:
        print("Error:", e)
        return "Unknown disease"

# 💬 AI Chat
def ai_chat(user_text):
    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert agriculture assistant. Help farmers with crops, diseases, fertilizers, and solutions. Keep answers simple."
                },
                {"role": "user", "content": user_text}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print("AI Error:", e)
        return "⚠️ Sorry, try again."

# 🌦 Weather (simple)
def weather_advice():
    return "🌦 Weather is suitable for spraying today."

# 📍 Nearby shop
def nearby_shop():
    return "📍 https://www.google.com/maps/search/pesticide+shop"

@app.route("/")
def home():
    return "AI Crop Doctor Running ✅"

# 🚀 MAIN BOT
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

💬 Ask anything about this disease!
"""
        msg.body(reply)
        return str(resp)

    # 👋 GREETING
    if incoming_msg.lower() in ["hi", "hello", "hey"]:
        msg.body(
            "👋 Welcome to AI Crop Doctor 🌾\n\n"
            "Ask anything about crops, diseases, fertilizers.\n"
            "Or send crop image 📸"
        )
        return str(resp)

    # 💬 NORMAL AI CHAT
    ai_reply = ai_chat(incoming_msg)

    final_reply = f"""
{ai_reply}

📘 Need advisory? Type: advisory
{weather_advice()}
{nearby_shop()}
"""

    msg.body(final_reply)
    return str(resp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
