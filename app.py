import streamlit as st
import sqlite3
from datetime import datetime
import bcrypt
import threading
import time

# Database setup
conn = sqlite3.connect('notes_app.db')
c = conn.cursor()

# Create tables if they don't exist
c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, note TEXT, notify_time TEXT)''')
conn.commit()

def register(username, password):
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed))
    conn.commit()

def login(username, password):
    c.execute('SELECT * FROM users WHERE username=?', (username,))
    user = c.fetchone()
    if user and bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):
        return user
    return None

def save_note(user_id, note, notify_time):
    c.execute('INSERT INTO notes (user_id, note, notify_time) VALUES (?, ?, ?)', (user_id, note, notify_time))
    conn.commit()

def get_notes(user_id):
    c.execute('SELECT * FROM notes WHERE user_id=?', (user_id,))
    return c.fetchall()

def notify():
    while True:
        now = datetime.now().strftime("%H:%M:%S")
        c.execute('SELECT * FROM notes')
        notes = c.fetchall()
        for note in notes:
            if note[3] == now:
                # Notify logic: For example, you could send an email here
                print(f"Notification: {note[2]} - Time: {note[3]}")
        time.sleep(60)  # Check every minute

# Start the notification service in a separate thread
threading.Thread(target=notify, daemon=True).start()

# Streamlit UI
st.title("Note-Taking App")

# Initialize session state
if 'user' not in st.session_state:
    st.session_state.user = None

menu = ["Login", "Register"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Register":
    st.subheader("Create New Account")
    new_user = st.text_input("Username")
    new_password = st.text_input("Password", type='password')

    if st.button("Register"):
        try:
            register(new_user, new_password)
            st.success("Account created successfully")
            st.info("Go to Login Menu to login")
        except Exception as e:
            st.error(f"Error: {str(e)}")

elif choice == "Login":
    st.subheader("Login to Your Account")
    username = st.text_input("Username")
    password = st.text_input("Password", type='password')

    if st.button("Login"):
        user = login(username, password)
        if user:
            st.session_state.user = user  # Store user in session state
            st.success(f"Logged in as {username}")
        else:
            st.warning("Incorrect Username/Password")

# If the user is logged in, show the notes interface
if st.session_state.user:
    st.subheader("Save a Note")
    note = st.text_area("Note")
    notify_time = st.time_input("Set Notify Time", datetime.now())

    if st.button("Save Note"):
        user_id = st.session_state.user[0]
        notify_time_str = notify_time.strftime("%H:%M:%S")
        save_note(user_id, note, notify_time_str)
        st.success("Note saved successfully")

    st.subheader("Your Notes")
    notes = get_notes(st.session_state.user[0])
    for n in notes:
        st.write(f"{n[2]} - Notify at {n[3]}")  # Changed to show the correct note text
else:
    st.warning("Please log in to save notes.")
