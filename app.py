import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

# --- CONFIGURATION ---
st.set_page_config(page_title="Consistency Tracker", page_icon="💪")

# --- DATA CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        data = conn.read(ttl="0s")
        required_cols = ["Date", "Pushups", "Squats", "Plank", "Walking", "Ropeflow", "Success", "XP"]
        if data is None or data.empty:
            return pd.DataFrame(columns=required_cols)
        return data
    except:
        return pd.DataFrame(columns=["Date", "Pushups", "Squats", "Plank", "Walking", "Ropeflow", "Success", "XP"])

df = load_data()

# Get today's row if it exists
today_str = datetime.now().strftime("%Y-%m-%d")
df['Date_Only'] = pd.to_datetime(df['Date']).dt.strftime("%Y-%m-%d")
today_data = df[df['Date_Only'] == today_str]

# --- SYNC FUNCTION ---
def sync_data(field, value):
    global df
    # If no entry for today, create one
    if today_data.empty:
        new_row = {col: False for col in ["Pushups", "Squats", "Plank", "Walking", "Ropeflow", "Success"]}
        new_row["Date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_row["XP"] = 0
        new_row[field] = value
        df = pd.concat([df.drop(columns=['Date_Only'], errors='ignore'), pd.DataFrame([new_row])], ignore_index=True)
    else:
        idx = today_data.index[0]
        df.at[idx, field] = value
        df.at[idx, "Date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S") # Update timestamp

    # Auto-calculate Success and XP
    idx = df[pd.to_datetime(df['Date']).dt.strftime("%Y-%m-%d") == today_str].index[0]
    
    # Points Logic
    pts = {"Pushups": 5, "Squats": 5, "Plank": 5, "Walking": 5, "Ropeflow": 10}
    current_xp = sum(pts[k] for k in pts if df.at[idx, k] == True)
    
    # Saturday Bonus
    if datetime.now().weekday() == 5 and df.at[idx, "Ropeflow"]:
        current_xp += 10
        
    df.at[idx, "XP"] = current_xp
    df.at[idx, "Success"] = all([df.at[idx, k] for k in pts])
    
    conn.update(data=df.drop(columns=['Date_Only'], errors='ignore'))
    st.toast(f"Synced {field}!")

# --- UI ---
st.title("Consistency Tracker")

# Progression Targets
def get_targets(data):
    base = {"Pushups": 20, "Squats": 30, "Plank": 60, "Walking": 5000, "Ropeflow": 3}
    perfect_days = pd.to_numeric(data['Success'], errors='coerce').fillna(0).sum()
    levels = int(perfect_days // 14)
    for i in range(levels):
        step = i % 3
        if step == 0: base["Pushups"] += 5
        elif step == 1: base["Squats"] += 5
        elif step == 2: base["Plank"] += 15
    return base

targets = get_targets(df)

# Dashboard Display
st.subheader("Today's Progress")
cols = st.columns(3)

# Load current state from DF for checkboxes
current_status = {k: False for k in targets.keys()}
if not today_data.empty:
    for k in targets.keys():
        current_status[k] = bool(today_data.iloc[0][k])

# Activities
for i, (task, target) in enumerate(targets.items()):
    col_idx = i % 3
    with cols[col_idx]:
        unit = "reps" if task in ["Pushups", "Squats"] else "secs" if task == "Plank" else "mins" if task == "Ropeflow" else "steps"
        val = st.checkbox(f"{task} ({target} {unit})", value=current_status[task], key=f"cb_{task}", 
                          on_change=lambda t=task: sync_data(t, st.session_state[f"cb_{t}"]))

# Analytics
st.divider()
if not df.empty:
    st.metric("Total XP Earned", int(df['XP'].sum()))
    
    # 30-Day Chart
    df_chart = df.copy()
    df_chart['Date'] = pd.to_datetime(df_chart['Date'])
    daily = df_chart.groupby(df_chart['Date'].dt.date)['XP'].sum().reset_index()
    fig = px.area(daily.tail(30), x='Date', y='XP', title="Daily Activity")
    st.plotly_chart(fig, use_container_width=True)
