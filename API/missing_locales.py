"""
Retrieves a list of locales missing in Pontoon for a single project by comparing with GitHub repo.

Output as CSV file with column Missing Locales.

"""

import argparse
import json
import requests
import sys
from urllib.parse import quote as urlquote
from urllib.request import urlopen


def retrieve_pontoon_locales(project):
    try:
        url = f"https://pontoon.mozilla.org/api/v2/projects/{project}"
        url = f"https://mozilla-pontoon-staging.herokuapp.com/api/v2/projects/{project}"
        page = 1
        locales = []
        while url:
            print(f"Reading locales for {project} (page {page})")
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            for localization in data.get("localizations", {}):
                locales.append(localization["locale"])

            # Get the next page URL
            url = data.get("next")
            page += 1
        locales.sort()

        return locales
    except Exception as e:
        sys.exit(e)


def retrieve_github_locales(owner, repo, path):
    query = f"/repos/{owner}/{repo}/contents/{path}"
    url = f"https://api.github.com{urlquote(query)}"

    ignored_folders = ["templates", "configs"]

    try:
        response = urlopen(url)
        json_data = json.load(response)

        # Ignore files, hidden folder, non-locale folders via ignore list
        locale_list = [
            e["name"]
            for e in json_data
            if e["type"] == "dir"
            and not e["name"].startswith(".")
            and e["name"] not in ignored_folders
        ]
        locale_list.sort()

        return locale_list
    except Exception as e:
        sys.exit(f"GitHub error: {e}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pontoon",
        required=True,
        dest="pontoon_project",
        help="Pontoon project name",
    )
    parser.add_argument(
        "--repo",
        required=True,
        dest="github_repo",
        help="GitHub repository name",
    )
    parser.add_argument(
        "--owner",
        required=False,
        default="mozilla-l10n",
        dest="github_owner",
        help="GitHub repository owner name",
    )
    parser.add_argument(
        "--path",
        required=False,
        default="",
        dest="github_path",
        help="GitHub path that contains locale folders",
    )
    parser.add_argument(
        "--csv",
        required=False,
        action="store_true",
        default=False,
        dest="csv_output",
        help="Store data as output.csv",
    )

    args = parser.parse_args()

    pontoon_locales = retrieve_pontoon_locales(args.pontoon_project)
    github_locales = retrieve_github_locales(
        args.github_owner, args.github_repo, args.github_path
    )

    output = ["Missing Locales"]
    missing_locales = list(set(github_locales) - set(pontoon_locales))
    missing_locales.sort()

    print(f"Missing locales in Pontoon: {', '.join(missing_locales)}")
    if args.csv_output:
        with open("output.csv", "w") as f:
            output.extend(missing_locales)
            f.write("\n".join(output))
            print("Missing locales saved to output.csv")


if __name__ == "__main__":
    main()
