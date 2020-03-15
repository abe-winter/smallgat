import functools, flask, json, uuid
from . import con

EXPIRE_SESSION = 3600 * 24 * 60

class RateError(Exception):
  "flask will catch these and show a nice page"

class FancyError(Exception):
  "show a nice page with message"
  # todo: actually show a nice page

def try_rate(name, count, bucket, value=None, crash=True):
  """Crashes or returns false (depending on crash param) if rate exceeded.
  name: name of the rate-limiter
  count: number allowed per bucket
  bucket: bucket size in second or minute ('1s', '5m')
  value: value to sub-bucket -- okay to leave null for global
  """
  # todo: make this not a no-op
  # todo: alert when exceeded
  # todo: provide an efficient way to check several of these at once
  return True

def external_ip():
  # todo
  return None

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
