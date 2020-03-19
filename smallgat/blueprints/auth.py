"magic link functionality"

import flask, uuid, json, logging, scrypt, os
from ..util import email, misc, con, rates

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

VERIFY_EMAIL_BODY = """<html><body>
<p>Thanks for joining! Follow this link to verify your email address.</p>
<p><a href="{link}">{link}</a></p>
<p>This link expires in 30 minutes, but you can resend it from <a href="{home_url}">your homepage</a> if that happens.</p>
<p>Also, if you click multiple times, only the last one will work.</p>
</body></html>"""

RATE_LOGIN = rates.MemRateLimiter(1000, 60)
RATE_LOGIN_IP = rates.MemValueLimiter(10, 60)
# todo: move email one to redis so it's cluster-global
RATE_LOGIN_EMAIL = rates.MemValueThrottle(1, 60)

EMAIL_MAXLEN = 256

def common_create_check(email_addr):
  "common guard logic for magic / non-magic logins"
  if len(email_addr) > EMAIL_MAXLEN:
    misc.abort_msg(400, 'email too long', 'Emails have to be less than 256 letters')
  misc.abort_rate('Global logins exceeded', RATE_LOGIN)
  misc.abort_rate('Per-IP logins exceeded', RATE_LOGIN_IP, misc.external_ip())

@APP.route('/login', methods=['POST'])
def post_login():
  email_addr = flask.request.form['email']
  common_create_check(email_addr)
  misc.abort_rate('Per-email logins exceeded', RATE_LOGIN_EMAIL, misc.normalize_email(email_addr))
  user_key = misc.rkey('ulog', email_addr)
  val = con.REDIS.get(user_key)
  if val:
    misc.abort_msg(400, "Login already in progress", "You already have an open login request -- check your email")
  body = {
    'email': email_addr,
    'magic': str(uuid.uuid4()),
  }
  email.send_email(email_addr, 'Magic login link', LINK_EMAIL_BODY.format(
    link=flask.url_for('auth.redeem_magic', key=body['magic'], _external=True, _scheme='https'),
    login_url=flask.url_for('auth.get_login', _external=True, _scheme='https'),
  ))
  con.REDIS.setex(user_key, EXPIRE_MAGIC, json.dumps(body))
  con.REDIS.setex(misc.rkey('magic', body['magic']), EXPIRE_MAGIC, json.dumps(body))
  return flask.render_template('ok_login.htm')

PASS_METH = 'password'

@APP.route('/join-pass', methods=['POST'])
def create_pass():
  "create account with password"
  form = flask.request.form
  if len(form['password']) < 3:
    misc.abort_msg(400, "Password too short", "Longer please")
  common_create_check(form['email'])
  with con.withcon() as dbcon, dbcon.cursor() as cur:
    cur.execute('select 1 from users where email = %s', (form['email'],))
    row = cur.fetchone()
    if row:
      misc.abort_msg(403, "Account already exists", "We already have an account for that email address.")
    salt = os.urandom(64)
    pass_hash = scrypt.hash(form['password'].encode(), salt)
    cur.execute('insert into users (email, auth_meth, pass_hash, pass_salt) values (%s, %s, %s, %s)', (form['email'], PASS_METH, pass_hash, salt))
    dbcon.commit()
  send_verify(form['email'])
  return flask.render_template('ok_create_pass.htm', email=form['email'])

@APP.route('/login-pass', methods=['POST'])
def login_pass():
  "login with password"
  form = flask.request.form
  common_create_check(form['email'])
  misc.abort_rate('Per-email logins exceeded', RATE_LOGIN_EMAIL, misc.normalize_email(form['email']))
  with con.withcon() as dbcon, dbcon.cursor() as cur:
    cur.execute('select userid, auth_meth, pass_hash, pass_salt from users where email = %s', (form['email'],))
    row = cur.fetchone()
  if not row:
    misc.abort_msg(404, "No such account", "Couldn't find that account, sorry")
  userid, auth_meth, pass_hash, salt = row
  if auth_meth != PASS_METH:
    misc.abort_msg(400, "Wrong login method", "This isn't a password-based account -- did you create it with magic link login?")
  if pass_hash.tobytes() != scrypt.hash(form['password'].encode(), salt.tobytes()):
    misc.abort_msg(403, "Wrong password", "Wrong password probably, use your back button and try again")
  flask.session['sessionid'] = misc.create_redis_session(userid, form['email'])
  return flask.redirect(flask.url_for('user.home'))

MAGIC_METH = 'magic'

