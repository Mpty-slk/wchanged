import hashlib
import time
import difflib
import datetime
import argparse
import requests

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
    """Log the changes to a log file."""
    with open(log_filename, 'a') as log_file:
        timestamp = datetime.datetime.now().isoformat()
        log_file.write(f'[{timestamp}] {identifier} has been changed!\n')
        for line_num, line_content, change_type in changes:
            log_file.write(f'{change_type} line {line_num}: {line_content}\n')
        log_file.write('\n' + '-'*40 + '\n')

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
                print(f'{filename} has been changed!')

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
                print(f'{url} has been changed!')

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
    parser = argparse.ArgumentParser(description="Monitor files for changes.")
    parser.add_argument('-f', '--file', type=str, help="File to monitor.")
    parser.add_argument('-fl', '--filelist', type=str, nargs='+', help="List of files to monitor.")
    parser.add_argument('-u', '--url', type=str, help="URL of the file to monitor.")
    parser.add_argument('-l', '--log', type=str, default='changes.log', help="Log file to save changes.")
    parser.add_argument('-t', '--interval', type=int, default=60, help="Time interval between checks (in seconds). Default is 60 seconds (1 minute).")
    args = parser.parse_args()

    files_to_monitor = []
    if args.file:
        files_to_monitor.append(args.file)
    if args.filelist:
        files_to_monitor.extend(args.filelist)

    if args.url:
        analyze_url(args.url, args.log, args.interval)
    elif files_to_monitor:
        for filename in files_to_monitor:
            # Start a separate monitoring loop for each file
            analyze_file(filename, args.log, args.interval)
    else:
        print("No files or URLs provided to monitor. Use -f, -fl, or -u to specify files or URLs.")

if __name__ == "__main__":
    main()
