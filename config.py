"Configuration."

import os
import os.path

import constants
import utils


ROOT_DIRPATH = os.path.dirname(os.path.abspath(__file__))

# Default configurable values; modified by letting 'init' read a JSON file.
CONFIG = dict(
    SERVER_NAME = '127.0.0.1:5002',
    SITE_NAME = 'webapp',
    SECRET_KEY = None,          # Must be set in 'config.json'
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
    SCHEMA_BASE_URL = 'http://127.0.0.1:5002/api/schema',
    # BOOTSTRAP_CSS_ATTRS = 'href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css" integrity="sha384-ggOyR0iXCbMQv3Xipma34MD+dH/1fQ784/j6cY/iJTQUOhcWr7x9JvoRxT2MZw1T" crossorigin="anonymous"',
    # JQUERY_JS_ATTRS = 'src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo" crossorigin="anonymous"',
    # POPPER_JS_ATTRS = 'src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.7/umd/popper.min.js" integrity="sha384-UO2eT0CpHqdSJQ6hJty5KVphtPhzWj9WO1clHTMGa3JDZwrnQq4sF86dIHNDz0W1" crossorigin="anonymous"',
    # BOOTSTRAP_JS_ATTRS = 'src="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.min.js" integrity="sha384-JjSmVgyd0p3pXB1rRibZUAYoIIy6OrQ6VrjIEaFf/nJGzIxFDsf4x0xIM+B07jRM" crossorigin="anonymous"',
    # DATATABLES_CSS_URL = 'https://cdn.datatables.net/1.10.18/css/dataTables.bootstrap4.min.css',
    # DATATABLES_JS_URL = 'https://cdn.datatables.net/1.10.18/js/jquery.dataTables.min.js',
    # DATATABLES_BOOTSTRAP_JS_URL = 'https://cdn.datatables.net/1.10.18/js/dataTables.bootstrap4.min.js'
)

def init(app):
    """Perform the configuration of the Flask app.
    Set the defaults, and then read JSON config file.
    Check the environment for a specific set of variables and use if defined.
    """
    # Set the defaults specified above.
    app.config.from_mapping(CONFIG)
    # Modify the configuration from a JSON config file.
    try:
        filepath = os.environ['CONFIG_FILEPATH']
        app.config.from_json(filepath)
        # Raises an error if filepath variable defined, but no such file.
    except KeyError:
        for filepath in ['config.json', 'site/config.json']:
            filepath = os.path.normpath(os.path.join(ROOT_DIRPATH, filepath))
            try:
                app.config.from_json(filepath)
            except FileNotFoundError:
                filepath = None
            else:
                break
    if filepath:
        print(' > Configuration file:', filepath)
    for key, convert in [('SECRET_KEY', str),
                         ('COUCHDB_URL', str),
                         ('COUCHDB_USERNAME', str),
                         ('COUCHDB_PASSWORD', str),
                         ('MAIL_SERVER', str),
                         ('MAIL_SERVER', str),
                         ('MAIL_USE_TLS', utils.to_bool),
                         ('MAIL_USERNAME', str),
                         ('MAIL_PASSWORD', str),
                         ('MAIL_DEFAULT_SENDER', str),
    ]:
        try:
            app.config[key] = convert(os.environ[key])
            print(' > From environment:', key)
        except (KeyError, TypeError, ValueError):
            pass
