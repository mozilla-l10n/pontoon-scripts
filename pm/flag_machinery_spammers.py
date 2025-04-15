"""
Retrieve a list of contributors that have submitted translations within the
given timeframe to a number of locales above the given threshold, and with a
ratio of translations copied from Machinery above the given threshold.

Output is formatted as CSV with the following columns:
- User
- Role
- Status (enabled/disabled)
- Profile URL
- Number of locales they contributed to
- Comma separated list of locales they contributed to
- Number of submitted translations
- Number of translations copied from Machinery
- Ratio of translations copied from Machinery

Run the script in Pontoon's Django shell, e.g.:
heroku run --app mozilla-pontoon ./manage.py shell
"""

from django.conf import settings
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Count, Q, F, ExpressionWrapper, FloatField
from django.urls import reverse
from django.utils.timezone import get_current_timezone, datetime
from pontoon.base.models import Translation, User
from urllib.parse import urljoin

# Configuration
START_DATE = (2025, 1, 15)
END_DATE = (2025, 4, 15)
MIN_LOCALES = 2
MIN_MACHINERY_PCT = 0.7  # 70%


def get_profile(username):
    return urljoin(
        settings.SITE_URL,
        reverse("pontoon.contributors.contributor.username", args=[username]),
    )


tz = get_current_timezone()
start_date = datetime(*START_DATE, tzinfo=tz)
end_date = datetime(*END_DATE, tzinfo=tz)

users = (
    Translation.objects.filter(user__isnull=False, date__range=(start_date, end_date))
    .values("user__email")
    .annotate(
        submitted_count=Count("id"),
        locale_count=Count("locale", distinct=True),
        locales=ArrayAgg("locale__code", distinct=True),
        machinery_count=Count("id", filter=Q(machinery_sources__len__gt=0)),
    )
    .annotate(
        machinery_pct=ExpressionWrapper(
            F("machinery_count") * 1.0 / F("submitted_count"), output_field=FloatField()
        )
    )
    .filter(locale_count__gte=MIN_LOCALES, machinery_pct__gte=MIN_MACHINERY_PCT)
)

output = []
output.append(
    "User,Role,Status,Profile URL,Number of Locales,Locales,Number of Submitted Translations,Number of Machinery Translations,Ratio of Machinery Translations"
)

for user in users:
    u = User.objects.get(email=user["user__email"])
    role = u.role()
    profile_url = get_profile(u.username)
    locales_list = locale_string = ",".join(user["locales"])
    user_status = "enabled" if u.is_active else "disabled"
    output.append(
        '{},{},{},{},{},"{}",{},{},{}'.format(
            user["user__email"],
            role,
            user_status,
            profile_url,
            user["locale_count"],
            locales_list,
            user["submitted_count"],
            user["machinery_count"],
            round(user["machinery_pct"], 2),
        )
    )

print("\n".join(output))
