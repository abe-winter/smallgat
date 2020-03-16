import functools, flask, json, uuid, re
from . import con

EXPIRE_SESSION = 3600 * 24 * 60

class RateError(Exception):
  "flask will catch these and show a nice page"

class FancyError(Exception):
  "show a nice page with message"
  # todo: actually show a nice page

ABORT_MESSAGE = """<html>
<head>
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
      ABORT_MESSAGE.format(message=message, maxrate=limiter.render_rate()),
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
