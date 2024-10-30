import streamlit as st
from pymongo import MongoClient
from typing import List, Dict
from database import *


import streamlit as st
from pymongo import MongoClient
from typing import List, Dict
from datetime import datetime

def get_unique_group_names() -> List[str]:
    """Get unique group names from whatsapp_chats collection"""
    try:
        unique_groups = db["whatsapp_chats"].distinct("group_name")
        return sorted(unique_groups)
    except Exception as e:
        st.error(f"Error fetching group names: {str(e)}")
        return []

def get_unique_members() -> List[str]:
    """Get unique member IDs from all chat groups"""
    try:
        # Get all documents from whatsapp_chats
        all_chats = db["whatsapp_chats"].find({})
        
        # Extract unique members from the nested chat_data
        unique_members = set()
        for chat in all_chats:
            for member in chat["chat_data"]:
                if member["id"] != "you":  # Exclude "you" from the list
                    unique_members.add(member["id"])
        
        return sorted(list(unique_members))
    except Exception as e:
        st.error(f"Error fetching member IDs: {str(e)}")
        return []

def get_zoom_attendance_data(member_id: str) -> List[Dict]:
    """Fetch Zoom attendance data for a specific member"""
    try:
        # Query the zoom_attendance collection for the specific user
        attendance_data = db["zoom_attendance"].find({"name": member_id})
        
        processed_data = []
        for data in attendance_data:
            attendance_info = {
                "group_name": data["group_name"],
                "date": data["date_of_file_upload"],
                "duration": data["duration_of_meet_mins"],
                "uploaded_by": data["uploaded_by"]
            }
            processed_data.append(attendance_info)
        
        return processed_data
    except Exception as e:
        st.error(f"Error fetching Zoom attendance data: {str(e)}")
        return []

def get_whatsapp_data(member_id: str) -> List[Dict]:
    """Fetch WhatsApp chat data for a specific member"""
    try:
        # Find all groups where the member has messages
        all_chats = db["whatsapp_chats"].find({})
        member_data = []
        
        for chat in all_chats:
            group_name = chat["group_name"]
            for member in chat["chat_data"]:
                if member["id"] == member_id:
                    # Format each message with additional context
                    for msg in member["messages"]:
                        member_data.append({
                            "group_name": group_name,
                            "date": msg["date"],
                            "time": msg["time_stamp"],
                            "message": msg["message"],
                            "tagged": msg["tagged"]
                        })
        
        return member_data
    except Exception as e:
        st.error(f"Error fetching WhatsApp data: {str(e)}")
        return []

def get_zoom_audio_data(member_id: str) -> List[Dict]:
    """Fetch Zoom audio chat data for a specific member"""
    try:
        # Query the zoom_audio_chat collection for the specific user
        zoom_data = db["Zoom_audio_chat"].find({"user_name": member_id})
        
        processed_data = []
        for data in zoom_data:
            for chat_session in data["chat"]:
                session_data = {
                    "group_name": data["group_name"],
                    "date": chat_session["date_of_upload"],
                    "total_duration": data["total_duration"],
                    "messages": chat_session["messages"]
                }
                processed_data.append(session_data)
        
        return processed_data
    except Exception as e:
        st.error(f"Error fetching Zoom audio data: {str(e)}")
        return []

def get_zoom_chatbox_data(member_id: str) -> List[Dict]:
    """Fetch Zoom chatbox data for a specific member"""
    try:
        # Query the zoom_chatbox_messages collection
        all_chats = db["zoom_chatbox_messages"].find({})
        
        processed_data = []
        for chat in all_chats:
            # Find the member's messages in the chat_data
            for participant in chat["chat_data"]:
                if participant["name"] == member_id:
                    session_data = {
                        "group_name": chat["group_name"],
                        "date": chat["date_of_upload"],
                        "messages": participant["messages"]
                    }
                    processed_data.append(session_data)
        
        return processed_data
    except Exception as e:
        st.error(f"Error fetching Zoom chatbox data: {str(e)}")
        return []

