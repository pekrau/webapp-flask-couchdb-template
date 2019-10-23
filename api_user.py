"User profile API endpoints."

import http.client

import flask

import user as user_module
import utils


blueprint = flask.Blueprint('api_user', __name__)

@blueprint.route('/')
def all():
    users = [
        {'username': u['username'],
         'href': utils.url_for('api_user.profile', username=u['username'])
        }
        for u in flask.g.systemdb['users'].find()
    ]
    return utils.jsonify(utils.get_json(users=users), schema='/users')

@blueprint.route('/<name:username>')
def profile(username):
    user = user_module.get_user(username=username)
    if not user_module.is_admin_or_self(user):
        flask.abort(http.client.FORBIDDEN)
    user.pop('password', None)
    user.pop('apikey', None)
    return utils.jsonify(utils.get_json(**user), schema='/user')
