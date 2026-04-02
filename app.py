from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import numpy as np
import tensorflow as tf
from PIL import Image
import requests
from io import BytesIO

app = Flask(__name__)

# Store user language
user_lang = {}

# Load AI model
model = tf.keras.models.load_model("keras_model.h5", compile=False)

# Load labels
with open("labels.txt", "r") as f:
    labels = [line.strip() for line in f.readlines()]

# AI Prediction
def predict_disease(image_url):
    try:
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content)).convert("RGB")

        img = img.resize((224, 224))
        img_array = np.array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)

        prediction = model.predict(img_array)
        index = np.argmax(prediction)

        return labels[index]

    except:
        return "Unknown disease"

# Language messages
def get_message(lang, key):
    messages = {
        "start": {
            "en": "🌍 Choose language:\n1️⃣ English\n2️⃣ Hindi\n3️⃣ Punjabi\n4️⃣ Telugu",
            "hi": "🌍 भाषा चुनें:\n1️⃣ English\n2️⃣ Hindi\n3️⃣ Punjabi\n4️⃣ Telugu",
            "pa": "🌍 ਭਾਸ਼ਾ ਚੁਣੋ:\n1️⃣ English\n2️⃣ Hindi\n3️⃣ Punjabi\n4️⃣ Telugu",
            "te": "🌍 భాషను ఎంచుకోండి:\n1️⃣ English\n2️⃣ Hindi\n3️⃣ Punjabi\n4️⃣ Telugu"
        },
        "send_image": {
            "en": "📸 Send crop image",
            "hi": "📸 फसल की फोटो भेजें",
            "pa": "📸 ਫਸਲ ਦੀ ਫੋਟੋ ਭੇਜੋ",
            "te": "📸 పంట ఫోటో పంపండి"
        }
    }
    return messages[key][lang]

@app.route("/")
def home():
    return "AI Crop Doctor Running"

@app.route("/webhook", methods=["POST"])
def whatsapp_bot():
    incoming_msg = request.values.get('Body', '').strip()
    sender = request.values.get('From')
    media_url = request.values.get('MediaUrl0')

    resp = MessagingResponse()
    msg = resp.message()

    # If language not selected
    if sender not in user_lang:
        if incoming_msg == "1":
            user_lang[sender] = "en"
        elif incoming_msg == "2":
            user_lang[sender] = "hi"
        elif incoming_msg == "3":
            user_lang[sender] = "pa"
        elif incoming_msg == "4":
            user_lang[sender] = "te"
        else:
            msg.body(get_message("en", "start"))
            return str(resp)

        msg.body(get_message(user_lang[sender], "send_image"))
        return str(resp)

    lang = user_lang[sender]

    # Image case
    if media_url:
        disease = predict_disease(media_url)

        if "spot" in disease.lower():
            pesticide = "Mancozeb"
        elif "yellow" in disease.lower():
            pesticide = "Urea"
        else:
            pesticide = "General fertilizer"

        # Language-wise reply
        if lang == "hi":
            reply = f"📸 फोटो प्राप्त!\n\n🧠 रोग: {disease}\n🧪 दवा: {pesticide}\n🌿 नीम तेल उपयोग करें"
        elif lang == "pa":
            reply = f"📸 ਫੋਟੋ ਮਿਲੀ!\n\n🧠 ਬਿਮਾਰੀ: {disease}\n🧪 ਦਵਾ: {pesticide}\n🌿 ਨੀਮ ਤੇਲ ਵਰਤੋ"
        elif lang == "te":
            reply = f"📸 ఫోటో వచ్చింది!\n\n🧠 వ్యాధి: {disease}\n🧪 మందు: {pesticide}\n🌿 నీమ్ ఆయిల్ ఉపయోగించండి"
        else:
            reply = f"📸 Image received!\n\n🧠 Disease: {disease}\n🧪 Chemical: {pesticide}\n🌿 Use neem oil"

    else:
        reply = get_message(lang, "send_image")

    msg.body(reply)
    return str(resp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
