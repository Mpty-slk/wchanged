import hashlib
import time
import datetime
import argparse
import requests
import threading
import os
import re
from dotenv import load_dotenv
from urllib.parse import urlparse, urljoin
from pathlib import Path

# Load environment variables
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    raise ValueError("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set in the environment variables.")


def send_telegram_message(message):
    """Send a simple text message to the Telegram bot."""
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
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
            os.remove(document_path)
            print(f"Document deleted after sending: {document_path}")


def get_url_hash(url):
    """Generate an MD5 hash for the contents of the file at the given URL."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return hashlib.md5(response.content).hexdigest(), response.text.splitlines()
    except requests.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return None, None


def extract_js_files(html_content):
    """
    Extract all JavaScript file paths from HTML content, including those
    in comments, concatenated strings, and unquoted text.
    """
    js_regex = r"""
        (?i)                              # Case-insensitive match
        (?:
            [\"']                        # Match opening quotes (optional)
        )?
        ([^\"'\s<>]+\.js(?:\?[^\"'\s<>]*)?)  # Match .js files, including query strings
        (?:
            [\"']                        # Match closing quotes (optional)
        )?
    """
    return re.findall(js_regex, html_content, re.VERBOSE)


def get_line_number(html_content, js_file):
    """Find the line number of a JS file in the HTML content."""
    for i, line in enumerate(html_content, start=1):
        if js_file in line:
            return i
    return None  # File not found


def thread_safe_write(log_filename, log_entry):
    """Thread-safe way to write log entries to a file."""
    with threading.Lock():
        with open(log_filename, 'a') as log_file:
            log_file.write(log_entry)



def analyze_js_files(base_url, js_files, log_filename, interval):
    """Monitor a list of JavaScript files for changes."""
    previous_files = {}  # Store JS file paths with their line numbers

    while True:
        _, html_content = get_url_hash(base_url)
        if not html_content:
            print(f"Failed to retrieve content from {base_url}. Retrying in {interval} seconds...")
            time.sleep(interval)
            continue

        # Extract current JS files and their line numbers
        current_files = {
            js_file: get_line_number(html_content, js_file)
            for js_file in extract_js_files("\n".join(html_content))
        }

        # Remove invalid entries (files without a valid line number)
        current_files = {js_file: line for js_file, line in current_files.items() if line}

        # Compare current files with previously tracked files
        added_files = {k: v for k, v in current_files.items() if k not in previous_files}
        removed_files = {k: v for k, v in previous_files.items() if k not in current_files}

        # If there are changes, log them
        if added_files or removed_files:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"{timestamp} {base_url}\n"

            # Collect changes grouped by line number
            all_changes = []

            # Add removed files
            for js_file, line in removed_files.items():
                all_changes.append((line, f"[-] line {line}: {js_file}"))

            # Add added files
            for js_file, line in added_files.items():
                all_changes.append((line, f"[+] line {line}: {js_file}"))

            # Sort changes by line number
            all_changes.sort(key=lambda x: x[0])

            # Write changes to the log
            for _, change in all_changes:
                log_entry += f"{change}\n"

            log_entry += "\n[!] Finished\n"

            # Write the log entry to the temp file
            with open(log_filename, 'w') as log_file:
                log_file.write(log_entry)

            # Send the log file to Telegram
            send_telegram_document(log_filename)

        # Update previous_files with current_files
        previous_files = current_files
        time.sleep(interval)



def analyze_url_with_js_extraction(url, log_filename, interval):
    """Analyze the URL, extract JS files from HTML, and monitor them for changes."""
    _, html_content = get_url_hash(url)
    if not html_content:
        print(f"Failed to retrieve content from {url}.")
        return
    js_files = extract_js_files("\n".join(html_content))
    if not js_files:
        print(f"No JavaScript files found in {url}.")
        return
    print(f"Extracted JavaScript files from {url}: {js_files}")
    analyze_js_files(url, js_files, log_filename, interval)


def main():
    parser = argparse.ArgumentParser(description="Monitor files and URLs for changes.")
    parser.add_argument('-c', '--config', type=str, required=True, help="Configuration file containing list of files or URLs to monitor.")
    parser.add_argument('-t', '--interval', type=int, default=60, help="Time interval between checks (in seconds).")
    parser.add_argument('--jjs', action='store_true', help="Extract JavaScript files from HTML and monitor them for changes.")
    args = parser.parse_args()

    try:
        with open(args.config, 'r') as config_file:
            items_to_monitor = config_file.readlines()
    except FileNotFoundError:
        print(f"Configuration file '{args.config}' not found.")
        return

    items_to_monitor = [line.strip() for line in items_to_monitor if line.strip()]
    threads = []
    for item in items_to_monitor:
        if item.startswith('http://') or item.startswith('https://'):
            if args.jjs:
                print(f"Extracting and monitoring JavaScript files from URL: {item}")
                # Generate log filename dynamically (e.g., based on the URL)
                log_filename = f"log_{item.split('//')[1].replace('/', '_')}.txt"
                thread = threading.Thread(target=analyze_url_with_js_extraction, args=(item, log_filename, args.interval))
            else:
                print(f"Monitoring URL: {item}")
                thread = threading.Thread(target=analyze_js_files, args=(item, [], generate_log_filename(item), args.interval))
        else:
            print(f"Monitoring File: {item}")
            thread = threading.Thread(target=analyze_file, args=(item, args.log, args.interval))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()



if __name__ == "__main__":
    main()
