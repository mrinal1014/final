from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import google.generativeai as genai
import os
import requests
import base64
from dotenv import load_dotenv
from fuzzywuzzy import fuzz
from nltk.stem import WordNetLemmatizer

# ✅ Load API Keys from .env
load_dotenv()

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
DEEPGRAM_TTS_URL = "https://api.deepgram.com/v1/speak"
GEMINI_API_KEY = os.getenv("AIzaSyAPx89UMmd80maKhZ0h9x3iGcIf9oseLy8")
eleven_api_key = os.getenv("sk_c7ca99169caae98bf33f19516e943b9238ed4cc47484c562")


# ✅ Configure Gemini AI
genai.configure(api_key=GEMINI_API_KEY)

# ✅ Define greeting & keyword categories
# Initialize Lemmatizer
lemmatizer = WordNetLemmatizer()

# Define expanded keyword categories
GREETINGS = [
    "hi", "hello", "hey", "howdy", "hola", "greetings", "sup", "what's up",
    "good morning", "good evening", "good afternoon", "gm", "ge", "morning",
    "yo", "hiya", "how’s it going", "how are you", "what’s good", "how have you been",
    "salutations", "wassup", "long time no see", "how do you do","hii",
]


CAREER_KEYWORDS = [
    "job", "career", "profession", "work", "occupation", "employment", "vacancy",
    "recruitment", "hiring", "jobs", "career path", "career growth", "opportunity",
    "job market", "corporate", "industry", "field", "sector", "business",
    "career change", "freelancing", "entrepreneurship", "internship", "training",
    "promotion", "salary negotiation", "career transition", "headhunting",
    "skills development", "career planning", "leadership", "management", "HR",
    "job security", "workforce", "job description", "networking", "career coaching","College"
    ,"Thankyou ","Salary","Subjects","Semester","bsc","btech","job","review","aiml","csf","cse","stream","innovation"
    "goal","describe","technology","future","books"
]


RESUME_KEYWORDS = [
    "resume", "cv", "cover letter", "portfolio", "bio", "curriculum vitae",
    "profile summary", "resume format", "job application", "applying", "apply",
    "cv writing", "professional summary", "experience", "qualifications",
    "achievements", "certifications", "career objectives", "skills", "references",
    "work history", "internship experience", "projects", "LinkedIn profile",
    "ATS-friendly resume", "resume builder", "resume review", "job interview",
    "personal statement", "employment history", "gap in resume", "resume templates"
]


MENTAL_HEALTH_KEYWORDS = [
    "stress", "burnout", "depression","help", "mental health", "anxiety", "pressure",
    "work-life balance", "overwhelmed", "fatigue", "exhausted", "therapy",
    "psychologist", "psychiatrist", "self-care", "meditation", "mindfulness",
    "counseling", "emotional support", "mental well-being", "loneliness",
    "panic attacks", "negative thoughts", "productivity anxiety", "toxic workplace",
    "relaxation techniques", "psychotherapy", "mental health day", "deep breathing",
    "coping mechanisms", "insomnia", "social anxiety", "bipolar disorder",
    "burnout recovery", "positivity", "mental resilience", "journaling","speak"
]


# Combine all keywords into a set
ALL_KEYWORDS = set(GREETINGS + CAREER_KEYWORDS + RESUME_KEYWORDS + MENTAL_HEALTH_KEYWORDS)
# ------------------- 🏠 HOME PAGE -------------------

def home(request):
    return render(request, "home.html")

# ------------------- 💬 CHATBOT PAGE -------------------

@login_required
def chat(request):
    return render(request, "chat.html")

# ------------------- 🎤 SPEECH-TO-TEXT (STT) API -------------------
# ------------------- 🤖 CHATBOT RESPONSE API -------------------
@csrf_exempt
def is_relevant_message(message):
    """Check if message contains words matching the allowed topics using fuzzy matching."""
    words = message.lower().split()

    for word in words:
        lemma = lemmatizer.lemmatize(word)  # Normalize words
        for keyword in ALL_KEYWORDS:
            if fuzz.ratio(lemma, keyword) > 80:  # Fuzzy match threshold
                return True
    return False


def chatbot_response(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=400)

    message = request.POST.get("message", "").strip().lower()
    if not message:
        return JsonResponse({"error": "No message provided"}, status=400)

    if not is_relevant_message(message):
        return JsonResponse({"response": "Sorry, I can only discuss career, resume, and mental health topics."})

    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(message)
        bot_response = response.text if response and hasattr(response, "text") else "Sorry, I couldn't generate a response."

        # Generate TTS
        audio_path = generate_tts_audio(bot_response)
        audio_url = request.build_absolute_uri(f"/{audio_path}") if audio_path else None

        return JsonResponse({
            "response": bot_response,
            "audio_url": audio_url
        })
    except Exception as e:
        return JsonResponse({"error": f"Internal server error: {str(e)}"}, status=500)

import uuid

def generate_tts_audio(text):
    if not os.path.exists("media"):
        os.makedirs("media")

    eleven_api_key = os.getenv("sk_c7ca99169caae98bf33f19516e943b9238ed4cc47484c562")
    voice_id = "1qEiC6qsybMkmnNdVMbK"
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
        "xi-api-key": eleven_api_key,
        "Content-Type": "application/json"
    }

    payload = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.75,
            "similarity_boost": 0.75
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            audio_data = response.content
            filename = f"tts_audio_{uuid.uuid4().hex}.mp3"
            audio_path = os.path.join("media", filename)
            with open(audio_path, "wb") as f:
                f.write(audio_data)
            return audio_path
        else:
            print("TTS Error:", response.text)
            return None
    except Exception as e:
        print("TTS Exception:", str(e))
        return None

# ✅ User Signup
def user_signup(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists. Choose another one.")
            return redirect("signup")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered. Try logging in.")
            return redirect("signup")

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect("signup")

        # ✅ Create and save the user
        user = User.objects.create_user(username=username, email=email, password=password1)
        user.save()

        messages.success(request, "Signup successful! You can now log in.")
        return redirect("login")

    return render(request, "signup.html")

# ✅ User Login
def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect("home")
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, "login.html")

# ✅ User Logout
def user_logout(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect("login")

DID_API_KEY = "bXJpbmFsc2Fob28yNUBnbWFpbC5jb20:HcxwFO6ED6piNQ3AD20O5"  # Replace with your D-ID API key

def generate_avatar_response(text):
    url = "https://api.d-id.com/talks"
    
    payload = {
        "source_url": "https://example.com/avatar.png",  # Your avatar image
        "script": {
            "type": "text",
            "input": text
        }
    }
    
    headers = {
        "Authorization": f"Bearer {DID_API_KEY}",
        "Content-Type": "application/json"
    }

       
    response = requests.post(url, json=payload, headers=headers)
    return response.json()