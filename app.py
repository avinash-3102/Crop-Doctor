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

# 🧠 AI Model
model = tf.keras.models.load_model("keras_model.h5", compile=False)

with open("labels.txt", "r") as f:
    labels = [line.strip() for line in f.readlines()]

# 🗂 User state
user_lang = {}
user_state = {}

# 📸 Image prediction
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

# 💬 Groq chat
def ai_chat(text):
    try:
        res = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "You are a helpful agriculture assistant for farmers. Keep answers simple."},
                {"role": "user", "content": text}
            ]
        )
        return res.choices[0].message.content
    except:
        return "Sorry, I couldn't understand."

# 🌐 Home
@app.route("/")
def home():
    return "AI Crop Doctor Running"

# 🚀 Main bot
@app.route("/webhook", methods=["POST"])
def whatsapp_bot():
    incoming_msg = request.values.get('Body', '').strip().lower()
    sender = request.values.get('From')
    media_url = request.values.get('MediaUrl0')

    resp = MessagingResponse()
    msg = resp.message()

    # 👋 STEP 1: ALWAYS HANDLE HI FIRST
    if incoming_msg in ["hi", "hello", "start"]:
        user_state[sender] = "menu"
        user_lang.pop(sender, None)

        msg.body(
            "👋 Welcome to AI Crop Doctor!\n\n"
            "1️⃣ Start Diagnosis\n"
            "2️⃣ Advisory\n"
            "3️⃣ Exit\n\n"
            "Reply with number"
        )
        return str(resp)

    # ❌ EXIT
    if incoming_msg == "3":
        user_state.pop(sender, None)
        user_lang.pop(sender, None)

        msg.body("👋 Thank you! Stay healthy 🌱")
        return str(resp)

    # 🌱 START → LANGUAGE
    if incoming_msg == "1" and user_state.get(sender) == "menu":
        user_state[sender] = "language"

        msg.body(
            "🌍 Choose language:\n"
            "1️⃣ English\n2️⃣ Hindi\n3️⃣ Punjabi\n4️⃣ Telugu"
        )
        return str(resp)

    # 📘 ADVISORY
    if incoming_msg == "2":
        msg.body(
            "📘 Advisory:\n\n"
            "🧪 Mancozeb 75% WP\n"
            "• Dose: 2g/L water\n\n"
            "🌿 Neem Oil\n"
            "• 5ml/L\n"
        )
        return str(resp)

    # 🌍 LANGUAGE SELECTION (ONLY ONCE)
    if user_state.get(sender) == "language":
        if incoming_msg == "1":
            user_lang[sender] = "en"
        elif incoming_msg == "2":
            user_lang[sender] = "hi"
        elif incoming_msg == "3":
            user_lang[sender] = "pa"
        elif incoming_msg == "4":
            user_lang[sender] = "te"
        else:
            msg.body("❌ Invalid choice (1–4)")
            return str(resp)

        user_state[sender] = "chat"

        msg.body("✅ Language selected!\n📸 Send crop image or ask question")
        return str(resp)

    # 📸 IMAGE CASE
    if media_url:
        disease = predict_disease(media_url)

        msg.body(
            f"📸 Image received!\n\n🧠 Disease: {disease}\n🧪 Use Mancozeb\n🌿 Neem oil recommended"
        )
        return str(resp)

    # 💬 CHAT MODE (GROQ)
    if user_state.get(sender) == "chat":
        reply = ai_chat(incoming_msg)
        msg.body(reply)
        return str(resp)

    # 🔁 FALLBACK
    msg.body("👋 Type 'hi' to start")
    return str(resp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
