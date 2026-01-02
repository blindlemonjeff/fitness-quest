import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

# --- CONFIGURATION ---
st.set_page_config(page_title="Consistency Tracker", page_icon="💪")
st.title("Consistency Tracker")

# Constants
POINTS = {
    "Pushups": 5,
    "Squats": 5,
    "Plank": 5,
    "Walking": 5,
    "Ropeflow": 10
}

# --- DATA CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        data = conn.read(ttl="0s")
        # Ensure all required columns exist in the dataframe to prevent KeyErrors
        required_cols = ["Date", "Pushups", "Squats", "Plank", "Walking", "Ropeflow", "Success", "XP"]
        if data is None or data.empty:
            return pd.DataFrame(columns=required_cols)
        
        # If columns are missing (new sheet), add them
        for col in required_cols:
            if col not in data.columns:
                data[col] = None
        return data
    except Exception:
        return pd.DataFrame(columns=["Date", "Pushups", "Squats", "Plank", "Walking", "Ropeflow", "Success", "XP"])

df = load_data()

# --- PROGRESSION LOGIC ---
def get_current_targets(data):
    # Base targets: Plank is in seconds, Walking is steps, Ropeflow is mins
    base = {"Pushups": 20, "Squats": 30, "Plank": 60, "Walking": 5000, "Ropeflow": 3}
    
    if data.empty or 'Success' not in data.columns:
        return base

    # Count 'perfect' days where all tasks were completed
    # We convert to numeric/bool to ensure sum() works
    perfect_days = pd.to_numeric(data['Success'], errors='coerce').fillna(0).sum()
    levels_gained = int(perfect_days // 14)
    
    # Cycle: Pushups -> Squats -> Planks
    for i in range(levels_gained):
        cycle_step = i % 3
        if cycle_step == 0:
            base["Pushups"] += 5
        elif cycle_step == 1:
            base["Squats"] += 5
        elif cycle_step == 2:
            base["Plank"] += 15
            
    return base

targets = get_current_targets(df)

# --- SIDEBAR & TIMESTAMP ---
if not df.empty and 'Date' in df.columns:
    try:
        df['Date'] = pd.to_datetime(df['Date'])
        last_val = df['Date'].max()
        st.sidebar.metric("Last Workout", last_val.strftime("%b %d"))
        st.sidebar.write(f"🕒 {last_val.strftime('%I:%M %p')}")
    except:
        st.sidebar.write("Date format sync pending...")
else:
    st.sidebar.write("No workouts recorded yet.")

# Saturday Weekly Challenge
if datetime.now().weekday() == 5: # 5 is Saturday
    st.warning("🏆 **SATURDAY CHALLENGE:** Double your Ropeflow time for +20 XP!")

# --- MAIN UI: DAILY QUESTS ---
st.subheader("Today's Quest")
cols = st.columns(5)
checks = {}

for i, (task, target) in enumerate(targets.items()):
    unit = "reps" if task in ["Pushups", "Squats"] else "m" if task == "Walking" else "mins"
    if task == "Plank": unit = "secs"
    
    with cols[i]:
