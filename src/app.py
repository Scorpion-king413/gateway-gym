# dep

import os
import pytz

import streamlit as st
import pandas    as pd

from datetime import datetime

from streamlit.logger import get_logger

from src.data import SwipeData


# const

ADMIN_PW = os.getenv('ADMIN_PW', 'admin')


# obj

logger = get_logger(__name__)
state  = st.session_state
data   = SwipeData(state)


# sign-in

st.markdown(
    "# Gateway Sign-In / Sign-Out Sheet"
)

st.markdown("## Scan or Enter ID")

with st.form("scan_form"):
    scan_input = st.text_input("Scan ID")
    submit = st.form_submit_button("Submit")

if submit:
    user_id = scan_input.strip()

    match = data.roster.df[
        data.roster.df["ID"] == user_id
    ]

    if match.empty:
        st.warning("ID not found in roster")
    else:
        name = match.iloc[0]["Name"]

        # health lookup (separate file)
        health_match = data.health.df[
            data.health.df["ID"] == user_id
        ]

        health_note = ""
        if not health_match.empty:
            health_note = health_match.iloc[0]["Health"]

        last = data.get_last_action(user_id)
        action = "OUT" if last == "IN" else "IN"

        time = datetime.now(pytz.timezone("US/Eastern"))

        new_row = {
            "ID": user_id,
            "Name": name,
            "Action": action,
            "Timestamp": time
        }

        data.attendance.df = pd.concat(
            [data.attendance.df, pd.DataFrame([new_row])],
            ignore_index=True
        )

        data.attendance.save()

        st.success(f"{name} checked {action}")

        if health_note:
            st.warning(f"⚠️ Health Note: {health_note}")


# attendance

st.markdown("## 📊 Attendance Log")

df = data.attendance.df

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

    data.attendance.df = df.loc[list(keep)].reset_index(drop=True)
    data.attendance.save()


# admin login

st.markdown("## 🔐 Admin")

with st.form("login"):
    pw = st.text_input("Password", type="password")
    login = st.form_submit_button("Login")

if login:
    if pw == ADMIN_PW:
        data.admin_auth.set(True)
        st.success("Logged in")
    else:
        st.error("Wrong password")

# admin panel

if data.admin_auth.val:

    # -------- ROSTER --------
    st.markdown("### Roster")

    roster = data.roster.df.copy()
    keep = []

    for idx, row in roster.iterrows():
        cols = st.columns([2,3,1])

        cols[0].write(row["ID"])
        cols[1].write(row["Name"])

        if cols[2].button("Delete", key=f"roster_{idx}"):
            continue
        keep.append(idx)

    data.roster.df = roster.loc[keep].reset_index(drop=True)
    data.roster.save()

    # add person
    st.markdown("### Add Person")

    with st.form("add_person"):
        nid  = st.text_input("ID")
        name = st.text_input("Name")
        add  = st.form_submit_button("Add")

    if add:
        if nid and name:
            if nid in data.roster.df["ID"].values:
                st.error("ID exists")
            else:
                data.roster.df = pd.concat(
                    [
                        data.roster.df,
                        pd.DataFrame([[nid,name]], columns=["ID","Name"])
                    ],
                    ignore_index=True
                )
                data.roster.save()
                st.success("Added")
        else:
            st.error("Fill all fields")

    # health (separate system)

    st.markdown("### 🩺 Health Records")

    health = data.health.df.copy()
    keep = []

    for idx, row in health.iterrows():
        cols = st.columns([2,4,1])

        cols[0].write(row["ID"])

        new_note = cols[1].text_input(
            "Health",
            value=row["Health"],
            key=f"health_{idx}"
        )

        data.health.df.loc[idx, "Health"] = new_note

        if cols[2].button("Delete", key=f"health_del_{idx}"):
            continue
        keep.append(idx)

    data.health.df = health.loc[keep].reset_index(drop=True)
    data.health.save()

    # add health note

    st.markdown("### Add Health Note")

    with st.form("add_health"):
        hid = st.text_input("ID")
        note = st.text_input("Health Note")
        addh = st.form_submit_button("Add")

    if addh:
        if hid and note:
            data.health.df = pd.concat(
                [
                    data.health.df,
                    pd.DataFrame([[hid,note]], columns=["ID","Health"])
                ],
                ignore_index=True
            )
            data.health.save()
            st.success("Health note added")
        else:
            st.error("Fill all fields")

    # download record(s)

    st.download_button(
        "Download Attendance",
        data=data.attendance.df.to_csv(index=False),
        file_name="attendance.csv"
    )

    if st.button("Logout"):
        data.admin_auth.set(False)