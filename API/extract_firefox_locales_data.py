#!/usr/bin/env python3

import requests
import sys


def main():
    locales = [
        "ach",
        "af",
        "an",
        "ar",
        "ast",
        "az",
        "be",
        "bg",
        "bn",
        "br",
        "bs",
        "ca",
        "ca-valencia",
        "cak",
        "cs",
        "cy",
        "da",
        "de",
        "dsb",
        "el",
        "en-CA",
        "en-GB",
        "eo",
        "es-AR",
        "es-CL",
        "es-ES",
        "es-MX",
        "et",
        "eu",
        "fa",
        "ff",
        "fi",
        "fr",
        "fy-NL",
        "ga-IE",
        "gd",
        "gl",
        "gn",
        "gu-IN",
        "he",
        "hi-IN",
        "hr",
        "hsb",
        "hu",
        "hy-AM",
        "ia",
        "id",
        "is",
        "it",
        "ja",
        "ka",
        "kab",
        "kk",
        "km",
        "kn",
        "ko",
        "lij",
        "lt",
        "lv",
        "mk",
        "mr",
        "ms",
        "my",
        "nb-NO",
        "ne-NP",
        "nl",
        "nn-NO",
        "oc",
        "pa-IN",
        "pl",
        "pt-BR",
        "pt-PT",
        "rm",
        "ro",
        "ru",
        "si",
        "sk",
        "sl",
        "son",
        "sq",
        "sr",
        "sv-SE",
        "ta",
        "te",
        "th",
        "tl",
        "tr",
        "trs",
        "uk",
        "ur",
        "uz",
        "vi",
        "xh",
        "zh-CN",
        "zh-TW",
    ]

    url = "https://pontoon.mozilla.org/api/v2/locales"
    page = 1
    locale_stats = {}
    try:
        while url:
            print(f"Reading locales (page {page})")
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            for locale in data.get("results", {}):
                if locale["code"] not in locales:
                    continue

                locale_stats[locale["code"]] = {
                    "projects": sorted(locale["projects"]),
                    "missing": locale["missing_strings"],
                    "unreviewed": locale["unreviewed_strings"],
                }

            # Get the next page URL
            url = data.get("next")
            page += 1
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        sys.exit()

    locale_stats = dict(sorted(locale_stats.items()))
    output = []
    output.append(
        "Locale,Number of Projects,Projects,Missing Strings,Pending Suggestions,Latest Activity"
    )
    for locale, locale_data in locale_stats.items():
        output.append(
            "{},{},{},{},{},".format(
                locale,
                len(locale_data["projects"]),
                " ".join(locale_data["projects"]),
                locale_data["missing"],
                locale_data["unreviewed"],
            )
        )
    # Save locally
    with open("output.csv", "w") as f:
        f.write("\n".join(output))
        print("Data stored as output.csv")


if __name__ == "__main__":
    main()
