"magic link functionality"

import flask
from ..util import email

APP = flask.Blueprint('auth', __name__)

@APP.route('/login')
def get_login():
  raise NotImplementedError

@APP.route('/login', methods=['POST'])
def post_login():
  # already have one non-redeemed
  # email can't log in more than once per minute
  raise NotImplementedError

@APP.route('/magic/<uuid:key>')
def redeem_magic():
  # already redeemed
  raise NotImplementedError
