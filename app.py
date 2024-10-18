import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# Database setup
conn = sqlite3.connect('notes_app.db')
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, note TEXT, notify_time TEXT)''')
conn.commit()

def register(username, password):
    c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
    conn.commit()

def login(username, password):
    c.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
    return c.fetchone()

def save_note(user_id, note, notify_time):
    c.execute('INSERT INTO notes (user_id, note, notify_time) VALUES (?, ?, ?)', (user_id, note, notify_time))
    conn.commit()

def get_notes(user_id):
    c.execute('SELECT * FROM notes WHERE user_id=?', (user_id,))
    return c.fetchall()

def notify():
    # Placeholder for notification logic
    pass

# Streamlit UI
st.title("Note-Taking App")

menu = ["Login", "Register"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Register":
    st.subheader("Create New Account")
    new_user = st.text_input("Username")
    new_password = st.text_input("Password", type='password')

    if st.button("Register"):
        register(new_user, new_password)
        st.success("Account created successfully")
        st.info("Go to Login Menu to login")

elif choice == "Login":
    st.subheader("Login to Your Account")
    username = st.text_input("Username")
    password = st.text_input("Password", type='password')

    if st.button("Login"):
        user = login(username, password)
        if user:
            st.success(f"Logged in as {username}")

            st.subheader("Save a Note")
            note = st.text_area("Note")
            notify_time = st.time_input("Set Notify Time", datetime.now() + timedelta(minutes=1))

            if st.button("Save Note"):
                user_id = user[0]
                save_note(user_id, note, notify_time.strftime("%H:%M:%S"))
                st.success("Note saved successfully")

            st.subheader("Your Notes")
            notes = get_notes(user[0])
            for n in notes:
                st.write(f"{n[1]} - Notify at {n[2]}")
        else:
            st.warning("Incorrect Username/Password")

st.sidebar.subheader("Notification Service")
if st.sidebar.button("Run Notification Service"):
    notify()
    st.sidebar.success("Notification Service is running")
