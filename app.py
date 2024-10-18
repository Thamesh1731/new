import streamlit as st
import pandas as pd
import sqlite3
from sqlalchemy import create_engine
from email_validator import validate_email, EmailNotValidError
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import threading
import time

# Email configuration
EMAIL = "dsproject490@gmail.com"
EMAIL_PASSWORD = "eyyb zkyv jptu nlip"

# Database setup
engine = create_engine('sqlite:///notes_app.db')

def create_tables():
    with engine.connect() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            password TEXT
        )
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            note TEXT,
            notify_time TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """)

create_tables()

def send_email(to_email, note, notify_time):
    msg = MIMEText(f"Reminder for your note: '{note}' set for {notify_time}.")
    msg['Subject'] = 'Note Reminder'
    msg['From'] = EMAIL
    msg['To'] = to_email

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(EMAIL, EMAIL_PASSWORD)
        server.sendmail(msg['From'], [msg['To']], msg.as_string())

def notify_users():
    while True:
        with engine.connect() as conn:
            notes_df = pd.read_sql("SELECT * FROM notes", conn)
            now = datetime.now()
            for _, row in notes_df.iterrows():
                notify_time = datetime.strptime(row['notify_time'], '%Y-%m-%d %H:%M')
                if now >= notify_time:
                    user_email = conn.execute(f"SELECT email FROM users WHERE id = {row['user_id']}").fetchone()[0]
                    threading.Thread(target=send_email, args=(user_email, row['note'], row['notify_time'])).start()
                    # Delete the note after notifying
                    conn.execute(f"DELETE FROM notes WHERE id = {row['id']}")
        time.sleep(60)  # Check every minute

threading.Thread(target=notify_users, daemon=True).start()

# Streamlit UI
st.title("Notes App")

menu = ["Login", "Register"]
choice = st.sidebar.selectbox("Select Activity", menu)

if choice == "Register":
    st.subheader("Create a New Account")
    email = st.text_input("Email")
    password = st.text_input("Password", type='password')
    
    if st.button("Register"):
        try:
            validate_email(email)
            with engine.connect() as conn:
                conn.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
                st.success("You have successfully registered!")
        except EmailNotValidError as e:
            st.error(str(e))
        except Exception as e:
            st.error("This email already exists or another error occurred.")
            
if choice == "Login":
    st.subheader("Login to Your Account")
    email = st.text_input("Email")
    password = st.text_input("Password", type='password')

    if st.button("Login"):
        with engine.connect() as conn:
            user = conn.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password)).fetchone()
            if user:
                st.success("Logged in successfully!")
                
                # Notes section
                st.subheader("Your Notes")
                notes = conn.execute("SELECT * FROM notes WHERE user_id = ?", (user[0],)).fetchall()
                if notes:
                    for note in notes:
                        st.write(note[2])  # Display the note

                new_note = st.text_area("New Note")
                notify_time = st.text_input("Set Reminder Time (YYYY-MM-DD HH:MM)", "")
                
                if st.button("Save Note"):
                    if new_note:
                        try:
                            notify_time_dt = datetime.strptime(notify_time, '%Y-%m-%d %H:%M')
                            conn.execute("INSERT INTO notes (user_id, note, notify_time) VALUES (?, ?, ?)", (user[0], new_note, notify_time_dt.strftime('%Y-%m-%d %H:%M')))
                            st.success("Note saved successfully!")
                        except ValueError:
                            st.error("Invalid date format.")
                    else:
                        st.error("Note cannot be empty.")
            else:
                st.error("Invalid email or password.")
