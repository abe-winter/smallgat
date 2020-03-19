"flask / gunicorn entrypoint"

import flask, os, werkzeug.middleware.proxy_fix

from .blueprints import auth, user, institution, group
from .util import con, misc

app = flask.Flask(__name__)
# note: x_for=2 is right for our prod kube setup but consider env config
app.wsgi_app = werkzeug.middleware.proxy_fix.ProxyFix(app.wsgi_app, x_for=2)
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
  return flask.jsonify({
    'ok': True,
    'remote_ip': misc.external_ip(),
  })

class IntentionalError(Exception):
  pass

@app.route('/crash')
def crash():
  misc.abort_msg(500, 'Intentional error', "You've discovered the crash route, which wakes somebody up to deal with errors.")
