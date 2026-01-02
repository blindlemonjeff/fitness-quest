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
        st.write(f"**{task}**")
        label = f"{target}{'k' if task=='Walking' and target >= 1000 else ''} {unit}"
        checks[task] = st.checkbox(label, key=task)

# --- SUBMISSION LOGIC ---
if st.button("Complete Quest", use_container_width=True):
    all_done = all(checks.values())
    
    # Calculate XP
    daily_xp = sum(POINTS[k] for k, v in checks.items() if v)
    if datetime.now().weekday() == 5 and checks["Ropeflow"]:
        daily_xp += 10 # Extra 10 for the Saturday challenge
        
    new_entry = pd.DataFrame([{
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Pushups": checks["Pushups"],
        "Squats": checks["Squats"],
        "Plank": checks["Plank"],
        "Walking": checks["Walking"],
        "Ropeflow": checks["Ropeflow"],
        "Success": all_done,
        "XP": daily_xp
    }])
    
    updated_df = pd.concat([df, new_entry], ignore_index=True)
    conn.update(data=updated_df)
    st.success("Quest Synced!")
    st.balloons()
    st.rerun()

# --- ANALYTICS & CHART ---
st.divider()
if not df.empty and 'XP' in df.columns:
    st.subheader("Progress Analytics")
    
    # Prepare chart data
    df_chart = df.copy()
    df_chart['Date Only'] = pd.to_datetime(df_chart['Date']).dt.date
    daily_xp = df_chart.groupby('Date Only')['XP'].sum().reset_index()
    
    # Show last 30 days
    cutoff = datetime.now().date() - timedelta(days=30)
    daily_xp = daily_xp[daily_xp['Date Only'] >= cutoff]
    
    if not daily_xp.empty:
        fig = px.area(daily_xp, x='Date Only', y='XP', title="XP Growth (Last 30 Days)")
        fig.update_traces(line_color='#00d4ff')
        st.plotly_chart(fig, use_container_width=True)

    # Progression Stats
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Total XP", int(df['XP'].sum()))
    with c2:
        perfect_days = pd.to_numeric(df['Success'], errors='coerce').fillna(0).sum()
        days_to_next = int(14 - (perfect_days % 14))
        st.metric("Next Level In", f"{days_to_next} Days")
