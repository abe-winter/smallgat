import functools, flask, json, uuid, re
from . import con

EXPIRE_SESSION = 3600 * 24 * 60

class RateError(Exception):
  "flask will catch these and show a nice page"

class FancyError(Exception):
  "show a nice page with message"
  # todo: actually show a nice page
  # todo: replace this everywhere with abort(response, status=)

ERR_TEMPLATE = """<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
</head>
<body>
<h3>🚨 Error: {title}</h3>
<p>{msg}</p>
<hr>
<p>Email support@smallgatherings.app if something seems fishy about this.</p>
</html>
"""

def abort_msg(status, title, msg):
  "helper to abort with status code and user-visible error"
  flask.abort(flask.Response(
    ERR_TEMPLATE.format(title=title, msg=msg),
    status=400
  ))

RATE_ERROR_MSG = """<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Error: rate limit</title>
</head>
<body>
  <h3>Error: you hit a rate limit</h3>
  <p>This could be because you personally are sending us too much traffic, or it could be because of global traffic to the site. Either way, set a timer on your phone and come back in a few minutes.</p>
  <p>If this keeps happening, tell support@smallgatherings.app.</p>
  <p>Details: {message}</p>
  <p>Max rate: {maxrate}</p>
</body>
</html>"""

def abort_rate(message, limiter, *args):
  "calls flask.abort with message if rate limit exceeded. passes down *args"
  if not limiter.try_push(*args):
    flask.abort(flask.Response(
      RATE_ERROR_MSG.format(message=message, maxrate=limiter.render_rate()),
      content_type='text/html',
      status=429
    ))

RE_PLUS_EMAIL = re.compile(r'^([^@\+]+)\+[^@]+(@[^@]+)$')

def normalize_email(raw):
  "normalize gmail addresses"
  match = RE_PLUS_EMAIL.match(raw)
  if not match:
    return raw
  groups = match.groups()
  return f'{groups[0]}{groups[1]}'

def external_ip():
  return flask.request.remote_addr

def rkey(key, val):
  "helper to format json-based redis keys"
  return json.dumps({'k': key, 'v': val}, sort_keys=True)

def session_key(sessionid):
  return rkey('sesh', sessionid)

def create_redis_session(userid, email_addr):
  "returns sessionid"
  sessionid = str(uuid.uuid4())
  con.REDIS.setex(
    session_key(sessionid),
    EXPIRE_SESSION,
    json.dumps({'email': email_addr, 'userid': userid})
  )
  return sessionid

def require_session(inner):
  @functools.wraps(inner)
  def outer(*args, **kwargs):
    # todo: remember redirect page
    sessionid = flask.session.get('sessionid')
    if not sessionid:
      return flask.redirect(flask.url_for('auth.get_login'))
    raw = con.REDIS.get(session_key(sessionid))
    if not raw:
      return flask.redirect(flask.url_for('auth.get_login'))
    flask.g.session_body = json.loads(raw)
    return inner(*args, **kwargs)
  return outer

def complete_user(cur, userid):
  "has the user done all the setup steps -- this gates most site actions"
  # warning: duplicated logic in home.htm vue
  cur.execute('select name, age, address, email_verified from users where userid = %s', (userid,))
  row = cur.fetchone()
  return bool(row and all(row))

def abort_complete(cur, userid):
  "abort if non-complete user"
  if not complete_user(cur, userid):
    abort_msg(
      403,
      "Please complete your profile",
      f'You just did something that requires a complete profile. Go to your <a href="{flask.url_for("user.home")}">profile page</a> and fill in all the red / required fields.'
    )
