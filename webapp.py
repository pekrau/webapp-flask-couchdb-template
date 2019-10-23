"Web app template. With user account handling."

import flask
import pymongo

import config
import constants
import utils

import about
import user
import api_schema
import api_user


app = flask.Flask(__name__)
app.url_map.converters['name'] = utils.NameConverter
app.url_map.converters['iuid'] = utils.IuidConverter

# Get the configuration; sanity check.
config.init(app)
assert app.config['SECRET_KEY']
assert app.config['SALT_LENGTH'] > 6
assert app.config['MIN_PASSWORD_LENGTH'] > 4

# Init the mail handler.
utils.mail.init_app(app)

# Set up the URL map.
app.register_blueprint(about.blueprint, url_prefix='/about')
app.register_blueprint(user.blueprint, url_prefix='/user')
app.register_blueprint(api_schema.blueprint, url_prefix='/api/schema')
app.register_blueprint(api_user.blueprint, url_prefix='/api/user')

# Add template filters.
app.add_template_filter(utils.thousands)

@app.context_processor
def setup_template_context():
    "Add useful stuff to the global context of Jinja2 templates."
    return dict(constants=constants,
                csrf_token=utils.csrf_token)

@app.before_request
def prepare():
    "Open the database connection; get the current user."
    utils.mongo_connect()
    flask.g.current_user = user.get_current_user()
    flask.g.is_admin = flask.g.current_user and \
                       flask.g.current_user['role'] == constants.ADMIN

@app.after_request
def finalize(response):
    "Close the database connection."
    flask.g.mongo.close()
    return response

@app.route('/')
def home():
    "Home page. Redirect to API root if JSON accepted."
    if utils.accept_json():
        return flask.redirect(flask.url_for('api_root'))
    return flask.render_template('home.html')

@app.route('/api')
def api_root():
    "API root."
    items = {}
    if flask.g.current_user:
        items['user'] = {
            'username': flask.g.current_user['username'],
            'href': utils.url_for('api_user.profile',
                                  username=flask.g.current_user['username'])
        }
    if flask.g.is_admin:
        items['users'] = {
            'href': utils.url_for('api_user.all')
        }
    return utils.jsonify(utils.get_json(**items), schema='/root')


# This code is used only during testing.
if __name__ == '__main__':
    app.run(debug=True)


