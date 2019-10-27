"Configuration."

import logging
import os
import os.path

import constants
import utils

logger = logging.getLogger('webapp')

ROOT_DIRPATH = os.path.dirname(os.path.abspath(__file__))

# Default configurable values; modified by letting 'init' read a JSON file.
SETTINGS = dict(
    SERVER_NAME = '127.0.0.1:5002',
    SITE_NAME = 'webapp',
    DEBUG = False,
    SECRET_KEY = None,          # Must be set in 'settings.json'
    SALT_LENGTH = 12,
    COUCHDB_URL = 'http://127.0.0.1:5984/',
    COUCHDB_USERNAME = None,
    COUCHDB_PASSWORD = None,
    COUCHDB_DBNAME = 'webapp',
    JSONIFY_AS_ASCII = False,
    JSON_SORT_KEYS = False,
    MIN_PASSWORD_LENGTH = 6,
    PERMANENT_SESSION_LIFETIME = 7 * 24 * 60 * 60, # seconds; 1 week
    MAIL_SERVER = 'localhost',
    MAIL_PORT = 25,
    MAIL_USE_TLS = False,
    MAIL_USERNAME = None,
    MAIL_PASSWORD = None,
    MAIL_DEFAULT_SENDER = None,
    USER_ENABLE_IMMEDIATELY = False,
    USER_ENABLE_EMAIL_WHITELIST = [], # List of regexp's
    SCHEMA_BASE_URL = 'http://127.0.0.1:5002/api/schema'
)

def init(app):
    """Perform the configuration of the Flask app.
    Set the defaults, and then read JSON settings file.
    Check the environment for a specific set of variables and use if defined.
    """
    messages = []
    # Set the defaults specified above.
    app.config.from_mapping(SETTINGS)
    # Modify the configuration from a JSON settings file.
    try:
        filepath = os.environ['SETTINGS_FILEPATH']
    except KeyError:
        for filepath in ['settings.json', 'site/settings.json']:
            filepath = os.path.normpath(os.path.join(ROOT_DIRPATH, filepath))
            try:
                app.config.from_json(filepath)
            except FileNotFoundError:
                filepath = None
            else:
                break
    else:
        # Raises an error if filepath variable defined, but no such file.
        app.config.from_json(filepath)

    if filepath:
        messages.append(f"Configuration file: {filepath}")
    for key, convert in [('SECRET_KEY', str),
                         ('COUCHDB_URL', str),
                         ('COUCHDB_USERNAME', str),
                         ('COUCHDB_PASSWORD', str),
                         ('MAIL_SERVER', str),
                         ('MAIL_SERVER', str),
                         ('MAIL_USE_TLS', utils.to_bool),
                         ('MAIL_USERNAME', str),
                         ('MAIL_PASSWORD', str),
                         ('MAIL_DEFAULT_SENDER', str)]:
        try:
            app.config[key] = convert(os.environ[key])
            messages.append(f"Configuration {key} from environment")
        except (KeyError, TypeError, ValueError):
            pass
    if app.config['DEBUG']:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.WARNING)
    for message in messages:
        logger.info(message)
