"""
Retrieves a list of locales missing in Pontoon for a single project by comparing with GitHub repo.

Output as CSV file with column Missing Locales.

"""

import argparse
import requests
import sys
from urllib.parse import quote as urlquote


def retrieve_pontoon_locales(project):
    try:
        url = f"https://pontoon.mozilla.org/api/v2/projects/{project}"
        page = 1
        locales = []
        while url:
            print(f"Reading locales for {project} (page {page})")
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            locales.extend(list(data.get("localizations", {}).keys()))

            # Get the next page URL
            url = data.get("next")
            page += 1
        locales.sort()

        return locales
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        sys.exit()


def retrieve_github_locales(owner, repo, path):
    query = f"/repos/{owner}/{repo}/contents/{urlquote(path)}"
    url = f"https://api.github.com{query}"

    ignored_folders = ["templates", "configs"]

    try:
        response = requests.get(url)
        response.raise_for_status()
        json_data = response.json()

        # Ignore files, hidden folder, non-locale folders via ignore list
        locale_list = [
            e["name"]
            for e in json_data
            if e["type"] == "dir"
            and not e["name"].startswith(".")
            and e["name"] not in ignored_folders
        ]
        # Use hyphens instead of underscores for locale codes
        locale_list = [locale.replace("_", "-") for locale in locale_list]
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

    # Clean up possible false positives
    locales_without_region = [loc.split("-")[0] for loc in pontoon_locales]
    ignored_locales = []
    for locale in missing_locales[:]:
        if locale in ["en-US", "en"] + locales_without_region:
            missing_locales.remove(locale)
            ignored_locales.append(locale)
    if ignored_locales:
        print(f"Ignored locales: {', '.join(ignored_locales)}")

    if missing_locales:
        print(f"Missing locales in Pontoon: {', '.join(missing_locales)}")
        if args.csv_output:
            with open("output.csv", "w") as f:
                output.extend(missing_locales)
                f.write("\n".join(output))
                print("Missing locales saved to output.csv")
    else:
        print("No missing locales found.")


if __name__ == "__main__":
    main()
