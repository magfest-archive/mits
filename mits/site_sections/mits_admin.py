from mits import *


@all_renderable(c.MITS_ADMIN)
class Root:
    def index(self, session, message=''):
        return {
            'message': message,
            'teams': session.mits_teams()
        }

    def team(self, session, id, message=''):
        return {
            'message': message,
            'team': session.mits_team(id)
        }
