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
    # Adding ttl=0 to ensure we get live data on every refresh
    return conn.read(ttl="0s")

df = load_data()

# --- PROGRESSION LOGIC ---
def get_current_targets(data):
    base = {"Pushups": 20, "Squats": 30, "Plank": 60, "Walking": 5000, "Ropeflow": 3}
    if data.empty or 'Success' not in data.columns:
        return base
        
    perfect_days = data['Success'].sum()
    levels_gained = int(perfect_days // 14)
    
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

# --- SIDEBAR & SATURDAY CHALLENGE ---
if not df.empty:
    df['Date'] = pd.to_datetime(df['Date'])
    last_val = df['Date'].max()
    st.sidebar.metric("Last Workout", last_val.strftime("%b %d"))
    st.sidebar.write(f"🕒 {last_val.strftime('%I:%M %p')}")
else:
    st.sidebar.write("No history found.")

if datetime.now().weekday() == 5: 
    st.warning("🏆 **SATURDAY CHALLENGE:** Double your Ropeflow time for +20 XP!")

# --- MAIN UI: QUESTS ---
st.subheader("Today's Quest")
cols = st.columns(5)
checks = {}

for i, (task, target) in enumerate(targets.items()):
    unit = "reps" if task in ["Pushups", "Squats"] else "m" if task == "Walking" else "mins"
    if task == "Plank": unit = "secs"
    
    with cols[i]:
        st.write(f"**{task}**")
        st.caption(f"Target: {target}{'k' if task=='Walking' else ''} {unit}")
        checks[task] = st.checkbox("Done", key=task)

if st.button("Submit Daily Progress", use_container_width=True):
    all_done = all(checks.values())
    new_entry = pd.DataFrame([{
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Pushups": checks["Pushups"],
        "Squats": checks["Squats"],
        "Plank": checks["Plank"],
        "Walking": checks["Walking"],
        "Ropeflow": checks["Ropeflow"],
        "Success": all_done,
        "XP": sum(POINTS[k] for k, v in checks.items() if v)
    }])
    
    updated_df = pd.concat([df, new_entry], ignore_index=True)
    conn.update(data=updated_df)
    st.success("Progress Saved!")
    st.balloons()

# --- VISUALIZATION: 30-DAY XP GROWTH ---
st.divider()
st.subheader("Progress Analytics")

if not df.empty:
    # Prepare data for chart
    df_chart = df.copy()
    df_chart['Date Only'] = df_chart['Date'].dt.date
    daily_xp = df_chart.groupby('Date Only')['XP'].sum().reset_index()
    
    # Filter for last 30 days
    last_30_days = datetime.now().date() - timedelta(days=30)
    daily_xp = daily_xp[daily_xp['Date Only'] >= last_30_days]
    
    # Create the chart
    fig = px.area(daily_xp, x='Date Only', y='XP', 
                  title="30-Day XP Trend",
                  labels={'XP': 'Daily XP', 'Date Only': 'Date'},
                  template="plotly_dark")
    fig.update_traces(line_color='#00d4ff')
    st.plotly_chart(fig, use_container_width=True)

    # Progression Stats
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Total XP", int(df['XP'].sum()))
    with c2:
        perfect_days = df['Success'].sum()
        days_to_next = 14 - (perfect_days % 14)
        st.metric("Days to Level Up", f"{days_to_next}/14")
