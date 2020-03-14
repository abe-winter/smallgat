"flask / gunicorn entrypoint"

import flask

from .blueprints import auth

app = flask.Flask(__name__)

@app.route('/')
def splash():
  return flask.render_template('splash.htm')
