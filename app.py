import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from email_validator import validate_email, EmailNotValidError
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import threading
import time
import bcrypt  # Import bcrypt for password hashing

# Email configuration
EMAIL = "dsproject490@gmail.com"
EMAIL_PASSWORD = "eyyb zkyv jptu nlip"

# Database setup
engine = create_engine('sqlite:///notes_app.db')

def create_tables():
    with engine.connect() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            password TEXT
        )
        """))
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            note TEXT,
            notify_time TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """))

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
                    user_email = conn.execute(text(f"SELECT email FROM users WHERE id = {row['user_id']}")).fetchone()[0]
                    threading.Thread(target=send_email, args=(user_email, row['note'], row['notify_time'])).start()
                    # Delete the note after notifying
                    conn.execute(text(f"DELETE FROM notes WHERE id = {row['id']}"))
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
                existing_user = conn.execute(text("SELECT * FROM users WHERE email = :email"), {"email": email}).fetchone()
                if existing_user:
                    st.error("This email is already registered.")
                else:
                    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                    conn.execute(text("INSERT INTO users (email, password) VALUES (:email, :password)"), 
                                 {"email": email, "password": hashed_password})
                    st.success("You have successfully registered!")
        except EmailNotValidError:
            st.error("Invalid email format.")
        except Exception as e:
            st.error(f"An error occurred during registration: {str(e)}")  # Show specific error message

if choice == "Login":
    st.subheader("Login to Your Account")
    email = st.text_input("Email")
    password = st.text_input("Password", type='password')

    if st.button("Login"):
        with engine.connect() as conn:
            user = conn.execute(text("SELECT * FROM users WHERE email = :email"), {"email": email}).fetchone()
            if user and bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):
                st.success("Logged in successfully!")
                
                # Notes section
                st.subheader("Your Notes")
                notes = conn.execute(text("SELECT * FROM notes WHERE user_id = :user_id"), 
                                     {"user_id": user[0]}).fetchall()
                if notes:
                    for note in notes:
                        st.write(note[2])  # Display the note

                new_note = st.text_area("New Note")
                notify_time = st.text_input("Set Reminder Time (YYYY-MM-DD HH:MM)", "")
                
                if st.button("Save Note"):
                    if new_note:
                        try:
                            notify_time_dt = datetime.strptime(notify_time, '%Y-%m-%d %H:%M')
                            conn.execute(text("INSERT INTO notes (user_id, note, notify_time) VALUES (:user_id, :note, :notify_time)"), 
                                         {"user_id": user[0], "note": new_note, 
                                          "notify_time": notify_time_dt.strftime('%Y-%m-%d %H:%M')})
                            st.success("Note saved successfully!")
                        except ValueError:
                            st.error("Invalid date format.")
                    else:
                        st.error("Note cannot be empty.")
            else:
                st.error("Invalid email or password.")

