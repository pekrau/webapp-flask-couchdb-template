"Stand-alone script to create an admin user account."

import getpass

import flask

import webapp
import constants
import user
import utils


with webapp.app.app_context():
    flask.g.db = utils.get_db()
    utils.update_designs()
    with user.UserContext() as ctx:
        ctx.set_username(input('username > '))
        ctx.set_email(input('email > '))
        ctx.set_password(getpass.getpass('password > '))
        ctx.set_role(constants.ADMIN)
        ctx.set_status(constants.ENABLED)
