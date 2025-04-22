"""
Send notifications to a specific group of users.
"""

import uuid

from django.db.models import Q
from pontoon.base.models import User
from notifications.signals import notify


# List of email addresses (or contact email addresses) to notify
email_list = []

# Email address of active user in Pontoon
SENDER = "email@example.com"
sender = User.objects.get(email=SENDER)
users = User.objects.filter(Q(profile__contact_email__in=email_list) | Q(email__in=email_list))

message = """
Your notification message goes here (supports HTML).
"""

for recipient in users:
    notify.send(
        sender,
        recipient=recipient,
        verb="has sent you a message",
        description=message,
        identifier=uuid.uuid4().hex
    )
