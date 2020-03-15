import flask, geopy.distance, collections, itertools, logging, psycopg2.extras
from ..util import misc, con

APP = flask.Blueprint('group', __name__)

User = collections.namedtuple('User', 'userid groupid lat lng')

class InstGroups:
  "represents users and groups for an institution and permits some distance queries"
  def __init__(self):
    self.groups = collections.defaultdict(list)
    self.users = {}

  def load(self, cur, instid):
    "load raw user / group / geo rows for institution"
    cur.execute(
      'select userid, groupid from users join group_members using (userid) join groups using (groupid) where instid = %s',
      (instid,)
    )
    user_groups = {userid: groupid for userid, groupid in cur.fetchall()}
    cur.execute("""select userid, geo->>'lat', geo->>'lng' from users
      left join memberships using (userid)
      where instid = %s and geo is not null
      """,
      (instid,)
    )
    for userid, lat, lng in cur.fetchall():
      user = User(userid, user_groups.get(userid), lat, lng)
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
    distances.sort()
    return distances

  def construct_group(self, userid, radius):
    "construct a group from closest not-spoken-for users inside radius"
    own_user = self.users[userid]
    user_loc = geopy.Point(own_user.lat, own_user.lng)
    distances = []
    for user in self.users.values():
      if user.groupid or str(user.userid) == userid:
        continue
      distance = geopy.distance.distance(
        user_loc,
        geopy.Point(user.lat, user.lng)
      )
      if distance.miles <= radius:
        distances.append((distance.miles, user.userid))
    distances.sort()
    return distances

def create_group(cur, instid, userids):
  "confirm users aren't in groups, create a group, return new groupid"
  cur.execute(
    'select userid from group_members join groups using (groupid) where instid = %s and userid in %s',
    (instid, userids)
  )
  already_assigned = [userid for userid, in cur.fetchall()]
  if already_assigned:
    logging.info('removing %d already_assigned from %d users', len(already_assigned), len(userids))
    userids = list(set(userids) - set(already_assigned))
  if not userids:
    raise NotImplementedError('todo: fancy error for race condition')
  cur.execute('insert into groups (instid) values (%s) returning groupid', (instid,))
  groupid, = cur.fetchone()
  print('userids', userids)
  psycopg2.extras.execute_batch(
    cur,
    'insert into group_members (groupid, userid) values (%s, %s)',
    [(groupid, userid) for userid in userids]
  )
  # todo: notify by email, and do it in a queue
  return groupid

def assign_group(cur, groupid, userid, group_size):
  "add user to group, fail if full"
  raise NotImplementedError

@APP.route('/find/<uuid:instid>', methods=['POST'])
@misc.require_session
def find_group(instid):
  """Find a group to join.
    In theory this is a clustering problem but assuming users join in a staggered
    way, I'm taking a 'find nearest not spoken for' approach.
  """
  userid = flask.g.session_body['userid']
  max_miles = float(flask.request.form['max_miles'])
  with con.withcon() as dbcon, dbcon.cursor() as cur:
    # todo: check complete user
    cur.execute('select 1 from memberships where instid = %s and userid = %s', (str(instid), userid))
    if not cur.fetchone():
      flask.abort(403) # todo: message 'you're already in a group'
    cur.execute('select group_size from institutions where instid = %s', (str(instid),))
    group_size, = cur.fetchone()
    groups = InstGroups().load(cur, str(instid))
  open_groups = groups.open_group(userid, group_size, max_miles)
  if open_groups:
    groupid = open_groups[0][0]
    with con.withcon() as dbcon, dbcon.cursor() as cur:
      assign_group(cur, groupid, userid, group_size)
      dbcon.commit()
    return flask.redirect(flask.url_for('group.view', groupid=groupid))
  people = groups.construct_group(userid, max_miles)
  if len(people):
    group_userids = (userid,) + list(zip(*people))[1]
    with con.withcon() as dbcon, dbcon.cursor() as cur:
      groupid = create_group(cur, str(instid), group_userids[:group_size])
      dbcon.commit()
    return flask.redirect(flask.url_for('group.view', groupid=groupid))
  return flask.render_template('checkback.htm')

@APP.route('/leave/<uuid:groupid>', methods=['POST'])
@misc.require_session
def leave(groupid):
  with con.withcon() as dbcon, dbcon.cursor() as cur:
    cur.execute('select instid from groups where groupid = %s', (str(groupid),))
    instid, = cur.fetchone()
    cur.execute('delete from group_members where groupid = %s and userid = %s', (str(groupid), flask.g.session_body['userid']))
    dbcon.commit()
  return flask.redirect(flask.url_for('institution.inst', instid=instid))

@APP.route('/view/<uuid:groupid>')
@misc.require_session
def view(groupid):
  with con.withcon() as dbcon, dbcon.cursor() as cur:
    cur.execute('select userid, name, email from group_members join users using (userid) where groupid = %s', (str(groupid),))
    members = cur.fetchall()
    if not any(row[0] == flask.g.session_body['userid'] for row in members):
      flask.abort(403)
    cur.execute('select groups.instid, name from groups join institutions using (instid) where groupid = %s', (str(groupid),))
    instid, name = cur.fetchone()
  return flask.render_template('group.htm', members=members, own_userid=flask.g.session_body['userid'], groupid=groupid, instid=instid, inst_name=name)
