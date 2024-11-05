import hashlib
import time
import difflib
import datetime
import argparse
import requests
import threading
import random
import string
import os
from decouple import config

# Load Telegram bot token and chat ID from environment variables or .env file
TELEGRAM_BOT_TOKEN = config('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = config('TELEGRAM_CHAT_ID')

def send_telegram_message(message):
    """Send a simple text message to the Telegram bot."""
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message
    }
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to send message to Telegram: {e}")

def send_telegram_document(document_path):
    """Send a document to the Telegram bot and delete it after sending."""
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument'
    with open(document_path, 'rb') as document:
        files = {'document': document}
        data = {'chat_id': TELEGRAM_CHAT_ID}
        try:
            response = requests.post(url, data=data, files=files)
            response.raise_for_status()
            print(f"Document sent to Telegram: {document_path}")
        except requests.RequestException as e:
            print(f"Failed to send document to Telegram: {e}")
        finally:
            # Delete the file after sending
            os.remove(document_path)
            print(f"Document deleted after sending: {document_path}")

def get_file_hash(filename):
    """Generate an MD5 hash for the contents of the given file."""
    try:
        with open(filename, 'rb') as f:
            file_hash = hashlib.md5()
            while chunk := f.read(8192):
                file_hash.update(chunk)
            return file_hash.hexdigest()
    except FileNotFoundError:
        return None

def get_url_hash(url):
    """Generate an MD5 hash for the contents of the file at the given URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return hashlib.md5(response.content).hexdigest(), response.text.splitlines()
    except requests.RequestException:
        return None, None

def read_file_content(filename):
    """Read the contents of the file and return as a list of lines."""
    try:
        with open(filename, 'r') as f:
            return f.readlines()
    except FileNotFoundError:
        return None

def log_changes(log_filename, identifier, changes):
    """Log the changes to a log file and send them to Telegram as a document."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Parse domain and path for URLs, or use filename directly for files
    if identifier.startswith("http://") or identifier.startswith("https://"):
        # Extract domain and path from URL
        domain = identifier.split("//")[1].split("/")[0]
        path = identifier.split(domain)[1].replace("/", "_")
    else:
        # For local files, use the identifier as the "domain+path"
        domain = "localfile"
        path = identifier.replace("/", "_").replace(":", "_")

    # Combine into desired filename format: domain+path+timestamp.txt
    change_log_path = f'{domain}{path}_{timestamp}.txt'
    
    # Write changes to log file and temporary change log
    with open(log_filename, 'a') as log_file, open(change_log_path, 'w') as change_log_file:
        log_file.write(f'[{timestamp}] {identifier} has been changed!\n')
        
        change_log_file.write(f'[{timestamp}] Changes in {identifier}:\n')
        for line_num, line_content, change_type in changes:
            log_file.write(f'{change_type} line {line_num}: {line_content}\n')
            change_log_file.write(f'{change_type} line {line_num}: {line_content}\n')
        log_file.write('\n' + '-'*40 + '\n')
        change_log_file.write('\n[!] Finished\n')
    
    # Send the change log file as a document to Telegram and delete it
    send_telegram_document(change_log_path)

def analyze_file(filename, log_filename, interval):
    """Analyze the given file for changes."""
    previous_hash = get_file_hash(filename)
    previous_content = read_file_content(filename)

    while True:
        current_hash = get_file_hash(filename)
        current_content = read_file_content(filename)
        
        if current_hash != previous_hash:
            if current_hash is None:
                print(f'{filename} does not exist or cannot be read.')
            else:
                print(f'{filename} has been changed! LogFile -> {log_filename}')

                if previous_content is not None and current_content is not None:
                    diff = list(difflib.ndiff(previous_content, current_content))
                    changes = []
                    line_num = 0

                    for line in diff:
                        if line.startswith('+ '):
                            changes.append((line_num + 1, line[2:].strip(), '[+]'))
                        elif line.startswith('- '):
                            changes.append((line_num + 1, line[2:].strip(), '[-]'))
                        if not line.startswith('- '):
                            line_num += 1

                    if changes:
                        log_changes(log_filename, filename, changes)
                    
                previous_content = current_content
            previous_hash = current_hash
            
        time.sleep(interval)

def analyze_url(url, log_filename, interval):
    """Analyze the file at the given URL for changes."""
    previous_hash, previous_content = get_url_hash(url)

    while True:
        current_hash, current_content = get_url_hash(url)
        
        if current_hash != previous_hash:
            if current_hash is None:
                print(f'{url} does not exist or cannot be read.')
            else:
                print(f'{url} has been changed! LogFile -> {log_filename}')

                if previous_content is not None and current_content is not None:
                    diff = list(difflib.ndiff(previous_content, current_content))
                    changes = []
                    line_num = 0

                    for line in diff:
                        if line.startswith('+ '):
                            changes.append((line_num + 1, line[2:].strip(), '[+]'))
                        elif line.startswith('- '):
                            changes.append((line_num + 1, line[2:].strip(), '[-]'))
                        if not line.startswith('- '):
                            line_num += 1

                    if changes:
                        log_changes(log_filename, url, changes)
                    
                previous_content = current_content
            previous_hash = current_hash
            
        time.sleep(interval)

def main():
    parser = argparse.ArgumentParser(description="Monitor files and URLs for changes.")
    parser.add_argument('-c', '--config', type=str, required=True, help="Configuration file containing list of files or URLs to monitor.")
    parser.add_argument('-l', '--log', type=str, default='changes.log', help="Log file to save changes.")
    parser.add_argument('-t', '--interval', type=int, default=60, help="Default time interval between checks (in seconds).")
    args = parser.parse_args()

    # Read configuration file
    try:
        with open(args.config, 'r') as config_file:
            items_to_monitor = config_file.readlines()
    except FileNotFoundError:
        print(f"Configuration file '{args.config}' not found.")
        return

    # Strip whitespace from each line
    items_to_monitor = [line.strip() for line in items_to_monitor if line.strip()]

    # Start monitoring each file or URL in a separate thread
    threads = []
    for item in items_to_monitor:
        if item.startswith('http://') or item.startswith('https://'):
            # If item is a URL, start a new thread to monitor it
            print(f"Monitoring URL: {item}")
            thread = threading.Thread(target=analyze_url, args=(item, args.log, args.interval))
        else:
            # If item is a file path, start a new thread to monitor it
            print(f"Monitoring File: {item}")
            thread = threading.Thread(target=analyze_file, args=(item, args.log, args.interval))
        
        thread.start()
        threads.append(thread)

    # Wait for all threads to complete (they won't, as each monitoring loop runs indefinitely)
    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()
