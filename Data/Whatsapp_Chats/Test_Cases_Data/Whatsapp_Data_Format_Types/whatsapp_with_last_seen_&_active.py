import re
from datetime import datetime
import json
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def parse_whatsapp_chat(file_path):
    # Dictionary to store user data
    users = {}
    
    def standardize_date(date_str):
        """Convert various date formats to DD/MM/YYYY"""
        try:
            date_str = date_str.strip(' []')
            date_formats = ['%d/%m/%y', '%d/%m/%Y', '%m/%d/%y', '%m/%d/%Y']
            
            for fmt in date_formats:
                try:
                    date_obj = datetime.strptime(date_str, fmt)
                    return date_obj.strftime('%d/%m/%Y')
                except ValueError:
                    continue
            return date_str
        except Exception as e:
            logger.error(f"Error standardizing date {date_str}: {e}")
            return date_str

    def convert_to_24hr(time_str):
        """Convert time to 24-hour format"""
        try:
            time_str = time_str.strip(' []')
            
            # Handle "am" and "pm" variations
            time_str = time_str.replace('am', ' AM').replace('pm', ' PM')
            
            if 'AM' in time_str.upper() or 'PM' in time_str.upper():
                try:
                    time_obj = datetime.strptime(time_str, '%I:%M %p')
                except ValueError:
                    time_obj = datetime.strptime(time_str, '%I:%M:%S %p')
            else:
                try:
                    time_obj = datetime.strptime(time_str, '%H:%M')
                except ValueError:
                    time_obj = datetime.strptime(time_str, '%H:%M:%S')
            
            return time_obj.strftime('%H:%M')
        except Exception as e:
            logger.error(f"Error converting time {time_str}: {e}")
            return time_str

    def update_user_status(user_name, date_str, time_str, is_left=None):
        """Update user's status in the users dictionary"""
        if user_name not in users:
            users[user_name] = {
                "id": user_name,
                "messages": [],
                "last_seen": f"{date_str} {time_str}"
            }
        else:
            users[user_name]["last_seen"] = f"{date_str} {time_str}"
        
        if is_left is not None:
            users[user_name]["is_present_in_group"] = not is_left

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                try:
                    line = line.strip()
                    if not line or 'Messages and calls are end-to-end encrypted' in line:
                        continue

                    # More specific pattern for date/time with phone numbers
                    full_pattern = r'(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}(?::\d{2})?\s*(?:am|pm|AM|PM)?)\s*-\s*([^:]+):\s*(.+)'
                    
                    match = re.match(full_pattern, line)
                    if match:
                        date_str = standardize_date(match.group(1))
                        time_str = convert_to_24hr(match.group(2))
                        user_name = match.group(3).strip()
                        message = match.group(4).strip()

                        # Extract tags
                        tags = re.findall(r'@(\d+)', message)
                        tags = tags if tags else None

                        # Update user status and add message
                        update_user_status(user_name, date_str, time_str, is_left=False)
                        
                        # Add message to user's messages
                        users[user_name]["messages"].append({
                            "date": date_str,
                            "time_stamp": time_str,
                            "message": message,
                            "tagged": tags
                        })
                        continue

                    # Check for system messages
                    system_patterns = [
                        (r'(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}(?::\d{2})?\s*(?:am|pm|AM|PM)?)\s*-\s*([^:]+) left', True),
                        (r'(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}(?::\d{2})?\s*(?:am|pm|AM|PM)?)\s*-\s*([^:]+) added ([^:]+)', False),
                        (r'(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}(?::\d{2})?\s*(?:am|pm|AM|PM)?)\s*-\s*([^:]+) removed ([^:]+)', True)
                    ]

                    for pattern, is_left in system_patterns:
                        system_match = re.match(pattern, line)
                        if system_match:
                            date_str = standardize_date(system_match.group(1))
                            time_str = convert_to_24hr(system_match.group(2))
                            
                            if len(system_match.groups()) == 4:  # added/removed
                                user_name = system_match.group(4).strip()
                            else:  # left
                                user_name = system_match.group(3).strip()
                            
                            update_user_status(user_name, date_str, time_str, is_left=is_left)
                            break

                except Exception as e:
                    logger.error(f"Error processing line: {line}\nError: {e}")
                    continue

        return list(users.values())

    except Exception as e:
        logger.error(f"Error processing file: {e}")
        raise

def save_to_json(data, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Example usage
if __name__ == "__main__":
    try:
        input_file = "/home/bhartrihari/UCSF_Project/UCSFR01/Stage_2_All_Data_Combined/Data/Whatsapp_Chats/WhatsApp Chat with Whatupppp_1.txt"
        output_file = "chat_output(vats_test).json"
        
        chat_data = parse_whatsapp_chat(input_file)
        save_to_json(chat_data, output_file)
        print(f"Successfully parsed chat and saved to {output_file}")
    except Exception as e:
        print(f"Error: {e}")
