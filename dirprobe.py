#!/usr/bin/env python3

import requests
import threading
import argparse
import os
import sys
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from time import sleep
from collections import defaultdict
from threading import Event


def parse_codes(codes_str, label):
    try:
        return [int(code.strip()) for code in codes_str.split(',')]
    except ValueError:
        print(f"Error: Invalid {label}. Must be a comma-separated list of integers.")
        sys.exit(1)


def adjust_status_codes(status_codes, negative_status, default_status_codes, default_negative_status):
    if status_codes:
        resolved_status_codes = status_codes
        resolved_negative_status = negative_status or default_negative_status
    else:
        resolved_status_codes = [code for code in default_status_codes if code not in negative_status]
        resolved_negative_status = negative_status

    return resolved_status_codes, resolved_negative_status


def print_banner(args):
    print("=" * 63)
    print(f"[+] Url:                     {args.url}")
    print(f"[+] Threads:                 {args.threads}")
    print(f"[+] Delay:                   {args.delay}s")
    print(f"[+] Wordlist:                {args.wordlist}")
    print(f"[+] Status codes:            {', '.join(map(str, args.status_codes))}")
    print(f"[+] Negative Status codes:   {', '.join(map(str, args.negative_status))}")
    if args.extensions:
        print(f"[+] Extensions:              {', '.join(args.extensions)}")
    print(f"[+] User Agent:              dirprobe")
    print(f"[+] Timeout:                 {args.timeout}s")
    if args.output:
        print(f"[+] Output file:             {args.output}")
    print("=" * 63)


def check_url_availability(url):
    try:
        response = requests.head(url, timeout=5)
        if response.status_code >= 400:
            print(f"Error: URL '{url}' returned a non-successful status code ({response.status_code}).")
            return False
    except requests.exceptions.ConnectionError:
        print(f"Error: Failed to connect to '{url}'. The server may be down or the URL is incorrect.")
        return False
    except requests.exceptions.Timeout:
        print(f"Error: Connection to '{url}' timed out.")
        return False
    except requests.exceptions.RequestException as e:
        print(f"Error: Unable to reach '{url}'. {str(e)}")
        return False
    return True


def test_directories(domain, wordlist, extensions, results, status_codes, negative_status, delay, timeout, lock, output_file, stop_event):
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    for word in wordlist:
        if stop_event.is_set():
            break

        urls = [f"{domain}/{word}"] if not extensions else [f"{domain}/{word}{ext}" for ext in extensions]

        for url in urls:
            if stop_event.is_set():
                break

            headers = {'User-Agent': 'dirprobe'}
            try:
                response = session.get(url, headers=headers, timeout=timeout)
                if response.status_code in status_codes and response.status_code not in negative_status:
                    size = len(response.content)
                    with lock:
                        if url not in results:
                            results[url] = (response.status_code, size)
                            print(f"{url} [Status code: {response.status_code}, Size: {size}]")
                            if output_file:
                                with open(output_file, "a") as f:
                                    f.write(url + "\n")
                sleep(delay)
            except requests.exceptions.ConnectionError:
                print(f"Warning: Failed to connect to '{url}'.")
            except requests.exceptions.Timeout:
                print(f"Warning: Connection to '{url}' timed out.")
            except requests.exceptions.RequestException as e:
                print(f"Warning: Request to '{url}' failed. {str(e)}")


def parse_args():
    parser = argparse.ArgumentParser(description="Directory Brute-forcing Tool")
    parser.add_argument("-u", "--url", required=True, help="Target URL (e.g., https://example.com)")
    parser.add_argument("-t", "--threads", type=int, default=4, help="Number of threads (default: 4)")
    parser.add_argument("-w", "--wordlist", required=True, help="Path to the wordlist file")
    parser.add_argument("-x", "--extensions", help="Comma-separated file extensions to append (e.g., .php,.txt)")
    parser.add_argument("--timeout", type=int, default=10, help="Request timeout in seconds (default: 10)")
    parser.add_argument("--delay", type=float, default=1, help="Delay between requests in seconds (default: 1)")
    parser.add_argument("-s", "--status-codes", help="Comma-separated valid status codes (default: 200,204,301,302,307,403)")
    parser.add_argument("-ns", "--negative-status", help="Comma-separated status codes to filter out (default: 404)")
    parser.add_argument("-o", "--output", help="File to save found URLs")
    return parser.parse_args()


def main():
    args = parse_args()

    if args.url.endswith('/'):
        args.url = args.url[:-1]

    if not os.path.isfile(args.wordlist):
        print(f"Error: Wordlist file '{args.wordlist}' not found!")
        return

    if not check_url_availability(args.url):
        sys.exit(1)

    user_status_codes = parse_codes(args.status_codes, "status codes") if args.status_codes else None
    user_negative_status = parse_codes(args.negative_status, "negative status codes") if args.negative_status else []

    args.extensions = args.extensions.split(',') if args.extensions else []

    default_status_codes = [200, 204, 301, 302, 307, 403]
    default_negative_status = [404]

    user_status_codes = parse_codes(args.status_codes, "status codes") if args.status_codes else None
    user_negative_status = (
        parse_codes(args.negative_status, "negative status codes")
        if args.negative_status
        else default_negative_status
    )

    args.status_codes, args.negative_status = adjust_status_codes(
        user_status_codes, user_negative_status, default_status_codes, default_negative_status
    )

    with open(args.wordlist, "r") as f:
        wordlist = f.read().splitlines()

    chunk_size = (len(wordlist) + args.threads - 1) // args.threads
    chunks = [wordlist[i:i + chunk_size] for i in range(0, len(wordlist), chunk_size)]

    print_banner(args)

    results = defaultdict(tuple)
    threads = []
    lock = threading.Lock()
    stop_event = Event()

    try:
        for chunk in chunks:
            thread = threading.Thread(
                target=test_directories,
                args=(args.url, chunk, args.extensions, results, args.status_codes, args.negative_status, args.delay, args.timeout, lock, args.output, stop_event)
            )
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

    except KeyboardInterrupt:
        print("\n[!] Keyboard interrupt detected. Stopping...")
        stop_event.set()
        for thread in threads:
            thread.join()

    finally:
        if args.output:
            with open(args.output, "w") as f:
                for url in results.keys():
                    f.write(url +"\n")

        print("\n")
        print("=" * 63)
        print("Scan complete.")
        print("=" * 63)


if __name__ == "__main__":
    main()
