import streamlit as st
import speech_recognition as sr
import pyttsx3
import requests
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key="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")  # Replace with your key

# Initialize text-to-speech
engine = pyttsx3.init()
engine.setProperty('rate', 170)

# --- Function: Voice input ---
def listen_to_voice():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎤 Listening... Speak your health condition.")
        audio = recognizer.listen(source, timeout=6, phrase_time_limit=8)
        try:
            text = recognizer.recognize_google(audio)
            st.success(f"You said: {text}")
            return text
        except sr.UnknownValueError:
            st.warning("Sorry, I couldn't understand you.")
        except sr.RequestError:
            st.error("Speech recognition service unavailable.")
    return None

# --- Function: Speak output ---
def speak(text):
    engine.say(text)
    engine.runAndWait()

# --- Function: Get location ---
def get_user_location():
    try:
        res = requests.get("https://ipinfo.io/json")
        data = res.json()
        return data.get("city"), data.get("region"), data.get("loc")
    except:
        return None, None, None

# --- Function: Find nearby hospitals ---
def find_nearby_hospitals(latitude, longitude):
    api_key = "AIzaSyAAqNeYQNzaUwvpxyfXKL4p6mQVCz4WjIo"  # 🔑 Replace with your Google Maps API key
    radius = 3000  # meters
    url = (
        f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?"
        f"location={latitude},{longitude}&radius={radius}&type=hospital&key={api_key}"
    )
    response = requests.get(url)
    results = response.json().get("results", [])
    hospitals = []
    for place in results[:5]:
        name = place.get("name")
        address = place.get("vicinity")
        hospitals.append((name, address))
    return hospitals

# --- Function: Generate AI response for fatigue/stress ---
def ai_medical_advice(user_input):
    prompt = f"""
    You are a smart medical assistant specialized in fatigue and stress management.
    The user said: {user_input}.
    1. Identify if the user describes fatigue, stress, or another issue.
    2. Give home treatment and relaxation tips.
    3. If severe, advise visiting nearby hospitals.
    4. Keep your response empathetic, short, and medically safe.
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": prompt}]
    )
    return response.choices[0].message.content

# --- Streamlit UI ---
st.set_page_config(page_title="🧠 AI Medical Assistant", page_icon="🩺", layout="centered")
st.title("🩺 Smart Health Assistant")
st.write("Your AI-powered voice chatbot for **fatigue** and **stress** relief 💬")

col1, col2 = st.columns([3, 1])
with col1:
    user_input = st.text_input("Describe your health condition (or use voice below):")
with col2:
    if st.button("🎙️ Speak"):
        user_input = listen_to_voice()

if user_input:
    st.subheader("💬 AI Diagnosis & Suggestions")
    ai_reply = ai_medical_advice(user_input)
    st.write(ai_reply)
    speak(ai_reply)

    # Get user location
    city, region, loc = get_user_location()
    if loc:
        lat, lon = loc.split(",")
        hospitals = find_nearby_hospitals(lat, lon)
        if hospitals:
            st.subheader(f"🏥 Nearby Hospitals in {city}, {region}")
            for name, address in hospitals:
                maps_url = f"https://www.google.com/maps/dir/?api=1&destination={name.replace(' ', '+')},{address.replace(' ', '+')}"
                st.markdown(f"**{name}** — {address}  \n[📍 View on Map]({maps_url})")
        else:
            st.warning("No hospitals found nearby.")
    else:
        st.warning("Unable to detect location. Please check your internet connection.")
