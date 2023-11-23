"""
Retrieve a list of active contributors for given locales, timeframe and roles.

Output is formatted as CSV with the following columns:
* locale
* date_joined
* profile_url
* user_role
* total_submission_count
* approved_count
* rejected_count
* unreviewed_count
* approved_rejected_ratio

Run the script in Pontoon's Django shell, e.g.:
heroku run --app mozilla-pontoon ./manage.py shell
"""

# Configuration
LOCALES = [
    "it",
]
START_DATE = "01/06/2023"  # DD/MM/YYYY
CURRENT_DATE = "01/07/2023"  # DD/MM/YYYY

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

tz = get_current_timezone()
start_date = tz.localize(datetime.strptime(START_DATE, "%d/%m/%Y"))
current_date = tz.localize(datetime.strptime(CURRENT_DATE, "%d/%m/%Y"))


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
    from urllib.parse import urljoin
    return urljoin(settings.SITE_URL,reverse("pontoon.contributors.contributor.username", args=[username]))


def get_contribution_data(user):
    contribution_period = Q(created_at__gte=current_date - relativedelta(days=365))
    contributions_map = get_contributions_map(user, contribution_period)
    contribution_types = {"user_translations": 0, "user_reviews": 0, "all_contributions": 0}
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

output = []
output.append("Locale,Profile,Role,Date Joined,Last Login(Date),Last Login(Months),Latest Activity,Submissions,Reviews,All Contributions")

for locale in locales:
    contributors = users_with_translations_counts(
        start_date, Q(locale=locale), None, None
    )
    for contributor in contributors:
        contribution_data = get_contribution_data(contributor)
        # Ignore "imported" strings
        if contributor.username == "Imported":
            continue
        output.append(
            "{},{},{},{},{},{},{},{},{},{}".format(
                locale.code,
                get_profile(contributor.username),
                contributor.locale_role(locale),
                contributor.date_joined.date(),
                last_login(contributor),
                time_since_login(contributor),
                get_latest_activity(contributor),
                contribution_data["user_translations"],
                contribution_data["user_reviews"],
                contribution_data["all_contributions"],
            )
        )

print("\n".join(output))
