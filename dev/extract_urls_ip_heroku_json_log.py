"""
This script can be used to extract the number of requests for IPs from
Papertrail's archives in JSON (or native json.gz) format.

Usage:
    python extract_ip_heroku_json_log.py ~/path_to_logs
"""

import argparse
import json
import glob
import gzip
import os
import sys


def iter_log_lines(fp):
    if fp.endswith(".gz"):
        with gzip.open(fp, "rt", errors="ignore") as f:
            for line in f:
                yield line
    else:
        with open(fp, "rt", errors="ignore") as f:
            for line in f:
                yield line


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "log_path",
        help="Path to folder with log file (.json Heroku format)",
    )
    parser.add_argument(
        "--ip",
        required=True,
        help="IP to analyze",
    )
    args = parser.parse_args()
    log_path = args.log_path

    archive_files = glob.glob(os.path.join(log_path, "*.json")) + glob.glob(
        os.path.join(log_path, "*.json.gz")
    )
    if not archive_files:
        sys.exit(f"File {log_path} doesn't include any log file.")
    else:
        print(f"Found {len(archive_files)} log files.")

    urls = {}
    for archive_file in archive_files:
        for line in iter_log_lines(archive_file):
            json_line = json.loads(line)
            ip = json_line.get("heroku", {}).get("fwd", "")
            if ip:
                num_ips = len(ip.split(","))
                if num_ips > 1:
                    ip = (
                        ip.split(",")[0].strip()
                        if num_ips == 2
                        else ip.split(",")[1].strip()
                    )

                if ip != args.ip:
                    continue

                url = json_line.get("heroku", {}).get("path", "")
                if url:
                    urls[url] = urls.get(url, 0) + 1

    urls = dict(sorted(urls.items(), key=lambda x: x[1], reverse=True))

    for url, count in urls.items():
        print(f"{url}: {count}")


if __name__ == "__main__":
    main()
