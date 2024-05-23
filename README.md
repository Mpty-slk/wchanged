# wchanged

**Analyze your file**

With this tool, you can monitor the files or url with its options, and you will be notified when the developer makes a change in it.

## Features
- Monitor a single file or multiple files for changes.
- Monitor a file from a URL for changes.
- Log changes with timestamps and detailed line differences.
- Customizable check intervals (default is 1 minute).

## Requirements

- Python 3.x
- `requests` library (for URL monitoring)

## Installation
1. Clone the repository:
```
git clone https://github.com/Mpty-slk/wchanged.git
cd wchanged
python3 wchanged.py -h
```
2. Install the required `requests` library:
```
pip install requests
```
## Usage
### Monitor a Single File
``` python3 wchanged.py -f path/to/yourfile.txt ```

### Monitor Multiple Files
``` python3 wchanged.py -fl path/to/yourfile1.txt path/to/yourfile2.txt ```

### Monitor a File from a URL
``` python3 wchanged.py -u http://example.com/yourfile.html ```

### Specify a Custom Log File
``` python3 wchanged.py -f path/to/yourfile.txt -l custom_log_file.log ```

### Specify a Custom Check Interval
``` python3 wchanged.py -f path/to/yourfile.txt -t 30 ```

### Complete Example
``` python3 wchanged.py -u http://example.com/yourfile.html -l custom_log_file.log -t 20 ```
