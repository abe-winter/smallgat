import flask
from ..util import misc

APP = flask.Blueprint('user', __name__)

@APP.route('/home')
@misc.require_session
def home():
  return f'hello {flask.g.session_body["email"]}'
