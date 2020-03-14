"flask / gunicorn entrypoint"

import flask

from .blueprints import auth
from .util import con

app = flask.Flask(__name__)
app.register_blueprint(auth.APP, url_prefix='/auth')

app.before_first_request(con.connect_all)

@app.route('/')
def splash():
  return flask.render_template('splash.htm')

@app.route('/terms')
def terms():
  return flask.render_template('terms.htm')
