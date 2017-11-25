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

    def set_status(self, session, id, status=None, confirmed=False, csrf_token=None, return_to='index', message=''):
        team = session.mits_team(id)
        matching = [t for t in session.mits_teams() if t.name == team.name and t.id != team.id]
        if confirmed or (status and not matching and team.status == c.PENDING and team.completion_percentage == 100):
            check_csrf(csrf_token)
            team.status = int(status)
            separator = '&' if '?' in return_to else '?'
            raise HTTPRedirect(return_to + separator + 'message={}{}{}', team.name, ' marked as ', team.status_label)

        return {
            'team': team,
            'message': message,
            'matching': matching,
            'return_to': return_to
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
