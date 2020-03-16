from ..util import rates

def test_mem_rate_limiter():
  lim = rates.MemRateLimiter(2, 2)
  lim.prune(1)
  assert lim.try_push(1)
  assert lim.try_push(1)
  assert not lim.try_push(1)
  assert not lim.try_push(2)
  assert lim.try_push(4)
  assert len(lim.deque) == 1

def test_MemValueThrottle():
  # class MemValueThrottle:
  lim = rates.MemValueThrottle(2, now=1)
  assert lim.dicts['hey'] is None
  lim.dicts['hey'] = 1
  assert lim.dicts['hey'] == 1
  assert not lim.rotate(1)
  assert not lim.try_push('hey', 1)
  assert lim.try_push('hey', 4)
  assert not lim.try_push('hey', 4)
  assert lim.try_push('hey2', 4)
  assert lim.dicts['hey'] == 4
  assert lim.rotate(7)

def test_MemValueLimiter():
  lim = rates.MemValueLimiter(2, 2, now=1)
  assert lim.try_push('one', 1)
  assert lim.try_push('one', 1)
  assert not lim.try_push('one', 1)
  assert lim.try_push('two', 1)
  assert lim.try_push('two', 1)
  assert not lim.try_push('two', 1)
  assert lim.try_push('one', 4)
