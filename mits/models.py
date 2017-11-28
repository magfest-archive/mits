from mits import *


@Session.model_mixin
class SessionMixin:
    def log_in_as_mits_team(self, team_id, redirect_to='../mits_applications/index'):
        try:
            team = self.mits_team(team_id)
            duplicate_teams = []
            while team.duplicate_of:
                duplicate_teams.append(team.id)
                team = self.mits_team(team.duplicate_of)
                assert team.id not in duplicate_teams, 'circular reference in duplicate_of: {}'.format(duplicate_teams)
        except:
            log.error('attempt to log into invalid team {}', team_id, exc_info=True)
            raise HTTPRedirect('../mits_applications/login_explanation')
        else:
            cherrypy.session['mits_team_id'] = team.id
            raise HTTPRedirect(redirect_to)

    def logged_in_mits_team(self):
        try:
            team = self.mits_team(cherrypy.session['mits_team_id'])
            assert not team.deleted or team.duplicate_of
        except:
            raise HTTPRedirect('../mits_applications/login_explanation')
        else:
            if team.duplicate_of:
                # the currently-logged-in team was deleted, so log back in as the correct team
                self.log_as_as_mits_team(team.id)
            else:
                return team

    def mits_teams(self, include_deleted=False):
        deleted_filter = [] if include_deleted else [MITSTeam.deleted == False]
        return (self.query(MITSTeam)
                    .filter(*deleted_filter)
                    .options(joinedload(MITSTeam.applicants).subqueryload(MITSApplicant.attendee),
                             joinedload(MITSTeam.games),
                             joinedload(MITSTeam.schedule),
                             joinedload(MITSTeam.pictures),
                             joinedload(MITSTeam.documents))
                    .order_by(MITSTeam.name))

    def delete_mits_file(self, model):
        try:
            os.remove(model.filepath)
        except:
            log.error('unexpected error deleting MITS file {}', modle.filepath)

        # Regardless of whether removing the file from the filesystem succeeded,
        # we still want the delete it from the database.  The most likely cause
        # of failure is if the file was already deleted or is otherwise not
        # present, so it wouldn't make sense to keep the database record around.
        self.delete(model)
        self.commit()


@Session.model_mixin
class Attendee:
    mits_applicants = relationship('MITSApplicant', backref='attendee')


class MITSTeam(MagModel):
    name = Column(UnicodeText)
    panel_interest = Column(Boolean, default=False)
    want_to_sell = Column(Boolean, default=False)
    address = Column(UnicodeText)
    submitted = Column(UTCDateTime, nullable=True)

    applied = Column(UTCDateTime, server_default=utcnow())
    status = Column(Choice(c.MITS_APP_STATUS), default=c.PENDING, admin_only=True)

    applicants = relationship('MITSApplicant', backref='team')
    games = relationship('MITSGame', backref='team')
    pictures = relationship('MITSPicture', backref='team')
    documents = relationship('MITSDocument', backref='team')
    schedule = relationship('MITSTimes', uselist=False, backref='team')

    duplicate_of = Column(UUID, nullable=True)
    deleted = Column(Boolean, default=False)
    """
    We've found that a lot of people start filling out an application and then
    instead of continuing their application just start over fresh and fill out
    a new one.  In these cases we mark the application as soft-deleted and then
    set the duplicate_of field so that when an applicant tries to log into the
    original application, we can redirect them to the correct application.
    """

    email_model_name = 'team'

    @property
    def accepted(self):
        return self.status == c.ACCEPTED

    @property
    def email(self):
        return [applicant.email for applicant in self.primary_contacts]

    @property
    def primary_contacts(self):
        return [a for a in self.applicants if a.primary_contact]

    @property
    def salutation(self):
        return ' and '.join(applicant.first_name for applicant in self.primary_contacts)

    @property
    def comped_badge_count(self):
        return len([a for a in self.applicants if a.attendee_id and a.attendee.paid in [c.NEED_NOT_PAY, c.REFUNDED]])

    @property
    def can_add_badges(self):
        uncomped_badge_count = len([a for a in self.applicants
                                    if a.attendee_id and a.attendee.paid not in [c.NEED_NOT_PAY, c.REFUNDED]])
        return len(self.applicants) - uncomped_badge_count < c.MITS_BADGES_PER_TEAM

    @property
    def can_save(self):
        return (c.HAS_MITS_ADMIN_ACCESS
            or self.status in [c.ACCEPTED, c.WAITLISTED]
            or (self.is_new and c.BEFORE_MITS_SUBMISSION_DEADLINE or c.BEFORE_MITS_EDITING_DEADLINE))

    @property
    def completed_hotel_form(self):
        """
        This is "any" rather than "all" because teams are allowed to add and
        remove members even after their application has been submitted.  Rather
        than suddenly downgrade their completion percentage, it makes more sense
        to send such teams an automated email indicating that they need to
        provide their remaining hotel info.
        """
        return any(a.declined_hotel_space or a.requested_room_nights for a in self.applicants)

    @property
    def steps_completed(self):
        if not self.games:
            return 1
        elif not self.pictures:
            return 2
        elif not self.schedule:
            return 3
        elif not self.completed_hotel_form:
            return 4
        elif not self.submitted:
            return 5
        else:
            return 6

    @property
    def completion_percentage(self):
        return 100 * self.steps_completed // c.MITS_APPLICATION_STEPS


class MITSApplicant(MagModel):
    team_id = Column(ForeignKey('mits_team.id'))
    attendee_id = Column(ForeignKey('attendee.id'), nullable=True)
    primary_contact = Column(Boolean, default=False)
    first_name = Column(UnicodeText)
    last_name = Column(UnicodeText)
    email = Column(UnicodeText)
    cellphone = Column(UnicodeText)
    contact_method = Column(Choice(c.MITS_CONTACT_OPTS), default=c.TEXTING)

    declined_hotel_space = Column(Boolean, default=False)
    requested_room_nights = Column(MultiChoice(c.MITS_ROOM_NIGHT_OPTS), default='')

    @property
    def full_name(self):
        return self.first_name + ' ' + self.last_name

    def has_requested(self, night):
        return night in self.requested_room_nights_ints


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
    personally_own = Column(Boolean, default=False)
    unlicensed = Column(Boolean, default=False)
    professional = Column(Boolean, default=False)


class MITSPicture(MagModel):
    team_id      = Column(UUID, ForeignKey('mits_team.id'))
    filename     = Column(UnicodeText)
    content_type = Column(UnicodeText)
    extension    = Column(UnicodeText)
    description  = Column(UnicodeText)

    @property
    def url(self):
        return '../mits_applications/view_picture?id={}'.format(self.id)

    @property
    def filepath(self):
        return os.path.join(c.MITS_PICTURE_DIR, str(self.id))


class MITSDocument(MagModel):
    team_id = Column(UUID, ForeignKey('mits_team.id'))
    filename = Column(UnicodeText)
    description  = Column(UnicodeText)

    @property
    def url(self):
        return '../mits_applications/download_doc?id={}'.format(self.id)

    @property
    def filepath(self):
        return os.path.join(c.MITS_PICTURE_DIR, str(self.id))


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
       team and raise an exception if it does not.  This check is bypassed for
       new things which have not yet been saved to the database.
    3) We set the "team" relationship on the model to the logged-in team.
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

    for name in ['mits_applicant', 'mits_game', 'mits_times', 'mits_picture', 'mits_document']:
        override_getter(name)
