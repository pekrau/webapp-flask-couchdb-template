"About info HTMl endpoints."

import sys

import flask
import jsonschema
import pymongo

import constants
import utils


blueprint = flask.Blueprint('about', __name__)

@blueprint.route('/software')
def software():
    "Show software versions."
    py = sys.version_info
    return flask.render_template(
        'about/software.html',
        softwares=[('webapp', 
                    flask.current_app.config['VERSION'],
                    flask.current_app.config['WEBAPP_URL']),
                   ('Python',
                    f"{py.major}.{py.minor}.{py.micro}",
                    'https://www.python.org/'),
                   ('Flask',
                    flask.__version__,
                    'http://flask.pocoo.org/'),
                   ('MongoDB',
                    flask.g.mongo.server_info()['version'],
                    'https://www.mongodb.com/'),
                   ('pymongo',
                    pymongo.version,
                    'https://pypi.org/project/pymongo/'),
                   ('jsonschema',
                    jsonschema.__version__,
                    'https://pypi.org/project/jsonschema/'),
                   ('Bootstrap',
                    flask.current_app.config['BOOTSTRAP_VERSION'],
                    'https://getbootstrap.com/'),
                   ('jQuery',
                    flask.current_app.config['JQUERY_VERSION'],
                    'https://jquery.com/'),
                   ('DataTables',
                    flask.current_app.config['DATATABLES_VERSION'],
                    'https://datatables.net/'),
        ])
