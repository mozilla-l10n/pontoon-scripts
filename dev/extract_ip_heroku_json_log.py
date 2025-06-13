"""
This script can be used to extract the number of requests for IPs from
Papertrail's archives in JSON format.

Usage:
    python extract_ip_heroku_json_log.py log.json
"""

from os.path import isfile
import argparse
import json
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "log_file",
        help="Path to log file",
    )
    parser.add_argument(
        "--threshold",
        required=False,
        default=1000,
        help="Threshold under which IPs are ignored",
    )
    args = parser.parse_args()
    log_file = args.log_file

    if not isfile(log_file):
        sys.exit(f"File {log_file} doesn't exist.")

    ip_stats = {}
    with open(log_file) as f:
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
