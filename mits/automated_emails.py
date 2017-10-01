from mits import *


class MITSEmail(AutomatedEmail):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('sender', c.MITS_EMAIL)
        AutomatedEmail.__init__(self, MITSTeam, *args, **kwargs)

AutomatedEmail.queries[MITSTeam] = lambda session: session.mits_teams()

# We wait an hour before sending out this email because the most common case
# of someone registering their team is that they'll immediately fill out the
# entire application, so there's no reason to send them an email showing their
# currently completion percentage when that info will probably be out of date
# by the time they read it.  By waiting an hour, we ensure this doesn't happen.
MITSEmail('Thanks for showing an interest in MITS!', 'mits_registered.txt',
          lambda team: not team.submitted and team.registered < datetime.now(UTC) - timedelta(hours=1),
          ident='mits_application_created')

# For similar reasons to the above, we wait at least 6 hours before sending this
# email because it would seem silly to immediately send someone a "last chance"
# email the minute they registered their team.  By waiting 6 hours, we wait
# until they've had a chance to complete the application and even receive the
# initial reminder email above before being pestered with this warning.
MITSEmail('Last chance to complete your MITS application!', 'mits_reminder.txt',
          lambda team: not team.submitted and team.registered < datetime.now(UTC) - timedelta(hours=6),
          when=days_before(3, c.MITS_SUBMISSION_DEADLINE),
          ident='mits_reminder')

MITSEmail('Thanks for submitting your MITS application!', 'mits_submitted.txt',
          lambda team: team.submitted,
          ident='mits_application_submitted')

# TODO: emails we still need to configure include but are not limited to:
# -> when teams have been accepted
# -> when teams have been declined
# -> when accepted teams have added people who have not given their hotel info
# -> final pre-event informational email
