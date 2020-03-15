import flask, geocoder, os, json
from ..util import misc, con

APP = flask.Blueprint('user', __name__)

@APP.route('/home')
@misc.require_session
def home():
  userid = flask.g.session_body['userid']
  with con.withcon() as dbcon, dbcon.cursor() as cur:
    cur.execute('select name, age, address from users where userid = %s', (userid,))
    name, age, address = cur.fetchone()
    cur.execute(
      """with role_insts as (select instid from inst_roles where userid = %s),
      member_insts as (select instid from memberships where userid = %s)
      select instid, name, url, kind from institutions where instid in (select instid from role_insts) or instid in (select instid from member_insts)
      """,
      (userid, userid)
    )
    insts = cur.fetchall()
    cur.execute(
      'select institutions.name, institutions.instid, groups.groupid from group_members join groups using (groupid) join institutions using (instid) where userid = %s',
      (userid,)
    )
    groups = cur.fetchall()
  return flask.render_template('home.htm', email=flask.g.session_body['email'], name=name, age=age, address=address, insts=insts, groups=groups)

@APP.route('/delete')
@misc.require_session
def delete_me():
  "delete a user, move them to deleted_users table so we can reconstruct as needed"
  with con.withcon() as dbcon, dbcon.cursor() as cur:
    userid = flask.g.session_body['userid']
    cur.execute('select created, modified from users where userid = %s', (userid,))
    created, modified = cur.fetchone()
    cur.excute(
      'insert into deleted_users (userid, email, orig_created, orig_modified) values (%s, %s, %s, %s)',
      (userid, flask.g.session_body['userid'], created, modified)
    )
    cur.execute('delete from users where userid = %s', (userid,))
    dbcon.commit()
  con.REDIS.delete(misc.session_key(flask.session['sessionid']))
  del flask.session['sessionid'] # todo: clear session completely instead
  return flask.redirect(flask.url_for('auth.get_login'))

@APP.route('/edit', methods=['POST'])
@misc.require_session
def edit_field():
  body = flask.request.json
  assert body['field'] in ('name', 'age', 'address')
  val = int(body['val']) if body['field'] == 'age' else body['val']
  with con.withcon() as dbcon, dbcon.cursor() as cur:
    cur.execute(f'update users set {body["field"]} = %s, modified = now() where userid = %s', (val, flask.g.session_body['userid']))
    dbcon.commit()
  if body['field'] == 'address':
    ret = geocoder.google(body['val'], key=os.environ['GEOCODING_API_KEY'])
    if ret.status != 'OK':
      raise NotImplementedError('geocoding error', ret.response)
    with con.withcon() as dbcon, dbcon.cursor() as cur:
      cur.execute(f'update users set geo = %s, modified = now() where userid = %s', (json.dumps(ret.json), flask.g.session_body['userid']))
      dbcon.commit()
    # todo: enqueue this instead of inline processing
    # todo: better error handling & show status to user
  return flask.jsonify({'ok': True, 'body': body})
