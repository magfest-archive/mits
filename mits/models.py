from mits import *


@Session.model_mixin
class SessionMixin:
    def logged_in_mits_team(self):
        try:
            return self.mits_team(cherrypy.session['mits_team_id'])
        except:
            raise HTTPRedirect('../mits_applications/team')

    def mits_teams(self):
        return self.query(MITSTeam).options(joinedload(MITSTeam.applicants), joinedload(MITSTeam.games), joinedload(MITSTeam.presenting))



class MITSTeam(MagModel):
    name = Column(UnicodeText)
    panel_interest = Column(Boolean, default=False)
    want_to_sell = Column(Boolean, default=False)
    address = Column(UnicodeText)

    applicants = relationship('MITSApplicant', backref='team')
    games = relationship('MITSGame', backref='team')
    presenting = relationship('MITSTimes', backref='team')

    @property
    def email(self):
        return [applicant.email for applicant in self.applicants if applicant.primary_contact]

    @property
    def can_save(self):
        return True
        return self.is_new and self.BEFORE_MITS_SUBMISSION_DEADLINE or self.BEFORE_MITS_EDITING_DEADLINE


class MITSApplicant(MagModel):
    team_id = Column(ForeignKey('mits_team.id'))
    attendee_id = Column(ForeignKey('attendee.id'), nullable=True)
    primary_contact = Column(Boolean, default=False)
    first_name = Column(UnicodeText)
    last_name = Column(UnicodeText)
    email = Column(UnicodeText)
    cellphone = Column(UnicodeText)
    contact_method = Column(Choice(c.MITS_CONTACT_OPTS), default=c.TEXTING)

    # TODO: add this to the form or add a separate form for it
    requested_room_nights = Column(MultiChoice(c.MITS_ROOM_NIGHT_OPTS), default='')


class MITSGame(MagModel):
    team_id = Column(ForeignKey('mits_team.id'))
    name = Column(UnicodeText)
    promo_blurb = Column(UnicodeText)
    description = Column(UnicodeText)
    genre = Column(UnicodeText)
    phase = Column(Choice(c.MITS_PHASE_OPTS))
    min_age = Column(Integer)
    min_players = Column(Integer, default=2)
    max_players = Column(Integer, default=4)
    personally_own = Column(Boolean, default=True)
    professional = Column(Boolean, default=False)

    # need attachments or links to pictures of game somehow


class MITSTimes(MagModel):
    team_id = Column(ForeignKey('mits_team.id'))
    availability = Column(MultiChoice(c.MITS_SCHEDULE_OPTS))
    multiple_tables = Column(MultiChoice(c.MITS_SCHEDULE_OPTS))


@on_startup
def add_applicant_restriction():
    """
    We use convenience functions for our form handling, e.g. to instantiate an
    attendee from an id or from form data we use the session.attendee() method.
    This method runs on startup and overrides the methods which are used for the
    game application forms to add a new "applicant" parameter.  If truthy, this
    triggers three additional behaviors:

    1) We check that there is currently a logged in team, and redirect to the
       initial application form if there is not.
    2) We check that the item being edited belongs to the currently-logged-in
       studio and raise an exception if it does not.  This check is bypassed for
       new things which have not yet been saved to the database.
    3) If the model is one with a "team" relationship, we set that to the
       currently-logged-in team.
    """
    def override_getter(method_name):
        orig_getter = getattr(Session.SessionMixin, method_name)

        @wraps(orig_getter)
        def with_applicant(self, *args, **kwargs):
            applicant = kwargs.pop('applicant', False)
            instance = orig_getter(self, *args, **kwargs)
            if applicant:
                team = self.logged_in_mits_team()
                assert instance.is_new or team == instance.team
                instance.team = team
            return instance
        setattr(Session.SessionMixin, method_name, with_applicant)

    for name in ['mits_applicant', 'mits_game', 'mits_times']:
        override_getter(name)
