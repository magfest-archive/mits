from mits import *


@all_renderable()
class Root:
    def index(self, session, message=''):
        return {
            'message': message,
            'team': session.logged_in_mits_team()
        }

    def logout(self):
        cherrypy.session.pop('mits_team_id', None)
        raise HTTPRedirect('team')

    def continue_app(self, id):
        cherrypy.session['mits_team_id'] = id
        raise HTTPRedirect('index')

    def view_picture(self, session, id):
        picture = session.mits_picture(id)
        return serve_file(picture.filepath, name=picture.filename, content_type=picture.content_type)

    def team(self, session, message='', **params):
        params.pop('id', None)
        team = session.mits_team(dict(params, id=cherrypy.session.get('mits_team_id', 'None')), restricted=True)
        applicant = session.mits_applicant(params, restricted=True)

        if cherrypy.request.method == 'POST':
            message = check(team)
            if not message and team.is_new:
                applicant.team = team
                message = check(applicant)
            if not message:
                session.add(team)
                if team.is_new:
                    applicant.primary_contact = True
                    session.add(applicant)
                raise HTTPRedirect('continue_app?id={}', team.id)

        return {
            'message': message,
            'team': team,
            'applicant': applicant
        }

    def applicant(self, session, message='', **params):
        applicant = session.mits_applicant(params, applicant=True)
        if applicant.attendee_id:
            raise HTTPRedirect('../registration/form?id={}&message={}', applicant.attendee_id)

        if cherrypy.request.method == 'POST':
            message = check(applicant)
            if not message:
                session.add(applicant)
                raise HTTPRedirect('index?message={}', 'Team member uploaded')

        return {
            'message': message,
            'applicant': applicant
        }

    @csrf_protected
    def set_primary_contact(self, session, id, enable=False):
        applicant = session.mits_applicant(id, applicant=True)
        if not enable and len(applicant.team.primary_contacts) == 1:
            raise HTTPRedirect('index?message={}', 'At least one team member must be designated to receive emails')
        else:
            applicant.primary_contact = bool(enable)
            raise HTTPRedirect('index?message={}', 'Email designation updated')

    @csrf_protected
    def delete_applicant(self, session, id):
        applicant = session.mits_applicant(id, applicant=True)
        if applicant.primary_contact and len(applicant.team.primary_contacts) == 1:
            raise HTTPRedirect('index?message={}', 'You cannot delete the only team member designated to receive emails')
        elif applicant.attendee_id:
            raise HTTPRedirect('../preregistration/confirm?id={}', 'Team members cannot be deleted after being granted a badge, but you may transfer this badge if you need to.')
        else:
            session.delete(applicant)
            raise HTTPRedirect('index?message={}', 'Team member deleted')

    def picture(self, session, message='', image=None, **params):
        picture = session.mits_picture(params, applicant=True)
        if cherrypy.request.method == 'POST':
            picture.filename = image.filename
            picture.content_type = image.content_type.value
            picture.extension = image.filename.split('.')[-1].lower()
            message = check(picture)
            if not message:
                with open(picture.filepath, 'wb') as f:
                    shutil.copyfileobj(image.file, f)
                raise HTTPRedirect('index?message={}', 'Picture Uploaded')

        return {
            'message': message,
            'picture': picture
        }

    @csrf_protected
    def delete_picture(self, session, id):
        picture = session.mits_picture(id, applicant=True)
        session.delete_mits_picture(picture)
        raise HTTPRedirect('index?message={}', 'Picture deleted')

    def game(self, session, message='', **params):
        game = session.mits_game(params, applicant=True)
        if cherrypy.request.method == 'POST':
            message = check(game)
            if not message:
                session.add(game)
                raise HTTPRedirect('index?message={}', 'Game saved')

        return {
            'game': game,
            'message': message
        }

    @csrf_protected
    def delete_game(self, session, id):
        game = session.mits_game(id, applicant=True)
        session.delete(game)
        raise HTTPRedirect('index?message={}', 'Game deleted')

    def schedule(self, session, message='', **params):
        times = session.mits_times(params, applicant=True)
        if cherrypy.request.method == 'POST':
            message = check(times)
            if not message:
                session.add(times)
                raise HTTPRedirect('index?message={}', 'Times saved')

        return {
            'times': times,
            'message': message,
            'grid': [
                (val, desc, val in times.availability_ints, val in times.multiple_tables_ints)
                for val, desc in c.MITS_SCHEDULE_OPTS
            ]
        }

    def hotel_requests(self, session, message='', **params):
        team = session.logged_in_mits_team()
        if cherrypy.request.method == 'POST':
            for applicant in team.applicants:
                applicant.declined_hotel_space = '{}-declined'.format(applicant.id) in params
                applicant.requested_room_nights = ','.join(listify(params.get('{}-night'.format(applicant.id), [])))
                if not applicant.declined_hotel_space and not applicant.requested_room_nights:
                    message = '{} must either declined hotel space or indicate which room nights they need'.format(applicant.full_name)
                    break
                elif applicant.declined_hotel_space and applicant.requested_room_nights:
                    message = '{} cannot both decline hotel space and request specific room nights'.format(applicant.full_name)
                    break

            if not message:
                raise HTTPRedirect('index?message={}', 'Room nights uploaded')

        return {
            'team': team,
            'message': message
        }

    def submit_for_judging(self, session):
        team = session.logged_in_mits_team()
        if team.steps_completed < c.MITS_APPLICATION_STEPS - 1:
            raise HTTPRedirect('index?message={}', 'You have not completed all of the required steps')
        elif c.AFTER_MITS_SUBMISSION_DEADLINE:
            raise HTTPRedirect('index?message={}', 'You cannot submit an application past the deadline')
        else:
            team.submitted = datetime.now(UTC)
            raise HTTPRedirect('index?message={}', 'Your application has been submitted')
