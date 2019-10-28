"Web app template."

import flask

import about
import config
import constants
import user
import utils

import api.about
import api.root
import api.schema
import api.user

app = flask.Flask(__name__)
app.url_map.converters['name'] = utils.NameConverter
app.url_map.converters['iuid'] = utils.IuidConverter

# Get the configuration.
config.init(app)

# Init the mail handler.
utils.mail.init_app(app)

# Add template filters.
app.add_template_filter(utils.thousands)

@app.context_processor
def setup_template_context():
    "Add useful stuff to the global context of Jinja2 templates."
    return dict(constants=constants,
                csrf_token=utils.csrf_token)

@app.before_first_request
def init_database():
    flask.g.db = utils.get_db()
    utils.update_designs()

@app.before_request
def prepare():
    "Open the database connection; get the current user."
    flask.g.dbserver = utils.get_dbserver()
    flask.g.db = utils.get_db(dbserver=flask.g.dbserver)
    flask.g.current_user = user.get_current_user()
    flask.g.is_admin = flask.g.current_user and \
                       flask.g.current_user['role'] == constants.ADMIN

@app.route('/')
def home():
    "Home page. Redirect to API root if JSON is accepted."
    if utils.accept_json():
        return flask.redirect(flask.url_for('api_root'))
    else:
        return flask.render_template('home.html')

# Set up the URL map.
app.register_blueprint(about.blueprint, url_prefix='/about')
app.register_blueprint(user.blueprint, url_prefix='/user')

app.register_blueprint(api.root.blueprint, url_prefix='/api')
app.register_blueprint(api.about.blueprint, url_prefix='/api/about')
app.register_blueprint(api.schema.blueprint, url_prefix='/api/schema')
app.register_blueprint(api.user.blueprint, url_prefix='/api/user')


# This code is used only during testing.
if __name__ == '__main__':
    app.run(debug=True)


