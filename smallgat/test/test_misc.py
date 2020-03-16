from ..util.misc import normalize_email

def test_normalize_email():
  raw = 'user.whatever@example.com'
  assert normalize_email(raw) == raw
  assert normalize_email('user.whatever+tail@example.com') == raw
