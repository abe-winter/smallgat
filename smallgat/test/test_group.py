import pytest, collections, geopy
from ..blueprints import group

@pytest.fixture
def igroup():
  igroup = group.InstGroups()
  igroup.users = {
    'a': group.User('a', 'group', 1, 1),
    'b': group.User('b', 'group', 1, 1),
    'c': group.User('c', 'group', 1, 1),
    'd': group.User('d', None, 2, 2),
    'e': group.User('e', None, 2, 2),
    'f': group.User('f', None, 2, 2),
    'g': group.User('g', None, 1, 1),
    'h': group.User('h', None, 1.001, 1.001),
  }
  igroup.groups = collections.defaultdict(list)
  for user in igroup.users.values():
    if user.groupid:
      igroup.groups[user.groupid].append(user.userid)
  return igroup

def test_centroid(igroup):
  assert igroup.centroid('abc') == geopy.Point(1, 1)

def test_open_group(igroup):
  assert igroup.open_group('g', 3, 0.5) == []
  assert igroup.open_group('g', 4, 0.5) == [(0, 'group')]
  assert igroup.open_group('h', 4, 0.05) == []
  assert igroup.open_group('h', 4, 1) == [(0.09748801418021727, 'group')]

def test_construct_group(igroup):
  # def construct_group(self, userid, group_size, radius):
  assert igroup.construct_group('g', 0.5) == [(0.09748801418021727, 'h')]
  assert igroup.construct_group('d', 0.5) == [(0, 'e'), (0, 'f')]
