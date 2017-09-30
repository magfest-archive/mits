from mits import *
from uber.model_checks import _invalid_phone_number
from email_validator import validate_email, EmailNotValidError

MITSTeam.required = [
    ('name', 'Production Team Name')
]
MITSApplicant.required = [
    ('first_name', 'First Name'),
    ('last_name', 'Last Name'),
    ('email', 'Email Address'),
    ('cellphone', 'Cellphone Number')
]
MITSGame.required = [
    ('name', 'Name'),
    ('promo_blurb', 'Promo Blurb'),
    ('description', 'Description'),
    ('genre', 'Game Genre')
]
MITSPicture.required = [
    ('description', 'Description')
]


@validation.MITSTeam
@validation.MITSApplicant
@validation.MITSGame
@validation.MITSPicture
@validation.MITSTimes
def is_saveable(inst):
    team = inst if isinstance(inst, MITSTeam) else inst.team
    if not team.can_save:
        if team.is_new:
            return 'New applications may not be submitted past the deadline'
        else:
            return 'We are now past the deadline and your application may no longer be edited'


@validation.MITSTeam
def address_required_for_sellers(team):
    if team.want_to_sell and not team.address.strip():
        return 'You must provide a business address if you wish to sell your merchandise'


@validation.MITSApplicant
def email_valid(applicant):
    try:
        validate_email(applicant.email)
    except EmailNotValidError as e:
        return 'Enter a valid email address. ' + str(e)


@validation.MITSApplicant
def valid_phone_number(applicant):
    if _invalid_phone_number(applicant.cellphone):
        return 'Your cellphone number was not a valid 10-digit US phone number.  Please include a country code (e.g. +44) for international numbers.'


@validation.MITSGame
def consistent_players(game):
    if game.min_players > game.max_players:
        return 'Min players must be less than or equal to max players'
