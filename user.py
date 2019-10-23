"User profile and login/logout HTMl endpoints."

import functools
import http.client
import json
import re

import flask
import flask_mail
import werkzeug.security

import constants
import utils


# Decorators

def login_required(f):
    "Decorator for checking if logged in. Send to login page if not."
    @functools.wraps(f)
    def wrap(*args, **kwargs):
        if not flask.g.current_user:
            url = flask.url_for('user.login', next=flask.request.base_url)
            return flask.redirect(url)
        return f(*args, **kwargs)
    return wrap

def admin_required(f):
    """Decorator for checking if logged in and 'admin' role.
    Otherwise return status 401 Unauthorized.
    """
    @functools.wraps(f)
    def wrap(*args, **kwargs):
        if not flask.g.is_admin:
            flask.abort(http.client.UNAUTHORIZED)
        return f(*args, **kwargs)
    return wrap


blueprint = flask.Blueprint('user', __name__)

@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    "Login to a user account."
    if utils.http_GET():
        return flask.render_template('user/login.html',
                                     next=flask.request.args.get('next'))
    if utils.http_POST():
        username = flask.request.form.get('username')
        password = flask.request.form.get('password')
        try:
            if username and password:
                do_login(username, password)
            else:
                raise ValueError
            try:
                next = flask.request.form['next']
            except KeyError:
                return flask.redirect(flask.url_for('home'))
            else:
                return flask.redirect(next)
        except ValueError:
            utils.flash_error('invalid user/password, or account disabled')
            return flask.redirect(flask.url_for('.login'))

@blueprint.route('/logout', methods=['POST'])
def logout():
    "Logout from the user account."
    del flask.session['username']
    return flask.redirect(flask.url_for('home'))

@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    "Register a new user account."
    if utils.http_GET():
        return flask.render_template('user/register.html')

    elif utils.http_POST():
        try:
            with UserContext() as ctx:
                ctx.set_username(flask.request.form.get('username'))
                ctx.set_email(flask.request.form.get('email'))
                ctx.set_role(constants.USER)
                ctx.set_password()
            user = ctx.user
        except ValueError as error:
            utils.flash_error(error)
            return flask.redirect(flask.url_for('.register'))
        # Directly enabled; send code to the user.
        if user['status'] == constants.ENABLED:
            send_password_code(user, 'registration')
            utils.flash_message('User account created; check your email.')
        # Was set to 'pending'; send email to admins.
        else:
            admins = flask.g.db['users'].find({'role': constants.ADMIN})
            emails = [u['email'] for u in admins]
            site = flask.current_app.config['SITE_NAME']
            message = flask_mail.Message(f"{site} user account pending",
                                         recipients=emails)
            url = utils.url_for('.profile', username=user['username'])
            message.body = f"To enable the user account, go to {url}"
            utils.mail.send(message)
            utils.flash_message('User account created; an email will be sent'
                                ' when it has been enabled by the admin.')
        return flask.redirect(flask.url_for('home'))

@blueprint.route('/reset', methods=['GET', 'POST'])
def reset():
    "Reset the password for a user account and send email."
    if utils.http_GET():
        return flask.render_template('user/reset.html',
                                     email=flask.request.args.get('email') or '')

    elif utils.http_POST():
        try:
            user = get_user(email=flask.request.form['email'])
            if user is None: raise KeyError
            if user['status'] != constants.ENABLED: raise KeyError
        except KeyError:
            pass
        else:
            with UserContext(user) as ctx:
                ctx.set_password()
            send_password_code(user, 'password reset')
        utils.flash_message('An email has been sent if the user account exists.')
        return flask.redirect(flask.url_for('home'))

@blueprint.route('/password', methods=['GET', 'POST'])
def password():
    "Set the password for a user account, and login user."
    if utils.http_GET():
        return flask.render_template(
            'user/password.html',
            username=flask.request.args.get('username'),
            code=flask.request.args.get('code'))

    elif utils.http_POST():
        try:
            username = flask.request.form['username']
            if not username: raise KeyError
            user = get_user(username=username)
            if user is None: raise KeyError
            if user['password'] != "code:{}".format(flask.request.form['code']):
                raise KeyError
            password = flask.request.form.get('password') or ''
            if len(password) < flask.current_app.config['MIN_PASSWORD_LENGTH']:
                raise ValueError
        except KeyError:
            utils.flash_error('no such user or wrong code')
        except ValueError:
            utils.flash_error('too short password')
        else:
            with UserContext(user) as ctx:
                ctx.set_password(password)
            do_login(username, password)
        return flask.redirect(flask.url_for('home'))

