import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# --- 1. CONFIGURATION ---
# I have updated these with your specific requests
EXERCISES = {
    "Pushups (20 reps)": 15,
    "Squats (30 reps)": 15,
    "Plank (1 min)": 20,
    "Walking (5000 steps)": 20,
    "Ropeflow (3 mins)": 10
}

# PASTE YOUR SHEET URL BELOW (Ensure it ends in #gid=0)
SQL_URL = "https://docs.google.com/spreadsheets/d/1c98F2hH63KycHXdUdGXi0HakGMIWW32PFVxBKP4iMc0/edit#gid=0"

# --- 2. CONNECTION SETUP ---
conn = st.connection("gsheets", type=GSheetsConnection)

def log_exercise_to_sheets(name, points):
    # This reads the sheet, adds the new row, and saves it back
    existing_data = conn.read(spreadsheet=SQL_URL, usecols=[0,1,2])
    new_entry = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d %H:%M"), name, points]], 
                             columns=["Date", "Exercise", "XP"])
    updated_df = pd.concat([existing_data, new_entry], ignore_index=True)
    conn.update(spreadsheet=SQL_URL, data=updated_df)

# --- 3. DATA CALCULATIONS ---
try:
    df = conn.read(spreadsheet=SQL_URL)
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Lifetime Score
    lifetime_xp = int(df["XP"].sum())
    
    # Weekly Score (Calculated from most recent Monday)
    today = datetime.now()
    monday = (today - timedelta(days=today.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    weekly_xp = int(df[df['Date'] >= monday]['XP'].sum())
    
    # Streak Calculation (Consecutive days hitting ALL 5 measures)
    df['DateOnly'] = df['Date'].dt.date
    daily_completion = df.groupby('DateOnly')['Exercise'].nunique()
    target_count = len(EXERCISES) # This is 5
    
    streak = 0
    check_date = today.date()
    # Check backward from today
    while check_date in daily_completion and daily_completion[check_date] >= target_count:
        streak += 1
        check_date -= timedelta(days=1)
        
except Exception:
    lifetime_xp, weekly_xp, streak = 0, 0, 0

# --- 4. THE INTERFACE ---
st.set_page_config(page_title="Fitness Quest", page_icon="⚔️")

st.title("🛡️ Warrior Dashboard")

# Top Stats display
c1, c2, c3 = st.columns(3)
c1.metric("Lifetime", f"{lifetime_xp} XP")
c2.metric("This Week", f"{weekly_xp} XP")
c3.metric("Streak", f"{streak} Days", delta="🔥" if streak > 0 else None)

# Level Bar
xp_in_level = lifetime_xp % 100
st.progress(xp_in_level / 100, text=f"Level {(lifetime_xp // 100) + 1} • {xp_in_level}/100 XP to next")

st.divider()

# Daily Quests
st.subheader("Today's Tasks")
st.caption("Complete all 5 to keep your streak!")
for exercise, xp in EXERCISES.items():
    if st.button(f"{exercise} (+{xp} XP)", use_container_width=True):
        log_exercise_to_sheets(exercise, xp)
        st.toast(f"Logged {exercise}!")
        st.rerun()

# History Table
with st.expander("Scroll of History"):
    if not df.empty:
        st.dataframe(df.sort_values(by="Date", ascending=False), use_container_width=True)
    else:
        st.write("No quests logged yet.")
