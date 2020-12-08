"About API endpoints."

import http.client

import flask

from webapp import utils


blueprint = flask.Blueprint("api", __name__)

@blueprint.route("")
def root():
    "API root."
    items = {
        "schema": {
            "root": {"href": flask.url_for("api_schema.root", _external=True)},
            "logs": {"href": flask.url_for("api_schema.logs", _external=True)},
            "user": {"href": flask.url_for("api_schema.user", _external=True)},
            "users": {"href": flask.url_for("api_schema.users",_external=True)},
            "about/software": {
                "href": flask.url_for("api_schema.about_software",
                                      _external=True)
            }
        },
        "about": {
            "software": {"href": flask.url_for("api_about.software",
                                               _external=True)}
        }
    }
    if flask.g.current_user:
        items["user"] = {
            "username": flask.g.current_user["username"],
            "href": flask.url_for("api_user.display",
                                  username=flask.g.current_user["username"],
                                  _external=True)
        }
    if flask.g.am_admin:
        items["users"] = {
            "href": flask.url_for("api_user.all", _external=True)
        }
    return utils.jsonify(utils.get_json(**items),
                         schema_url=flask.url_for("api_schema.root",
                                                  _external=True))
