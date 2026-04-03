from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import numpy as np
from PIL import Image
import requests
from io import BytesIO
from groq import Groq
import tensorflow as tf
import os

# 🔇 Reduce TensorFlow logs (important for Render)
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

app = Flask(__name__)

# 🔐 API KEY (from Render)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# 🧠 Lazy load model (prevents crash)
model = None

def load_model_once():
    global model
    if model is None:
        print("Loading model...")
        model = tf.keras.models.load_model("keras_model.h5", compile=False)
    return model

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

        prediction = load_model_once().predict(img_array)
        return labels[np.argmax(prediction)]

    except Exception as e:
        print("Error:", e)
        return "Unknown disease"

# 💬 AI Chat
def ai_chat(user_text):
    try:
        api_key = os.environ.get("GROQ_API_KEY")

        if not api_key:
            return "❌ API key missing in Render"

        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "You are an agriculture expert."},
                {"role": "user", "content": user_text}
            ]
        )

        return response.choices[0].message.content

    except Exception as e:
        print("AI ERROR:", str(e))
        return f"⚠️ AI error: {str(e)}"

# 🌦 Weather
def weather_advice():
    return "🌦 Weather is suitable for spraying today."

# 📍 Shop
def nearby_shop():
    return "📍 https://www.google.com/maps/search/pesticide+shop"

@app.route("/")
def home():
    return "✅ AI Crop Doctor LIVE"

@app.route("/webhook", methods=["POST"])
def whatsapp_bot():
    incoming_msg = request.values.get('Body', '').strip()
    media_url = request.values.get('MediaUrl0')

    resp = MessagingResponse()
    msg = resp.message()

    # 📸 Image case
    if media_url:
        disease = predict_disease(media_url)

        msg.body(f"""
📸 Detected: {disease}

🧪 Use:
• Mancozeb spray
• Neem oil

{weather_advice()}
{nearby_shop()}
""")
        return str(resp)

    # 👋 Greeting
    if incoming_msg.lower() in ["hi", "hello"]:
        msg.body("👋 Welcome to AI Crop Doctor 🌾\nSend crop image or ask question.")
        return str(resp)

    # 💬 AI chat
    ai_reply = ai_chat(incoming_msg)

    msg.body(f"{ai_reply}\n\n{weather_advice()}")
    return str(resp)

# 🚀 Run (Render compatible)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
