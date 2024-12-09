# Dirprobe
Dirprobe is a fast and customizable directory brute-forcing tool designed to help you find hidden directories and files on web servers. With multithreading, adjustable request parameters, and support for extensions, Dirprobe is a powerful utility for web penetration testing and discovery.

## Installation

1. Clone this repository:
   ```bash
   https://github.com/jitmondal1/Dirprobe.git
   cd Dirprobe
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Make the script executable::
   ```bash
   chmod +x dirprobe.py
   ```

## Usage
  ```bash
  ./dirprobe.py -u <URL> -w <WORDLIST> [OPTIONS]
  ```
### Required Arguments
  - -u, --url: Target URL (e.g., https://example.com).
  - -w, --wordlist: Path to the wordlist file

### Optional Arguments
  - -t, --threads: Number of threads to use (default: 4).
  - -x, --extensions: Comma-separated file extensions to append (e.g., .php,.txt).
  - --timeout: Request timeout in seconds (default: 10).
  - --delay: Delay between requests in seconds (default: 1).
  - -s, --status-codes: Comma-separated HTTP status codes to include (default: 200, 204, 301, 302, 307, 403).
  - -ns, --negative-status: Comma-separated HTTP status codes to exclude (default: 404).\
  - -o, --output: File to save discovered URLs.

## Examples
1. Help menu:
   ```bash
   ./dirprobe.py -h
   ```
2. Basic Scan:
   ```bash
   ./dirprobe.py -u https://example.com -w wordlist.txt
   ```
3. Add Extensions:
   ```bash
   ./dirprobe.py -u https://example.com -w wordlist.txt -x .php,.html
   ```
4. Customize Status Codes:
   ```bash
   ./dirprobe.py -u https://example.com -w wordlist.txt -s 200,301 -ns 403
   ```
5. Save Output to File:
   ```bash
   ./dirprobe.py -u https://example.com -w wordlist.txt -o results.txt
   ```

## Disclaimer
Dirprobe is intended for authorized security testing and educational purposes only. Unauthorized use of this tool is prohibited. The developer is not responsible for any misuse.
