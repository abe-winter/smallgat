"rate-limiting primitives"
# todo: pick a library for this

import collections, time

class MemRateLimiter:
  maxobs: int
  window_sec: int
  deque: collections.deque
  # todo: read docs and confirm that this still has mem saving in py3
  __slots__ = ('maxobs', 'window_sec', 'deque')

  def __init__(self, maxobs, window_sec):
    self.maxobs = maxobs
    self.window_sec = window_sec
    self.deque = collections.deque(maxlen=maxobs)

  def prune(self, now):
    "clean up old values"
    if self.deque:
      if now - self.deque[-1] > self.window_sec:
        self.deque.clear()
      else:
        while self.deque and now - self.deque[0] > self.window_sec:
          self.deque.popleft()

  def try_push(self, now=None) -> bool:
    "pass in `now` param for unit tests. returns True if not rate-limited, False if full"
    # todo: redesign this to bucket by second
    now = now or time.time()
    self.prune(now)
    if len(self.deque) >= self.maxobs:
      return False
    self.deque.append(now)
    return True

  def render_rate(self):
    return f'{self.maxobs} per {self.window_sec} second(s)'

TimePair = collections.namedtuple('TimePair', 'time val')

class RotatableDict:
  def __init__(self, now):
    self.dicts = collections.deque(
      [TimePair(now, {}), TimePair(now, {})],
      maxlen=2
    )

  def rotate(self, now, window_sec) -> bool:
    """rotate older dict; this is to prevent needing a culling mechanism.
    return True means it was rotated.
    """
    if now - self.dicts[0].time > window_sec:
      # note: because of deque maxlen, this also rotates out the older dict
      self.dicts.append(TimePair(now, {}))
      return True
    return False

  def __getitem__(self, key):
    "get value from dicts, newest to oldest"
    for pair in reversed(self.dicts):
      val = pair.val.get(key)
      if val is not None:
        return val
    return None

  def __setitem__(self, key, val):
    self.dicts[-1].val[key] = val

class MemValueThrottle:
  """rate-limiter variant that prevents more than 1
  (efficient variant of MemValueLimiter for 1-per-bucket case)
  to prevent this from getting overwhelmed by many-value DDOS, this must be behind a non-value rate limit.
  """
  def __init__(self, window_sec, now=None):
    now = now or time.time()
    self.window_sec = window_sec
    self.dicts = RotatableDict(now)

  def rotate(self, now):
    return self.dicts.rotate(now, self.window_sec)

  def try_push(self, key, now=None):
    "returns True if rate is not limited, False if full"
    now = now or time.time()
    self.rotate(now)
    prev = self.dicts[key]
    if prev is not None and now - prev < self.window_sec:
      return False
    self.dicts[key] = now
    return True

  def render_rate(self):
    return f'1 per {self.window_sec} second(s)'

class MemValueLimiter:
  "rate-limiter variant that keeps a MemRateLimiter per value"
  maxobs: int
  window_sec: int
  dicts: RotatableDict

  def __init__(self, maxobs, window_sec, now=None):
    now = now or time.time()
    self.maxobs = maxobs
    self.window_sec = window_sec
    self.dicts = RotatableDict(now)

  def try_push(self, key, now=None):
    "returns True if not limited"
    now = now or time.time()
    self.dicts.rotate(now, self.window_sec)
    limiter = self.dicts[key]
    if limiter is None:
      limiter = self.dicts[key] = MemRateLimiter(self.maxobs, self.window_sec)
    return limiter.try_push(now)

  def render_rate(self):
    return f'{self.maxobs} per {self.window_sec} second(s)'
