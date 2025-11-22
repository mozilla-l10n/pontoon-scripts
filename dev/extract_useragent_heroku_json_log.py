"""
This script can be used to extract the number of requests for user agents from
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
        "--threshold",
        required=False,
        default=1000,
        help="Threshold under which IPs are ignored",
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

    ip_stats = {}
    for archive_file in archive_files:
        for line in iter_log_lines(archive_file):
            json_line = json.loads(line)
            ip = json_line.get("apache", {}).get("userAgent", "")
            if ip:
                if len(ip.split(",")) > 1:
                    ip = ip.split(",")[0].strip()
                if ip not in ip_stats:
                    ip_stats[ip] = 1
                else:
                    ip_stats[ip] += 1

    ip_stats = {
        ip: count for ip, count in ip_stats.items() if count >= int(args.threshold)
    }
    ip_stats = dict(sorted(ip_stats.items(), key=lambda x: x[1], reverse=True))

    for ip, count in ip_stats.items():
        print(f"{ip}: {count}")


if __name__ == "__main__":
    main()
