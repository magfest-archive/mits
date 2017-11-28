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

    def badges(self, session):
        possibles = defaultdict(list)
        for a in session.valid_attendees():
            possibles[a.email.lower()].append(a)
            possibles[a.first_name, a.last_name].append(a)

        applicants = []
        for team in session.mits_teams():
            if team.status == c.ACCEPTED:
                for a in team.applicants:
                    if not a.attendee_id:
                        applicants.append([a, set(possibles[a.email.lower()] + possibles[a.first_name, a.last_name])])

        return {'applicants': applicants}

    @ajax
    def link_badge(self, session, applicant_id, attendee_id):
        try:
            applicant = session.mits_applicant(applicant_id)
            applicant.attendee_id = attendee_id
            session.commit()
        except:
            log.error('unexpected error linking applicant to a badge', exc_info=True)
            return {'error': 'Unexpected error: unable to link applicant to badge.'}
        else:
            return {
                'name': applicant.full_name,
                'comp_count': applicant.team.comped_badge_count
            }

    @ajax
    def create_badge(self, session, applicant_id):
        try:
            applicant = session.mits_applicant(applicant_id)
            applicant.attendee = Attendee(
                placeholder=True,
                paid=c.NEED_NOT_PAY,
                badge_type=c.ATTENDEE_BADGE,
                first_name=applicant.first_name,
                last_name=applicant.last_name,
                email=applicant.email,
                cellphone=applicant.cellphone
            )
            session.add(applicant.attendee)
            session.commit()
        except:
            log.error('unexpected error adding new applicant', exc_info=True)
            return {'error': 'Unexpected error: unable to add attendee'}
        else:
            return {'comp_count': applicant.team.comped_badge_count}

    @csv_file
    def hotel_requests(self, out, session):
        for team in session.mits_teams().filter_by(status=c.ACCEPTED):
            for applicant in team.applicants:
                if applicant.requested_room_nights:
                    out.writerow([
                        team.name,
                        applicant.full_name,
                        applicant.email,
                        applicant.cellphone
                    ] + [
                        desc if val in applicant.requested_room_nights_ints else ''
                        for val, desc in c.MITS_ROOM_NIGHT_OPTS
                    ])

    @csv_file
    def schedule_requests(self, out, session):
        out.writerow([''] + [desc for val, desc in c.MITS_SCHEDULE_OPTS])
        for team in session.mits_teams().filter_by(status=c.ACCEPTED):
            available = getattr(team.schedule, 'availability_ints', [])
            multiple = getattr(team.schedule, 'multiple_tables_ints', [])
            out.writerow([team.name] + [
                'multiple' if val in multiple else
                '1 table' if val in available else ''
                for val, desc in c.MITS_SCHEDULE_OPTS
            ])
