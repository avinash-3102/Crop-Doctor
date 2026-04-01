from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import numpy as np
import tensorflow as tf
from PIL import Image
import requests

app = Flask(__name__)

# 🗂 Store user language
user_lang = {}

# ✅ Load AI Model
model = tf.keras.models.load_model("keras_model.h5", compile=False)

# ✅ Load labels
with open("labels.txt", "r") as f:
    labels = [line.strip() for line in f.readlines()]

# 🧠 AI Prediction Function
def predict_disease(image_url):
    img_data = requests.get(image_url).content
    with open("leaf.jpg", "wb") as f:
        f.write(img_data)

    img = Image.open("leaf.jpg").convert("RGB")
    img = img.resize((224, 224))

    img_array = np.array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)

    prediction = model.predict(img_array)
    index = np.argmax(prediction)

    return labels[index]

# 🌦 Simple Weather Logic
def weather_advice():
    return "🌦 Weather looks fine for spraying today."

# 📍 Nearby link
def nearby_shop():
    return "https://www.google.com/maps/search/pesticide+shop"

# ✅ Home route
@app.route("/")
def home():
    return "✅ AI Crop Doctor Running!"

# 🚀 WhatsApp Bot
@app.route("/webhook", methods=["POST"])
def whatsapp_bot():
    incoming_msg = request.values.get('Body', '').lower()
    sender = request.values.get('From')
    media_url = request.values.get('MediaUrl0')

    resp = MessagingResponse()
    msg = resp.message()

    # 🌍 LANGUAGE SELECTION (TEXT BUTTON STYLE)
    if any(word in incoming_msg for word in ["english", "hindi", "punjabi", "telugu"]):
        if "english" in incoming_msg:
            user_lang[sender] = "en"
        elif "hindi" in incoming_msg:
            user_lang[sender] = "hi"
        elif "punjabi" in incoming_msg:
            user_lang[sender] = "pa"
        elif "telugu" in incoming_msg:
            user_lang[sender] = "te"

        msg.body(
            "✅ Language selected!\n\n"
            "📸 Send crop image\n"
            "💬 Or describe problem\n\n"
            "👉 Type 'advisory' for detailed help"
        )
        return str(resp)

    # Ask language if not selected
    if sender not in user_lang:
        msg.body(
            "🌍 Choose your language:\n\n"
            "👉 English\n"
            "👉 Hindi\n"
            "👉 Punjabi\n"
            "👉 Telugu\n\n"
            "💬 Type your language"
        )
        return str(resp)

    # 📘 Advisory Mode
    if "advisory" in incoming_msg:
        msg.body(
            "📘 Detailed Advisory\n\n"
            "🧪 Mancozeb 75% WP\n"
            "• Dose: 2g/L water\n"
            "• Spray every 7 days\n\n"
            "🌿 Neem Oil\n"
            "• 5ml/L\n\n"
            "📈 Result: Disease stops in 5–7 days\n"
            "⚠️ Use proper safety"
        )
        return str(resp)

    # 📸 IMAGE CASE (AI DETECTION)
    if media_url:
        disease = predict_disease(media_url)

        # Smart pesticide suggestion
        if "spot" in disease.lower():
            pesticide = "Mancozeb"
        elif "yellow" in disease.lower():
            pesticide = "Urea"
        else:
            pesticide = "General fertilizer"

        reply = f"""
📸 Image received!

🧠 AI Detected: {disease}

🧪 Chemical:
• {pesticide}

🌿 Natural:
• Neem oil spray

{weather_advice()}

📍 Nearby Shop:
{nearby_shop()}

👉 Type 'advisory' for full details
"""

    # 💬 TEXT CASE
    else:
        reply = (
            "🤖 Send crop image\n"
            "Or type problem like:\n"
            "• yellow leaves\n"
            "• brown spots"
        )

    msg.body(reply)
    return str(resp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)