import streamlit as st
import json
import os
import hashlib

# Load car database
with open("car_database.json") as f:
    car_db = json.load(f)

# Load or initialize Q-table
if os.path.exists("q_table.json"):
    with open("q_table.json") as f:
        q_table = json.load(f)
else:
    q_table = {}

# Function to convert persona to a unique key
def persona_to_key(persona):
    key_str = f"{persona['budget']}_{persona['fuel']}_{persona['transmission']}_{persona['space']}_{persona['usage']}"
    return hashlib.md5(key_str.encode()).hexdigest()

# Function to update Q-table based on feedback
def update_q_table(state, action, reward, alpha=0.1):
    if state not in q_table:
        q_table[state] = {}
    if action not in q_table[state]:
        q_table[state][action] = 0
    q_table[state][action] += alpha * (reward - q_table[state][action])
    with open("q_table.json", "w") as f:
        json.dump(q_table, f)

# Function to match cars based on persona and Q-table
def match_car(persona, cars, q_table):
    persona_key = persona_to_key(persona)
    matches = []
    for car in cars:
        score = 0
        if float(persona["budget"]) >= car["price"]:
            score += 1
        if persona["fuel"].lower() in car["fuel"].lower():
            score += 1
        if persona["transmission"].lower() in car["transmission"].lower():
            score += 1
        if persona["space"].lower() in car["space"].lower():
            score += 1
        if persona["usage"].lower() in car["usage"].lower():
            score += 1
        # Add Q-table score if available
        q_score = q_table.get(persona_key, {}).get(car["name"], 0)
        total_score = score + q_score
        matches.append((car["name"], total_score))
    matches.sort(key=lambda x: x[1], reverse=True)
    return matches[:3]  # Top 3 matches

# Streamlit app
st.title("🚗 Find Your Perfect Car")

# Initialize session state
if "persona" not in st.session_state:
    st.session_state.persona = {}

questions = {
    "budget": "What is your budget? (in INR Lakhs)",
    "fuel": "Preferred fuel type? (Petrol/Diesel/Electric/Hybrid)",
    "transmission": "Automatic or Manual?",
    "space": "Do you need more seating or boot space?",
    "usage": "City, Highway, or Off-roading?"
}

# Collect user inputs
for key, question in questions.items():
    if key not in st.session_state.persona:
        response = st.text_input(question, key=key)
        if response:
            st.session_state.persona[key] = response

# Once all inputs are collected
if len(st.session_state.persona) == len(questions):
    st.success("✅ Persona created!")
    st.write(st.session_state.persona)

    # Match cars
    top_cars = match_car(st.session_state.persona, car_db, q_table)
    st.subheader("🔍 Top Car Matches")
    for car, score in top_cars:
        st.write(f"**{car}** - Score: {score:.2f}")

    # Feedback mechanism
    feedback = st.slider("How would you rate this recommendation ?", 1, 5, key="feedback")
    if feedback:
        reward = 1 if feedback >= 3 else -1
        persona_key = persona_to_key(st.session_state.persona)
        update_q_table(persona_key, top_cars[0][0], reward)
        st.write("Thank you for your feedback! The system will learn from this.")