@blueprint.route('/profile/<name:username>')
@login_required
def profile(username):
    "Display the profile of the given user."
    user = get_user(username=username)
    if user is None:
        utils.flash_error('no such user')
        return flask.redirect(flask.url_for('home'))
    if not is_admin_or_self(user):
        utils.flash_error('access not allowed')
        return flask.redirect(flask.url_for('home'))
    return flask.render_template('user/profile.html',
                                 user=user,
                                 enable_disable=is_admin_and_not_self(user),
                                 deletable=is_empty(user))

@blueprint.route('/profile/<name:username>/edit',
                 methods=['GET', 'POST', 'DELETE'])
@login_required
def edit(username):
    "Edit the user profile. Or delete the user."
    user = get_user(username=username)
    if user is None:
        utils.flash_error('no such user')
        return flask.redirect(flask.url_for('home'))
    if not is_admin_or_self(user):
        utils.flash_error('access not allowed')
        return flask.redirect(flask.url_for('home'))

    if utils.http_GET():
        return flask.render_template('user/edit.html',
                                     user=user,
                                     change_role=is_admin_and_not_self(user))

    elif utils.http_POST():
        with UserContext(user) as ctx:
            email = flask.request.form.get('email')
            if email != user['email']:
                ctx.set_email(enail)
            if is_admin_and_not_self(user):
                ctx.set_role(flask.request.form.get('role'))
            if flask.request.form.get('apikey'):
                ctx.set_apikey()
        return flask.redirect(
            flask.url_for('.profile', username=user['username']))

    elif utils.http_DELETE():
        if not is_empty(user):
            utils.flash_error('cannot delete non-empty user account')
            return flask.redirect(flask.url_for('.profile', username=username))
        flask.g.db['users'].delete_one({'_id': user['_id']})
        utils.flash_message(f"Deleted user {username}.")
        if flask.g.is_admin:
            return flask.redirect(flask.url_for('.users'))
        else:
            return flask.redirect(flask.url_for('home'))

@blueprint.route('/profile/<name:username>/logs')
@login_required
def logs(username):
    "Display the log records of the given user."
    user = get_user(username=username)
    if user is None:
        utils.flash_error('no such user')
        return flask.redirect(flask.url_for('home'))
    if not is_admin_or_self(user):
        utils.flash_error('access not allowed')
        return flask.redirect(flask.url_for('home'))
    logs = list(flask.g.db['user_logs'].find({'username': username}))
    logs.sort(key=lambda l: l['timestamp'], reverse=True)
    return flask.render_template('user/logs.html', user=user, logs=logs)

@blueprint.route('/all')
@admin_required
def all():
    "Display list of all users."
    users = list(flask.g.db['users'].find())
    return flask.render_template('user/all.html', users=users)

@blueprint.route('/enable/<name:username>', methods=['POST'])
@admin_required
def enable(username):
    "Enable the given user account."
    user = get_user(username=username)
    if user is None:
        utils.flash_error('no such user')
        return flask.redirect(flask.url_for('home'))
    with UserContext(user) as ctx:
        ctx.set_status(constants.ENABLED)
        ctx.set_password()
    send_password_code(user, 'enabled')
    return flask.redirect(flask.url_for('.profile', username=username))

@blueprint.route('/disable/<name:username>', methods=['POST'])
@admin_required
def disable(username):
    "Disable the given user account."
    user = get_user(username=username)
    if user is None:
        utils.flash_error('no such user')
        return flask.redirect(flask.url_for('home'))
    with UserContext(user) as ctx:
        ctx.set_status(constants.DISABLED)
    return flask.redirect(flask.url_for('.profile', username=username))


