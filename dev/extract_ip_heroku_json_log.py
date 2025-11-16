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
from ipaddress import ip_address, ip_network


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

    # Copy from Heroku settings
    blocked_ip_setting = ""

    BLOCKED_IPS = []
    BLOCKED_IP_RANGES = []
    for ip in blocked_ip_setting.split(","):
        ip = ip.strip()
        if ip == "":
            continue
        try:
            # If the IP is valid, store it directly as string
            ip_obj = ip_address(ip)
            BLOCKED_IPS.append(ip)
        except ValueError:
            try:
                # Check if it's a valid IP range (CIDR notation)
                ip_obj = ip_network(ip, strict=False)
                BLOCKED_IP_RANGES.append(ip_obj)
            except ValueError:
                print(f"Invalid IP or IP range defined in BLOCKED_IPS: {ip}")

    ip_stats = {}
    for archive_file in archive_files:
        for line in iter_log_lines(archive_file):
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
        try:
            ip_obj = ip_address(ip)
        except ValueError:
            print(f"Invalid IP extracted from log: {ip}")
            continue
        blocked = False
        if ip in BLOCKED_IPS:
            blocked = True
        for ip_range in BLOCKED_IP_RANGES:
            if ip_obj in ip_range:
                blocked = True

        print(f"{ip}{' (blocked)' if blocked else ''}: {count}")


if __name__ == "__main__":
    main()
