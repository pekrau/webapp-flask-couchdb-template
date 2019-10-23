"Stand-alone script to create an admin user account."

import getpass

import flask

import constants
import webapp
import user
import utils


with webapp.app.app_context():
    utils.mongo_connect()
    with user.UserContext() as ctx:
        ctx.set_username(input('username > '))
        ctx.set_email(input('email > '))
        ctx.set_password(getpass.getpass('password > '))
        ctx.set_role(constants.ADMIN)
        ctx.set_status(constants.ENABLED)
