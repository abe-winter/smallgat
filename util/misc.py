class RateError(Exception):
  "flask will catch these and show a nice page"

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
