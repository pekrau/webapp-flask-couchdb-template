"Various utility functions and classes."

import datetime
import functools
import http.client
import json
import logging
import time
import uuid

import couchdb2
import flask
import flask_mail
import jinja2.utils
import werkzeug.routing

from webapp import constants

def init(app):
    """Initialize app.
    - Add URL map converters.
    - Add template filters.
    - Update CouchDB design document.
    """
    app.url_map.converters["identifier"] = IdentifierConverter
    app.url_map.converters["iuid"] = IuidConverter
    app.add_template_filter(thousands)
    app.add_template_filter(tojson2)
    db = get_db(app=app)
    logger = get_logger(app)
    if db.put_design("logs", DESIGN_DOC):
        logger.info("Updated logs design document.")

DESIGN_DOC = {
    "views": {
        "doc": {"map": "function(doc) {if (doc.doctype !== 'log') return; emit([doc.docid, doc.timestamp], null);}"}
    },
}

# Global logger instance.
_logger = None
def get_logger(app=None):
    global _logger
    if _logger is None:
        if app is None:
            config = flask.current_app.config
        else:
            config = app.config
        _logger = logging.getLogger(config["LOG_NAME"])
        if config["LOG_DEBUG"]:
            _logger.setLevel(logging.DEBUG)
        else:
            _logger.setLevel(logging.WARNING)
        if config["LOG_FILEPATH"]:
            if config["LOG_ROTATING"]:
                loghandler = logging.TimedRotatingFileHandler(
                    config["LOG_FILEPATH"],
                    when="midnight",
                    backupCount=config["LOG_ROTATING"])
            else:
                loghandler = logging.FileHandler(config["LOG_FILEPATH"])
        else:
            loghandler = logging.StreamHandler()
        loghandler.setFormatter(logging.Formatter(config["LOG_FORMAT"]))
        _logger.addHandler(loghandler)
    return _logger

def log_access(response):
    "Record access using the logger."
    if flask.g.current_user:
        username = flask.g.current_user["username"]
    else:
        username = None
    get_logger().debug(f"{flask.request.remote_addr} {username}"
                       f" {flask.request.method} {flask.request.path}"
                       f" {response.status_code}")
    return response

# Global instance of mail interface.
mail = flask_mail.Mail()

# Decorators for endpoints
def login_required(f):
    "Decorator for checking if logged in. Send to login page if not."
    @functools.wraps(f)
    def wrap(*args, **kwargs):
        if not flask.g.current_user:
            url = flask.url_for("user.login", next=flask.request.base_url)
            return flask.redirect(url)
        return f(*args, **kwargs)
    return wrap

def admin_required(f):
    """Decorator for checking if logged in and 'admin' role.
    Otherwise return status 401 Unauthorized.
    """
    @functools.wraps(f)
    def wrap(*args, **kwargs):
        if not flask.g.am_admin:
            flask.abort(http.client.UNAUTHORIZED)
        return f(*args, **kwargs)
    return wrap


class IdentifierConverter(werkzeug.routing.BaseConverter):
    "URL route converter for an identifier."
    def to_python(self, value):
        if not constants.ID_RX.match(value):
            raise werkzeug.routing.ValidationError
        return value

class IuidConverter(werkzeug.routing.BaseConverter):
    "URL route converter for a IUID."
    def to_python(self, value):
        if not constants.IUID_RX.match(value):
            raise werkzeug.routing.ValidationError
        return value.lower()    # Always lower case

class Timer:
    "CPU timer."
    def __init__(self):
        self.start = time.process_time()
    def __call__(self):
        "Return CPU time (in seconds) since start of this timer."
        return time.process_time() - self.start
    @property
    def milliseconds(self):
        "Return CPU time (in milliseconds) since start of this timer."
        return round(1000 * self())

def get_iuid():
    "Return a new IUID, which is a UUID4 pseudo-random string."
    return uuid.uuid4().hex

def to_bool(s):
    "Convert string value into boolean."
    if not s: return False
    s = s.lower()
    return s in ("true", "t", "yes", "y")

def get_time(offset=None):
    """Current date and time (UTC) in ISO format, with millisecond precision.
    Add the specified offset in seconds, if given.
    """
    instant = datetime.datetime.utcnow()
    if offset:
        instant += datetime.timedelta(seconds=offset)
    instant = instant.isoformat()
    return instant[:17] + "{:06.3f}".format(float(instant[17:])) + "Z"

def http_GET():
    "Is the HTTP method GET?"
    return flask.request.method == "GET"

