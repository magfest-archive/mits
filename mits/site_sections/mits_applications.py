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

    def view_screenshot(self, session, id):
        screenshot = session.mits_screenshot(id)
        return serve_file(screenshot.filepath, name=screenshot.filename, content_type=screenshot.content_type)

    def team(self, session, message='', **params):
        params.pop('id', None)
        team = session.mits_team(dict(params, id=cherrypy.session.get('mits_team_id', 'None')), restricted=True)
        applicant = session.mits_applicant(params, restricted=True)

        if cherrypy.request.method == 'POST' and team.can_save:
            message = check(team)
            if not message and team.is_new:
                message = check(applicant)
            if not message:
                session.add(team)
                if team.is_new:
                    applicant.team = team
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

    def screenshot(self, session, message='', image=None, **params):
        screenshot = session.mits_screenshot(params, applicant=True)
        if cherrypy.request.method == 'POST':
            screenshot.filename = image.filename
            screenshot.content_type = image.content_type.value
            screenshot.extension = image.filename.split('.')[-1].lower()
            message = check(screenshot)
            if not message:
                with open(screenshot.filepath, 'wb') as f:
                    shutil.copyfileobj(image.file, f)
                raise HTTPRedirect('index?message={}', 'Screenshot Uploaded')

        return {
            'message': message,
            'screenshot': screenshot
        }

    @csrf_protected
    def delete_screenshot(self, session, id):
        screenshot = session.mits_screenshot(id, applicant=True)
        session.delete_mits_screenshot(screenshot)
        raise HTTPRedirect('index?message={}', 'Screenshot deleted')

    
