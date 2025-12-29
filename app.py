import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. Configuration - Change these to your favorite exercises!
EXERCISES = {
    "Pushups (20 reps)": 15,
    "Squats (30 reps)": 15,
    "Plank (1 min)": 20,
    "Walk/Run (1 mile)": 50
}
DATA_FILE = "fitness_log.csv"

# 2. Database Logic - This creates a file to save your progress
if not os.path.exists(DATA_FILE):
    df = pd.DataFrame(columns=["Date", "Exercise", "XP"])
    df.to_csv(DATA_FILE, index=False)

def log_exercise(name, points):
    # This adds a new row to your CSV file
    new_entry = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d %H:%M"), name, points]], 
                             columns=["Date", "Exercise", "XP"])
    new_entry.to_csv(DATA_FILE, mode='a', header=False, index=False)

# 3. App Interface - What you see on your iPhone
st.set_page_config(page_title="Fitness Quest", page_icon="⚔️")

# Calculate Level Stats
df_history = pd.read_csv(DATA_FILE)
total_xp = df_history["XP"].sum()
level = (total_xp // 100) + 1
xp_in_level = total_xp % 100

st.title(f"🛡️ Level {level} Warrior")
st.progress(xp_in_level / 100, text=f"{xp_in_level} / 100 XP to Level {level + 1}")

st.subheader("Daily Quests")

# Generate big buttons
for exercise, xp in EXERCISES.items():
    if st.button(f"{exercise} (+{xp} XP)", use_container_width=True):
        log_exercise(exercise, xp)
        st.toast(f"Logged {exercise}! +{xp} XP")
        st.rerun()

# Activity History
with st.expander("View Activity Log"):
    st.dataframe(df_history.sort_index(ascending=False), use_container_width=True)