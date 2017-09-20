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
