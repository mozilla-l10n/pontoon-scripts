"""
Retrieve a list of contributors submitting translations to a given number of locales
within a given timeframe and with a given ratio of translations copied from Machinery.

Output is formatted as CSV with the following columns:
* User
* Number of locales contributing to
* Number of submitted translations
* Number of translations copied from Machinery
* Ratio of translations copied from Machinery

Run the script in Pontoon's Django shell, e.g.:
heroku run --app mozilla-pontoon ./manage.py shell
"""

# Configuration
START_DATE = (2025, 1, 15)
END_DATE = (2025, 4, 15)
MIN_LOCALES = 2
MIN_MACHINERY_PCT = 0.7  # 70%

# Script
from datetime import datetime
from django.db.models import Count, Q, F, ExpressionWrapper, FloatField
from django.utils.timezone import get_current_timezone, datetime
from pontoon.base.models import Translation, User

tz = get_current_timezone()
start_date = datetime(*START_DATE, tzinfo=tz)
end_date = datetime(*END_DATE, tzinfo=tz)

users = (
    Translation.objects
    .filter(
        user__isnull=False,
        date__range=(start_date, end_date)
    )
    .values('user__email')
    .annotate(
        submitted_count=Count('id'),
        locale_count=Count('locale', distinct=True),
        machinery_count=Count('id', filter=Q(machinery_sources__len__gt=0))
    )
    .annotate(
        machinery_pct=ExpressionWrapper(
            F('machinery_count') * 1.0 / F('submitted_count'),
            output_field=FloatField()
        )
    )
    .filter(
        locale_count__gte=MIN_LOCALES,
        machinery_pct__gte=MIN_MACHINERY_PCT
    )
)

output = []
output.append(
    "User,Role,Number of Locales,Number of Submitted Translations,Number of Machinery Translations,Ratio of Machinery Translations"
)

for user in users:
    u = User.objects.get(email=user["user__email"])
    role = u.role()
    output.append(
        "{},{},{},{},{},{}".format(
            user["user__email"],
            role,
            user["locale_count"],
            user["submitted_count"],
            user["machinery_count"],
            user["machinery_pct"],
        )
    )

print("\n".join(output))
