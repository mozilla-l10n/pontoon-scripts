"""
Retrieve a list of active contributors for given locales, timeframe and roles.

Output is formatted as CSV with the following columns:
* Locale
* Profile URL
* Role
* Date Joined
* Last Login (date)
* Last Login (months ago)
* Latest Activity
* Submissions
* Reviews
* All Contributions
* Approved
* Rejected
* Pending


Run the script in Pontoon's Django shell, e.g.:
heroku run --app mozilla-pontoon ./manage.py shell
"""

# Configuration
LOCALES = [
    "it",
]
EXCLUDED_USERS = ["Imported", "google-translate", "translation-memory"]
END_DATE = "17/05/2023"  # DD/MM/YYYY
DAYS_INTERVAL = 365

# Script
from __future__ import division
from dateutil.relativedelta import relativedelta
from django.db.models import Count, Q
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from pontoon.base.models import Locale
from pontoon.base.models import Locale, Translation
from pontoon.contributors.utils import (
    users_with_translations_counts,
    get_contributions_map,
)
from django.utils.timezone import get_current_timezone
from datetime import datetime
from pontoon.base.utils import convert_to_unix_time
from django.db.models.functions import TruncDay
from urllib.parse import urljoin
from pontoon.contributors.utils import users_with_translations_counts

tz = get_current_timezone()
end_date = tz.localize(datetime.strptime(END_DATE, "%d/%m/%Y"))
start_date = end_date - relativedelta(days=DAYS_INTERVAL)


def get_latest_activity(user):
    translations = Translation.objects.filter(Q(user=user) | Q(approved_user=user))
    if not translations.exists():
        return "No activity yet"
    translated = translations.latest("date").date
    approved = translations.latest("approved_date").approved_date
    activities = []
    if translated:
        activities.append(translated)
    if approved:
        activities.append(approved)
    activities.sort()
    return activities[-1].date() if len(activities) > 0 else None


def last_login(user):
    if not user.last_login:
        return "Never logged in"
    else:
        return user.last_login.date()


def time_since_login(user):
    now = timezone.now()
    if not user.last_login:
        return "Never logged in"
    last_login = user.last_login
    time_since = relativedelta(now, last_login)
    return time_since.months + (time_since.years * 12)


def get_profile(username):
    return urljoin(
        settings.SITE_URL,
        reverse("pontoon.contributors.contributor.username", args=[username]),
    )


def get_contribution_data(user):
    contribution_period = Q(created_at__gte=start_date)
    contributions_map = get_contributions_map(user, contribution_period)
    contribution_types = {
        "user_translations": 0,
        "user_reviews": 0,
        "all_contributions": 0,
    }
    for contribution_type in contribution_types:
        if contribution_type not in contributions_map.keys():
            continue
        contributions_qs = contributions_map[contribution_type]
        contributions_data = {
            convert_to_unix_time(item["timestamp"]): item["count"]
            for item in (
                contributions_qs.annotate(timestamp=TruncDay("created_at"))
                .values("timestamp")
                .annotate(count=Count("id"))
                .values("timestamp", "count")
            )
        }
        contribution_types[contribution_type] = sum(contributions_data.values())
    return contribution_types


locales = Locale.objects.all()
if LOCALES:
    locales = Locale.objects.filter(code__in=LOCALES)

locales_list = [loc.code for loc in locales]
locales_list.sort()
output = [
    f"Locales: {','.join(locales_list)}\n",
    f"Start date: {start_date.strftime('%d/%m/%Y')}",
    f"End date: {end_date.strftime('%d/%m/%Y')}\n",
]
output.append(
    "Locale,Profile URL,Role,Date Joined,Last Login (date),Last Login (months ago),Latest Activity,Submissions,Reviews,All Contributions,Approved,Rejected,Pending"
)

for locale in locales:
    contributors = users_with_translations_counts(
        start_date, Q(locale=locale, date__lte=end_date), None
    )
    for contributor in contributors:
        contribution_data = get_contribution_data(contributor)
        if (
            locale.code == "it"
            and contributor.username == "mZuzEFP7EcmgBBTbvtgJP2LFFTY"
        ):
            # Remap flod as manager for Italian
            role = "Manager"
        elif (
            locale.code == "fr"
            and contributor.username == "ekwOqIIpgEhqGiWPIs0ZjonPg90"
        ):
            # Remap tchevalier as manager for French
            role = "Manager"
        else:
            role = contributor.locale_role(locale)
        # Ignore admins
        if role == "Admin":
            continue
        # Ignore imported strings and pretranslations
        if contributor.username in EXCLUDED_USERS:
            continue
        output.append(
            "{},{},{},{},{},{},{},{},{},{},{},{},{}".format(
                locale.code,
                get_profile(contributor.username),
                role,
                contributor.date_joined.date(),
                last_login(contributor),
                time_since_login(contributor),
                get_latest_activity(contributor),
                contribution_data["user_translations"],
                contribution_data["user_reviews"],
                contribution_data["all_contributions"],
                contributor.translations_approved_count,
                contributor.translations_rejected_count,
                contributor.translations_unapproved_count,
            )
        )

print("\n".join(output))
