import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import bcrypt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import schedule
import time
import threading

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

def send_email(subject, body, recipient_email):
    sender_email = "dsproject490@gmail.com"  # Replace with your email
    sender_password = "eyyb zkyv jptu nlip"  # Replace with your password

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)

def notify(note, recipient_email):
    send_email("Note Reminder", f"Reminder for your note: {note[2]}", recipient_email)

def schedule_notifications():
    while True:
        schedule.run_pending()
        time.sleep(1)

# Start the scheduling thread
threading.Thread(target=schedule_notifications, daemon=True).start()

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
    notify_date = st.date_input("Set Notify Date", datetime.now().date())
    notify_time = st.time_input("Set Notify Time", datetime.now().time())

    if st.button("Save Note"):
        user_id = st.session_state.user[0]
        notify_datetime = datetime.combine(notify_date, notify_time).strftime("%Y-%m-%d %H:%M:%S")  # Combine date and time
        save_note(user_id, note, notify_datetime)
        # Schedule the notification
        schedule_time = datetime.strptime(notify_datetime, "%Y-%m-%d %H:%M:%S")
        schedule.every().day.at(schedule_time.strftime("%H:%M")).do(notify, (user_id, note, st.session_state.user[1]))
        st.success("Note saved successfully and notification scheduled.")

    st.subheader("Your Notes")
    notes = get_notes(st.session_state.user[0])
    for n in notes:
        st.write(f"{n[2]} - Notify at {n[3]}")  # Display note and notification time
else:
    st.warning("Please log in to save notes.")
