#!/usr/bin/env python3

import requests
import sys


def main():
    projects = [
        "firefox-for-android",
        "firefox-for-ios",
        "firefox-monitor-website",
        "firefox-relay-website",
        "firefox",
        "mozilla-accounts",
        "mozilla-vpn-client",
    ]

    # Get stats from Pontoon
    locales_data = {}
    for project in projects:
        try:
            url = f"https://pontoon.mozilla.org/api/v2/projects/{project}"
            page = 1
            while url:
                print(f"Reading data for {project} (page {page})")
                response = requests.get(url)
                response.raise_for_status()
                data = response.json()

                for locale_data in data.get("localizations", []):
                    locale = locale_data["locale"]["code"]
                    if locale not in locales_data:
                        locales_data[locale] = {
                            "projects": 0,
                            "missing": 0,
                            "approved": 0,
                            "pretranslated": 0,
                            "total": 0,
                            "completion": 0,
                        }
                    locales_data[locale]["missing"] += locale_data["missing_strings"]
                    locales_data[locale]["pretranslated"] += locale_data[
                        "pretranslated_strings"
                    ]
                    locales_data[locale]["approved"] += (
                        locale_data["approved_strings"]
                        + locale_data["strings_with_warnings"]
                    )
                    locales_data[locale]["total"] += locale_data["total_strings"]
                    locales_data[locale]["projects"] += 1

                # Get the next page URL
                url = data.get("next")
                page += 1
        except requests.RequestException as e:
            print(f"Error fetching data: {e}")
            sys.exit()

    # Calculate completion percentage
    for locale in locales_data:
        if locales_data[locale]["total"] > 0:
            locales_data[locale]["completion"] = round(
                (locales_data[locale]["approved"] / locales_data[locale]["total"])
                * 100,
                2,
            )
        else:
            locales_data[locale]["completion"] = 0

    output = []
    output.append("Locale,Number of Projects,Completion,Approved strings,Total Strings")
    for locale in sorted(list(locales_data.keys())):
        locale_stats = locales_data[locale]
        output.append(
            f"{locale},{locale_stats['projects']},{locale_stats['completion']},{locale_stats['approved']},{locale_stats['total']}"
        )

    # Save locally
    with open("output.csv", "w") as f:
        f.write("\n".join(output))
        print("Data stored as output.csv")


if __name__ == "__main__":
    main()
