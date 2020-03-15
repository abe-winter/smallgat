"flask / gunicorn entrypoint"

import flask, os

from .blueprints import auth, user, institution, group
from .util import con

app = flask.Flask(__name__)
app.secret_key = os.environ['FLASK_SECRET']
app.register_blueprint(auth.APP, url_prefix='/auth')
app.register_blueprint(user.APP, url_prefix='/user')
app.register_blueprint(institution.APP, url_prefix='/inst')
app.register_blueprint(group.APP, url_prefix='/group')

app.before_first_request(con.connect_all)

@app.route('/')
def splash():
  return flask.render_template('splash.htm')

@app.route('/terms')
def terms():
  return flask.render_template('terms.htm')

@app.route('/health')
def health():
  return flask.jsonify({'ok': True})

class IntentionalError(Exception):
  pass

@app.route('/crash')
def crash():
  raise IntentionalError
