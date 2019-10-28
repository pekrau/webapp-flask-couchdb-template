"Command-line interface."

import argparse
import getpass
import sys

import flask

import webapp
import constants
import user
import utils


def get_parser():
    "Get the parser for the command line tool."
    p = argparse.ArgumentParser(prog='webapp.cli', usage='%(prog)s [options]',
                                description='webapp command line tool')
    p.add_argument('-d', '--debug', action='store_true',
                    help='Debug logging output.')
    x0 = p.add_mutually_exclusive_group()
    x0.add_argument('-u', '--update', action='store_true',
                    help='Update the design document in the CouchDB database.')
    x0.add_argument('-A', '--create_admin', action='store_true',
                    help='Create an admin user.')
    x0.add_argument('-U', '--create_user', action='store_true',
                    help='Create a user.')
    return p

def execute(pargs):
    "Execute the command."
    if pargs.debug:
        flask.current_app.config['DEBUG'] = True
    if pargs.update:
        utils.update_designs()
    if pargs.create_admin:
        with user.UserContext() as ctx:
            ctx.set_username(input('username > '))
            ctx.set_email(input('email > '))
            ctx.set_password(getpass.getpass('password > '))
            ctx.set_role(constants.ADMIN)
            ctx.set_status(constants.ENABLED)
    if pargs.create_user:
        with user.UserContext() as ctx:
            ctx.set_username(input('username > '))
            ctx.set_email(input('email > '))
            ctx.set_password(getpass.getpass('password > '))
            ctx.set_role(constants.USER)
            ctx.set_status(constants.ENABLED)

def main():
    "Entry point for command line tool."
    parser = get_parser()
    pargs = parser.parse_args()
    if len(sys.argv) == 1:
        parser.print_usage()
    with webapp.app.app_context():
        flask.g.db = utils.get_db()
        execute(pargs)

if __name__ == '__main__':
    main()