def http_POST(csrf=True):
    "Is the HTTP method POST? Check whether used for method tunneling."
    if flask.request.method != "POST": return False
    if flask.request.form.get("_http_method") in (None, "POST"):
        if csrf: check_csrf_token()
        return True
    else:
        return False

def http_PUT():
    "Is the HTTP method PUT? Is not tunneled."
    return flask.request.method == "PUT"

def http_DELETE(csrf=True):
    "Is the HTTP method DELETE? Check for method tunneling."
    if flask.request.method == "DELETE": return True
    if flask.request.method == "POST":
        if csrf: check_csrf_token()
        return flask.request.form.get("_http_method") == "DELETE"
    else:
        return False

def csrf_token():
    "Output HTML for cross-site request forgery (CSRF) protection."
    # Generate a token to last the session's lifetime.
    if "_csrf_token" not in flask.session:
        flask.session["_csrf_token"] = get_iuid()
    html = '<input type="hidden" name="_csrf_token" value="%s">' % \
           flask.session["_csrf_token"]
    return jinja2.utils.Markup(html)

def check_csrf_token():
    "Check the CSRF token for POST HTML."
    # Do not use up the token; keep it for the session's lifetime.
    token = flask.session.get("_csrf_token", None)
    if not token or token != flask.request.form.get("_csrf_token"):
        flask.abort(http.client.BAD_REQUEST)

def error(message, url=None):
    """"Return redirect response to the given URL, or referrer, or home page.
    Flash the given message.
    """
    flash_error(message)
    return flask.redirect(url or referrer_or_home())

def referrer_or_home():
    "Return the URL for the referring page 'referer' or the home page."
    return flask.request.headers.get('referer') or flask.url_for('home')    

def flash_error(msg):
    "Flash error message."
    flask.flash(str(msg), "error")

def flash_message(msg):
    "Flash information message."
    flask.flash(str(msg), "message")

def thousands(value):
    "Template filter: Output integer with thousands delimiters."
    if isinstance(value, int):
        return "{:,}".format(value)
    else:
        return value

def tojson2(value, indent=2):
    """Transform to string JSON representation keeping single-quotes
    and indenting by 2 by default.
    """
    return json.dumps(value, indent=indent)

def accept_json():
    "Return True if the header Accept contains the JSON content type."
    acc = flask.request.accept_mimetypes
    best = acc.best_match([constants.JSON_MIMETYPE, constants.HTML_MIMETYPE])
    return best == constants.JSON_MIMETYPE and \
        acc[best] > acc[constants.HTML_MIMETYPE]

def get_json(**data):
    "Return the JSON structure after fixing up for external representation."
    result = {"$id": flask.request.url,
              "timestamp": get_time()}
    try:
        result["iuid"] = data.pop("_id")
    except KeyError:
        pass
    data.pop("_rev", None)
    data.pop("doctype", None)
    result.update(data)
    return result

def jsonify(result, schema_url=None):
    """Return a Response object containing the JSON of "result".
    Optionally add a header Link to the schema."""
    response = flask.jsonify(result)
    if schema_url:
        response.headers.add("Link", schema_url, rel="schema")
    return response

def get_dbserver(app=None):
    "Get the connection to the CouchDB database server."
    if app is None:
        app = flask.current_app
    return couchdb2.Server(href=app.config["COUCHDB_URL"],
                           username=app.config["COUCHDB_USERNAME"],
                           password=app.config["COUCHDB_PASSWORD"])

def get_db(dbserver=None, app=None):
    if app is None:
        app = flask.current_app
    if dbserver is None:
        dbserver = get_dbserver(app=app)
    return dbserver[app.config["COUCHDB_DBNAME"]]

def get_logs(docid, cleanup=True):
    """Return the list of log entries for the given document identifier,
    sorted by reverse timestamp.
    """
    result = [r.doc for r in flask.g.db.view("logs", "doc",
                                             startkey=[docid, "ZZZZZZ"],
                                             endkey=[docid],
                                             descending=True,
                                             include_docs=True)]
    if cleanup:
        for log in result:
            for key in ["_id", "_rev", "doctype", "docid"]:
                log.pop(key)
    return result


class JsonException(Exception):
    "JSON API error response."

    status_code = 400

    def __init__(self, message, status_code=None, data=None):
        super().__init__()
        self.message = str(message)
        if status_code is not None:
            self.status_code = status_code
        self.data = data

    def to_dict(self):
        result = dict(self.data or ())
        result["status_code"] = self.status_code
        result["message"] = self.message
        return result
