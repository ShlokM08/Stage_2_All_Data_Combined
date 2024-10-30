# moderator_main.py

import streamlit as st
from pymongo import MongoClient
from .whatsapp_chat_parser import *
from .zoom_audio_service import ZoomAudioService, handle_zoom_audio_upload
from .zoom_chat_service import ZoomChatService, handle_zoom_chat_upload
from .zoom_attendence_service import ZoomAttendanceService, handle_zoom_attendance_upload
from database import *

# Initializing database
client = MongoClient(MONGO_URI)
db = client['kushal_maa_data']
st.session_state.db = db

zoom_chat_service = ZoomChatService(st.session_state.db)

def get_moderator_groups(db, user_name):
    """Get list of groups assigned to moderator"""
    user = db['users'].find_one({"name": user_name, "user_type": "Moderator"})
    if user and "current_groups" in user:
        return user['current_groups']
    return []

def handle_whatsapp_upload(whatsapp_service, group_name, uploaded_file, user_name):
    """Handle WhatsApp chat file upload and processing"""
    try:
        # Read and process the file
        content = uploaded_file.getvalue().decode('utf-8')
        
        # Process the chat content
        process_result = whatsapp_service.process_chat_file(content)
        
        if process_result["status"] == "error":
            st.error(f"Error processing file: {process_result['message']}")
            return
            
        # Show preview of parsed data
        st.write("Preview of parsed data:")
        st.write(process_result["message"])
        
        # Save button
        if st.button(f"Save {group_name}'s WhatsApp chat to database"):
            save_result = whatsapp_service.save_chat_data(
                group_name,
                process_result["data"],
                user_name
            )
            
            if save_result["status"] == "success":
                st.success(f"""
                    WhatsApp chat for {group_name} uploaded and saved successfully!
                    Database ID: {save_result['data']['chat_id']}
                """)
            else:
                st.error(f"Error saving to database: {save_result['message']}")
                
    except Exception as e:
        st.error(f"Error handling WhatsApp chat: {str(e)}")

def moderator_page(user_name):
    """Main moderator interface"""
    st.title(f"Welcome, {user_name}!")
    
    # Initialize MongoDB connection
    if 'db' not in st.session_state:
        st.error("Database not initialized. Please contact Admin.")
        return
        
    # Initialize services
    whatsapp_service = WhatsAppService(st.session_state.db)
    zoom_audio_service = ZoomAudioService(st.session_state.db)
    zoom_attendance_service = ZoomAttendanceService(st.session_state.db)
    
    # Retrieve current groups
    groups = get_moderator_groups(st.session_state.db, user_name)
    
    if not groups:
        st.warning("You are not assigned to any group currently.")
        return

    st.subheader("You are currently assigned to the following groups:")
    
    # Display each group and file upload options
    for group in groups:
        group_name = group['group_name']
        st.write(f"Group: {group_name}")
        
        # Create tabs for different upload types
        tabs = st.tabs(["WhatsApp Chat", "Zoom Audio", "Zoom Chat", "Zoom Attendance"])
        
        # WhatsApp Chat Tab
        with tabs[0]:
            whatsapp_chat = st.file_uploader(
                f"Upload WhatsApp chat for {group_name}",
                type=["txt"],
                key=f"whatsapp_{group_name}"
            )
            
            if whatsapp_chat:
                handle_whatsapp_upload(whatsapp_service, group_name, whatsapp_chat, user_name)
        
        # Zoom Audio Tab
        with tabs[1]:
            zoom_audio = st.file_uploader(
                f"Upload Zoom audio transcript for {group_name}",
                type=["txt"],
                key=f"transcript_{group_name}"
            )
            if zoom_audio:
                handle_zoom_audio_upload(zoom_audio_service, group_name, zoom_audio, user_name)        
        # Zoom Chat Tab
        with tabs[2]:
            zoom_chat = st.file_uploader(
                f"Upload Zoom chat file for {group_name}",
                type=["txt"],
                key=f"chat_{group_name}"
            )
            if zoom_chat:
                handle_zoom_chat_upload(zoom_chat_service, group_name, zoom_chat, user_name)
        
        # Zoom Attendance Tab
        with tabs[3]:
            zoom_attendance = st.file_uploader(
                f"Upload Zoom attendance file for {group_name}",
                type=["csv", "xls", "xlsx"],
                key=f"attendance_{group_name}"
            )
            if zoom_attendance:
                handle_zoom_attendance_upload(zoom_attendance_service,
                                              group_name,
                                              zoom_attendance,
                                              user_name)

# if __name__ == "__main__":
#     # Initialize MongoDB connection
#     try:
#         client = MongoClient(MONGO_URI)
#         db = client['kushal_maa_data']
#         st.session_state.db = db
#         moderator_page("test_moderator")
#     except Exception as e:
#         st.error(f"Failed to connect to database: {e}")
