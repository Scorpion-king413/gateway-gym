import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import os
import base64

# ----------------------------
# python -m streamlit run main.py (Opens program)
# ----------------------------


# ----------------------------
# FILE PATHS
# ----------------------------
ROSTER_FILE = "roster.csv"
ATTENDANCE_FILE = "attendance.csv"

# ----------------------------
# SESSION STATE INIT
# ----------------------------
if "roster_df" not in st.session_state:
    if os.path.exists(ROSTER_FILE):
        st.session_state.roster_df = pd.read_csv(ROSTER_FILE, dtype={"ID": str})
    else:
        st.session_state.roster_df = pd.DataFrame(columns=["ID", "Name"])
        st.session_state.roster_df.to_csv(ROSTER_FILE, index=False)

if "attendance_df" not in st.session_state:
    if os.path.exists(ATTENDANCE_FILE):
        st.session_state.attendance_df = pd.read_csv(ATTENDANCE_FILE, dtype={"ID": str})
    else:
        st.session_state.attendance_df = pd.DataFrame(columns=["ID", "Name", "Action", "Timestamp"])
        st.session_state.attendance_df.to_csv(ATTENDANCE_FILE, index=False)

if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False

# ----------------------------
# HELPER FUNCTIONS
# ----------------------------
def save_roster():
    st.session_state.roster_df.to_csv(ROSTER_FILE, index=False)

def save_attendance():
    st.session_state.attendance_df.to_csv(ATTENDANCE_FILE, index=False)

def get_last_action(user_id):
    df = st.session_state.attendance_df
    logs = df[df["ID"] == user_id]
    if logs.empty:
        return None
    return logs.iloc[-1]["Action"]

# ----------------------------
# TITLE WITH LOGO AND CREATOR
# ----------------------------

# Centered title and subtitle
st.markdown(
    """
    <h1 style='text-align: center; font-size: 36px; white-space: nowrap;'>
        Gateway Sign-In / Sign-Out Sheet
    </h1>
    <p style='text-align: center; font-size: 14px; color: gray;'>
        By: Ismael Perez from the Gateway CS Club
    </p>
    """,
    unsafe_allow_html=True
)

# Load logo and encode it as Base64
with open("static/CSC logo.png", "rb") as image_file:
    encoded_logo = base64.b64encode(image_file.read()).decode()

# Display logo perfectly centered
st.markdown(
    f"""
    <div style="text-align: center; margin-top: 10px;">
        <img src="data:image/png;base64,{encoded_logo}" width="120">
    </div>
    """,
    unsafe_allow_html=True
)

# ----------------------------
# SCAN FORM
# ----------------------------
st.header("Scan or Enter ID")
with st.form("scan_form"):
    scan_input = st.text_input("Scan ID (keep leading zeros)")
    submit_scan = st.form_submit_button("Submit")

if submit_scan:
    user_id = str(scan_input.strip())
    roster_dict = dict(zip(st.session_state.roster_df["ID"], st.session_state.roster_df["Name"]))
    
    if user_id in roster_dict:
        name = roster_dict[user_id]
        last_action = get_last_action(user_id)
        action = "OUT" if last_action == "IN" else "IN"
        
        # Get current time in US Eastern in 12-hour AM/PM format
        eastern = pytz.timezone("US/Eastern")
        current_time = datetime.now(eastern).strftime("%Y-%m-%d %I:%M:%S %p")
        
        new_entry = {"ID": user_id, "Name": name, "Action": action, "Timestamp": current_time}
        st.session_state.attendance_df = pd.concat([st.session_state.attendance_df, pd.DataFrame([new_entry])], ignore_index=True)
        save_attendance()
        st.success(f"{name} checked {action} at {current_time}")
    else:
        st.warning("ID not found. Admin must add user.")

# ----------------------------
# ATTENDANCE LOG WITH DELETE BUTTONS
# ----------------------------
st.header("📊 Attendance Log")
df = st.session_state.attendance_df.copy()
if not df.empty:
    rows_to_keep = []
    for idx, row in df.iterrows():
        cols = st.columns([1, 2, 1, 1, 1])
        cols[0].write(row["ID"])
        cols[1].write(row["Name"])
        cols[2].write(row["Action"])
        cols[3].write(row["Timestamp"])
        delete_clicked = cols[4].button("Delete", key=f"delete_att_{idx}")
        if not delete_clicked:
            rows_to_keep.append(idx)

    st.session_state.attendance_df = st.session_state.attendance_df.loc[rows_to_keep].reset_index(drop=True)
    save_attendance()
else:
    st.write("Attendance log is empty.")

# ----------------------------
# ADMIN LOGIN
# ----------------------------
st.header("🔐 Admin Panel")
with st.form("login_form"):
    password = st.text_input("Enter Admin Password", type="password")
    login_btn = st.form_submit_button("Login")

if login_btn:
    if password == "123456":
        st.session_state.admin_authenticated = True
        st.success("Logged in as admin")
    else:
        st.error("Incorrect password")

# ----------------------------
# ADMIN FUNCTIONS (Roster as table with delete)
# ----------------------------
if st.session_state.admin_authenticated:
    st.subheader("Current Roster")
    roster_df = st.session_state.roster_df.copy()
    if not roster_df.empty:
        rows_to_keep = []
        for idx, row in roster_df.iterrows():
            cols = st.columns([2, 3, 1])
            cols[0].write(row["ID"])
            cols[1].write(row["Name"])
            delete_clicked = cols[2].button("Delete", key=f"delete_roster_{idx}")
            if not delete_clicked:
                rows_to_keep.append(idx)
        st.session_state.roster_df = st.session_state.roster_df.loc[rows_to_keep].reset_index(drop=True)
        save_roster()
    else:
        st.write("Roster is empty.")

    st.subheader("Add New Person")
    with st.form("add_user_form"):
        new_id = st.text_input("New ID (keep leading zeros)")
        new_name = st.text_input("Full Name")
        add_btn = st.form_submit_button("Add Person")

    if add_btn:
        new_id = str(new_id.strip())
        if new_id in st.session_state.roster_df["ID"].values:
            st.error("ID already exists!")
        else:
            st.session_state.roster_df = pd.concat(
                [st.session_state.roster_df, pd.DataFrame([[new_id, new_name]], columns=["ID","Name"])],
                ignore_index=True
            )
            save_roster()
            st.success(f"Added {new_name}")

    if st.button("Logout"):
        st.session_state.admin_authenticated = False