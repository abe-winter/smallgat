"magic link functionality"

import flask, uuid, json, logging
from ..util import email, misc, con

APP = flask.Blueprint('auth', __name__)

EXPIRE_MAGIC = 30 * 60

@APP.route('/login')
def get_login():
  return flask.render_template('login.htm')

LINK_EMAIL_BODY = """<html><body>
<p>Thanks for logging in / signing up!</p>
<p><a href="{link}">{link}</a></p>
<p>This link will expire in 30 minutes, just <a href="{login_url}">log in again</a> if that happens.</p>
</body></html>"""

@APP.route('/login', methods=['POST'])
def post_login():
  email_addr = flask.request.form['email']
  if len(email_addr) > 256:
    # todo: show to user
    raise ValueError('email too long')
  misc.try_rate('login', 1000, '1m')
  misc.try_rate('login.ip', 10, '1m', misc.external_ip())
  misc.try_rate('login.email', 1, '10s', email_addr) # todo: normalize email here
  user_key = misc.rkey('ulog', email_addr)
  val = con.REDIS.get(user_key)
  if val:
    raise misc.RateError("you already have an open login request -- check your email")
  body = {
    'email': email_addr,
    'magic': str(uuid.uuid4()),
  }
  # todo: make sure this keeps https in prod
  email.send_email(email_addr, 'Magic login link', LINK_EMAIL_BODY.format(
    link=flask.url_for('auth.redeem_magic', key=body['magic'], _external=True),
    login_url=flask.url_for('auth.get_login', _external=True),
  ))
  con.REDIS.setex(user_key, EXPIRE_MAGIC, json.dumps(body))
  con.REDIS.setex(misc.rkey('magic', body['magic']), EXPIRE_MAGIC, json.dumps(body))
  return flask.render_template('ok_login.htm')

def lookup_or_create_user(email_addr):
  "returns userid"
  with con.withcon() as dbcon, dbcon.cursor() as cur:
    cur.execute('select userid from users where email = %s', (email_addr,))
    row = cur.fetchone()
    if row is not None:
      return row[0]
    logging.info('creating user %s', email_addr)
    cur.execute('insert into users (email) values (%s) returning userid', (email_addr,))
    userid, = cur.fetchone()
    dbcon.commit()
    return userid

@APP.route('/magic/<uuid:key>')
def redeem_magic(key):
  misc.try_rate('redeem', 1000, '1m')
  misc.try_rate('redeem.ip', 10, '1m', misc.external_ip())
  # warning: fun race conditions here
  magic_key = misc.rkey('magic', str(key))
  raw = con.REDIS.get(magic_key)
  if not raw:
    raise ValueError("todo: tell user bad link, give instructions")
  body = json.loads(raw)
  con.REDIS.delete(magic_key)
  con.REDIS.delete(misc.rkey('ulog', body['email']))
  userid = lookup_or_create_user(body['email'])
  # todo: store list of active sessions somewhere so user can audit devices
  flask.session['sessionid'] = misc.create_redis_session(userid, body['email'])
  return flask.redirect(flask.url_for('user.home'))

@APP.route('/logout', methods=['POST'])
@misc.require_session
def post_logout():
  sessionid = flask.session.pop('sessionid')
  con.REDIS.delete(misc.session_key(sessionid))
  return flask.redirect(flask.url_for('user.home'))
