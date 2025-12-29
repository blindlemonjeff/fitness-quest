import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# --- 1. CONFIGURATION ---
EXERCISES = {
    "Pushups (20 reps)": 15,
    "Squats (30 reps)": 15,
    "Plank (1 min)": 20,
    "Walking (5000 steps)": 20,
    "Ropeflow (3 mins)": 10
}

# Ensure this ID is correct!
SQL_URL = "https://docs.google.com/spreadsheets/d/1c98F2hH63KycHXdUdGXi0HakGMIWW32PFVxBKP4iMc0/edit#gid=0"

# --- 2. CONNECTION SETUP ---
conn = st.connection("gsheets", type=GSheetsConnection)

def log_exercise_to_sheets(name, points):
    try:
        # Try to read the sheet. If it fails or is empty, create a fresh DataFrame
        try:
            existing_data = conn.read(spreadsheet=SQL_URL)
            if existing_data is None or existing_data.empty:
                existing_data = pd.DataFrame(columns=["Date", "Exercise", "XP"])
        except:
            existing_data = pd.DataFrame(columns=["Date", "Exercise", "XP"])
        
        # Create new row
        new_entry = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d %H:%M"), name, points]], 
                                 columns=["Date", "Exercise", "XP"])
        
        # Clean data types to prevent "unsupported operation" errors
        new_entry["XP"] = pd.to_numeric(new_entry["XP"])
        if not existing_data.empty:
            existing_data["XP"] = pd.to_numeric(existing_data["XP"], errors='coerce')

        # Combine
        updated_df = pd.concat([existing_data, new_entry], ignore_index=True)
        
        # Update the sheet
        conn.update(spreadsheet=SQL_URL, data=updated_df)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error logging to sheets: {e}")
        return False

# --- 3. DATA LOAD & CALCULATIONS ---
try:
    df = conn.read(spreadsheet=SQL_URL)
    if df is not None and not df.empty:
        df['Date'] = pd.to_datetime(df['Date'])
        df['XP'] = pd.to_numeric(df['XP'], errors='coerce').fillna(0)
        
        lifetime_xp = int(df["XP"].sum())
        
        today = datetime.now()
        monday = (today - timedelta(days=today.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        weekly_xp = int(df[df['Date'] >= monday]['XP'].sum())
        
        df['DateOnly'] = df['Date'].dt.date
        daily_completion = df.groupby('DateOnly')['Exercise'].nunique()
        target_count = len(EXERCISES)
        
        streak = 0
        check_date = today.date()
        while check_date in daily_completion and daily_completion[check_date] >= target_count:
            streak += 1
            check_date -= timedelta(days=1)
    else:
        lifetime_xp, weekly_xp, streak = 0, 0, 0
        df = pd.DataFrame(columns=["Date", "Exercise", "XP"])
except Exception:
    lifetime_xp, weekly_xp, streak = 0, 0, 0
    df = pd.DataFrame(columns=["Date", "Exercise", "XP"])

# --- 4. UI DISPLAY ---
st.set_page_config(page_title="Fitness Quest", page_icon="⚔️")

st.title("🛡️ Warrior Dashboard")

c1, c2, c3 = st.columns(3)
c1.metric("Lifetime", f"{lifetime_xp} XP")
c2.metric("Weekly", f"{weekly_xp} XP")
c3.metric("Streak", f"{streak} Days", delta="🔥" if streak > 0 else None)

st.divider()

st.subheader("Today's Tasks")
for exercise, xp in EXERCISES.items():
    if st.button(f"{exercise} (+{xp} XP)", use_container_width=True):
        if log_exercise_to_sheets(exercise, xp):
            st.toast(f"Logged {exercise}!")
            st.rerun()

with st.expander("History Log"):
    st.dataframe(df.sort_index(ascending=False), use_container_width=True)
