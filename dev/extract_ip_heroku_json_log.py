"""
This script can be used to extract the number of requests for IPs from
Papertrail's archives in JSON format.

Usage:
    python extract_ip_heroku_json_log.py log.json
"""

from os.path import isfile
import argparse
import json
import glob
import os
import sys


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

    json_files = glob.glob(os.path.join(log_path, "*.json"))

    if not json_files:
        sys.exit(f"File {log_path} doesn't include any log file.")

    ip_stats = {}
    for json_file in json_files:
        with open(json_file) as f:
            content = f.readlines()
            for line in content:
                json_line = json.loads(line)
                ip = json_line.get("heroku", {}).get("fwd", "")
                if ip:
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
