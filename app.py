import streamlit as st
from sqlalchemy import create_engine, text
import bcrypt

# Database setup
engine = create_engine('sqlite:///notes_app.db')

# Create tables if they don't exist
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

# Streamlit UI
st.title("Notes App")

menu = ["Login", "Register"]
choice = st.sidebar.selectbox("Select Activity", menu)

if choice == "Register":
    st.subheader("Create a New Account")
    email = st.text_input("Email")
    password = st.text_input("Password", type='password')
    
    if st.button("Register"):
        with engine.connect() as conn:
            existing_user = conn.execute(text("SELECT * FROM users WHERE email = :email"), {"email": email}).fetchone()
            if existing_user:
                st.error("This email is already registered.")
            else:
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')  # Hash password
                conn.execute(text("INSERT INTO users (email, password) VALUES (:email, :password)"), 
                             {"email": email, "password": hashed_password})  # Store as string
                st.success("You have successfully registered!")

elif choice == "Login":
    st.subheader("Login to Your Account")
    email = st.text_input("Email")
    password = st.text_input("Password", type='password')

    if st.button("Login"):
        with engine.connect() as conn:
            user = conn.execute(text("SELECT * FROM users WHERE email = :email"), {"email": email}).fetchone()
            if user:
                if bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):  # Check password
                    st.success("Logged in successfully!")
                    
                    # Notes section
                    st.subheader("Your Notes")
                    new_note = st.text_area("New Note")
                    notify_time = st.text_input("Set Reminder Time (YYYY-MM-DD HH:MM)", "")
                    
                    if st.button("Save Note"):
                        if new_note:
                            # Save the note to the database
                            conn.execute(text("INSERT INTO notes (user_id, note, notify_time) VALUES (:user_id, :note, :notify_time)"), 
                                         {"user_id": user[0], "note": new_note, "notify_time": notify_time})
                            st.success("Note saved successfully!")
                        else:
                            st.error("Note cannot be empty.")
                else:
                    st.error("Invalid email or password.")
            else:
                st.error("Invalid email or password.")