def format_duration(seconds: int) -> str:
    """Convert seconds to hours:minutes:seconds format"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    remaining_seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{remaining_seconds:02d}"

def display_overview():
    """Main function to display overview dashboard"""
    st.header("Overview Dashboard")
    
    # Display unique group names
    groups = get_unique_group_names()
    if groups:
        st.subheader("Available Groups")
        for group in groups:
            st.write(f"- {group}")
    else:
        st.warning("No groups found in the database")
    
    # Member selection dropdown
    members = get_unique_members()
    if members:
        selected_member = st.selectbox(
            "Select Member",
            options=members,
            help="Choose a member to view their data"
        )
        
        # Data type selection dropdown
        data_type = st.selectbox(
            "Select Data Type",
            options=["Zoom Attendance", "WhatsApp Chat", "Zoom Audio", "Zoom Chatbox"],
            help="Choose the type of data to view"
        )
        
        if st.button("Show Data"):
            if data_type == "Zoom Attendance":
                attendance_data = get_zoom_attendance_data(selected_member)
                if attendance_data:
                    st.subheader(f"Zoom Attendance Data for {selected_member}")
                    
                    # Group attendance by group name
                    attendance_by_group = {}
                    for record in attendance_data:
                        group = record["group_name"]
                        if group not in attendance_by_group:
                            attendance_by_group[group] = []
                        attendance_by_group[group].append(record)
                    
                    # Display attendance organized by group
                    for group, records in attendance_by_group.items():
                        st.write(f"### Group: {group}")
                        total_duration = sum(record["duration"] for record in records)
                        st.write(f"**Total Duration**: {total_duration} minutes")
                        
                        for record in records:
                            st.write(f"""
                            **Date**: {record['date']}  
                            **Duration**: {record['duration']} minutes  
                            **Uploaded by**: {record['uploaded_by']}  
                            ---
                            """)
                else:
                    st.info("No Zoom attendance data found for this member")
                    
            elif data_type == "WhatsApp Chat":
                chat_data = get_whatsapp_data(selected_member)
                if chat_data:
                    st.subheader(f"WhatsApp Chat Data for {selected_member}")
                    
                    # Group messages by group name
                    messages_by_group = {}
                    for msg in chat_data:
                        group = msg["group_name"]
                        if group not in messages_by_group:
                            messages_by_group[group] = []
                        messages_by_group[group].append(msg)
                    
                    # Display messages organized by group
                    for group, messages in messages_by_group.items():
                        st.write(f"### Group: {group}")
                        for msg in messages:
                            tagged_info = f" (Tagged: {msg['tagged']})" if msg['tagged'] else ""
                            st.write(f"""
                            **Date**: {msg['date']} {msg['time']}  
                            **Message**: {msg['message']}{tagged_info}  
                            ---
                            """)
                else:
                    st.info("No WhatsApp chat data found for this member")
                    
            elif data_type == "Zoom Audio":
                zoom_data = get_zoom_audio_data(selected_member)
                if zoom_data:
                    st.subheader(f"Zoom Audio Data for {selected_member}")
                    
                    for session in zoom_data:
                        st.write(f"### Group: {session['group_name']}")
                        st.write(f"**Session Date**: {session['date']}")
                        st.write(f"**Total Duration**: {format_duration(session['total_duration'])}")
                        
                        st.write("#### Messages:")
                        for msg in session["messages"]:
                            st.write(f"""
                            **Time**: {msg['time_stamp']}  
                            **Message**: {msg['messages']}  
                            ---
                            """)
                else:
                    st.info("No Zoom audio data found for this member")
                    
            else:  # Zoom Chatbox data # See this once more !!!
                chatbox_data = get_zoom_chatbox_data(selected_member)
                if chatbox_data:
                    st.subheader(f"Zoom Chatbox Data for {selected_member}")
                    
                    for session in chatbox_data:
                        st.write(f"### Group: {session['group_name']}")
                        st.write(f"**Session Date**: {session['date']}")
                        
                        st.write("#### Messages:")
                        for msg in session["messages"]:
                            tagged_info = f" (Tagged: {msg['tagged']})" if msg['tagged'] else ""
                            st.write(f"""
                            **Time**: {msg['time_stamp']}  
                            **Message**: {msg['message']}{tagged_info}  
                            ---
                            """)
                else:
                    st.info("No Zoom chatbox data found for this member")
    else:
        st.error("No members found in the database")
