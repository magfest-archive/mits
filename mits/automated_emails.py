from mits import *


class MITSEmail(AutomatedEmail):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('sender', c.MITS_EMAIL)
        AutomatedEmail.__init__(self, MITSTeam, *args, **kwargs)

MITSEmail('Thanks for showing an interest in MITS!', 'mits_registered.txt',
          lambda team: not team.submitted and team.registered < datetime.now(UTC) - timedelta(hours=1),
          ident='mits_application_created')

MITSEmail('Thanks for submitting your MITS application!', 'mits_submitted.txt',
          lambda team: team.status == c.ACCEPTED,
          ident='mits_application_submitted')

MITSEmail('Last chance to complete your MITS application!', 'mits_reminder.txt',
          lambda team: not team.submitted and team.registered < datetime.now(UTC) - timedelta(hours=6),
          when=days_before(3, c.MITS_SUBMISSION_DEADLINE),
          ident='mits_reminder')
