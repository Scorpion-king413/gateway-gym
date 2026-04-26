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
HEALTH_FILE = "health.csv"

# ----------------------------
# SAFE LOAD FUNCTION (fixes empty csv crash)
# ----------------------------
def load_csv_safe(path, columns):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        df = pd.DataFrame(columns=columns)
        df.to_csv(path, index=False)
        return df

    try:
        return pd.read_csv(path, dtype={"ID": str})
    except pd.errors.EmptyDataError:
        df = pd.DataFrame(columns=columns)
        df.to_csv(path, index=False)
        return df

# ----------------------------
# INIT SESSION STATE
# ----------------------------
if "roster_df" not in st.session_state:
    st.session_state.roster_df = load_csv_safe(ROSTER_FILE, ["ID", "Name"])

if "attendance_df" not in st.session_state:
    st.session_state.attendance_df = load_csv_safe(
        ATTENDANCE_FILE, ["ID", "Name", "Action", "Timestamp"]
    )

if "health_df" not in st.session_state:
    st.session_state.health_df = load_csv_safe(HEALTH_FILE, ["ID", "Health"])

if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False

# ----------------------------
# SAVE FUNCTIONS
# ----------------------------
def save_roster():
    st.session_state.roster_df.to_csv(ROSTER_FILE, index=False)

def save_attendance():
    st.session_state.attendance_df.to_csv(ATTENDANCE_FILE, index=False)

def save_health():
    st.session_state.health_df = st.session_state.health_df.drop_duplicates(
        subset=["ID"], keep="last"
    )
    st.session_state.health_df.to_csv(HEALTH_FILE, index=False)

def get_last_action(user_id):
    logs = st.session_state.attendance_df[
        st.session_state.attendance_df["ID"] == user_id
    ]
    if logs.empty:
        return None
    return logs.iloc[-1]["Action"]

# ----------------------------
# TITLE
# ----------------------------
st.markdown(
    "<h1 style='text-align:center;'>Gateway Sign-In / Sign-Out Sheet</h1>",
    unsafe_allow_html=True
)

# ----------------------------
# SCAN
# ----------------------------
st.header("Scan or Enter ID")

with st.form("scan_form"):
    scan_input = st.text_input("Scan ID")
    submit = st.form_submit_button("Submit")

if submit:
    user_id = scan_input.strip()

    roster = st.session_state.roster_df
    match = roster[roster["ID"] == user_id]

    if match.empty:
        st.warning("ID not found in roster")
    else:
        name = match.iloc[0]["Name"]

        # health lookup (separate file)
        health_match = st.session_state.health_df[
            st.session_state.health_df["ID"] == user_id
        ]

        health_note = ""
        if not health_match.empty:
            health_note = health_match.iloc[0]["Health"]

        last = get_last_action(user_id)
        action = "OUT" if last == "IN" else "IN"

        time = datetime.now(pytz.timezone("US/Eastern"))

        new_row = {
            "ID": user_id,
            "Name": name,
            "Action": action,
            "Timestamp": time
        }

        st.session_state.attendance_df = pd.concat(
            [st.session_state.attendance_df, pd.DataFrame([new_row])],
            ignore_index=True
        )

        save_attendance()

        st.success(f"{name} checked {action}")

        if health_note:
            st.warning(f"⚠️ Health Note: {health_note}")

# ----------------------------
# ATTENDANCE LOG
# ----------------------------
st.header("📊 Attendance Log")

df = st.session_state.attendance_df

if not df.empty:
    display = df.iloc[::-1].reset_index()
    keep = set(df.index)

    for _, row in display.iterrows():
        idx = row["index"]

        cols = st.columns([1,2,1,2,1])
        cols[0].write(row["ID"])
        cols[1].write(row["Name"])
        cols[2].write(row["Action"])
        cols[3].write(row["Timestamp"])

        if cols[4].button("Delete", key=f"att_{idx}"):
            keep.discard(idx)

    st.session_state.attendance_df = df.loc[list(keep)].reset_index(drop=True)
    save_attendance()

# ----------------------------
# ADMIN LOGIN
# ----------------------------
st.header("🔐 Admin")

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "123456")

with st.form("login"):
    pw = st.text_input("Password", type="password")
    login = st.form_submit_button("Login")

if login:
    if pw == ADMIN_PASSWORD:
        st.session_state.admin_authenticated = True
        st.success("Logged in")
    else:
        st.error("Wrong password")

# ----------------------------
# ADMIN PANEL
# ----------------------------
if st.session_state.admin_authenticated:

    # -------- ROSTER --------
    st.subheader("Roster")

    roster = st.session_state.roster_df.copy()
    keep = []

    for idx, row in roster.iterrows():
        cols = st.columns([2,3,1])

        cols[0].write(row["ID"])
        cols[1].write(row["Name"])

        if cols[2].button("Delete", key=f"roster_{idx}"):
            continue
        keep.append(idx)

    st.session_state.roster_df = roster.loc[keep].reset_index(drop=True)
    save_roster()

    # ADD PERSON
    st.subheader("Add Person")

    with st.form("add_person"):
        nid = st.text_input("ID")
        name = st.text_input("Name")
        add = st.form_submit_button("Add")

    if add:
        if nid and name:
            if nid in st.session_state.roster_df["ID"].values:
                st.error("ID exists")
            else:
                st.session_state.roster_df = pd.concat(
                    [st.session_state.roster_df,
                     pd.DataFrame([[nid,name]], columns=["ID","Name"])],
                    ignore_index=True
                )
                save_roster()
                st.success("Added")
        else:
            st.error("Fill all fields")

    # -------- HEALTH (SEPARATE SYSTEM) --------
    st.subheader("🩺 Health Records")

    health = st.session_state.health_df.copy()
    keep = []

    for idx, row in health.iterrows():
        cols = st.columns([2,4,1])

        cols[0].write(row["ID"])

        new_note = cols[1].text_input(
            "Health",
            value=row["Health"],
            key=f"health_{idx}"
        )

        st.session_state.health_df.loc[idx, "Health"] = new_note

        if cols[2].button("Delete", key=f"health_del_{idx}"):
            continue
        keep.append(idx)

    st.session_state.health_df = health.loc[keep].reset_index(drop=True)
    save_health()

    # ADD HEALTH NOTE
    st.subheader("Add Health Note")

    with st.form("add_health"):
        hid = st.text_input("ID")
        note = st.text_input("Health Note")
        addh = st.form_submit_button("Add")

    if addh:
        if hid and note:
            st.session_state.health_df = pd.concat(
                [st.session_state.health_df,
                 pd.DataFrame([[hid,note]], columns=["ID","Health"])],
                ignore_index=True
            )
            save_health()
            st.success("Health note added")
        else:
            st.error("Fill all fields")

    # -------- DOWNLOAD --------
    st.download_button(
        "Download Attendance",
        data=st.session_state.attendance_df.to_csv(index=False),
        file_name="attendance.csv"
    )

    if st.button("Logout"):
        st.session_state.admin_authenticated = False