class UserContext:
    "Context for creating, modifying and saving a user account."

    def __init__(self, user=None):
        if user is None:
            if flask.current_app.config['USER_ENABLE_IMMEDIATELY']:
                status = constants.ENABLED
            else:
                status = constants.PENDING
            self.user = {'_id': utils.get_iuid(),
                         'status': status, 
                         'created': utils.get_time()}
            self.orig = {}
        else:
            self.user = user
            self.orig = user.copy()

    def __enter__(self):
        return self

    def __exit__(self, etyp, einst, etb):
        if etyp is not None: return False
        for key in ['username', 'email', 'role', 'status']:
            if not self.user.get(key):
                raise ValueError("invalid user: %s not set" % key)
        self.user['modified'] = utils.get_time()
        
        # Insert or update user entry.
        coll = flask.g.db['users']
        coll.replace_one({'_id': self.user['_id']}, self.user, upsert=True)

        # Add log entry.
        new = {}
        for key, value in self.user.items():
            if value != self.orig.get(key):
                new[key] = value
        # Trivially always different; skip.
        new.pop('modified')
        # Do not show new password.
        try:
            password = new['password']
        except KeyError:
            pass
        else:
            if not password.startswith('code:'):
                new['password'] = '***'
        entry = {'_id': utils.get_iuid(), 
                 'username': self.user['username'],
                 'new': new,
                 'timestamp': utils.get_time()}
        if hasattr(flask.g, 'current_user') and flask.g.current_user:
            entry['editor'] = flask.g.current_user['username']
        else:
            entry['editor'] = None
        if flask.has_request_context():
            entry['remote_addr'] = str(flask.request.remote_addr)
            entry['user_agent'] = str(flask.request.user_agent)
        else:
            entry['remote_addr'] = None
            entry['user_agent'] = None
        flask.g.db['user_logs'].insert_one(entry)

    def set_username(self, username):
        if 'username' in self.user:
            raise ValueError('username cannot be changed')
        if not constants.NAME_RX.match(username):
            raise ValueError('invalid username; must be an name')
        if get_user(username=username):
            raise ValueError('username already in use')
        self.user['username'] = username

    def set_email(self, email):
        if not constants.EMAIL_RX.match(email):
            raise ValueError('invalid email')
        if get_user(email=email):
            raise ValueError('email already in use')
        self.user['email'] = email
        if self.user.get('status') == constants.PENDING:
            for rx in flask.current_app.config['USER_ENABLE_EMAIL_WHITELIST']:
                if re.match(rx, email):
                    self.set_status(constants.ENABLED)
                    break

    def set_status(self, status):
        if status not in constants.USER_STATUSES:
            raise ValueError('invalid status')
        self.user['status'] = status

    def set_role(self, role):
        if role not in constants.USER_ROLES:
            raise ValueError('invalid role')
        self.user['role'] = role

    def set_password(self, password=None):
        "Set the password; a one-time code if no password provided."
        config = flask.current_app.config
        if password is None:
            self.user['password'] = "code:%s" % utils.get_iuid()
        else:
            if len(password) < config['MIN_PASSWORD_LENGTH']:
                raise ValueError('password too short')
            self.user['password'] = werkzeug.security.generate_password_hash(
                password, salt_length=config['SALT_LENGTH'])

    def set_apikey(self):
        "Set a new API key."
        self.user['apikey'] = utils.get_iuid()


# Utility functions

def get_user(username=None, email=None, apikey=None):
    """Return the user for the given username, email or apikey.
    Return None if no such user.
    """
    coll = flask.g.db['users']
    if username:
        user = coll.find_one({'username': username})
        if user: return user
    if email:
        user = coll.find_one({'email': email})
        if user: return user
    if apikey:
        user = coll.find_one({'apikey': apikey})
        if user: return user
    return None

def get_current_user():
    """Return the user for the current session.
    Return None if no such user, or disabled.
    """
    user = get_user(username=flask.session.get('username'),
                    apikey=flask.request.headers.get('x-apikey'))
    if user is None or user['status'] != constants.ENABLED:
        flask.session.pop('username', None)
        return None
    return user

def do_login(username, password):
    """Set the session cookie if successful login.
    Raise ValueError if some problem.
    """
    user = get_user(username)
    if user is None: raise ValueError
    if not werkzeug.security.check_password_hash(user['password'], password):
        raise ValueError
    if user['status'] != constants.ENABLED:
        raise ValueError
    flask.session['username'] = user['username']
    flask.session.permanent = True

def send_password_code(user, action):
    "Send an email with the one-time code to the user's email address."
    site = flask.current_app.config['SITE_NAME']
    message = flask_mail.Message(f"{site} user account {action}",
                                 recipients=[user['email']])
    url = utils.url_for('.password',
                        username=user['username'],
                        code=user['password'][len('code:'):])
    message.body = f"To set your password, go to {url}"
    utils.mail.send(message)

def is_empty(user):
    "Is the given user account empty? No data associated with it."
    # XXX Need reimplementation.
    return True

def is_admin_or_self(user):
    "Is the current user admin, or the same as the given user?"
    if not flask.g.current_user: return False
    if flask.g.is_admin: return True
    return flask.g.current_user['username'] == user['username']

def is_admin_and_not_self(user):
    "Is the current user admin, but not the same as the given user?"
    if flask.g.is_admin:
        return flask.g.current_user['username'] != user['username']
    return False
