#!/usr/bin/env python3

import requests
import sys


def main():
    # Get completion stats for locales from Pontoon

    pending_suggestions = {}
    try:
        # Get the number of pending suggestions for each locale
        url = "https://pontoon.mozilla.org/api/v2/locales"
        url = "https://mozilla-pontoon-staging.herokuapp.com/api/v2/locales"
        page = 1
        while url:
            print(f"Reading pending suggestions (page {page})")
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            for localization in data.get("results", []):
                locale = localization["code"]
                if locale not in pending_suggestions:
                    pending_suggestions[locale] = 0
                pending_suggestions[locale] += localization["unreviewed_strings"]
            # Get the next page URL
            url = data.get("next")
            page += 1
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        sys.exit()

    pending_suggestions = dict(sorted(pending_suggestions.items()))
    output = []
    output.append("Locale,Pending Suggestions")
    # Only print requested locales
    for locale, suggestions in pending_suggestions.items():
        output.append("{},{}".format(locale, pending_suggestions[locale]))

    # Save locally
    with open("output.csv", "w") as f:
        f.write("\n".join(output))
        print("Data stored as output.csv")


if __name__ == "__main__":
    main()