def lookup_or_create_magic_user(email_addr):
  "returns userid"
  with con.withcon() as dbcon, dbcon.cursor() as cur:
    cur.execute('select userid, auth_meth from users where email = %s', (email_addr,))
    row = cur.fetchone()
    if row is not None:
      if row[1] != MAGIC_METH:
        misc.abort_msg(400, "Wrong login method", "You can't sign in with a magic link for a password-based account")
      return row[0]
    logging.info('creating magic user %s', email_addr)
    cur.execute('insert into users (email, auth_meth, email_verified) values (%s, %s, true) returning userid', (email_addr, MAGIC_METH))
    userid, = cur.fetchone()
    dbcon.commit()
    return userid

RATE_REDEEM = rates.MemRateLimiter(1000, 60)
RATE_REDEEM_IP = rates.MemValueLimiter(10, 60)

@APP.route('/magic/<uuid:key>')
def redeem_magic(key):
  misc.abort_rate('Global link redeems exceeded', RATE_REDEEM)
  misc.abort_rate('Per-IP link redeems exceeded', RATE_REDEEM_IP, misc.external_ip())
  # warning: fun race conditions here
  magic_key = misc.rkey('magic', str(key))
  raw = con.REDIS.get(magic_key)
  if not raw:
    misc.abort_msg(400, "Bad or expired link", "Hi! You clicked a bad or expired magic link. Re-send from your homepage.")
  body = json.loads(raw)
  con.REDIS.delete(magic_key)
  con.REDIS.delete(misc.rkey('ulog', body['email']))
  userid = lookup_or_create_magic_user(body['email'])
  # todo: store list of active sessions somewhere so user can audit devices
  flask.session['sessionid'] = misc.create_redis_session(userid, body['email'])
  return flask.redirect(flask.url_for('user.home'))

RATE_REDEEM_V = rates.MemRateLimiter(1000, 60)
RATE_REDEEM_V_IP = rates.MemValueLimiter(10, 60)

@APP.route('/verify/<uuid:key>')
def redeem_verify(key):
  misc.abort_rate('Global verifies exceeded', RATE_REDEEM_V)
  misc.abort_rate('Per-IP verifies exceeded', RATE_REDEEM_V_IP, misc.external_ip())
  vkey = misc.rkey('verify-key', str(key))
  raw = con.REDIS.get(vkey)
  if not raw:
    misc.abort_msg(400, "Bad or expired link", "Hi! You clicked a bad or expired verification link. Re-send from your homepage.")
  body = json.loads(raw)
  con.REDIS.delete(vkey)
  con.REDIS.delete(misc.rkey('ulog-pass', body['email']))
  with con.withcon() as dbcon, dbcon.cursor() as cur:
    cur.execute('update users set email_verified = true where email=%s', (body['email'],))
    dbcon.commit()
  return flask.redirect(flask.url_for('user.home'))

@APP.route('/logout', methods=['POST'])
@misc.require_session
def post_logout():
  sessionid = flask.session.pop('sessionid')
  con.REDIS.delete(misc.session_key(sessionid))
  return flask.redirect(flask.url_for('user.home'))

RATE_VERIFY = rates.MemRateLimiter(1000, 60)
RATE_VERIFY_IP = rates.MemValueLimiter(10, 60)
# todo: move email one to redis so it's cluster-global
RATE_VERIFY_EMAIL = rates.MemValueThrottle(1, 60)

def send_verify(addr):
  "send verification email for non-magic case (i.e. password login)"
  misc.abort_rate('Global rate exceeded', RATE_VERIFY)
  misc.abort_rate('Per-IP rate exceeded', RATE_VERIFY_IP, misc.external_ip())
  misc.abort_rate('Per-email rate exceeded', RATE_VERIFY_EMAIL, misc.normalize_email(addr))
  user_key = misc.rkey('ulog-pass', addr)
  body = {
    'email': addr,
    'verify-key': str(uuid.uuid4()),
  }
  con.REDIS.setex(user_key, EXPIRE_MAGIC, json.dumps(body))
  con.REDIS.setex(misc.rkey('verify-key', body['verify-key']), EXPIRE_MAGIC, json.dumps(body))
  email.send_email(addr, 'Verify your email address', VERIFY_EMAIL_BODY.format(
    link=flask.url_for('auth.redeem_verify', key=body['verify-key'], _external=True, _scheme='https'),
    home_url=flask.url_for('user.home', _external=True, _scheme='https'),
  ))
  return flask.render_template('ok_send_verify.htm')

@APP.route('/reverify', methods=['POST'])
@misc.require_session
def reverify():
  "send verification email"
  return send_verify(flask.g.session_body['email'])
