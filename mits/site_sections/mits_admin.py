from mits import *


@all_renderable(c.MITS_ADMIN)
class Root:
    def index(self, session, message=''):
        return {
            'message': message,
            'teams': session.mits_teams()
        }

    def create_new_application(self):
        cherrypy.session.pop('mits_team_id', None)
        raise HTTPRedirect('../mits_applications/team')

    def team(self, session, id, message=''):
        return {
            'message': message,
            'team': session.mits_team(id)
        }

    def delete_team(self, session, id, duplicate_of=None, csrf_token=None, message=''):
        team = session.mits_team(id)
        if cherrypy.request.method == 'POST':
            check_csrf(csrf_token)
            team.deleted = True
            team.duplicate_of = duplicate_of or None
            raise HTTPRedirect('index?message={}{}{}', team.name, ' marked as deleted',
                ' and as a duplicate' if duplicate_of else '')

        other = [t for t in session.mits_teams() if t.id != id]
        return {
            'team': team,
            'message': message,
            'match_count': len([t for t in other if t.name == team.name]),
            'other_teams': sorted(other, key=lambda t: (t.name != team.name, t.name))
        }
