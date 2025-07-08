#!/usr/bin/env python3

import requests


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
    locale_data = {}
    for project in projects:
        url = f"https://pontoon.mozilla.org/api/v2/projects/{project}"
        url = f"https://mozilla-pontoon-staging.herokuapp.com/api/v2/projects/{project}"
        page = 1
        while url:
            print(f"Reading data for {project} (page {page})")
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            for localization in data.get("localizations", {}):
                locale = localization["locale"]
                if locale not in locale_data:
                    locale_data[locale] = {
                        "projects": 0,
                        "missing": 0,
                        "approved": 0,
                        "pretranslated": 0,
                        "total": 0,
                        "completion": 0,
                    }
                locale_data[locale]["missing"] += localization["missing_strings"]
                locale_data[locale]["pretranslated"] += localization[
                    "pretranslated_strings"
                ]
                locale_data[locale]["approved"] += (
                    localization["approved_strings"]
                    + localization["strings_with_warnings"]
                )
                locale_data[locale]["total"] += localization["total_strings"]
                locale_data[locale]["projects"] += 1

            # Get the next page URL
            url = data.get("next")
            page += 1

    # Calculate completion percentage
    for locale in locale_data:
        if locale_data[locale]["total"] > 0:
            locale_data[locale]["completion"] = round(
                (locale_data[locale]["approved"] / locale_data[locale]["total"]) * 100,
                2,
            )
        else:
            locale_data[locale]["completion"] = 0

    output = []
    output.append("Locale,Number of Projects,Completion,Approved strings,Total Strings")
    for locale in sorted(list(locale_data.keys())):
        locale_stats = locale_data[locale]
        output.append(
            f"{locale},{locale_stats['projects']},{locale_stats['completion']},{locale_stats['approved']},{locale_stats['total']}"
        )

    # Save locally
    with open("output.csv", "w") as f:
        f.write("\n".join(output))
        print("Data stored as output.csv")


if __name__ == "__main__":
    main()
