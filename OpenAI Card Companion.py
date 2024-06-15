import os
import base64
import requests
import json
import shutil
import logging
from unidecode import unidecode
import re
from datetime import datetime
import unicodedata

# Function to read API key, logging level, and cleanup mode from tcg.cfg file
def read_config():
    config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tcg.cfg')
    if not os.path.exists(config_file):
        print("Configuration file 'tcg.cfg' not found.")
        return None, 'WARNING', True
    
    api_key = None
    logging_level = 'WARNING'
    cleanup_mode = True
    
    with open(config_file, 'r') as file:
        lines = file.readlines()
        for line in lines:
            if "openai_api_key=" in line:
                api_key = line.split("=", 1)[1].strip()
            elif "logging_level=" in line:
                logging_level = line.split("=", 1)[1].strip().upper()
            elif "CleanUpMode=" in line:
                cleanup_mode = line.split("=", 1)[1].strip().lower() == 'true'
    
    if not api_key:
        logging.error("API key not found in 'tcg.cfg'.")
    
    return api_key, logging_level, cleanup_mode

# Set up logging
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log.txt')
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s:%(message)s', handlers=[logging.FileHandler(log_file), logging.StreamHandler()])

API_KEY, LOGGING_LEVEL, CLEAN_UP_MODE = read_config()

logging.getLogger().setLevel(getattr(logging, LOGGING_LEVEL, logging.WARNING))

if not API_KEY:
    print("No API key found. Please ensure you have your OpenAI API key listed in tcg.cfg")
    logging.error("No API key found. Please ensure you have your OpenAI API key listed in tcg.cfg")
    input("Press Enter to exit.")
    exit()

def encode_image(image_path):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        log_error(f"Failed to encode image {image_path}: {str(e)}")
        return None

def log_error(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{timestamp} - Error occurred. Check log.txt for details.")
    logging.error(message)

def sanitize_filename(name):
    # Replace '&' with 'and'
    name = name.replace('&', 'and')
    # Normalize Unicode characters
    nfkd_form = unicodedata.normalize('NFD', name)
    sanitized_name = ''.join([c for c in nfkd_form if not unicodedata.combining(c)])
    # Remove special characters except spaces, hyphens, and periods
    sanitized_name = re.sub(r'[^\w\s.-]', '', sanitized_name)
    # Replace multiple spaces with a single space
    sanitized_name = re.sub(r'\s+', ' ', sanitized_name).strip()
    return sanitized_name

def process_image(image_path):
    base64_image = encode_image(image_path)
    if not base64_image:
        log_error(f"Image encoding failed for {image_path}")
        return None, None
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": "You are a trading card game expert that responds in JSON."},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Please identify this card. Return the card name and TCG name."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 300
    }
    
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    
    if response.status_code == 200:
        response_data = response.json()
        logging.debug(f"Received response for {image_path}: {response_data}")
        try:
            content = response_data['choices'][0]['message']['content']
            content_json = json.loads(content.strip('```json\n'))
            return content_json.get("card_name"), content_json.get("tcg_name")
        except (KeyError, json.JSONDecodeError) as e:
            log_error(f"Error parsing JSON response for {image_path}: {str(e)}")
            return None, None
    else:
        log_error(f"API request failed for {image_path} with status code {response.status_code}")
        logging.debug(f"Response content: {response.content}")
        return None, None

def move_file(src, dest_dir, new_name):
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    
    base_name, extension = os.path.splitext(new_name)
    new_path = os.path.join(dest_dir, new_name)
    count = 1
    
    while os.path.exists(new_path):
        new_name = f"{base_name}_{count}{extension}"
        new_path = os.path.join(dest_dir, new_name)
        count += 1
    
    shutil.move(src, new_path)
    return new_name

def process_directory(base_directory):
    for game_name in os.listdir(base_directory):
        game_path = os.path.join(base_directory, game_name)
        if os.path.isdir(game_path):
            for set_name in os.listdir(game_path):
                set_path = os.path.join(game_path, set_name)
                if os.path.isdir(set_path):
                    errors_path = os.path.join(set_path, "Errors")
                    if os.path.exists(errors_path):
                        relative_errors_path = os.path.relpath(errors_path, base_directory)
                        error_files = [f for f in os.listdir(errors_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                        print(f"Now processing {relative_errors_path} directory")
                        print(f"Found {len(error_files)} error files")
                        for root, dirs, files in os.walk(errors_path):
                            for file in files:
                                if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                                    file_path = os.path.join(root, file)
                                    card_name, tcg_name = process_image(file_path)
                                    
                                    if card_name and tcg_name:
                                        sanitized_card_name = sanitize_filename(card_name)
                                        dest_dir = os.path.dirname(errors_path)
                                        
                                        original_name = file
                                        new_name = f"{sanitized_card_name}{os.path.splitext(file)[1]}"
                                        new_name = move_file(file_path, dest_dir, new_name)
                                        relative_original_path = os.path.relpath(file_path, base_directory)
                                        relative_new_path = os.path.relpath(os.path.join(dest_dir, new_name), base_directory)
                                        print(f"Renamed '{relative_original_path}' to '{relative_new_path}'")
                                        logging.info(f"Renamed '{relative_original_path}' to '{relative_new_path}'")
                                    else:
                                        log_error(f"Failed OCR recognition for '{file}'")
                        
                        # Check if the Errors directory is empty and remove it if CleanUpMode is enabled
                        if CLEAN_UP_MODE and not os.listdir(errors_path):
                            os.rmdir(errors_path)
                            print(f"Removed empty directory: {relative_errors_path}")
                            logging.info(f"Removed empty directory: {relative_errors_path}")

if __name__ == "__main__":
    print("EasyOCR Card Companion is running!")
    base_directory = os.path.dirname(os.path.abspath(__file__))
    process_directory(base_directory)
    logging.info("Processing complete. Press Enter to exit.")
    input("Processing complete. Press Enter to exit.")
