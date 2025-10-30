import streamlit as st
import requests
import random
import uuid
import time
import os
import json

# --- Constants ---
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
API_KEY = "AIzaSyAa20OkB7cfPWUMH3tVNoyETZjidpYyN2E"  # Replace with your actual API key
USE_API_QUESTIONS = True  # Set to False to use only placeholder questions

# --- Helper Functions ---
# Optional script directory (kept for future assets) -- images removed per request
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Data Structures ---
class Question:
    def __init__(self, question, options, correct_answer, category, difficulty, explanation):
        self.id = str(uuid.uuid4())
        self.question = question
        self.options = options
        self.correct_answer = correct_answer
        self.category = category
        self.difficulty = difficulty
        self.explanation = explanation

# --- Placeholder Questions ---
def get_placeholder_questions():
    return [
        # Current Affairs
        Question("Who is the current President of India as of 2024?", ["Draupadi Murmu", "Ram Nath Kovind", "Pranab Mukherjee", "Narendra Modi"], "Draupadi Murmu", "Current Affairs", "Easy", "Draupadi Murmu became the President of India in July 2022."),
        Question("Which Indian city hosted the G20 Summit in 2023?", ["New Delhi", "Mumbai", "Bengaluru", "Hyderabad"], "New Delhi", "Current Affairs", "Medium", "The G20 Summit 2023 was held in New Delhi, India."),
        # Sports
        Question("Who won the 2023 Cricket World Cup?", ["Australia", "India", "England", "New Zealand"], "Australia", "Sports", "Medium", "Australia won the 2023 ICC Cricket World Cup."),
        Question("Which Indian athlete won a gold medal in javelin at the Tokyo 2020 Olympics?", ["Neeraj Chopra", "Bajrang Punia", "P.V. Sindhu", "Dutee Chand"], "Neeraj Chopra", "Sports", "Easy", "Neeraj Chopra won gold in javelin at the Tokyo 2020 Olympics."),
        # General Knowledge
        Question("What is the capital of India?", ["New Delhi", "Mumbai", "Kolkata", "Chennai"], "New Delhi", "General Knowledge", "Easy", "New Delhi is the capital city of India."),
        Question("Who wrote the Indian national anthem?", ["Rabindranath Tagore", "Bankim Chandra Chatterjee", "Sarojini Naidu", "Subhas Chandra Bose"], "Rabindranath Tagore", "General Knowledge", "Easy", "Rabindranath Tagore wrote the Indian national anthem, 'Jana Gana Mana'."),
        # History
        Question("Who was the first Emperor of the Maurya Dynasty in India?", ["Chandragupta Maurya", "Ashoka", "Bindusara", "Samudragupta"], "Chandragupta Maurya", "History", "Medium", "Chandragupta Maurya founded the Maurya Empire in 322 BCE."),
        Question("The Battle of Plassey was fought in which year?", ["1757", "1857", "1764", "1801"], "1757", "History", "Hard", "The Battle of Plassey was fought on 23 June 1757."),
    ]

# --- Streamlit Session Initialization ---
def initialize_session():
    if 'page' not in st.session_state:
        st.session_state.page = 'opening'
    if 'difficulty' not in st.session_state:
        st.session_state.difficulty = 'Easy'
    if 'questions' not in st.session_state:
        st.session_state.questions = []
    if 'current_question_index' not in st.session_state:
        st.session_state.current_question_index = 0
    if 'score' not in st.session_state:
        st.session_state.score = 0
    if 'question_start_time' not in st.session_state:
        st.session_state.question_start_time = None
    if 'question_start_index' not in st.session_state:
        st.session_state.question_start_index = None

# Time per question (seconds)
TIME_PER_QUESTION = 20

# --- UI Screens ---

