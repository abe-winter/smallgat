import flask, geopy, collections, itertools
from ..util import misc, con

APP = flask.Blueprint('group', __name__)

User = collections.namedtuple('User', 'userid groupid lat lng')

class InstGroups:
  "represents users and groups for an institution and permits some distance queries"
  def __init__(self, instid):
    self.instid = instid
    self.groups = collections.defaultdict(list)
    self.users = {}

  def load(self, cur, instid):
    "load raw user / group / geo rows for institution"
    cur.execute("""select userid, groupid, geo->>'lat', geo->>'lng' from users
      left join memberships using (userid)
      where inst = %s and geo is not null
      """,
      (instid,)
    )
    for user in itertools.starmap(User, cur.fetchall()):
      self.users[user.userid] = user
      if user.groupid:
        self.groups[user.userid].append(user.userid)
    return self

  def centroid(self, userids):
    "helper to get approx centroid for list of users"
    # todo: there's a lot wrong with using average as centroid (bad weighting, breaks at the meridian)
    users = [self.users[userid] for userid in userids]
    return geopy.Point(
      latitude=sum(user.lat for user in users) / len(users),
      longitude=sum(user.lng for user in users) / len(users)
    )

  def open_group(self, userid, group_size, radius):
    "find an open group with centroid in radius"
    user = self.users[userid]
    user_loc = geopy.Point(user.lat, user.lng)
    distances = []
    for groupid, userids in self.groups.items():
      if len(userids) < group_size:
        centroid = self.centroid(userids)
        distance = geopy.distance.distance(user_loc, centroid)
        if distance.miles <= radius:
          distances.append((distance.miles, groupid))
    if distances:
      distances.sort()
      return distances[0][1]
    return None

  def construct_group(self, userid, group_size, radius):
    "construct a group from closest not-spoken-for users inside radius"
    own_user = self.users[userid]
    user_loc = geopy.Point(own_user.lat, own_user.lng)
    distances = []
    for userid, user in self.users.items():
      if user.groupid or user.userid == userid:
        continue
      distance = geopy.distance.distance(
        user_loc,
        geopy.Point(user.lat, user.lng)
      )
      if distance.miles <= radius:
        distances.append((distance.miles, userid))
    if distances:
      distances.sort()
      return distances[0][1]
    return None

@APP.route('/find/<uuid:instid>')
@misc.require_session
def find_group(instid):
  """Find a group to join.
    In theory this is a clustering problem but assuming users join in a staggered
    way, I'm taking a 'find nearest not spoken for' approach.
  """
  with con.withcon() as dbcon, dbcon.cursor() as cur:
    cur.execute('select 1 from memberships where instid = %s and userid = %s', (str(instid), flask.g.session_body['userid']))
    if not cur.fetchone():
      raise NotImplementedError('todo 403')
    groups = InstGroups(str(instid)).load(cur, str(instid))
  print(groups)
  raise NotImplementedError
  # form['max_miles']
  # inst.group_size
  # load all users & groups
  # find nearby groups with centroid in radius and open space
  # find N nearest users
