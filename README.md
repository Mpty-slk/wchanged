
# JavaScript File Monitor with Telegram Notifications

This Python script monitors JavaScript files or HTML pages for changes and sends updates to a Telegram chat. It can detect new or removed JavaScript files from URLs and send a log of the changes to Telegram.

## Features

- Monitors JavaScript files in URLs for changes.
- Sends notifications about added or removed JavaScript files via Telegram.
- Periodically checks for updates based on a configurable interval.
- Supports both file and URL monitoring.
- Sends logs to Telegram with details of the changes.

## Requirements

- Python 3.8+
- External Libraries:
  - `requests`
  - `python-dotenv`
  - `argparse`

Install dependencies via `pip`:

```bash
pip install requests python-dotenv
```

## Setup

1. **Telegram Setup**: You will need a Telegram bot and a chat ID to receive the messages.

   - Create a new Telegram bot via [BotFather](https://core.telegram.org/bots#botfather).
   - Get your Telegram chat ID. (You can find this by using a bot like [@userinfobot](https://t.me/userinfobot) to get your chat ID.)

2. **Environment Variables**: Create a `.env` file in the project directory and add your bot credentials:
   ```dotenv
   TELEGRAM_BOT_TOKEN=<your_telegram_bot_token>
   TELEGRAM_CHAT_ID=<your_telegram_chat_id>
   ```

## Usage

1. **Configuration File**: Create a configuration file (e.g., `config.txt`) to list the URLs or files you want to monitor. Each item should be listed on a new line:

   Example `config.txt`:
   ```
   https://example.com
   https://example.com/page.html
   ```

2. **Run the Script**: You can run the script with the following command:

   ```bash
   python monitor.py -c config.txt -t 60 --jjs
   ```

   **Arguments**:
   - `-c` or `--config`: The path to the configuration file.
   - `-t` or `--interval`: Time interval (in seconds) between checks (default: 60).
   - `--jjs`: If set, the script will extract and monitor JavaScript files in the HTML content of the URLs.

## How It Works

1. **Extract JavaScript Files**: If the `--jjs` flag is used, the script extracts JavaScript files from the HTML content of the provided URLs.

2. **Monitor for Changes**: The script monitors for changes by comparing the previously fetched JavaScript files with the new ones. It detects additions and removals.

3. **Telegram Notifications**: When a change is detected, the script generates a log and sends it to your Telegram chat as a document.

4. **Log File**: The log file is generated dynamically, showing the changes with timestamps.

## Example

For example, if a new JavaScript file is added or an existing one is removed, the log will look like this:

```
2025-01-11 12:00:00 https://example.com
[+] line 10: /scripts/new_file.js
[-] line 15: /scripts/old_file.js

[!] Finished
```

The log will be sent as a document to your Telegram chat.

## License

This project is licensed under the MIT License.
