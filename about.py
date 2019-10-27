"About info HTMl endpoints."

import sys

import couchdb2
import flask
import jsonschema

import constants


blueprint = flask.Blueprint('about', __name__)

@blueprint.route('/software')
def software():
    "Show software versions."
    return flask.render_template('about/software.html',
                                 software=get_software())

def get_software():
    v = sys.version_info
    return [
        ('webapp', constants.VERSION, constants.SOURCE_URL),
        ('Python', f"{v.major}.{v.minor}.{v.micro}", 'https://www.python.org/'),
        ('Flask', flask.__version__, 'http://flask.pocoo.org/'),
        ('CouchDB', flask.g.dbserver.version, 'https://couchdb.apache.org/'),
        ('CouchDB2', couchdb2.__version__, 'https://pypi.org/project/couchdb2'),
        ('jsonschema', jsonschema.__version__, 
         'https://pypi.org/project/jsonschema'),
        ('Bootstrap', constants.BOOTSTRAP_VERSION, 'https://getbootstrap.com/'),
        ('jQuery', constants.JQUERY_VERSION, 'https://jquery.com/'),
        ('DataTables', constants.DATATABLES_VERSION, 'https://datatables.net/'),
    ]
