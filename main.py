import streamlit as st
from dotenv import load_dotenv
from auth import *
from database import *
from admin_features import *
from moderator_features import *
import os
from pymongo import MongoClient
import base64

# Load the environment variables first
load_dotenv()
default_users_path = os.getenv("DEFAULT_USERS_PATH")

# Function to encode image to base64
def get_base64_image(image_file):
    with open(image_file, "rb") as image:
        encoded = base64.b64encode(image.read()).decode()
    return encoded

# Add custom CSS with backdrop image
def set_background(image_file):
    base64_image = get_base64_image(image_file)
    st.markdown(
        f"""
        <style>
        .stApp {{
           background-image: url("data:image/jpeg;base64,{base64_image}");
            background-size: cover;
            background-position: center;
        }}
        
        .main {{ background-color: rgba(255, 255, 255, 0.8); padding: 20px; border-radius: 8px; }}
        
        /* Title and Headers */
        .title-style {{ 
            font-family: 'Arial', sans-serif; 
            color: #333; 
            font-size: 2.5em; 
            text-align: center; 
            margin-top: 20px; 
        }}
        .subtitle-style {{ 
            font-family: 'Arial', sans-serif; 
            color: #555; 
            font-size: 1.5em; 
            text-align: center; 
            margin-bottom: 20px; 
        }}

        /* Buttons */
        .stButton > button {{
            background-color: #6c757d; 
            color: white; 
            padding: 10px 20px;
            border-radius: 5px; 
            border: none; 
            font-size: 1em;
            cursor: pointer;
        }}
        .stButton > button:hover {{
            background-color: #5a6268;
        }}

        /* Input fields */
        .stTextInput > div > input {{
            border: 1px solid #ddd;
            padding: 8px;
            font-size: 1em;
            border-radius: 4px;
            width: 100%;
        }}
        
        /* Error and Warning Messages */
        .stAlert {{
            color: #d9534f;
            font-weight: bold;
        }}
        </style>
        """, unsafe_allow_html=True
    )

# Initialize database
def initialize_database():
    if 'client' not in st.session_state or st.session_state.client is None:
        st.session_state.client = MongoClient(MONGO_URI)  # Ensure the client is always initialized
        st.session_state.db = st.session_state.client['kushal_maa_data']

def main():
    # Set background image (provide path to your local image)
    set_background("WIN_20240316_23_02_33_Pro.jpg")
    
    st.markdown("<h1 class='title-style'>Kushal Maa Platform</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle-style'>An Interactive Platform for Admins and Moderators</p>", unsafe_allow_html=True)
    
    # Initialize database connection
    initialize_database()
    
    # Initialize session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.user_name = None
        st.session_state.user_type = None

    if not st.session_state.logged_in:
        # Add the json file of default users to the database
        insert_initial_users_from_file(default_users_path)
        
        # User input section
        email = st.text_input("Please enter your registered Email", placeholder="Enter your email")
        
        if st.button("Login", key="login_button"):
            if email:
                user = check_user(email)
                user_name = get_user_name(email)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_name = user_name
                    st.session_state.user_type = user["user_type"]
                    st.experimental_rerun()
                else:
                    st.error("User email id not registered. Please Contact Admin")
            else:
                st.warning("Please enter an email address.")
    else:
        if st.session_state.user_type == "Admin":
            admin_main.admin_page(st.session_state.user_name)
        elif st.session_state.user_type == "Moderator":
            moderator_main.moderator_page(st.session_state.user_name)
        else:
            st.error("Invalid user type")
        
        if st.button("Logout", key="main_logout_button"):
            st.session_state.logged_in = False
            st.session_state.user_name = None
            st.session_state.user_type = None
            # Close the database connection
            if 'client' in st.session_state:
                st.session_state.client.close()
                del st.session_state.client
                del st.session_state.db
            st.experimental_rerun()

if __name__ == "__main__":
    main()
