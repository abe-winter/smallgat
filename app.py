"flask / gunicorn entrypoint"

import flask, os

from .blueprints import auth, user
from .util import con

app = flask.Flask(__name__)
app.secret_key = os.environ['FLASK_SECRET']
app.register_blueprint(auth.APP, url_prefix='/auth')
app.register_blueprint(user.APP, url_prefix='/user')

app.before_first_request(con.connect_all)

@app.route('/')
def splash():
  return flask.render_template('splash.htm')

@app.route('/terms')
def terms():
  return flask.render_template('terms.htm')