def show_opening():
    # Hero/header
    st.markdown("""
    <div class="hero">
      <h1>AI Quiz Game</h1>
      <p class="subtitle">Fast, fun, and smart quizzes — now in a navy-blue theme</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Start Quiz"):
        st.session_state.page = 'start'
        return


def show_start():
    st.markdown("<h2 class='section'>Select Difficulty</h2>", unsafe_allow_html=True)
    # Use explicit buttons for difficulty so colors contrast well and are fully stylable
    col1, col2, col3 = st.columns(3)
    started = False
    with col1:
        st.markdown("<div style='background:#2ecc40;color:#012103;padding:6px;border-radius:6px;text-align:center;font-weight:bold'>Easy</div>", unsafe_allow_html=True)
        if st.button("Select Easy", key="diff_easy"):
            st.session_state.difficulty = "Easy"
            started = True
    with col2:
        st.markdown("<div style='background:#ff851b;color:#4a2500;padding:6px;border-radius:6px;text-align:center;font-weight:bold'>Medium</div>", unsafe_allow_html=True)
        if st.button("Select Medium", key="diff_medium"):
            st.session_state.difficulty = "Medium"
            started = True
    with col3:
        st.markdown("<div style='background:#ff4136;color:#330000;padding:6px;border-radius:6px;text-align:center;font-weight:bold'>Hard</div>", unsafe_allow_html=True)
        if st.button("Select Hard", key="diff_hard"):
            st.session_state.difficulty = "Hard"
            started = True

    if started:
        # Start quiz using the chosen difficulty
        st.session_state.questions = get_placeholder_questions()[:5]  # Limit to 5 questions
        st.session_state.current_question_index = 0
        st.session_state.score = 0
        st.session_state.page = 'quiz'
        return

    # Provide a cancel/back button below
    back_col, _ = st.columns([1, 3])
    with back_col:
        if st.button("Back to Home", key="start_back"):
            st.session_state.page = 'opening'
            return


def show_quiz():
    idx = st.session_state.current_question_index
    questions = st.session_state.questions
    if idx >= len(questions):
        st.session_state.page = 'score'
        return
    total = len(questions)

    # Initialize or reset question start time when we arrive at a question
    if st.session_state.question_start_index != idx:
        st.session_state.question_start_time = time.time()
        st.session_state.question_start_index = idx

    # Auto-advance if time already expired for this question (handles back navigation)
    while True:
        q = questions[idx]
        elapsed = time.time() - st.session_state.question_start_time
        remaining = max(0, int(TIME_PER_QUESTION - elapsed))
        if remaining <= 0:
            # mark as skipped and move on
            st.session_state.current_question_index += 1
            idx = st.session_state.current_question_index
            if idx >= total:
                st.session_state.page = 'score'
                return
            st.session_state.question_start_time = time.time()
            st.session_state.question_start_index = idx
            continue
        break

    # Progress bar
    progress_pct = int((idx / total) * 100)
    st.progress(progress_pct)

    st.markdown(f"<div class='card'><h3>Question {idx + 1} of {total}</h3><p class='question'>{q.question}</p></div>", unsafe_allow_html=True)
    # Timer display
    timer_col, _ = st.columns([1, 3])
    with timer_col:
        st.markdown(f"<div style='font-weight:bold;color:#cfe9ff'>Time left: {remaining}s</div>", unsafe_allow_html=True)

    choice = st.radio("Select an option:", q.options, key=f"q{idx}", label_visibility="collapsed")
    submit_col, spacer_col = st.columns([1, 2])
    with submit_col:
        if st.button("Submit Answer", key=f"submit_{idx}"):
            if choice == q.correct_answer:
                st.session_state.score += 1
            st.session_state.current_question_index += 1
            # reset timer for next question
            st.session_state.question_start_time = None
            st.session_state.question_start_index = None
            return


def show_score():
    st.markdown("<h2 class='section'>Quiz Complete!</h2>", unsafe_allow_html=True)
    score = st.session_state.score
    total = len(st.session_state.questions)
    st.markdown(f"<div class='score'>Your Score: <strong>{score} / {total}</strong></div>", unsafe_allow_html=True)
    st.markdown("<h3 class='section'>Review your answers</h3>", unsafe_allow_html=True)
    for i, q in enumerate(st.session_state.questions):
        correctness = "✅" if q.correct_answer == q.correct_answer else "❌"
        st.markdown(f"<div class='review'><b>Q{i+1}:</b> {q.question}<br/><b>Answer:</b> {q.correct_answer}<br/><i>{q.explanation}</i></div>", unsafe_allow_html=True)
    if st.button("Play Again"):
        st.session_state.page = 'opening'
        return

def inject_theme():
        css = '''
        <style>
        :root{
            --navy:#001f3f;
            --blue:#0074D9;
            --muted:#f3f6fb;
            --card:#04263b;
            --text:#ffffff;
        }
        .stApp {
            background: linear-gradient(180deg, var(--navy) 0%, #002b52 100%);
            color: var(--text) !important;
        }
        .hero {text-align:center; padding:40px 10px; color: var(--text)}
        .hero h1{font-size:42px; margin-bottom:6px}
        .hero .subtitle{color:#cfe9ff; margin-top:0}
        .section{color:var(--text)}
        .card{background:rgba(255,255,255,0.03); padding:18px; border-radius:10px; margin-bottom:12px}
        .card .question{font-size:18px; color:var(--text)}
        .score{background:rgba(255,255,255,0.03); padding:12px; border-radius:8px; display:inline-block}
        .review{background:rgba(255,255,255,0.02); padding:10px; border-radius:8px; margin-bottom:8px}
        div.stButton > button {
            background: linear-gradient(90deg, #0074D9, #005f99) !important;
            color: #ffffff !important;
            border: none !important;
            padding: 10px 18px !important;
            border-radius: 8px !important;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
        }
        div.stButton > button:hover {filter: brightness(1.05);}
        .stRadio label, .stRadio .css-1b1fbeo {color: var(--text) !important}
        </style>
        '''
        st.markdown(css, unsafe_allow_html=True)

# --- Main Application ---

def main():
    initialize_session()
    inject_theme()
    if st.session_state.page == 'opening':
        show_opening()