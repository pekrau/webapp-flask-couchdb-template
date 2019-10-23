"JSON schemas for the API."

import flask

_USERNAME = {'type': 'string', 'pattern': '^[a-zA-Z][a-zA-Z0-9_-]*$'}
_URI      = {'type': 'string', 'format': 'uri'}
_DATETIME = {'type': 'string', 'format': 'date-time'}

ROOT = {
    'type': 'object',
    'properties': {
        '$id': _URI,
        'timestamp': _DATETIME
    },
    'required': [
        '$id',
        'timestamp'
    ]
}

USER = {
    'type': 'object',
    'properties': {
        '$id': _URI,
        'timestamp': _DATETIME,
        'iuid': {'type': 'string', 'pattern': '^[a-f0-9]{32}$'},
        'username': _USERNAME,
        'email': {'type': 'string', 'format': 'email'},
        'role': {'type': 'string', 'enum': ['admin', 'user']},
        'status': {'type': 'string', 'enum': ['pending', 'enabled', 'disabled']},
        'created': _DATETIME,
        'modified': _DATETIME
    },
    'required': [
        '$id',
        'timestamp',
        'iuid',
        'username',
        'email',
        'role',
        'status',
        'created',
        'modified'
    ],
    'additionalProperties': False
}

USERS = {
    'type': 'object',
    'properties': {
        '$id': _URI,
        'timestamp': _DATETIME,
        'users': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'username': _USERNAME,
                    'href': _URI
                },
                'required': ['username', 'href'],
                'additionalProperties': False
            }
        }
    },
    'required': [
        '$id',
        'timestamp',
        'users'
    ],
    'additionalProperties': False
}

blueprint = flask.Blueprint('api_schema', __name__)

@blueprint.route('/root', methods=['GET'])
def root():
    return flask.jsonify(ROOT)

@blueprint.route('/user', methods=['GET'])
def user():
    return flask.jsonify(USER)
